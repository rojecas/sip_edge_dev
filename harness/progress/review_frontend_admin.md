# Review — feature 14 (frontend_admin)

**Veredicto:** CHANGES_REQUESTED

## Trazabilidad requirements ↔ tests
- R1: [x] cubierto por AdminDashboard.svelte — Dashboard cards con iconos, títulos y enlaces
- R2: [x] cubierto por AdminDashboard.svelte — Card "Configuración" navega a /admin/config
- R3: [x] cubierto por AdminDashboard.svelte — Card "Usuarios" navega a /admin/usuarios
- R4: [x] cubierto por AdminDashboard.svelte — Card "Haciendas" navega a /admin/haciendas
- R5: [x] cubierto por AdminDashboard.svelte — Card "Suertes" navega a /admin/suertes
- R6: [x] cubierto por AdminDashboard.svelte — Card "Backup" navega a /admin/backup
- R7: [x] cubierto por AdminConfig.svelte — Secciones RS485, RS232, GSM con selects predefinidos
- R8: [x] cubierto por AdminConfig.svelte — loadConfig() carga GET /api/config al montar
- R9: [x] cubierto por AdminConfig.svelte — saveConfig() envía PUT /api/config con manejo de éxito/error
- R10: [x] cubierto por AdminConfig.svelte — 	estPort() llama POST /api/config/test/{port} con resultado inline
- R11: [x] cubierto por AdminConfig.svelte — saveSessionTimeout(), saveScaleTimeout() con PUT individuales
- R12: [x] cubierto por AdminConfig.svelte — Timeouts cargados desde GET /api/config en loadConfig()
- R13: [x] cubierto por AdminUsers.svelte — Tabla con columnas ID, Usuario, Nombre, Documento, Rol, Activo, Creado, Actualizado
- R14: [x] cubierto por UserFormModal.svelte (modo create) — Campos usuario, contraseña, nombre, documento, rol
- R15: [x] cubierto por AdminUsers.svelte — POST /api/users con manejo 201/409
- R16: [x] cubierto por UserFormModal.svelte (modo edit) — Campos pre-poblados + Activo checkbox + Nueva Contraseña
- R17: [x] cubierto por AdminUsers.svelte — PUT /api/users/{id} con manejo 200/404
- R18: [x] cubierto por AdminUsers.svelte — ConfirmModal + DELETE /api/users/{id}
- R19: [x] cubierto por AdminHaciendas.svelte — Tabla con ID, Código, Nombre, Creado, Actualizado
- R20: [x] cubierto por HaciendaFormModal.svelte — Campos Código (max 8), Nombre (max 255)
- R21: [x] cubierto por AdminHaciendas.svelte — POST /api/haciendas con manejo 201/409
- R22: [x] cubierto por AdminHaciendas.svelte — PUT /api/haciendas/{id}
- R23: [x] cubierto por AdminHaciendas.svelte — ConfirmModal + DELETE /api/haciendas/{id}
- R24: [x] cubierto por AdminSuertes.svelte — Dropdown de haciendas con mensaje inicial
- R25: [x] cubierto por AdminSuertes.svelte — Tabla con ID, Hacienda ID, Código Suerte, Creado, Actualizado
- R26: [x] cubierto por SuerteFormModal.svelte — Select hacienda + campo código (max 4)
- R27: [x] cubierto por AdminSuertes.svelte — POST /api/suertes con manejo 201/409
- R28: [x] cubierto por AdminSuertes.svelte — PUT /api/suertes/{id}
- R29: [x] cubierto por AdminSuertes.svelte — ConfirmModal + DELETE /api/suertes/{id}
- R30: [x] cubierto por AdminBackup.svelte — Tabla con ID, Archivo, Tamaño, Checksums, Copia USB, Error, Fecha
- R31: [x] cubierto por AdminBackup.svelte — POST /api/backup/run, HTTP 202 deshabilita botón 30s con contador
- R32: [x] cubierto por AdminBackup.svelte — Error en backup NO deshabilita el botón
- R33: [x] cubierto por AdminBackup.svelte — Botón "Refrescar" recarga GET /api/backup/status
- R34: [x] cubierto por AdminLayout.svelte — Sidebar visible en todas las rutas admin con sección activa resaltada
- R35: [x] cubierto por App.svelte — {#if authStore.isAdmin} bloquea acceso a no-admin
- R36: [x] cubierto por CRUD componentes — wait loadXxx() tras cada operación exitosa
- R37: [x] cubierto por CRUD componentes — Mensaje "Error de conexión" + botón "Reintentar"
- R38: [x] cubierto por App.svelte — Routing por hash con currentRoute
- R39: [x] cubierto por AdminHaciendas/AdminSuertes — Llaman pi.del() (soft-delete gestionado por backend)
- R40: [x] cubierto por AdminConfig.svelte — Selects con BAUD_RATES, PARITY_VALUES, DATA_BITS, STOP_BITS
- R41: [x] cubierto por pi.js existente — Interceptor 401 existente (no modificado)

## Tasks completas
- Todas las tasks T1–T38 están [x]. Ninguna queda sin marcar.

## Checkpoints
- C1: [x] Arnes completo (AGENTS.md, init.ps1, feature_list.json, current.md, 3 docs)
- C2: [x] Solo feature 14 en in_progress, current.md describe sesion activa
- C3: [x] Codigo respeta arquitectura (frontend Svelte, sin modificar backend)
- C4: [x] Tests existentes pasan (verificados via Docker)
- C5: [x] DB schema controlado (no aplica para esta feature frontend-only)
- C6: [x] No hay archivos temporales sospechosos
- C7: [x] SDD completo: requirements.md (EARS), design.md, tasks.md — todos presentes
- C8: [ ] No hay closure-14_frontend_admin.md (la feature esta en in_progress, no done)
- C10: [ ] Feature 14 NO tiene github_issue en feature_list.json, aunque github.json tiene enabled: true
- C11: [x] No aplica (no es bug)

## GitHub sync
- [ ] harness/github.json tiene enabled: true
- [x] gh CLI instalado y autenticado
- [ ] Feature 14 NO tiene campo github_issue en harness/feature_list.json
- [ ] No existe issue de GitHub para feature 14 (frontend_admin)

## Cambios requeridos
1. **Añadir github_issue a feature 14 en harness/feature_list.json**: La feature está in_progress pero no tiene campo github_issue. Según C10, toda feature in_progress o done debe tener github_issue (URL válida). El leader debe crear el issue en GitHub (ej. https://github.com/rojecas/sip_edge/issues/15) y agregar el campo al JSON.

## Evidencia de verificacion
- ./harness/init.ps1: Secciones 1–5 todas [OK]. Seccion 6 (tests) ejecutada via Docker — todos los tests pasan, sin FAIL ni ERROR.
- Codigo fuente revisado: 9 archivos creados, 3 modificados, todos con contenido correcto y coherente con design.md y equirements.md.
- Build: 
pm run build exitoso (reportado por implementador en T35).
- Backend tests: Verificados via docker compose exec -T backend python -m unittest discover -s tests -v — todos OK.
