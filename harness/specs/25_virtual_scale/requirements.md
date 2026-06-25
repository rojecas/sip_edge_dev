# Requirements — Balanza Virtual DINI ARGEO DFWLI-2 para Desarrollo y Pruebas

> Feature 25 — virtual_scale
> Formato: EARS (Easy Approach to Requirements Syntax)

---

## R1

CUANDO se ejecuta `python src/tools/virtual_scale.py` con parámetros válidos, el sistema DEBE abrir el puerto serial especificado, cargar el dataset CSV indicado, y quedar a la escucha de comandos del protocolo DINI ARGEO DFWLI-2 (REXT, TARE, TMAN, ZERO, CLEAR) así como de entrada del teclado para el REPL interactivo.

---

## R2

CUANDO el sistema recibe `00REXT\r\n` por el puerto serial, el sistema DEBE responder con una cadena extendida en formato `01ST,1,<peso_actual>,PT 0.0,0,kg\r\n`, donde `<peso_actual>` corresponde al peso del sub-paso activo (muestra, mineral o vegetal) según el archivo CSV cargado.

---

## R3

CUANDO el sistema recibe `00TARE\r\n`, `00ZERO\r\n` o `00CLEAR\r\n` por el puerto serial, el sistema DEBE responder inmediatamente con `OK\r\n`.

---

## R4

CUANDO el sistema recibe `00TMAN<valor>\r\n` por el puerto serial (donde `<valor>` es un número decimal de hasta 8 caracteres), el sistema DEBE responder inmediatamente con `OK\r\n`.

---

## R5

CUANDO el sistema recibe `00REXT\r\n` y la columna `status_<sub_paso>` del CSV para el sub-paso activo contiene `ST`, el sistema DEBE responder inmediatamente sin demora artificial.

---

## R6

CUANDO el sistema recibe `00REXT\r\n` y la columna `status_<sub_paso>` del CSV para el sub-paso activo contiene `US`, el sistema DEBE esperar un intervalo aleatorio entre 200 milisegundos y 3 segundos antes de enviar la respuesta.

---

## R7

MIENTRAS el REPL interactivo está activo, el sistema DEBE aceptar las siguientes teclas de una sola pulsación (sin requerir Enter):
- `n` — avanzar a la siguiente medida completa (incrementar fila, resetear sub-paso a muestra)
- `p` — retroceder un sub-paso dentro de la medida actual (vegetal→mineral→muestra→medida anterior)
- `w` — solicitar un valor numérico por consola y usarlo como override del peso del sub-paso actual
- `g` — solicitar un número de índice por consola y saltar a esa medida (fila del CSV)
- `s` — mostrar el estado actual: dataset, fila/total, sub-paso, peso actual, modo override
- `q` — salir del programa
- `Espacio` o `d` — simular botón PRINT: enviar la lectura actual por el serial sin delay de estabilidad y sin avanzar el puntero

---

## R8

CUANDO el usuario presiona la tecla `p` en el REPL, el sistema DEBE retroceder un sub-paso: si el sub-paso actual es vegetal (índice 2), pasa a mineral (índice 1); si es mineral, pasa a muestra (índice 0); si es muestra, pasa al vegetal de la medida anterior (fila−1, sub-paso 2). El sistema NO DEBE permitir retroceder más allá de la primera medida (fila 0, sub-paso 0).

---

## R9

CUANDO el usuario presiona `Espacio` o `d` en el REPL, el sistema DEBE enviar la lectura actual por el puerto serial con status `ST` sin aplicar delay de estabilidad (incluso si el CSV indica `US`) y SIN avanzar el puntero de fila ni sub-paso.

---

## R10

El sistema DEBE cargar archivos CSV con exactamente 7 columnas en el siguiente orden: `status_muestra`, `peso_muestra`, `status_mineral`, `peso_mineral`, `status_vegetal`, `peso_vegetal`, `unit`. El separador DEBE ser coma (`,`). La primera línea DEBE contener los nombres de columna (header).

---

## R11

El sistema DEBE incluir 5 datasets pre-generados (A–E) de 50 medidas cada uno, para un total de 250 medidas, almacenados como archivos CSV individuales en una carpeta `data/readings/` con los nombres `dataset_A.csv`, `dataset_B.csv`, `dataset_C.csv`, `dataset_D.csv` y `dataset_E.csv`.

---

## R12

DONDE se especifique `--dataset <letra>` en la línea de comandos, el sistema DEBE cargar el dataset indicado (A, B, C, D o E, mayúscula o minúscula). SI no se especifica `--dataset`, el sistema DEBE cargar `dataset_A.csv` por defecto.

---

## R13

El script `src/tools/virtual_scale.py` DEBE aceptar los siguientes argumentos de línea de comandos:
- `--port` — ruta del puerto serial (por defecto `COM1`)
- `--baudrate` — velocidad en baudios (por defecto `9600`)
- `--dataset` — letra del dataset A–E (por defecto `A`)
- `--data-dir` — ruta a la carpeta que contiene los archivos CSV (por defecto `data/readings/`)

---

## R14

CUANDO se ejecuta `python src/tools/virtual_scale.py --help`, el sistema DEBE mostrar todos los parámetros configurables con sus descripciones y valores por defecto.

---

## R15

El sistema DEBE proporcionar el script `scripts/generate_readings.py` que genera los 5 datasets CSV (A–E) con las siguientes distribuciones estadísticas:
- Dataset A: contaminación baja (pesos muestra ~200–350, mineral ~10–50, vegetal ~2–15)
- Dataset B: contaminación media (mineral ~30–120, vegetal ~10–50)
- Dataset C: contaminación alta con tendencia creciente en el tiempo
- Dataset D: outliers ocasionales en mineral y vegetal
- Dataset E: valores aleatorios con distribución uniforme dentro de rangos típicos

---

## R16

CUANDO se ejecuta `python scripts/generate_readings.py`, el sistema DEBE generar los 5 archivos CSV en `data/readings/` (o en la ruta especificada por `--output-dir`) utilizando el generador de números aleatorios `random` de la stdlib de Python.

---

## R17

SI el archivo CSV del dataset especificado no existe o no es legible, ENTONCES el sistema DEBE imprimir un mensaje de error en stderr y salir con código de retorno distinto de cero.

---

## R18

SI el puerto serial especificado no puede abrirse (puerto no existe, ocupado, o permisos insuficientes), ENTONCES el sistema DEBE imprimir un mensaje de error en stderr y salir con código de retorno distinto de cero.

---

## R19

SI la columna `status_<sub_paso>` del CSV contiene un valor distinto de `ST` o `US`, ENTONCES el sistema DEBE tratar ese valor como `ST` (estable, respuesta inmediata) y registrar una advertencia en stderr.

---

## R20

El sistema DEBE incluir documentación de conexión física en `docs/virtual_scale_setup.md` que describa:
- Componentes necesarios: workstation Windows, cable USB–RS232, conversor RS232/RS485, EdgeBox con puerto RS485
- Diagrama de conexión: `Workstation USB → RS232 → Conversor RS232/RS485 → EdgeBox RS485`
- Parámetros de puerto recomendados: baudrate 9600, 8 data bits, sin paridad, 1 stop bit
- Procedimiento de verificación de conectividad
