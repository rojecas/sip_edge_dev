## ADDED Requirements

### Requirement: Gestor de mensajes SMS
El sistema SHALL enviar mensajes SMS a un listado preconfigurado de usuarios autorizados mediante módulo GSM utilizando comandos AT sobre puerto serial.

#### Scenario: Envío de SMS exitoso
- **WHEN** el sistema necesita enviar una notificación SMS
- **THEN** envía el comando AT correspondiente al módulo GSM y confirma la entrega

#### Scenario: Fallo en envío SMS
- **WHEN** el módulo GSM no responde o la señal es insuficiente
- **THEN** el sistema registra el error en log y reintenta según política configurada

### Requirement: Reportes programados
El sistema SHALL enviar automáticamente un resumen de turno a las 06:00, 14:00 y 22:00, con horarios configurables por el Administrador.

#### Scenario: Reporte automático de turno
- **WHEN** son las 06:00, 14:00 o 22:00 (u horario configurado por Admin)
- **THEN** el sistema compila el resumen del turno anterior y lo envía vía SMS a los destinatarios configurados

#### Scenario: Admin configura horario de reporte
- **WHEN** un Administrador modifica los horarios de reporte programado
- **THEN** el sistema aplica los nuevos horarios para los próximos envíos

### Requirement: Alertas de seguridad
El sistema SHALL notificar inmediatamente vía SMS cualquier intento de operación por usuarios con rol no autorizado o sesión expirada.

#### Scenario: Intento de acceso no autorizado
- **WHEN** un usuario con rol no autorizado intenta realizar una operación restringida
- **THEN** el sistema envía una alerta SMS inmediata a los administradores y registra el evento

#### Scenario: Sesión expirada
- **WHEN** un usuario intenta realizar una operación con sesión expirada
- **THEN** el sistema redirige a la pantalla de login y envía alerta SMS al administrador
