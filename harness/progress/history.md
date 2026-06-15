# Bitacora historica de la fabrica (append-only)

> Cada vez que se cierra una sesion del harness, su resumen se anade aqui.
> No edites entradas anteriores. Solo anades al final.

---

## 2026-06-11 — Setup wizard integrado

- **Agente:** implementer
- **Cambios:** `scripts/setup_wizard.ps1` generico con deteccion de stack y delegacion a `.opencode/templates/<stack>/setup_wizard.ps1`. `init.ps1` Docker-aware. Scaffold copia `setup_wizard.ps1`.
- **Resultado:** 5 features pendientes (wizards python, typescript, rust, go, cpp-iot).
- **Lecciones:** 6 reglas duras aprendidas (PowerShell here-strings, UTF-8 BOM, TCP port checks, evitar `docker compose run`, no redirigir stderr de Docker).

## 2026-06-12 — Mejora de documentacion historica (v1.2.0)

- **Agente:** implementer
- **Cambios:** `harness/docs/architecture.md` (seccion SOLID), `harness/docs/sessions.md` (nuevo: estandar de planes, closures, bloqueos), `harness/AGENTS.md` (reglas duras ampliadas, S5/S6 reescritas), `harness/progress/current.md` (template con tabla indice), `harness/CHECKPOINTS.md` (C8: documentacion historica)
- **Resultado:** Inspirado en el sistema CCMT legacy de `plans/` + `handoffs/`, se adopto un sistema de 3 artefactos por feature: plan (antes), closure (al hacer `done`), registro de bloqueo (al `blocked`). Arquitectura reforzada con principios SOLID y checklist de evaluacion para el reviewer.
- **Lecciones:** Version y Changelog deben actualizarse como parte del cierre de sesion. El harness de cada proyecto derivado debe recibir las mismas actualizaciones.

## 2026-06-13 — system_config (feature 1) completada

- **Agente:** leader → spec-author → implementer → reviewer
- **Feature:** Configuracion del Sistema — Puertos RS485/RS232 y GSM
- **Cambios:** `src/config.py` (dataclasses + persistencia YAML), `src/main.py` (endpoints API), `tests/test_config.py` (20 tests), `requirements.txt` (pyserial, httpx), `Dockerfile` (gh CLI, git)
- **Resultado:** Endpoints GET/PUT /api/config y POST /api/config/test/{port} funcionando. GSM usa ModemManager (mmcli). Atomic writes con os.replace(). 20 tests pasan, init.ps1 verde.
- **Lecciones:** El spec-author debe leer el codigo existente (src/main.py FastAPI) antes de escribir el spec — produjo CLI en intentos 1 y 2. La autenticacion gh se pierde al recrear el contenedor (no persistida en volumen). El label "sdd" en GitHub debio crearse manualmente.

## 2026-06-13 — auth_rbac (feature 2) completada

- **Agente:** leader → spec-author → implementer → reviewer
- **Feature:** Autenticacion JWT, RBAC y Bloqueo por Inactividad
- **Cambios:** `src/database.py` (SQLAlchemy + MariaDB), `src/models.py` (User ORM), `src/auth.py` (JWT + dependencias), `src/seed.py` (admin seed), `src/config.py` (SessionConfig), `src/main.py` (endpoints auth/setup + proteccion), `tests/test_auth.py` (30 tests), `tests/test_database.py` (9 tests), `harness/init.ps1` (Docker test fix)
- **Resultado:** 60 tests pasan, init.ps1 verde (con fix de Docker). Login JWT bcrypt, RBAC 3 roles (admin/operator/corresponsal), timeout de inactividad configurable via /api/setup/session (solo admin, default 15 min), seed admin automatico. Tabla users completa (cubre feature 3).
- **Lecciones:** El reviewer bloqueo por init.ps1 que ejecutaba tests nativos en vez de Docker — se corrigio en harness v1.7.1. Issues menores (bare tuple type hint, lazy import) no bloquean pero deben corregirse. El spec-author produjo un spec de 25 requirements en EARS sin necesidad de re-trabajo esta vez, gracias al contexto detallado provisto por el leader.

## 2026-06-13 — user_management (feature 3) completada

- **Agente:** leader → spec-author → implementer → reviewer
- **Feature:** Gestion de Usuarios (CRUD)
- **Cambios:** `src/users.py` (Pydantic schemas + CRUD endpoints), `src/main.py` (router registrado), `tests/test_users.py` (30 tests CRUD), `tests/test_auth.py` (fix test isolation)
- **Resultado:** 88 tests pasan, init.ps1 verde. CRUD completo de usuarios con desactivacion logica. Password hasheado con bcrypt en create/update. Solo admin.
- **Lecciones:** El modelo User completo creado por auth_rbac simplifico user_management — solo faltaban endpoints y schemas. No se necesito migracion de BD.

## 2026-06-13 — farm_lot_crud (feature 4) completada

- **Agente:** leader → spec-author → implementer → reviewer
- **Feature:** Gestion de Haciendas y Suertes
- **Cambios:** `src/models.py` (Hacienda + Suerte ORM), `src/haciendas.py` (10 endpoints CRUD), `src/main.py` (routers), `tests/test_haciendas.py` (84 tests)
- **Resultado:** 144 tests pasan, init.ps1 verde. CRUD de haciendas y suertes con soft delete, unique compuesto (hacienda_id + codigo_suerte), cascade loading via query param.
- **Lecciones:** Esquema de dos tablas normalizadas decidido en discusion con el humano. Patron de users.py reutilizado exitosamente para haciendas.py.

## 2026-06-14 — scale_integration (feature 5) completada

- **Agente:** leader → spec-author → implementer → reviewer
- **Feature:** Integracion Serial con Bascula DINI ARGEO DFWLI-2
- **Cambios:** `src/scale.py` (ScaleService singleton, comandos REXT/TARE/TMAN/ZERO/CLEAR, async listener), `src/config.py` (ScaleConfig), `src/main.py` (endpoint setup/scale), `tests/test_scale.py` (30 tests)
- **Resultado:** 174 tests pasan, init.ps1 verde. Comunicacion RS485 bidireccional, timeout configurable 1-10s, escucha asincrona para boton PRINT de la balanza.
- **Lecciones:** Protocolo real de la balanza (DINI ARGEO DFWLI-2) documentado por el humano. Diseno de ScaleService como singleton con thread-safety y queue para datos asincronos.

## 2026-06-14 — weighing_capture (feature 6) completada

- **Agente:** leader → spec-author → implementer → reviewer
- **Feature:** Captura de Pesaje Multipaso con Confirmacion y Envio RS232
- **Cambios:** `src/models.py` (Weighing ORM), `src/weighings.py` (CRUD + WS + RS232 stub), `src/auth.py` (require_any_role), `src/main.py` (routers + WS /ws/scale), `src/haciendas.py` (operator GET), `tests/test_weighings.py` (21 tests)
- **Resultado:** 195 tests pasan, init.ps1 verde. Primer feature con rol operator activo. Focus management via WebSocket. RS232 stub para feature 11.
- **Lecciones:** La discusion detallada del flujo de trabajo (9 pasos, tractomula/vagon/guia, 3 pesos separados) fue esencial para disenar la tabla y endpoints correctos.

---

## 2026-06-14 — Infraestructura: DEV_MODE, EdgeBox setup y llama.cpp

- **Agente:** operaciones / devops
- **Feature:** ninguna (preparacion de entorno)
- **Cambios:**
  - `compose.yml` — Anadida variable `DEV_MODE` para saltar hardware en dev
  - `src/scale.py` — `ScaleService.__init__` acepta `dev_mode`, `start()` salta serial si activo
  - `src/main.py` — Lee `DEV_MODE` de entorno y lo pasa a `ScaleService`
  - `requirements.txt` — Anadidos `pyserial==3.5` y `httpx==0.28.1` (locales, sin commit)
  - `docs/Informe 02 - Configuracion del Entorno de Ejecucion.md` — Documentacion completa del entorno
- **EdgeBox (192.168.1.42):**
  - SSH configurado con clave dedicada (`~/.ssh/sip_edge_edgebox`)
  - MariaDB 11.8.6 instalado, BD `sip_edge` y usuario `sip_user` creados
  - Repositorio clonado via SSH (deploy key en GitHub)
  - Python 3.13.5 venv con 34 dependencias instaladas
  - Servicio systemd `sip-edge.service` creado y activo (auto-start)
  - PolicyKit configurado para acceso al modem sin sudo
  - `.env` con 8 variables de entorno para produccion
  - `config.yaml` generado con defaults de hardware EdgeBox
- **llama.cpp:** Actualizado de b8763 (ggml 0.14.0, 42 binarios) → b9632 (ggml 0.15.1, 49 binarios)
  - 870 commits de diferencia, compilado en la EdgeBox (~30 min con -j1)
  - Verificacion: Qwen2.5 1.5B Q4_K_M → 7.7 t/s prompt, 3.6 t/s generacion
- **Resultado:** `./init.ps1` verde, 195 tests. Entorno dev y produccion listos.
- **Lecciones:**
  - El `.env` en raiz no se usa; las variables van en `compose.yml` (dev) y en `.env` del servicio (EdgeBox)
  - `pyserial` y `httpx` estaban en `requirements.txt` local pero no habian sido comiteados
  - La EdgeBox tiene PEP 668 activo (externally-managed-environment), requiere venv o `--break-system-packages`
  - 4 de los 7 binarios "nuevos" de llama.cpp son deprecados (wrappers pre-mtmd); 2 son benchmarks x86
  - El CM4 no tiene DOTPROD/I8MM/SVE — solo FMA para aceleracion SIMD
  - Cambiar de Docker en produccion a nativo libero ~500MB RAM y simplifico el deploy (git pull + restart)
  - Conveniencia de tener un shell SSH con clave para administrar la EdgeBox remotamente
  - `sudo` requiere tty en la EdgeBox; usar `-S` con password para comandos batch

---

## 2026-06-14 — Feature 10 backup_system + harness sync

- **Agente:** opencode (leader + implementer)
- **Feature:** 10 (backup_system) — spec_ready → in_progress → done
- **Archivos modificados:** 13 source/test files, 4 new files
- **Tests:** 23 nuevos (218 total, 0 fallos)
- **Verificacion EdgeBox:** mysqldump + cron 23:55 instalado
- **Harness update:** version 1.7.0 sincronizada desde fabrica (`.session`, `close.ps1`, `.opencode/` auto-descubrimiento)
- **Lecciones:**
  - `mysqldump` requiere flag `--password` para leer la contrasena por stdin
  - El wrapper `./scripts/close.ps1` espera rutas relativas al proyecto desde `scripts/`
  - La tabla `backup_logs` ya existia en `models.py` antes de iniciar la feature
  - `JSONResponse` con `status_code=202` necesario para POST (FastAPI default 200 en dict returns)
  - Tests de `run_backup` necesitan patchear `src.database.SessionLocal` (no solo `src.backup`)
  - SQLite in-memory acumula registros entre tests; truncar `backup_logs` en `setUp`
