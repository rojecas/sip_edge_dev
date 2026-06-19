# Plan — Frontend Admin: Configuración y Backup (Feature 15)

> Revisión y validación de spec existente. Estado final: `spec_ready`.

---

## Resumen de lo revisado

- **requirements.md** (99 líneas): 11 requirements en EARS estricto (R1–R11). Cubren
  todos los criterios de aceptación RF-F14-02a → RF-F14-02h. Cada R<n> es
  verificable. Sin verbos blandos. Sin IDs duplicados o faltantes. ✓

- **design.md** (80 líneas originales): Documenta arquitectura, archivos a verificar,
  comportamiento esperado de AdminConfig y AdminBackup, y estado actual del código.
  **Deficiencias encontradas y corregidas:**
  - ❌ Faltaba la sección obligatoria **Contrato API** (7 endpoints documentados).
  - ❌ El "problema conocido" de AdminBackup mencionaba `.items` extracción, pero
    el bug real es un **field name mismatch** entre frontend (español) y backend
    (inglés) en los nombres de campo del historial de backups.

- **tasks.md** (86 líneas originales): 12 tareas discretas en fase ordenada (F1–F3).
  Cada tarea referencia R<n>s. **Deficiencias encontradas y corregidas:**
  - ❌ Faltaba una tarea explícita para corregir el field name mismatch de
    AdminBackup. Se agregó **T6a**.

- **Código fuente verificado:**
  - `AdminConfig.svelte` — Correcto. Carga GET /api/config, guarda PUT /api/config,
    testea POST /api/config/test/{port}, timeouts con PUT /api/setup/session y
    PUT /api/setup/scale. Estados: loading, saving, testing, error, success.  ✓
  - `AdminBackup.svelte` — El fallback `result.items || result || []` maneja
    correctamente el array directo del backend, pero los field names no coinciden
    (CRITICAL: inglés vs español). Se documenta en spec para que el implementer lo corrija.
  - `constants.js` — Contiene todos los endpoints necesarios (CONFIG, CONFIG_TEST,
    SETUP_SESSION, SETUP_SCALE, BACKUP_STATUS, BACKUP_RUN). ✓
  - Backend endpoints — Todos existen y responden según lo documentado en Contrato API. ✓

## Cambios realizados

| Archivo | Cambio |
|---------|--------|
| `harness/specs/15_frontend_admin_operations/design.md` | Sección 6: Contrato API añadido (7 endpoints). Sección 7: Known issue corregido (field name mismatch en AdminBackup). |
| `harness/specs/15_frontend_admin_operations/tasks.md` | T6a añadido: corregir field name mismatch en AdminBackup. T6 actualizado para reflejar fallback real. |
| `harness/feature_list.json` | Feature 15 status: `"pending"` → `"spec_ready"`. |

## Conclusión

Spec validado y marcado como `spec_ready`. El spec cubre todos los acceptance
criteria, sigue EARS, tiene trazabilidad R<n> ↔ tareas, y documenta los problemas
conocidos reales. Pendiente de aprobación humana.
