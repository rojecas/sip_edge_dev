# Closure — backup_system

- **Feature ID:** 10
- **Fecha de cierre:** 2026-06-14
- **GitHub Issue:** https://github.com/rojecas/sip_edge/issues/7
- **Verificacion:** `./init.ps1` [OK] todos los bloques

## Archivos modificados

| Archivo | Accion |
|---------|--------|
| `src/config.py` | Anadido `BackupConfig` dataclass, `load_config` retorna 4-tupla, `_atomic_write_sections` incluye `backup` |
| `src/main.py` | Importado `BackupConfig`/`BackupLog`/`APIRouter`/`BackgroundTasks`, `lifespan` desempaqueta 4 valores, anadido `backup_router` con `GET /api/backup/status` y `POST /api/backup/run` (202) |
| `src/backup.py` | **Nuevo**: `_compute_crc32`, `_mysqldump_to_file` (password por stdin), `_rotate_backups`, `run_backup` |
| `scripts/backup.py` | **Nuevo**: script standalone para cron (usa venv python) |
| `tests/test_backup.py` | **Nuevo**: 23 tests (config, CRC32, mysqldump mock, rotacion, ciclo completo, endpoints) |
| `tests/test_config.py` | Adaptados callers a 4-tupla, `app.state.backup_config` en fixtures |
| `tests/test_scale.py` | Adaptados callers a 4-tupla, `app.state.backup_config` en fixtures |
| `tests/test_auth.py` | `app.state.backup_config` en fixture |
| `tests/test_haciendas.py` | `app.state.backup_config` en fixture |
| `tests/test_users.py` | `app.state.backup_config` en fixture |
| `tests/test_weighings.py` | `app.state.backup_config` en fixture |

## Decisiones tecnicas

1. **Password de mysqldump por stdin** — El flag `--password` sin valor hace que mysqldump lea de stdin. `subprocess.communicate(input=password.encode())` pasa la contrasena. No aparece en `ps aux`.

2. **BackupConfig por defecto** — Si la seccion `backup` no existe en config.yaml, se usan valores default ajustados al entorno `sipedge` en la EdgeBox:
   - `local_dir: /home/sipedge/backups`
   - `usb_mount_path: /mnt/backup_usb`
   - `keep_days: 30`
   - Configurado en config.yaml de EdgeBox via `config.yaml` seccion `backup`.

3. **Cron como `sipedge`** — El script se ejecuta con el venv Python (`/home/sipedge/sip_edge/venv/bin/python`). Logs a `/home/sipedge/backups/cron.log`.

## Verificacion

### Local (Docker)
```
docker compose exec -T backend python -m unittest discover -s tests -v
→ 218 tests, 0 failures
```

### EdgeBox (hardware real)
- `mysqldump` disponible: `mysqldump from 11.8.6-MariaDB, client 10.19`
- `scripts/backup.py` ejecutado exitosamente: backup_20260615_001355.sql.gz (1794 bytes, crc32=8f089414)
- `backup_logs` registra ejecucion (1 exitoso, 1 fallo del intento inicial sin `--password`)
- cron instalado: `55 23 * * *`
- USB no disponible en este momento (no interrumpe el proceso)

## Trazabilidad

| R<n> | Test(s) |
|------|---------|
| R1, R2, R3, R4 | TestBackupConfig (4 tests) |
| R5, R6, R7 | TestMysqldumpToFile (3 tests) |
| R8, R9 | TestRotateBackups (3 tests) |
| R10, R12, R14 | TestRunBackup (4 tests) |
| R11 | TestComputeCRC32 (3 tests) |
| R13, R15 | verificados implicitamente (BackupLog en models.py, create_all en lifespan) |
| R16, R17, R18 | scripts/backup.py + EdgeBox execution |
| R19, R20, R21 | TestBackupEndpoints (6 tests) |
| R22 | TestRunBackup + verificacion EdgeBox |
| R23, R24 | TestMysqldumpToFile (password por stdin, variables de entorno) |
