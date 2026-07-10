# Lecciones para el Lider (Orquestador)

## Sesion 2026-07-09 — Apertura de Feature 13, spec-validator PoC
- Al reabrir una feature (spec ya existe, status incorrecto), no aplicar Caso A estandar.
- El spec-validator es un subagente `general` con instrucciones detalladas.
- Despues de spec-validator, el estado es `spec-reviewed`, NO `approved`.
- El humano sigue siendo la puerta entre `spec-reviewed` e `in_progress`.
- Siempre preservar respaldo de archivos originales (`.old.md`) antes de sobreescribir.
