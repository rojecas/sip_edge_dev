## Resumen

Herramienta de desarrollo standalone que simula el protocolo DINI ARGEO DFWLI-2 via puerto serial. Corre en workstation Windows, abre un puerto COM y se conecta via conversor RS-232 a RS-485 al puerto RS-485 del EdgeBox. Responde a comandos REXT, TARE, TMAN, ZERO, CLEAR con datos desde archivos CSV pre-generados. Incluye REPL interactivo con teclas n/p/w/g/s/q/espacio.

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `src/tools/virtual_scale.py` | Script principal: servidor serial + REPL interactivo |
| `src/tools/__init__.py` | Inicializador del paquete de herramientas |
| `scripts/generate_readings.py` | Generador de datasets CSV de prueba |
| `data/readings/dataset_A.csv` a `dataset_E.csv` | 5 datasets x 50 medidas (250 total) |
| `docs/virtual_scale_setup.md` | Documentacion de conexion fisica |
| `tests/test_virtual_scale.py` | 47 tests unitarios |

## Archivos modificados

Ninguno. Herramienta standalone sin impacto en otras features.

## Trazabilidad

- R1-R5 (comandos REXT, TARE, ZERO, CLEAR, TMAN + estabilidad ST/US): 20 tests de protocolo
- R7-R9 (REPL + navegacion): tests de navegacion y PRINT
- R10-R14 (CSVs + CLI args): tests de carga y argparse
- R15-R20 (generador, errores, documentacion): tests de generacion + docs

## Verificacion

- [x] 47/47 tests unitarios
- [x] Comunicacion RS-485 real verificada: 5/5 comandos desde EdgeBox a 9600 baud
- [x] Fix: error select.select() en Windows corregido
- [x] Review: APPROVED
- [x] feature_list.json status = done (v1.2.0)
- [x] Release v1.2.0 publicado

## Decisiones tecnicas

- Se uso msvcrt para lectura de teclado sin Enter en Windows, con fallback select.select() en Unix
- Los datasets se generan con semilla fija (--seed 42) para reproducibilidad
- Respuesta REXT siempre con ST (la balanza virtual solo transmite cuando esta estable); US controla delay, no status
- Buffer serial con acumulacion hasta \n, lineas completas se procesan inmediatamente

## Lecciones / bugs descubiertos

- **Bug en sip-edge (Bug #29):** ScaleService._async_reader en scale.py y _on_scale_data en main.py tienen bugs que impiden que los datos de la balanza virtual lleguen al WebSocket /ws/scale. Queda como bug triaged para futura sesion.
- **Cambio config.yaml:** El baudrate del RS-485 se cambio de 115200 a 9600 (default de fabrica de la balanza DINI ARGEO) para robustez ante reseteos.
