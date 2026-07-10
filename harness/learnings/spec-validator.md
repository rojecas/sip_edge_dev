# Lecciones para el Spec-Validator

## Variante A (spec nuevo)
- Verificar que cada RF del ERS tiene al menos un R<n> cubriendolo.
- Confirmar semanticamente que los R<n> implementan la solucion correcta,
  no solo que "mencionan" el RF.
- Si hay gaps, reportarlos y sugerir R<n> adicionales.

## Variante B (auditor + corrector)
- Antes de corregir, renombrar archivos originales a *.old.md para preservar
  trazabilidad.
- Cada correccion debe documentarse en harness/progress/spec_review_<name>.md
  con tabla de trazabilidad ERS -> R<n>.
- El archivo de informe DEBE incluir: hallazgos, archivos modificados,
  archivos nuevos requeridos, y lista de archivos a modificar por el
  implementer.
