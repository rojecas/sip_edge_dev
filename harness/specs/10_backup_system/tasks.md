# Tasks — backup_system

> Pasos discretos en orden de implementacion. Cada task referencia los R<n> que cubre.

---

## Fase 1: Modelo de datos

- [x] T1 — Crear clase `BackupLog` en `src/models.py` con todas las columnas
  de la tabla `backup_logs` (id, filename, file_size, local_checksum,
  usb_copied, usb_checksum, error_message, created_at). Cubre: R13, R15.

## Fase 2: Configuracion de backup

- [x] T2 — Crear dataclass `BackupConfig` en `src/config.py` con campos
  `usb_mount_path: str`, `local_dir: str`, `keep_days: int` y constantes de
  default correspondientes. Cubre: R2.

- [x] T3 — Modificar `load_config` en `src/config.py` para leer la seccion
  `backup` de `config.yaml` y devolver `tuple[SystemConfig, SessionConfig,
  ScaleConfig, BackupConfig]`. Validar `keep_days > 0` con fallback al default.
  Cubre: R1, R3, R4.

- [x] T4 — Modificar `_atomic_write_sections` en `src/config.py` para incluir la
  seccion `backup` con valores default al crear `config.yaml` por primera vez.
  Adaptar `_save_system_config_atomic` para preservar la seccion `backup` si ya
  existe. Cubre: R1.

- [x] T5 — Adaptar callers de `load_config` en `src/main.py` (lifespan) para
  recibir los 4 elementos de la tupla y almacenar `app.state.backup_config`.
  Adaptar tambien los callers en `tests/test_config.py`, `tests/test_scale.py`,
  `tests/test_auth.py`, `tests/test_weighings.py`, `tests/test_users.py` y
  `tests/test_haciendas.py` para que desempaqueten 4 valores donde antes
  desempaquetaban 3. Asignar `app.state.backup_config` en las fixtures de test
  que inicializan `app.state`. Cubre: R3.

## Fase 3: Logica de backup

- [x] T6 — Crear `src/backup.py` con funciones `_compute_crc32(filepath)`,
  `_mysqldump_to_file(output_path)`, `_rotate_backups(local_dir, keep_days)`,
  y `run_backup(usb_mount_path, local_dir, keep_days)`. Cubre: R5, R6, R7, R8,
  R9, R10, R11, R12, R14, R23, R24.

## Fase 4: Script standalone

- [x] T7 — Crear `scripts/backup.py` con imports minimos, inicializacion de BD,
  carga de config y llamada a `run_backup()`. Cubre: R16, R17, R18.

## Fase 5: Endpoints

- [x] T8 — Anadir `backup_router` en `src/main.py` con `GET /api/backup/status`
  (admin, retorna ultimos 10 registros de `backup_logs`). Dependencias:
  `check_inactivity` + `require_role("admin")`. Cubre: R19, R21.

- [x] T9 — Anadir `POST /api/backup/run` en `backup_router` (admin, dispara
  backup en background via `BackgroundTasks`, retorna 202). Dependencias:
  `check_inactivity` + `require_role("admin")`. Cubre: R20, R21, R22.

- [x] T10 — Registrar `backup_router` con `app.include_router(backup_router)`
  en `src/main.py`. Cubre: R19, R20.

## Fase 6: Tests

- [x] T11 — Crear `tests/test_backup.py` con `TestBackupConfig`: carga desde
  YAML, fallback a defaults, `keep_days <= 0` usa default. Cubre: R1, R2, R3, R4.

- [x] T12 — Anadir `TestMysqldumpToFile` en `tests/test_backup.py`: mock de
  `subprocess.Popen` con salida exitosa, fallo lanza `RuntimeError`, crea
  directorio si no existe. Cubre: R5, R6, R7.

- [x] T13 — Anadir `TestRotateBackups` en `tests/test_backup.py`: elimina el
  mas antiguo al exceder `keep_days`, no afecta archivos no `.sql.gz`, no
  elimina si hay `keep_days` exactos. Cubre: R8, R9.

- [x] T14 — Anadir `TestComputeCRC32` en `tests/test_backup.py`: calculo
  consistente, diferente para contenido diferente. Cubre: R11.

- [x] T15 — Anadir `TestRunBackup` en `tests/test_backup.py`: ciclo completo
  exitoso, fallo de mysqldump registra error, USB no montado no interrumpe,
  CRC32 mismatch en USB registra error. Cubre: R10, R12, R14.

- [x] T16 — Anadir `TestBackupEndpoints` en `tests/test_backup.py`: GET status
  con admin 200, POST run con admin 202, ambos 401 sin token, ambos 403 con
  token operator. Cubre: R19, R20, R21.

- [x] T17 — Ejecutar `docker compose exec backend python -m unittest discover -s
  tests -v` y verificar que todos los tests pasan (incluyendo los 195
  existentes). Cubre: todos.

## Fase 7: Verificacion en EdgeBox

- [x] T18 — Verificar que `mysqldump` esta disponible en la EdgeBox. Si no,
  instalar `mariadb-client`. Verificar que el script `scripts/backup.py` se
  ejecuta correctamente con el entorno de produccion.

- [x] T19 — Configurar cron en la EdgeBox para ejecutar `scripts/backup.py` a
  las 23:55 diariamente. Verificar que el log de cron muestra ejecucion exitosa.
  Cubre: R16.
