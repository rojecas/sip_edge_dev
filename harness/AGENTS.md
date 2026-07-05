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

### Estado: DRY_RUN activo, 0 SMS reales. SIM bloqueada.

### Lo que funciona
- Filtro autorizacion: solo admin (3502490204) y corresponsal (3002162251) reciben respuestas
- DRY_RUN: SMS_DRY_RUN=true en .env, sin envios reales
- Rate limiter: 60s entre envios al mismo numero
- DeepSeek como backend primario con circuit breaker
- Schemas DB local/remoto identicos (tipo_cosecha ya migrado en EdgeBox)

### Problema PENDIENTE: DeepSeek no consulta la BD
- Herramientas SQL (12) estan definidas y funcionan (verificar con scripts/Consulta.py)
- tool_choice=required en llm_client.py
- Pero el LLM responde con datos inventados ("2024", "0 registros") sin llamar tools
- Verificar: logs del llamador a DeepSeek, payload enviado, respuesta recibida

### Para probar (con DRY_RUN, sin SIM)
1. Limpiar sms_messages
2. Corresponsal envia "cuantas toneladas el 24 de junio"
3. Verificar en BD que la tool SI se ejecuto (respuesta no dice "2024")

### Cuando funcione con DRY_RUN
4. Conseguir SIM nueva
5. Quitar SMS_DRY_RUN del .env
6. Probar F12 (password reset SMS)
7. Probar F9 (emergencia SMS)
8. Release-manager para F27 y Bug 26

### Linea de tiempo de SIMs
- SIM #1 (573013643187): quemada 2026-07-03 por ~40 SMS sin rate limiter
- SIM #2 (573008163109): quemada 2026-07-04 por loop retroalimentacion sin rate limiter
- SIM #3: NO INSERTAR hasta que DRY_RUN confirme todo el flujo

<!-- SESSION_REMINDER_END -->





