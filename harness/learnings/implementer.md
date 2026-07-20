# Lecciones para el Implementer

## Sesion 2026-07-14/15 — F28 ai_multi_turn
- Al modificar el ENUM de sms_messages.status (agregar sending), tambien verificar que la migracion original en database/migrations/ coincida con el codigo.
- file_get_or_create_ai_conversation debe manejar el caso de conversation_id pre-creada por el dispatcher con workflow_type='unknown'.
- El modem Quectel recicla IDs de SMS tras reinicio. No confiar en modem_sms_id como identificador unico persistente.
- Al agregar metodos a sms_persistence.py, verificar que el metodo no exista ya en otro lugar (get_body_by_modem_id fue innecesario).

## Sesion 2026-07-19 — F38 y F39
- **Skills consultados OBLIGATORIO:** Todo informe de implementacion (impl_<feature>.md) DEBE incluir seccion "## Skills consultados" documentando que skills fueron cargados (ej. svelte5). Si el proyecto tiene skills en `.opencode/skills/`, el implementer DEBE cargarlos y documentarlos. Fallo recurrente: 3 veces rechazado por reviewer por este motivo.
- **Compilar frontend y copiar correctamente:** `npm run build` + `Copy-Item -Recurse -Path "frontend/dist" -Destination "src/static"`. NUNCA usar wildcard `frontend/dist/*` porque aplana la carpeta `assets/` (los archivos JS/CSS quedan en `src/static/` en vez de `src/static/assets/`). Verificar con `Get-ChildItem -Recurse src/static`.
- **Leer el spec COMPLETO antes de implementar:** El spec de F38 fue reescrito 2 veces por malentendidos de alcance (solo crear vs CRUD completo, incluir/excluir DELETE). Verificar acceptance criteria contra requirements antes de tocar codigo.

- **Ejecutar migraciones en la BD de desarrollo:** Crear el archivo de migracion NO es suficiente. El implementer DEBE ejecutar la migracion contra la base de datos. Las migraciones usan SQL directo (no Alembic). Aplicar con: `docker compose exec mariadb mysql -usip_user -psip_pass sip_edge -e "SQL..."`. Verificar con `DESCRIBE tabla` que la columna existe.
- **Reiniciar el contenedor tras cambios de codigo:** Aunque `src/` esta montado como volumen, Python cachea modulos importados. Si un cambio no se refleja, hacer `docker compose restart backend`.
- **FK con tipos coincidentes:** Al agregar FK, verificar que el tipo de la columna coincida EXACTAMENTE con la columna referenciada. `users.id` es `bigint(20)` (SIGNED), usar `BIGINT` en migracion, NO `BIGINT UNSIGNED`.
