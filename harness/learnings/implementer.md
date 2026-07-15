# Lecciones para el Implementer

## Sesion 2026-07-14/15 — F28 ai_multi_turn
- Al modificar el ENUM de sms_messages.status (agregar sending), tambien verificar que la migracion original en database/migrations/ coincida con el codigo.
- file_get_or_create_ai_conversation debe manejar el caso de conversation_id pre-creada por el dispatcher con workflow_type='unknown'.
- El modem Quectel recicla IDs de SMS tras reinicio. No confiar en modem_sms_id como identificador unico persistente.
- Al agregar metodos a sms_persistence.py, verificar que el metodo no exista ya en otro lugar (get_body_by_modem_id fue innecesario).
