# Lecciones para el Spec-Author

## Trazabilidad ERS -> R<n>
- Cada requirement (R1, R2, ...) DEBE poderse mapear a un RF del ERS.
  Si un RF no tiene al menos un R<n> que lo implemente, el spec tiene un gap.
- El spec-validator (harness/docs/specs.md) verifica esta trazabilidad.
  Ejecuta tu mismo la verificacion antes de marcar spec_ready para evitar
  rechazos.

## Tamanio de specs
- Limite duro: 20 requirements por feature. Si el analisis produce mas,
  divide en sub-features (ej: 14a, 14b, 14c).
- Un spec de 40+ requirements es inmanejable para el implementer y el
  reviewer. La division temprana ahorra retrabajo.
