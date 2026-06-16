## MODIFIED Requirements

### Requirement: Interacción bidireccional con báscula vía RS-485
El sistema SHALL comunicarse con la báscula mediante protocolo activo comando-respuesta sobre bus RS-485 en modo half-duplex, utilizando un adaptador USB-RS485. El sistema SHALL controlar la dirección de transmisión (TX/RX) mediante el pin RTS del puerto USB serial o un GPIO dedicado. El sistema SHALL soportar direccionamiento de dispositivos en el bus RS-485 según configuración.

El sistema SHALL enviar comandos (string/hex) al puerto serial al presionar botones de control y esperar respuesta con timeout configurable entre 500ms y 3000ms (valor por defecto: 1500ms).

#### Scenario: Lectura de peso exitosa en RS-485
- **WHEN** el operador presiona un botón de control (ej: Tara Total, Peso Mineral)
- **THEN** el sistema activa el modo transmisión (RTS alto), envía el comando con la dirección del dispositivo, cambia a modo recepción (RTS bajo), recibe la respuesta dentro del timeout, y muestra el peso en la UI

#### Scenario: Timeout de comunicación RS-485
- **WHEN** el sistema envía un comando serial y no recibe respuesta dentro del timeout configurado
- **THEN** el sistema muestra un error "Sin respuesta de báscula" y permite reintentar

#### Scenario: Configuración de timeout y dirección RS-485
- **WHEN** un Administrador modifica el timeout (500ms-3000ms) o la dirección del dispositivo RS-485
- **THEN** el sistema aplica los nuevos valores en la próxima comunicación

## ADDED Requirements

### Requirement: Configuración de terminación RS-485
El sistema SHALL permitir habilitar o deshabilitar la terminación del bus RS-485 mediante configuración en `config.yaml` e interfaz Admin, reflejando el estado físico del puente de terminación en el adaptador.

#### Scenario: Admin configura terminación
- **WHEN** un Administrador activa la terminación RS-485 en la configuración
- **THEN** el sistema registra el cambio y muestra una nota recordando verificar el puente físico de terminación en el adaptador

### Requirement: Detección de colisiones en bus RS-485
El sistema SHALL implementar un mecanismo de detección de colisiones en el bus half-duplex, con reintento automático después de un backoff aleatorio.

#### Scenario: Colisión en el bus
- **WHEN** el sistema detecta datos corruptos o sin sentido inmediatamente después de cambiar a modo recepción
- **THEN** el sistema espera un backoff aleatorio (50-200ms) y reintenta el comando hasta 3 veces antes de reportar error

## REMOVED Requirements

### Requirement: Interacción bidireccional con báscula
**Reason**: Reemplazado por el nuevo requisito RS-485 que incluye control half-duplex y direccionamiento
**Migration**: Actualizar adaptador USB-RS232 a USB-RS485 y configurar dirección de dispositivo en Admin
