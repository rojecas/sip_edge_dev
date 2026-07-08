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
## Recordatorio — Proxima sesion (2026-07-08)

### Lo que funcionó
- **Sincronizacion de tablas:** users (remoto→local), haciendas/suertes/weighings (local→remoto) completada
- **Script generador:** `scripts/generate_historical_weighings.py` — 4221 pesajes historicos (65 dias × ~65/dia)
- **Arquitectura SMS revisada:** 5 modulos analizados (sms_service, sms_persistence, sms_dispatcher_v2, sms_send_queue, emergency_mode)

### Estado del repositorio
- Bug 26 (emergency_request_wrong_sms) → **triaged** ← PROXIMA ACCION
- Bug 29 (scale_service_async_crashes) → **triaged**
- F28 (ai_multi_turn) → **pending**
- F17 (frontend_analytics) → **pending**

### Pendiente para la proxima sesion
1. **Bug #26** (emergency_request_wrong_sms) — lanzar bug-fixer
   - Symptom: al solicitar modo manual desde kiosco, el admin recibe "Lo siento, el
     sistema de analisis no esta disponible" en vez de la solicitud de emergencia
   - Causa raiz en `src/agent_orchestrator.py:175` dentro de `handle_sms_query()`
   - Bug-fixer debe diagnosticar por qué el emergency handler deriva al AI handler

### Configuracion actual
| Parametro | Valor |
|-----------|-------|
| AI_PRIMARY_BACKEND | remote (DeepSeek API) |
| SMS_DRY_RUN | false (en EdgeBox) |
| DEV_MODE | true (local) |
| MariaDB local | v10.5 (Docker) |
| MariaDB remoto | v11.8 (EdgeBox) |
| Diferencia collation | utf8mb4_general_ci vs utf8mb4_uca1400_ai_ci |

<!-- SESSION_REMINDER_END -->







## 2. Flujo de trabajo: Como descomponer tareas

Este es el flujo que el agente lider debe seguir para procesar features y bugs.
Lee siempre el status de la primera entrada no-`done` / no-`blocked` en `harness/feature_list.json`
y aplica el caso correspondiente.

### Caso A — status == `"pending"` Y type == `"feature"` Y sdd == `true`

1. Lanza **1 subagente `spec-author`** pasandole `id` y `name`.
2. El `spec-author` redacta `harness/specs/{NN}_{name}/{requirements.md, design.md, tasks.md}` y cambia el status a `spec_ready`.
3. **PARAS.** No lanzas implementer. Tu mensaje al humano:
   > "Spec listo en `harness/specs/{NN}_{name}/`. Revisalo y di **'aprobado'** para continuar con la implementacion, o pideme cambios."

### Caso B — status == `"spec_ready"` Y el humano acaba de aprobar (feature SDD)

1. Cambia el status a `in_progress` en `harness/feature_list.json`.
2. Lanza **1 subagente `implementer`** pasandole la ruta `harness/specs/{NN}_{name}/` como input.
   El `implementer` trabaja a partir del spec, no del `acceptance` original.
3. Cuando termine -> lanza **1 `reviewer`** que verifica trazabilidad tests <-> requirements
   y que `tasks.md` queda completo.
4. Cuando el reviewer apruebe -> cambia el status a `testing`. **PARAS.**
   Pregunta al humano: "Implementacion lista. **autorizo cierre**?"
5. Cuando el humano autorice el cierre -> lanza **1 subagente `release-manager (register)`**
   pasandole `id` y `name`.

### Caso C — status == `"spec_ready"` SIN aprobacion humana

NO continues. El humano todavia no ha leido el spec. Recuerdale que le toca.

### Caso D — status == `"in_progress"`

Sesion interrumpida. Pregunta al humano si reanudas al implementer o abortas.

### Caso E — `type: "bug"`, status == `"untriaged"`

1. Presenta el bug al humano: description, reproduction, affected features.
2. Pregunta: "confirmas que este bug es valido?"
3. Si humano confirma:
   a. Cambia el status a `"triaged"` en `harness/feature_list.json`.
4. Si humano rechaza -> pregunta si marcar `done` con justificacion `"rejected"` o mantener `untriaged`.

### Caso F — `type: "bug"`, status == `"triaged"`

1. Verifica que no haya otro item en curso (feature en `in_progress` u otro bug siendo atendido).
2. Lanza **1 subagente `bug-fixer`** pasandole `id` y `name`.
3. Cuando el `bug-fixer` reporta `done`:
   a. Lanza **1 `reviewer`** con instrucciones de revision de bug (verificar `reproduction` cubierto por test, no exigir trazabilidad R<n>).
   b. Si el reviewer aprueba -> cambia el status a `testing`. **PARAS.**
      Pregunta al humano: "Bug listo. **autorizo cierre**?"
   c. Si el reviewer rechaza -> reabre con `triaged` para que el bug-fixer corrija.
4. Cuando el humano autorice el cierre (desde `testing`):
   a. Lanza **1 subagente `release-manager (register)`** pasandole `id` y `name`.
5. Si el `bug-fixer` reporta `blocked`:
   a. Mantiene `blocked` y documenta la razon en `progress/current.md`.

### Caso G — `type: "bug"`, status == `"in_progress"`

Sesion interrumpida. Pregunta al humano si reanudar al `bug-fixer` o abortar.

### Caso H — `sdd: false` (o sin `sdd`) Y `type` no es `"bug"`, status == `"pending"`

1. Cambia el status a `in_progress` en `harness/feature_list.json`.
2. Lanza **1 subagente `implementer`** con instruccion: "sin carpeta `specs/`, trabaja desde `acceptance`
   en `feature_list.json`, crea `harness/progress/plan-<name>.md` antes de tocar codigo".
3. Cuando termine -> lanza **1 `reviewer`**.
4. Cuando el reviewer apruebe -> cambia el status a `testing`. **PARAS.**
   Pregunta al humano: "Implementacion lista. **autorizo cierre**?"
5. Cuando el humano autorice el cierre -> lanza **1 subagente `release-manager (register)`**
   pasandole `id` y `name`.

