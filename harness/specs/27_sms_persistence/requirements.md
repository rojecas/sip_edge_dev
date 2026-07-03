# Requirements — SMS Persistence, Dispatcher v2 y Cola Asincrona

> Feature 27 — Infraestructura de persistencia y despacho de SMS.
> Redactado en EARS (Easy Approach to Requirements Syntax).

---

## R1 — Tabla sms_conversations
El sistema DEBE crear la tabla `sms_conversations` con las columnas: `id` (BIGINT UNSIGNED AUTO_INCREMENT PK), `peer_number` (VARCHAR(20) NOT NULL), `workflow_type` (ENUM 'emergency','password_reset','ai_query','unknown' NOT NULL), `status` (ENUM 'active','completed','expired','cancelled','failed' NOT NULL DEFAULT 'active'), `started_at` (DATETIME(3) NOT NULL), `last_activity` (DATETIME(3) NOT NULL), `expires_at` (DATETIME(3) NULL), `metadata` (JSON NULL), e índices `idx_peer_status` (peer_number, status) e `idx_expires` (status, expires_at).

## R2 — Tabla sms_messages
El sistema DEBE crear la tabla `sms_messages` con las columnas: `id` (BIGINT UNSIGNED AUTO_INCREMENT PK), `conversation_id` (BIGINT UNSIGNED NOT NULL FK → sms_conversations.id), `direction` (ENUM 'sent','received' NOT NULL), `peer_number` (VARCHAR(20) NOT NULL), `body` (TEXT NOT NULL), `handler` (VARCHAR(32) NULL), `status` (ENUM 'pending','sent','failed','timeout','delivered','received' NOT NULL DEFAULT 'pending'), `error_message` (TEXT NULL), `modem_sms_id` (INT NULL), `created_at` (DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)).

## R3 — Persistencia de SMS entrante antes de delegar
CUANDO el IncomingSmsDispatcher recibe un SMS entrante (desde mmcli o cola de desarrollo), el sistema DEBE persistir el SMS en `sms_messages` con `direction='received'` y `status='received'` ANTES de delegar a cualquier handler registrado.

## R4 — Creación de conversación al recibir primer SMS
CUANDO el IncomingSmsDispatcher recibe un SMS entrante y no existe una conversación activa para ese `peer_number` con el mismo `workflow_type`, el sistema DEBE crear un registro en `sms_conversations` con `status='active'` y `workflow_type` determinado por el handler que procese el mensaje.

## R5 — Eliminación de handler catch-all
El sistema NO DEBE tener un handler catch-all en el IncomingSmsDispatcher que envíe automáticamente SMS no reconocidos al AI handler (agent_orchestrator.handle_sms_query).

## R6 — Respuesta de ayuda para SMS no reconocido
SI ningún handler registrado retorna `True` para un SMS entrante ENTONCES el sistema DEBE responder al remitente con el texto: "Comando no reconocido. Comandos validos: manual on, manual off, reset password <usuario>", y DEBE persistir la conversación como `workflow_type='unknown'`, `status='completed'`.

## R7 — SMS del carrier
SI un SMS entrante proviene del carrier telefónico (números cortos, TIGO, saldo, etc.) ENTONCES el sistema DEBE persistir el mensaje en `sms_messages`, crear una conversación con `workflow_type='unknown'` y `status='completed'`, y NO DEBE enviar respuesta al remitente.

## R8 — Cola de envío asíncrona
El sistema DEBE tener un thread dedicado (cola de envío asíncrona) que consuma registros de `sms_messages` con `direction='sent'` y `status='pending'`, y ejecute el envío físico via mmcli sin bloquear el event loop de FastAPI.

## R9 — Timeout configurable por SMS
DURANTE el envío de un SMS en la cola asíncrona, el timeout por cada llamada a mmcli DEBE ser configurable (valor por defecto 20 segundos).

## R10 — Reintentos de envío
SI un envío de SMS falla ENTONCES el sistema DEBE reintentar hasta 3 veces, incrementando un contador interno; si se superan los 3 intentos, el sistema DEBE marcar el `status` del mensaje como `'failed'` y registrar el error en `error_message`.

## R11 — Envío no bloqueante
El envío de SMS a través de la cola asíncrona NO DEBE bloquear el event loop de uvicorn, y NO DEBE disparar el watchdog de systemd (WATCHDOG=1 debe enviarse regularmente durante la operación).

## R12 — Emergency: persistencia y vinculación
CUANDO `emergency_mode.process_incoming_sms()` procesa un comando SMS válido, el sistema DEBE:
- Persistir el SMS entrante en `sms_messages`.
- Crear o recuperar una conversación en `sms_conversations` con `workflow_type='emergency'`.
- Vincular `conversation_id` de `sms_messages` al `request_id` correspondiente en `emergency_mode_log`.
- Persistir los SMS de respuesta (activación, extensión, desactivación) en `sms_messages` con `direction='sent'`.

## R13 — Password reset: validación de rol admin
CUANDO `password_reset.handle_incoming_sms()` recibe un comando 'reset password <usuario>', el sistema DEBE verificar que `sender_phone` pertenece a un usuario con rol 'admin'; SI el remitente no es admin ENTONCES el sistema DEBE responder "Solo administradores pueden solicitar reset de contrasena", persistir el SMS, y retornar `True` (SMS manejado).

## R14 — Password reset: auto-reset prohibido
CUANDO `password_reset.handle_incoming_sms()` detecta que el remitente (admin) está solicitando reset de su propia contraseña, el sistema DEBE rechazar la operación, responder "No puede solicitar reset de su propia contrasena por SMS", y NO generar un PIN.

## R15 — Password reset: límite de intentos de PIN
MIENTRAS una conversación `password_reset` está activa, el sistema DEBE llevar un contador de intentos fallidos de verificación de PIN; SI se alcanzan 3 intentos fallidos ENTONCES el sistema DEBE invalidar el PIN actual y marcar la conversación como `'cancelled'`.

## R16 — Password reset: nuevo request invalida PIN anterior
CUANDO llega un nuevo comando 'reset password <usuario>' para un usuario que ya tiene un PIN activo (conversación `password_reset` en estado `'active'`), el sistema DEBE:
- Invalidar el PIN anterior (marcar conversación anterior como `'cancelled'`).
- Crear una nueva conversación con nuevo PIN.
- Enviar SMS al remitente notificando: "Nuevo PIN generado para '<usuario>'. El PIN anterior ya no es valido."

## R17 — Auditoría completa
El sistema DEBE registrar en `sms_messages` todos los SMS enviados y recibidos, incluyendo aquellos generados automáticamente por los handlers, para permitir trazabilidad completa de todas las comunicaciones SMS.

## R18 — Refactor de sms_service.send_sms()
CUANDO `sms_service.send_sms()` envía un SMS, el sistema DEBE persistir el mensaje en `sms_messages` con `direction='sent'` y `status='pending'` ANTES de delegar el envío físico a mmcli, y DEBE actualizar el `status` a `'sent'` o `'failed'` según el resultado.
