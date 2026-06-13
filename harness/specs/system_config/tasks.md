# Tasks — system_config

> Feature: Configuración del Sistema y Persistencia
> Cada task referencia al menos un R<n> que cubre.

---

## Bloque A: Infraestructura base

- [ ] T1 — Crear `src/config.py` con modelos Pydantic (`ScaleConfig`, `PCConfig`, `GSMConfig`, `ReportsConfig`, `SystemConfig`) y validaciones de campo (baudrate range, formato hora HH:MM, formato teléfono internacional). Cubre: R2, R3, R3.2, R9, R10.
- [ ] T2 — Crear `src/config_service.py` con clase `ConfigService`: método `load()` (leer/defaults), `save()` (validar + atomic write), `get_config()`. Cubre: R6, R7, R11.
- [ ] T3 — Crear `src/dependencies.py` con `get_config_service()` y placeholder `require_admin()`. Cubre: R7, R12.

## Bloque B: API Endpoints

- [ ] T4 — Crear `src/routers/__init__.py` y `src/routers/config.py` con endpoints:
  - `GET /api/config` → devuelve `SystemConfig` como JSON.
  - `PUT /api/config` → recibe `SystemConfig`, valida, guarda en `config_service.save()`.
  - `POST /api/config/test-scale` → prueba conexión serial RS485 báscula.
  - `POST /api/config/test-rs232` → prueba conexión serial RS232 PC.
  - `POST /api/config/test-gsm` → prueba conexión serial módem GSM.
  - Respuestas JSON con `{success: bool, message: str, data?: dict}`.
  Cubre: R1, R4, R5, R5.2, R6.

- [ ] T5 — Modificar `src/main.py`: añadir lifespan que instancia `ConfigService`, llama `load()`, sincroniza reloj, y registra el router de config. Cubre: R7, R8.

## Bloque C: Frontend HTMX

- [ ] T6 — Crear `templates/admin/config.html`: página Admin con layout base, tabs/secciones Hardware y SMS. Carga partials vía HTMX. Cubre: R1, R12.
- [ ] T7 — Crear `templates/admin/config_form.html`: partial HTMX con formulario de RS485 + RS232 + GSM + botones Test. Maneja respuestas de validación inline. Cubre: R2, R3, R3.2, R4, R5, R5.2, R6.
- [ ] T8 — Crear `templates/admin/config_sms.html`: partial HTMX con lista de destinatarios, horarios de reportes, inputs dinámicos para añadir/quitar. Cubre: R9, R10.

## Bloque D: Dependencias

- [ ] T9 — Añadir `pyserial==3.5` a `requirements.txt` y rebuild del contenedor Docker. Cubre: R4, R5.

## Bloque E: Tests

- [ ] T10 — Crear `tests/test_config.py`: tests unitarios de modelos Pydantic (validación de campos, defaults, valores inválidos, modelos ScaleConfig, PCConfig, GSMConfig). Cubre: R2, R3, R3.2, R6, R9, R10.
- [ ] T11 — Crear `tests/test_config_service.py`: tests de `ConfigService` con `tempfile.TemporaryDirectory()` (carga desde archivo, guardado atómico, defaults si no existe, archivo corrupto). Cubre: R6, R7, R11.
- [ ] T12 — Crear `tests/test_config_api.py`: tests de endpoints FastAPI con `TestClient` (GET config, PUT config válido, PUT con datos inválidos, test-scale, test-rs232, test-gsm con/sin puerto, acceso sin auth). Cubre: R1, R4, R5, R5.2, R6, R12.

---

## Trazabilidad Tasks → Requirements

| Task | R1 | R2 | R3 | R3.2 | R4 | R5 | R5.2 | R6 | R7 | R8 | R9 | R10 | R11 | R12 |
|------|:--:|:--:|:--:|:---:|:--:|:--:|:---:|:--:|:--:|:--:|:--:|:---:|:---:|:---:|
| T1   |    | X  | X  |  X  |    |    |     |    |    |    | X  |  X  |     |     |
| T2   |    |    |    |     |    |    |     | X  | X  |    |    |     |  X  |     |
| T3   |    |    |    |     |    |    |     |    | X  |    |    |     |     |  X  |
| T4   | X  |    |    |     | X  | X  |  X  | X  |    |    |    |     |     |     |
| T5   |    |    |    |     |    |    |     |    | X  | X  |    |     |     |     |
| T6   | X  |    |    |     |    |    |     |    |    |    |    |     |     |  X  |
| T7   |    | X  | X  |  X  | X  | X  |  X  | X  |    |    |    |     |     |     |
| T8   |    |    |    |     |    |    |     |    |    |    | X  |  X  |     |     |
| T9   |    |    |    |     | X  | X  |  X  |    |    |    |    |     |     |     |
| T10  |    | X  | X  |  X  |    |    |     | X  |    |    | X  |  X  |     |     |
| T11  |    |    |    |     |    |    |     | X  | X  |    |    |     |  X  |     |
| T12  | X  |    |    |     | X  | X  |  X  | X  |    |    |    |     |     |  X  |
