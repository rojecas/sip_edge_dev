# Review — feature 9 (emergency_mode)

**Veredicto:** CHANGES_REQUESTED

---

## T20 — Verificación de estado documentado

| Aspecto | Resultado | Detalle |
|---------|-----------|---------|
| 1. tasks.md T20 [x] | ❌ Contradictorio | T20 marcado [x] pero el texto finaliza con: **"PENDIENTE: Requiere acceso a la EdgeBox para verificación de hardware (Nivel 4)."** |
| 2. impl_emergency_mode.md T20 no dice "PENDIENTE" | ❌ Falla | Línea 5: *"Status: tasks T1-T19 completed, T20 pending (EdgeBox)"* — dice **pending**, no completado. Líneas 97-103: título "COMPLETADO" pero cuerpo son pasos sin ejecutar. |
| 3. closure-emergency_mode.md EdgeBox completada | ❌ Contradictorio | Línea 5: "T20 completado". Línea 13-14: "queda completado por requerir acceso al hardware real" (sintaxis rota, probablemente quiso decir "queda **pendiente**"). Líneas 40-61: Sección **"Pendiente: Verificacion EdgeBox"** lista comandos como tareas futuras. |
| 4. ./init.ps1 | ⚠️ Pasos 1-5 OK. Paso 6 timeout (tests unitarios ya verificados previamente). [WARN] sesión anterior abierta. | |
| 5. github_issue en feature_list.json | ✅ "github_issue": "https://github.com/rojecas/sip_edge/issues/9" | |

## Inconsistencias detectadas

Los 3 documentos que documentan T20 se contradicen entre sí:

1. **tasks.md** dice [x] pero añade "PENDIENTE"
2. **impl_emergency_mode.md** dice "T20 pending" en el status line
3. **closure-emergency_mode.md** dice "T20 completado" y a renglón seguido tiene una sección completa "Pendiente: Verificacion EdgeBox"

No es posible determinar si T20 está realmente completado o pendiente.

## Cambios requeridos

1. **tasks.md** — Si T20 está realmente completado: quitar la nota **PENDIENTE** de la línea 206. Si no lo está: cambiar [x] a [ ].
2. **impl_emergency_mode.md** — Línea 5: actualizar status a "T20 completed (EdgeBox)" si se ejecutó, o mantener "pending" si no. Líneas 97-103: o confirmar que los pasos se ejecutaron, o marcarlos claramente como no ejecutados.
3. **closure-emergency_mode.md** — Línea 13-14: corregir sintaxis. Si T20 no se ejecutó, cambiar "completado" por "pendiente". Si sí se ejecutó, eliminar la sección "Pendiente: Verificacion EdgeBox" (líneas 40-61) o reemplazarla por confirmación de ejecución.
4. **Cerrar sesión correctamente**: Ejecutar harness/scripts/close.ps1 para limpiar harness/.session.
