## ADDED Requirements

### Requirement: Botón "Enviar a LIMS" en formulario de pesaje
La UI del kiosko SHALL incluir un botón "Enviar a LIMS" en el formulario de pesaje. El botón SHALL permanecer deshabilitado hasta que todos los campos obligatorios del formulario estén completos (tipo de material, peso, hacienda, suerte, guía, vagón). Una vez completos, el botón se habilita para que el operador lo presione.

#### Scenario: Botón deshabilitado con datos incompletos
- **WHEN** el formulario de pesaje tiene campos obligatorios sin completar
- **THEN** el botón "Enviar a LIMS" se muestra pero deshabilitado (gris)

#### Scenario: Botón habilitado con datos completos
- **WHEN** todos los campos obligatorios del formulario de pesaje están completos y válidos
- **THEN** el botón "Enviar a LIMS" se habilita para su pulsación

#### Scenario: Envío exitoso muestra feedback visual
- **WHEN** el operador presiona "Enviar a LIMS" y el envío es exitoso
- **THEN** el sistema muestra indicador visual verde con mensaje "Datos enviados a LIMS"

#### Scenario: Error de envío muestra feedback visual
- **WHEN** el operador presiona "Enviar a LIMS" y el envío falla
- **THEN** el sistema muestra indicador visual rojo con mensaje "Error al enviar a LIMS" y el botón permanece habilitado para reintentar
