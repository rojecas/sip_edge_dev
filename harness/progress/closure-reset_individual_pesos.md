## Resumen

Se reemplazo el boton unico de Reset general de la medida actual por tres botones de reset individual, uno por cada campo de peso (peso_muestra, peso_mineral, peso_vegetal_extrano) en el formulario de pesaje del kiosko. Cada boton Reset borra solo ese valor, permitiendo al operador corregir un error en una sola lectura sin perder las otras dos.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/weighings.py` | Schema `ResetFieldRequest` + endpoint `POST /api/weighings/reset` modificado con step opcional |
| `frontend/src/components/WeightField.svelte` | Prop `onReset` + boton "Reset" individual |
| `frontend/src/components/KioskForm.svelte` | 3 manejadores de reset individual + reset general relegado a "Limpiar todo" secundario |
| `tests/test_weighings.py` | 4 tests nuevos de reset individual |
| `frontend/src/components/__tests__/WeightField.test.js` | Nuevo archivo con 3 tests |

## Trazabilidad

- R1 (boton Reset junto a cada peso): WeightField.test.js
- R2 (solo ese campo se limpia): WeightField.test.js + test_reset_individual_step_valid
- R4-R8 (endpoint, validacion, backward compat, auth): test_weighings.py

## Verificacion

- [x] Backend: 4 tests nuevos en test_weighings.py
- [x] Frontend: 3 tests en WeightField.test.js
- [x] Review: APPROVED
- [x] Feature registrada en tracker.json
- [x] feature_list.json status = done
- [x] GitHub issue #21 creado

## Decisiones tecnicas

- El endpoint acepta body opcional para mantener backward compatibility con clientes que envian POST sin body (reset general)
- Los steps validos se definen en `VALID_RESET_STEPS` en weighings.py
- En el frontend, el boton Reset solo se renderiza si `onReset` no es null, permitiendo reuso de WeightField en otros contextos

## Lecciones

- La backward compatibility del endpoint POST /api/weighings/reset (sin body = reset general) evita romper clientes existentes
- El componente WeightField se diseno generico: si no hay onReset, no se muestra el boton
