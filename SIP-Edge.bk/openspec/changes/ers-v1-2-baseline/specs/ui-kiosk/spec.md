## ADDED Requirements

### Requirement: Interfaz estilo kiosco
La UI SHALL estar diseñada para pantallas ≥13" con teclado y mouse, con feedback visual mediante códigos de color universales (Verde=Éxito, Rojo=Error, Amarillo=Procesando).

#### Scenario: Pesaje exitoso muestra verde
- **WHEN** el operador completa un pesaje exitosamente
- **THEN** la UI muestra indicador verde y confirma el registro

#### Scenario: Error de comunicación muestra rojo
- **WHEN** ocurre un error de comunicación con la báscula
- **THEN** la UI muestra indicador rojo con el mensaje de error correspondiente

#### Scenario: Procesamiento muestra amarillo
- **WHEN** el sistema está procesando una operación (ej: consulta al agente IA)
- **THEN** la UI muestra indicador amarillo mientras la operación está en curso

### Requirement: Campo de peso readonly
El campo de peso en la UI SHALL ser de solo lectura. Solo SHALL poder modificarse mediante respuesta serial válida de la báscula, excepto durante el modo manual de emergencia (RF-020).

#### Scenario: Operador no puede editar peso manualmente
- **WHEN** el operador intenta escribir en el campo de peso
- **THEN** el sistema impide la edición directa del campo

#### Scenario: Peso se actualiza desde báscula
- **WHEN** la báscula envía una respuesta serial válida
- **THEN** el sistema actualiza el campo de peso con el valor recibido

### Requirement: Selección en cascada Hacienda-Suerte
La UI SHALL cargar dinámicamente las suertes según la hacienda seleccionada.

#### Scenario: Selección de hacienda carga suertes
- **WHEN** el operador selecciona una hacienda en el formulario
- **THEN** el sistema carga y muestra solo las suertes activas de esa hacienda en el campo de suertes
