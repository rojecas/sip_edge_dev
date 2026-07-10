# Lecciones para el Reviewer

## Trazabilidad y cobertura
- Verifica que CADA R<n> del spec tenga al menos un test concreto mapeado.
  No aceptes "cobertura implicita" como excusa.
- El implementer DEBE documentar el mapa R<n> -> test en su informe
  (harness/progress/impl_<name>.md). Si no esta, rechaza directamente.

## Encoding en archivos revisados
- Si ves caracteres como "A!" donde deberia haber "a", "A3" donde
  deberia haber "o", o "A+-A'" donde deberia haber "->", el archivo
  tiene corrupcion de encoding. No apruebes hasta que este corregido.
- La causa tipica es doble codificacion UTF-8 -> CP-1252 -> UTF-8.
- Pide al implementer que lea harness/learnings/common.md seccion Encoding.
