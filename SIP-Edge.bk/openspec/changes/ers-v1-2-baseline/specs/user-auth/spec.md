## ADDED Requirements

### Requirement: Autenticación por credenciales
El sistema SHALL validar la identidad del usuario mediante usuario y contraseña con hash seguro bcrypt. El acceso a cualquier funcionalidad del sistema SHALL requerir autenticación previa.

#### Scenario: Login exitoso
- **WHEN** un usuario ingresa credenciales válidas (usuario y contraseña correctos)
- **THEN** el sistema concede acceso según el rol del usuario y registra el inicio de sesión

#### Scenario: Login fallido por contraseña incorrecta
- **WHEN** un usuario ingresa una contraseña incorrecta
- **THEN** el sistema rechaza el acceso y muestra un mensaje de error genérico ("Credenciales inválidas")

#### Scenario: Bloqueo por intentos fallidos
- **WHEN** un usuario excede 3 intentos fallidos consecutivos en 5 minutos
- **THEN** el sistema bloquea la cuenta temporalmente por 15 minutos

### Requirement: Control de Acceso Basado en Roles (RBAC)
El sistema SHALL restringir funcionalidades según el rol del usuario autenticado.

#### Scenario: Operador accede solo a pesaje
- **WHEN** un usuario con rol Operador inicia sesión
- **THEN** el sistema muestra únicamente el formulario de pesaje y los registros de su turno actual

#### Scenario: Administrador accede a configuración
- **WHEN** un usuario con rol Administrador inicia sesión
- **THEN** el sistema concede acceso total incluyendo configuración, gestión de usuarios y respaldos

#### Scenario: Operador intenta acceder a configuración
- **WHEN** un usuario con rol Operador intenta acceder a la interfaz de configuración
- **THEN** el sistema deniega el acceso y redirige al formulario de pesaje

### Requirement: Administración de Usuarios (CRUD)
El sistema SHALL proveer una interfaz gráfica para que el Administrador cree, lea, actualice y desactive usuarios (Nombre, Documento, Rol, Estado).

#### Scenario: Admin crea un nuevo usuario
- **WHEN** un Administrador completa el formulario de nuevo usuario con nombre, documento, rol y contraseña
- **THEN** el sistema crea el usuario con hash bcrypt de la contraseña y lo muestra en la lista de usuarios activos

#### Scenario: Admin desactiva un usuario
- **WHEN** un Administrador cambia el estado de un usuario a "inactivo"
- **THEN** el sistema aplica borrado lógico y ese usuario no puede iniciar sesión
