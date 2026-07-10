# Plan: Bug #31 — sms_dispatcher_v2_crashes

## Sintoma
- Al recibir un SMS entrante, `IncomingSmsDispatcherV2._dispatch()` persiste correctamente el SMS en `sms_messages`, pero al intentar validar el whitelist (línea 299) lanza `AttributeError: 'SmsPersistenceService' object has no attribute 'get_user_role_by_phone'`.
- El SMS queda persistido con `handler=NULL` y la conversación sin procesar.
- El comando nunca se ejecuta (no se delega a ningún handler).

## Causa raiz
- `sms_dispatcher_v2.py:299` llama `self._persistence.get_user_role_by_phone(sender_phone)`.
- El método **nunca fue implementado** en `SmsPersistenceService` (`src/sms_persistence.py`).
- La clase `SmsPersistenceService` solo sabe de `SmsConversation` y `SmsMessage`, no de `User`.

## Archivos implicados
| Archivo | Cambio |
|---------|--------|
| `src/sms_persistence.py` | Agregar `User` al import de `src.models`. Agregar método `get_user_role_by_phone()`. |
| `tests/test_sms_persistence.py` | Agregar tests para el nuevo método. |

## Fix propuesto
1. **Import**: Agregar `User` a la línea `from src.models import SmsConversation, SmsMessage`.
2. **Nuevo método** `get_user_role_by_phone(self, phone: str) -> str | None`:
   - Abre sesión de BD.
   - Busca `User` por `phone`.
   - Si encuentra, retorna `user.role` (string).
   - Si no, retorna `None`.
   - Cierra sesión en `finally`.

## Plan de verificación
1. Test: `test_get_user_role_by_phone_returns_role` — crea usuario con phone y role, verifica retorno correcto.
2. Test: `test_get_user_role_by_phone_returns_none_for_unknown` — phone no registrado retorna None.
3. Ejecutar `./init.ps1` para verificar que todos los tests pasan.
