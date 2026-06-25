# Design — Balanza Virtual DINI ARGEO DFWLI-2 para Desarrollo y Pruebas

> Feature 25 — virtual_scale

## Archivos nuevos

| Archivo | Propósito |
|---------|-----------|
| `src/tools/virtual_scale.py` | Script principal: servidor serial + REPL interactivo que simula balanza DINI ARGEO DFWLI-2 |
| `scripts/generate_readings.py` | Generador de datasets CSV de prueba |
| `data/readings/` | Carpeta contenedora de los 5 datasets CSV |
| `data/readings/dataset_A.csv` | Dataset A — contaminación baja (50 medidas) |
| `data/readings/dataset_B.csv` | Dataset B — contaminación media (50 medidas) |
| `data/readings/dataset_C.csv` | Dataset C — contaminación alta con tendencia (50 medidas) |
| `data/readings/dataset_D.csv` | Dataset D — outliers (50 medidas) |
| `data/readings/dataset_E.csv` | Dataset E — aleatoria uniforme (50 medidas) |
| `docs/virtual_scale_setup.md` | Documentación de conexión física y puesta en marcha |

## Archivos modificados

Ninguno. Esta feature es un **script standalone** que no modifica código de aplicación existente (`src/` principal), tests existentes, ni configuración del sistema.

## Arquitectura general

```
┌─────────────────────────────────────────────────────┐
│               src/tools/virtual_scale.py             │
│                                                     │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ CLI Args  │───▶│  Cargador CSV │───▶│  Puntero  │  │
│  │ (argparse)│    │  (datasets)   │    │ (row,sub) │  │
│  └──────────┘    └──────────────┘    └─────┬─────┘  │
│                                           │         │
│  ┌──────────────────┐    ┌────────────────┴──────┐  │
│  │  Keyboard REPL   │◀──▶│   Bucle Principal     │  │
│  │  (msvcrt: sin ENTER)  │   (select serial/stdin) │  │
│  └──────────────────┘    └──────────┬───────────┘  │
│                                     │               │
│  ┌──────────────────┐    ┌──────────┴───────────┐  │
│  │  Simulación      │    │  Manejador Serial    │  │
│  │  de Estabilidad  │◀──▶│  (pyserial)          │  │
│  │  (delay si US)   │    │                      │  │
│  └──────────────────┘    └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Flujo principal

1. Parsear argumentos CLI con `argparse` (`--port`, `--baudrate`, `--dataset`, `--data-dir`)
2. Cargar archivo CSV del dataset indicado en memoria como lista de dicts
3. Inicializar puntero: `row = 0`, `sub_step = 0` (0=muestra, 1=mineral, 2=vegetal)
4. Abrir puerto serial con `serial.Serial(port, baudrate, timeout=0.1)`
5. Entrar en bucle principal:
   - Leer datos del puerto serial (non-blocking con timeout corto)
   - Leer tecla del teclado (non-blocking con `msvcrt.kbhit()`)
   - Procesar comando serial o tecla

### Protocolo de respuestas

El script responde a comandos seriales según el protocolo documentado en `docs/Balance_Comm_procotol.md`:

| Comando recibido | Respuesta | Condiciones |
|-----------------|-----------|-------------|
| `00REXT\r\n` | `01ST,1,<peso>,PT 0.0,0,kg\r\n` | Si ST → inmediato; si US → delay 200ms–3s |
| `00TARE\r\n` | `OK\r\n` | Inmediato |
| `00TMAN<v>\r\n` | `OK\r\n` | Inmediato (no se persiste el valor de tara) |
| `00ZERO\r\n` | `OK\r\n` | Inmediato |
| `00CLEAR\r\n` | `OK\r\n` | Inmediato |

**Nota importante:** El status en la respuesta SIEMPRE es `ST` (la balanza virtual solo transmite cuando está estable). Los valores `US` en el CSV controlan únicamente el delay artificial, no el status de la respuesta.

## Estructura del puntero (row, sub_step)

El puntero de navegación es una tupla `(row: int, sub_step: int)`:

| sub_step | Columna status | Columna peso |
|----------|---------------|-------------|
| 0 | `status_muestra` | `peso_muestra` |
| 1 | `status_mineral` | `peso_mineral` |
| 2 | `status_vegetal` | `peso_vegetal` |

### Navegación

- **Tecla `n` (next):** si `sub_step < 2` → `sub_step += 1`; si `sub_step == 2` → `row += 1, sub_step = 0`. Si `row >= total_rows`, el puntero no avanza (se queda en la última medida).
- **Tecla `p` (previous):** si `sub_step > 0` → `sub_step -= 1`; si `sub_step == 0` → si `row > 0` → `row -= 1, sub_step = 2`; si `row == 0` → no retrocede.
- **Espacio/`d` (PRINT):** envía la lectura actual SIN modificar el puntero ni aplicar delay (simula botón físico).
- **Tecla `g`:** solicita un índice numérico (0–total_rows-1). Establece `row = índice, sub_step = 0`.
- **Tecla `w`:** solicita un valor flotante. Activa un flag `override_weight` con ese valor para el sub-paso actual. El peso override se transmite en lugar del valor del CSV. El override se descarta al avanzar el puntero.

## Formato de los CSV

```csv
status_muestra,peso_muestra,status_mineral,peso_mineral,status_vegetal,peso_vegetal,unit
ST,245.3,US,25.7,ST,8.2,kg
US,312.1,ST,45.3,US,12.8,kg
```

Los valores numéricos usan punto decimal. La columna `unit` es siempre `kg` para todos los datasets.

## REPL interactivo

### Implementación con `msvcrt`

En Windows, `msvcrt` permite lectura de teclado sin buffer ni Enter. El bucle principal usa `msvcrt.kbhit()` para detectar tecla y `msvcrt.getch()` para leerla.

### Mapa de teclas

| Tecla | Acción | Cubre |
|-------|--------|-------|
| `n` | Avanzar siguiente sub-paso o medida | R7 |
| `p` | Retroceder un sub-paso | R8 |
| `w` | Override de peso del sub-paso actual | R7 |
| `g` | Ir a medida específica (por índice) | R7 |
| `s` | Mostrar status actual en consola | R7 |
| `q` | Cerrar puerto serial y salir | R7 |
| `Espacio` / `d` | Simular PRINT: enviar sin delay ni avance | R9 |

### Status (`s`)

Muestra:
```
Dataset: A | Medida: 12/50 | Sub-paso: mineral (1/3)
Peso actual: 45.300 kg | Status CSV: US | Override: NO
Puerto: COM3 @ 9600 baud | Conectado: SI
```

## Simulación de estabilidad

- El dataset CSV contiene la columna `status_<sub_paso>` con valores `ST` o `US`.
- Cuando el comando `REXT` llega:
  - Si `status == ST`: respuesta inmediata (sin delay).
  - Si `status == US`: `time.sleep(random.uniform(0.2, 3.0))` antes de responder.
- La respuesta SIEMPRE lleva `status_code = ST` en la trama (la balanza virtual solo transmite cuando está estable, así que si hay US, espera y luego envía ST).

## Configuración del puerto serial

| Parámetro | Default | CLI flag |
|-----------|---------|----------|
| Port | `COM1` | `--port` |
| Baudrate | 9600 | `--baudrate` |
| Data bits | 8 | fijo |
| Parity | None | fijo |
| Stop bits | 1 | fijo |
| Timeout lectura | 0.1s | fijo (non-blocking poll) |

## Excepciones

No se introducen excepciones nuevas. El script usa:
- `serial.SerialException` — error de apertura/lectura/escritura del puerto (envuelto en mensaje a stderr)
- `SystemExit` — via `sys.exit(1)` en errores fatales
- `ValueError` — si el CSV contiene datos no numéricos donde se esperan números

## Distribuciones estadísticas de los datasets

Generador en `scripts/generate_readings.py` usando `random` de stdlib:

| Dataset | muestra | mineral | vegetal | Característica |
|---------|---------|---------|---------|----------------|
| A | 200–350 | 10–50 | 2–15 | Baja contaminación, mayormente ST |
| B | 200–350 | 30–120 | 10–50 | Media contaminación, ~40% US |
| C | 200–400 (creciente) | 50–200 (creciente) | 15–80 (creciente) | Alta contaminación, tendencia al alza |
| D | 180–350 | 8–300 (outliers 200–300) | 1–80 (outliers 40–80) | Outliers ocasionales |
| E | uniform(150, 400) | uniform(5, 300) | uniform(1, 100) | Aleatoria uniforme |

Cada dataset: 50 medidas, 3 sub-pasos = 150 lecturas individuales. Total: 250 medidas, 750 lecturas.

## Alternativa descartada

**Opción descartada: Web service REST + serial bridge.**

Se consideró implementar la balanza virtual como un servicio web (FastAPI) que actuara como bridge: recibiría peticiones HTTP y las traduciría a comandos seriales, o viceversa. Esto habría permitido probar la UI del kiosco sin hardware. Se descartó porque:
1. Introduce latencia y complejidad innecesaria (el objetivo es probar el protocolo serial, no la API HTTP).
2. Requiere modificar la aplicación existente (añadir modo virtual en ScaleService).
3. La balanza virtual debe comportarse como un dispositivo serial real en el mismo protocolo que la balanza física, para que el EdgeBox no distinga entre real y virtual.
4. Un script standalone es más simple, autocontenido y fácil de mantener.

**Opción descartada: pytest como driver de simulación.**

Se consideró usar pytest con fixtures para simular la balanza en tests. Se descartó porque pytest está diseñado para verificación, no para simulación interactiva en tiempo real. El REPL es necesario para que el desarrollador avance manualmente a través de las lecturas durante debugging.

## Persistencia

Esta feature NO toca la base de datos, no requiere migraciones, ni modifica configuraciones existentes.

## Impacto en APIs existentes

Ninguno. Esta feature es una herramienta de desarrollo standalone que no modifica ni consume APIs del backend.

## GitHub labels

`tooling`, `development`, `serial`, `dini-argeo`, `dfwli-2`, `simulation`, `testing-tool`
