## ADDED Requirements

### Requirement: Configuración dinámica de puertos
El sistema SHALL proveer una interfaz gráfica para que el Administrador modifique rutas hardware (Báscula, Módem), baudrate y paridad sin editar archivos manualmente.

#### Scenario: Admin cambia puerto de báscula
- **WHEN** un Administrador selecciona un nuevo puerto serial y baudrate para la báscula
- **THEN** el sistema guarda la configuración y la aplica sin necesidad de reinicio completo

#### Scenario: Admin prueba conectividad
- **WHEN** un Administrador hace clic en "Test" para verificar comunicación serial/GSM
- **THEN** el sistema ejecuta una prueba de conectividad y muestra el resultado antes de guardar cambios

### Requirement: Persistencia de configuración
El sistema SHALL guardar la configuración en `config.yaml`, aplicarla automáticamente tras reinicio y sincronizar el reloj del sistema.

#### Scenario: Configuración persiste tras reinicio
- **WHEN** el sistema se reinicia
- **THEN** el sistema carga la configuración desde `config.yaml` y aplica todos los parámetros incluyendo puertos y sincronización de reloj

### Requirement: Rutina de respaldo automático
El sistema SHALL ejecutar una tarea diaria de volcado de base de datos (`dump.sql.gz`) con rotación FIFO de 30 días, eliminando el respaldo más antiguo al día 31.

#### Scenario: Respaldo diario exitoso
- **WHEN** se ejecuta la rutina diaria de respaldo
- **THEN** el sistema genera un `dump.sql.gz` con timestamp y elimina el archivo más antiguo si existen más de 30 respaldos

#### Scenario: Exportación a medios externos
- **WHEN** un Administrador solicita copiar respaldos a un USB/SD conectado
- **THEN** el sistema copia los archivos con verificación CRC32 y confirma la integridad

### Requirement: Modo manual de emergencia
El sistema SHALL permitir al Administrador activar un modo manual mediante comando SMS predefinido (`MANUAL_ON`), que desactiva temporalmente la restricción de peso readonly por un máximo de 15 minutos.

#### Scenario: Admin activa modo manual
- **WHEN** un Administrador envía el comando SMS `MANUAL_ON` al número del sistema
- **THEN** el sistema activa modo manual por 15 minutos, permitiendo edición del campo de peso en la UI

#### Scenario: Timeout de modo manual
- **WHEN** transcurren 15 minutos desde la activación del modo manual
- **THEN** el sistema desactiva automáticamente el modo manual y retorna el campo de peso a readonly
