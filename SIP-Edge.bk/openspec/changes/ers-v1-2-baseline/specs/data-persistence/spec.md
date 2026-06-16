## ADDED Requirements

### Requirement: Persistencia de registros de peso
El sistema SHALL almacenar en MariaDB los siguientes campos por cada pesaje: Peso, ID Usuario, Fecha, Hora, Tipo de Material, Hacienda, Suerte.

#### Scenario: Registro de pesaje exitoso
- **WHEN** el operador confirma un pesaje válido
- **THEN** el sistema persiste el registro en MariaDB con todos los campos requeridos y confirma visualmente el éxito

### Requirement: Integridad transaccional
El sistema SHALL garantizar que cada registro de peso y su metadata se persistan como una transacción atómica única con commit/rollback.

#### Scenario: Fallo en medio del registro
- **WHEN** ocurre un error de base de datos durante la inserción de un pesaje
- **THEN** el sistema ejecuta rollback y no persiste datos parciales; muestra mensaje de error al operador

### Requirement: Gestión de Haciendas
El sistema SHALL proveer una interfaz para que el Administrador cree, edite y desactive (borrado lógico) haciendas. Sin eliminación física si existen registros asociados.

#### Scenario: Admin crea una hacienda
- **WHEN** un Administrador ingresa el nombre de una nueva hacienda y guarda
- **THEN** el sistema crea la hacienda y la muestra en la lista de haciendas activas

#### Scenario: Admin intenta eliminar hacienda con registros
- **WHEN** un Administrador intenta eliminar físicamente una hacienda que tiene registros de pesaje asociados
- **THEN** el sistema rechaza la operación e indica que debe usar desactivación

### Requirement: Gestión de Suertes/Lotes
El sistema SHALL gestionar suertes vinculadas obligatoriamente a una Hacienda padre, con carga dinámica en cascada según la hacienda seleccionada.

#### Scenario: Carga de suertes por hacienda
- **WHEN** el operador selecciona una hacienda en el formulario de pesaje
- **THEN** el sistema carga dinámicamente solo las suertes activas asociadas a esa hacienda

#### Scenario: Creación de suerte vinculada
- **WHEN** un Administrador crea una nueva suerte seleccionando una hacienda padre
- **THEN** el sistema asocia la suerte a esa hacienda y la muestra al seleccionar la hacienda en pesaje
