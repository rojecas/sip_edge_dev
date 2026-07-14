# AGENTS.md Ã¢â‚¬â€ Mapa de navegacion para agentes de IA

> Este archivo es el **punto de entrada** para cualquier agente que trabaje en este
> repositorio. NO es una biblia de reglas: es un **mapa**. Lee solo lo que
> necesites cuando lo necesites (divulgacion progresiva).

---

## 1. Antes de empezar (obligatorio)

1. Ejecuta `harness/init.ps1` (o `.\harness\init.ps1` en PowerShell) y verifica que termina sin errores. Si falla, **para**
   y resuelve el entorno antes de tocar codigo.
2. Si `init.ps1` reporto `[WARN]` en la seccion 1.5 (`.session = open`), advierte
   al usuario: "La sesion anterior no se cerro correctamente. Revisa
   harness/progress/current.md". Pregunta si desea continuar o ejecutar
   `./scripts/close.ps1` primero.
3. Escribe `open` en `harness/.session` para activar el fusible de proteccion.
   El script `./scripts/close.ps1` lo pondra en `closed` al finalizar.
4. Lee `harness/progress/current.md` para entender en que estado quedo la ultima sesion.
5. Lee `harness/feature_list.json`. Toda feature nueva (`"sdd": true`) pasa por
   **Spec Driven Development** Ã¢â‚¬â€ ver `harness/docs/specs.md` y S4 de este archivo.
6. Lee `harness/docs/specs.md` antes de tocar cualquier spec o feature `sdd: true`.
7. Lee `harness/docs/sessions.md` para conocer el estandar de documentacion
   (planes, cierres, bloqueos).
8. Lee las lecciones acumuladas en harness/learnings/. Primero common.md
   (herramientas disponibles, reglas de escritura), luego el archivo especifico
   de tu rol si existe:
   - leader.md para el agente lider
   - implementer.md para el implementer
   - reviewer.md para el reviewer
   - spec-author.md para el spec-author
- spec-validator.md para el spec-validator (subagente general)

## 2. Flujo de trabajo: Como descomponer tareas

Este es el flujo que el agente lider debe seguir para procesar features y bugs.
Lee siempre el status de la primera entrada no-`done` / no-`blocked` en `harness/feature_list.json`
y aplica el caso correspondiente.

### Caso A — status == `"pending"` Y type == `"feature"` Y sdd == `true`

1. Lanza **1 subagente `spec-author`** pasandole `id` y `name`.
2. El `spec-author` redacta `harness/specs/{NN}_{name}/{requirements.md, design.md, tasks.md}` y cambia el status a `spec_ready`.
3. Lanza **1 subagente `spec-validator`** (subagente `general` con instrucciones detalladas). El spec-validator audita el spec contra los RF del ERS, cierra gaps, cambia el status a `spec-reviewed`, y renombra los archivos originales a `*.old.md` si aplica correcciones.
4. **PARAS.** No lanzas implementer. Tu mensaje al humano:
   > "Spec validado en `harness/specs/{NN}_{name}/`. Revisalo y di **'aprobado'** para continuar con la implementacion, o pideme cambios."

### Caso B — status == `"spec-reviewed"` Y el humano acaba de aprobar (feature SDD)

1. Cambia el status a `in_progress` en `harness/feature_list.json`.
2. Lanza **1 subagente `implementer`** pasandole la ruta `harness/specs/{NN}_{name}/` como input.
   El `implementer` trabaja a partir del spec, no del `acceptance` original.
3. Cuando termine -> lanza **1 `reviewer`** que verifica trazabilidad tests <-> requirements
   y que `tasks.md` queda completo.
4. Cuando el reviewer apruebe -> cambia el status a `testing`. **PARAS.**
   Anuncia: "Feature en `testing` — avisame cuando termines las pruebas."
5. Cuando el humano autorice el cierre -> lanza **1 subagente `release-manager (register)`**
   pasandole `id` y `name`.

### Caso C — status == `"spec-reviewed"` SIN aprobacion humana

NO continues. El spec ya fue validado por el spec-validator pero el humano todavia no lo ha aprobado. Recuerdale que le toca.

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
      Anuncia: "Bug en `testing` — avisame cuando termines las pruebas."
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
   Anuncia: "Feature en `testing` — avisame cuando termines las pruebas."
5. Cuando el humano autorice el cierre -> lanza **1 subagente `release-manager (register)`**
   pasandole `id` y `name`.

