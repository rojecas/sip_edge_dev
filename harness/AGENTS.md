# AGENTS.md â€” Mapa de navegacion para agentes de IA

> Este archivo es el **punto de entrada** para cualquier agente que trabaje en este
> repositorio. NO es una biblia de reglas: es un **mapa**. Lee solo lo que
> necesites cuando lo necesites (divulgacion progresiva).

---

## 1. Antes de empezar (obligatorio)

1. Ejecuta `./init.ps1` y verifica que termina sin errores. Si falla, **para**
   y resuelve el entorno antes de tocar codigo.
2. Si `init.ps1` reporto `[WARN]` en la seccion 1.5 (`.session = open`), advierte
   al usuario: "La sesion anterior no se cerro correctamente. Revisa
   harness/progress/current.md". Pregunta si desea continuar o ejecutar
   `./scripts/close.ps1` primero.
3. Escribe `open` en `harness/.session` para activar el fusible de proteccion.
   El script `./scripts/close.ps1` lo pondra en `closed` al finalizar.
4. Lee `harness/progress/current.md` para entender en que estado quedo la ultima sesion.
5. Lee `harness/feature_list.json`. Toda feature nueva (`"sdd": true`) pasa por
   **Spec Driven Development** â€” ver `harness/docs/specs.md` y S4 de este archivo.
6. Lee `harness/docs/specs.md` antes de tocar cualquier spec o feature `sdd: true`.
7. Lee `harness/docs/sessions.md` para conocer el estandar de documentacion
   (planes, cierres, bloqueos).
8. **Session reminder:** Revisa si hay contenido entre las marcas
   <!-- SESSION_REMINDER_START -->
## Recordatorio — Proxima sesion (2026-07-05)

### Bugs resueltos en esta sesion
- **Bug A (tool_choice=required en 2da vuelta):** FIXED — DeepSeek ahora parafrasea correctamente.
- **Bug B1/B2/B3 (loop SMS huerfanos):** FIXED — _delete_orphan_sms, filtro unknown, DRY_RUN completo.
- **modem_sms_id:** FIXED — se puebla tanto para entrantes como salientes.
- **Logging LLM:** AHORA DISPONIBLE — `journalctl -u sip-edge -f | grep "LLM:"`

### Estado actual EdgeBox
- F27 (sms_persistence) → **DONE**
- Bug 26 (emergency_request_wrong_sms) → **TRIAGED** — pendiente de probar con SIM nueva
- AI_PRIMARY_BACKEND=local (Qwen 1.5B en puerto 8080, taskset -c 0-2 -t 3)
- phpMyAdmin en :8081
- SMS_DRY_RUN=true
- llm_timeout=240s

### Pendiente: Probar Bug 26 con SIM nueva
1. Insertar SIM #3
2. Quitar SMS_DRY_RUN del .env
3. Probar solicitud de emergencia desde kiosko (POST /api/emergency/request)
4. Verificar que el admin recibe el SMS correcto (no el mensaje de error del LLM)
5. Verificar que responder "manual on" activa el modo manual
6. Si todo funciona → release-manager para Bug 26

### Linea de tiempo de SIMs
- SIM #1 (573013643187): quemada 2026-07-03 por ~40 SMS sin rate limiter
- SIM #2 (573008163109): quemada 2026-07-04 por loop retroalimentacion sin rate limiter
- SIM #3: NO INSERTAR hasta que DRY_RUN confirme todo el flujo (YA confirmado)

<!-- SESSION_REMINDER_END -->






