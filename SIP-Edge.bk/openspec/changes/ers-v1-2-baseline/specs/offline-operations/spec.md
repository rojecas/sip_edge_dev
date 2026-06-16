## ADDED Requirements

### Requirement: Operación offline garantizada
El sistema SHALL operar al 100% sin conexión a internet. La falta de señal GSM SHALL afectar únicamente el envío de SMS, no el registro de pesajes ni la funcionalidad principal.

#### Scenario: Pesaje sin conexión GSM
- **WHEN** no hay señal GSM disponible
- **THEN** el sistema registra el pesaje normalmente y pone en cola los SMS pendientes para envío posterior

#### Scenario: Pesaje sin internet
- **WHEN** no hay conexión a internet
- **THEN** el sistema opera con normalidad, sin afectación a ninguna funcionalidad

### Requirement: Recuperación ante fallos
El sistema SHALL gestionar servicios críticos mediante systemd con `Restart=always` y watchdog de 30 segundos.

#### Scenario: Servicio se detiene inesperadamente
- **WHEN** un servicio crítico del sistema se detiene por error
- **THEN** systemd reinicia automáticamente el servicio y se registra el evento

#### Scenario: Watchdog detecta falta de respuesta
- **WHEN** un servicio no responde al watchdog por más de 30 segundos
- **THEN** systemd fuerza el reinicio del servicio
