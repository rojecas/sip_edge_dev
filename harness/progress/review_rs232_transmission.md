# Review — feature 11 (rs232_transmission)

**Veredicto:** APPROVED

## Trazabilidad requirements ↔ tests

| R<n> | Test | Estado |
|------|------|--------|
| R1 — POST /api/weighings invoca send_frame | test_create_weighing_sends_rs232 (test_weighings.py) | [x] |
| R2 — 15 campos CSV en orden literal | test_csv_format_15_fields (test_rs232.py) | [x] |
| R3 — Vagon sin modificación | test_vagon_unmodified (test_rs232.py) | [x] |
| R4 — Carga config desde config.yaml | test_config_loaded_and_used (test_rs232.py) | [x] |
| R5 — enviado_pc = True tras envío exitoso | test_create_weighing_sends_rs232 (test_weighings.py) | [x] |
| R6 — Error serial → logging, no relanza | test_error_on_port_unavailable (test_rs232.py), test_create_weighing_rs232_stub_import_error (test_weighings.py) | [x] |
| R7 — DEV_MODE omite E/S serial | test_dev_mode_skips_serial (test_rs232.py) | [x] |
| R8 — Trama termina con CRLF | test_crlf_termination (test_rs232.py) | [x] |
| R9 — Guía desde numero_guia | test_guia_from_numero_guia (test_rs232.py) | [x] |
| R10 — Pesos con 3 decimales | test_pesos_three_decimals (test_rs232.py) | [x] |

**Conclusión:** Todos los 10 requirements tienen cobertura de test. ✅

## Tasks completas

| Task | Descripción | Estado |
|------|-------------|--------|
| T1 | Crear src/rs232.py con send_frame() | [x] |
| T2 | Modificar _send_rs232_frame() en src/weighings.py | [x] |
| T3 | Crear tests/test_rs232.py con 8 unit tests | [x] |
| T4 | Modificar tests/test_weighings.py agregando test de integración | [x] |
| T5 | Ejecutar tests y verificar que todos pasan | [x] |

**Conclusión:** Todas las 5 tasks están marcadas [x] y completadas. ✅

## Verificación de tests

```
$ docker compose exec backend python -m unittest discover -s tests -v
Ran 310 tests in 218.984s
OK
```

Todos los 310 tests pasan sin errores. Sin regresiones. ✅

## Verificación del harness (init.ps1)

```
./init.ps1 → todos los bloques [OK], exit code 0
```

✅

## Arquitectura y convenciones

### src/rs232.py (CREADO) ✅
- Module docstring presente
- Rs232Error(Exception) como excepción base correcta
- send_frame() con firma según design.md
- DEV_MODE detection sigue el patrón de main.py y scale.py (case-insensitive)
- Import local de serial y load_config (mismo patrón que scale.py)
- Construcción CSV con f-strings, comillas dobles
- Apertura/cierre de puerto serial con try/finally garantizando cierre
- Excepciones SerialException y OSError envueltas como Rs232Error
- Sin print(), sin TODOs, sin archivos temporales

### src/weighings.py (MODIFICADO) ✅
- frame_data["id"] = record.id añadido correctamente
- format="json" → format="csv" actualizado
- Error logging con logger.error() (patrón %s por lazy eval, aceptable)
- Sin regresiones en el flujo de creación de pesaje

### tests/test_rs232.py (CREADO) ✅
- Module docstring, clase TestSendFrame(unittest.TestCase)
- Nombres de test siguen test_<funcion>_<escenario>
- Uso de tempfile.TemporaryDirectory() para config YAML real
- Uso de unittest.mock.patch para simular serial
- Sin mocks de sistema de archivos

### tests/test_weighings.py (MODIFICADO) ✅
- test_create_weighing_sends_rs232 añadido (cubre R1, R5)
- test_create_weighing_rs232_stub_import_error actualizado para usar mock

### SOLID ✅
- **S**: Cada función tiene una responsabilidad única
- **O**: El código es extensible mediante parámetros (config_path, format)
- **L**: Sin herencia problemática
- **I**: Interfaz limpia basada en dict
- **D**: Dependencias inyectadas via parámetros (config_path)

## Checkpoints (CHECKPOINTS.md)

| Checkpoint | Estado |
|------------|--------|
| C1 — Arnés completo | [x] |
| C2 — Estado coherente | [x] |
| C3 — Código respeta arquitectura | [x] |
| C4 — Verificación real | [x] |
| C5 — BD bajo control | [x] |
| C6 — Sesión limpia | [x] |
| C7 — SDD completo | [x] |
| C8 — Documentación histórica | [ ] (closure aún no creado — feature en in_progress) |
| C10 — GitHub sync | [ ] (ver sección GitHub sync) |
| C11 — Bug workflow | N/A (feature, no bug) |

## GitHub sync

harness/github.json tiene enabled: true, pero la feature #11 (rs232_transmission)
en estado in_progress **no tiene el campo github_issue** en harness/feature_list.json.

**Acción requerida:** El leader debe crear un issue en GitHub y agregar el campo
github_issue a feature #11 antes de marcar done.

## Hallazgos adicionales (no bloqueantes)

1. **Constante _DEV_MODES no implementada** (T1): El task menciona una constante
   pero el código implementa la detección inline, consistente con el design.md y
   los patrones existentes en main.py/scale.py. No requiere corrección.

2. **Sin test para el branch OSError** (R6): send_frame() tiene except OSError
   pero solo serial.SerialException se prueba. El spec solo requiere un test de
   error. Aceptable.

3. **Parámetro format sombrea builtin**: Acceptado explícitamente en design.md
   por compatibilidad con punto de llamada existente.

## Cambios requeridos (previo a marcar done)

1. [ ] Agregar github_issue a feature #11 en harness/feature_list.json con URL
   del issue creado en GitHub.
2. [ ] Crear harness/progress/closure-rs232_transmission.md al marcar done.

## Release

- [ ] La feature/bug esta lista para release-manager (closure existe)

---

**Resumen:** Código limpio, bien estructurado, sigue las convenciones del proyecto,
todos los tests pasan, todas las tasks completadas, todos los requirements tienen
cobertura de test. APROBADO con las notas de GitHub sync arriba indicadas.
