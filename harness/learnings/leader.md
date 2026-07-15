# Lecciones para el Lider (Orquestador)

## Sesion 2026-07-09 — Apertura de Feature 13, spec-validator PoC
- Al reabrir una feature (spec ya existe, status incorrecto), no aplicar Caso A estandar.
- El spec-validator es un subagente `general` con instrucciones detalladas.
- Despues de spec-validator, el estado es `spec-reviewed`, NO `approved`.
- El humano sigue siendo la puerta entre `spec-reviewed` e `in_progress`.
- Siempre preservar respaldo de archivos originales (`.old.md`) antes de sobreescribir.

## Sesion 2026-07-09 - Correccion de fase testing
- JAMAS preguntar autorizo cierre al entrar en testing
- testing significa: el humano prueba. Solo anuncias Feature/Bug en testing - avisame cuando termines las pruebas
- El humano dira autorizo cierre cuando este listo

## Sesion 2026-07-14/15 — F28 ai_multi_turn + sesion multi-objetivo
- El dispatcher v2 se reinicia en cada restart del servicio (no persiste estado).
- Nunca implementar fixes sin discutir primero con el usuario (error: modifique message_exists_by_modem_id dos veces innecesariamente).
- La deteccion de auto-generados por modem_id causa mas problemas de los que resuelve. Confiar en status != received del modem.
- SESSION_REMINDER debe actualizarse en cada cierre de sesion, no eliminarse.
- Para sesiones largas con multiples features: documentar cada hallazgo a medida que ocurre.
