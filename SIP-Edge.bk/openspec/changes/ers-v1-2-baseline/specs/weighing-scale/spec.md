## ADDED Requirements

### Requirement: Interacción bidireccional con báscula
El sistema SHALL comunicarse con la báscula mediante protocolo activo comando-respuesta sobre puerto serial RS232/USB. El sistema SHALL enviar comandos (string/hex) al puerto serial al presionar botones de control y esperar respuesta con timeout configurable entre 500ms y 3000ms (valor por defecto: 1500ms).

#### Scenario: Lectura de peso exitosa
- **WHEN** el operador presiona un botón de control (ej: Tara Total, Peso Mineral)
- **THEN** el sistema envía el comando serial correspondiente, recibe la respuesta dentro del timeout, y muestra el peso en la UI

#### Scenario: Timeout de comunicación serial
- **WHEN** el sistema envía un comando serial y no recibe respuesta dentro del timeout configurado
- **THEN** el sistema muestra un error "Sin respuesta de báscula" y permite reintentar

#### Scenario: Configuración de timeout
- **WHEN** un Administrador modifica el timeout de comunicación serial entre 500ms y 3000ms
- **THEN** el sistema aplica el nuevo timeout en la próxima comunicación
