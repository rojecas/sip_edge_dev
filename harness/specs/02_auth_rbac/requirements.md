# Requirements — auth_rbac (EARS)

> Feature: Autenticacion JWT, RBAC y Bloqueo por Inactividad
> Covers: RF-001, RF-002, RNF-008
> Depends on: feature 1 (system_config)

---

## Autenticacion (Login)

### R1
CUANDO un cliente HTTP realiza `POST /api/auth/login` con un body JSON
`{"username": "<str>", "password": "<str>"}`, el sistema DEBE verificar las
credenciales contra la tabla `users` en MariaDB. Si las credenciales son
validas, el sistema DEBE devolver status 200 con un body JSON
`{"access_token": "<jwt>", "token_type": "bearer", "role": "<rol>"}`.

### R2
CUANDO el sistema genera un token JWT para un usuario autenticado, el payload
DEBE contener los claims `sub` (user_id como string), `role` (rol del usuario)
y `iat` (timestamp Unix de emision). El algoritmo de firma DEBE ser HS256 y la
clave secreta DEBE leerse de la variable de entorno `JWT_SECRET_KEY`.

### R3
SI `POST /api/auth/login` recibe credenciales invalidas (username inexistente o
password incorrecta) ENTONCES el sistema DEBE devolver status 401 con
`{"detail": "Invalid username or password"}`.

### R4
SI `POST /api/auth/login` recibe un body que no contiene los campos `username` y
`password`, o los campos estan vacios, ENTONCES el sistema DEBE devolver status
422 con un mensaje de error descriptivo.

### R5
El sistema DEBE almacenar las contrasenas de los usuarios exclusivamente como
hashes bcrypt. El sistema NO DEBE almacenar ni transmitir contrasenas en texto
plano en ningun momento.

### R6
CUANDO un usuario con rol `corresponsal` intenta autenticarse via
`POST /api/auth/login`, el sistema DEBE devolver status 403 con
`{"detail": "Corresponsal role does not permit system login"}`.

---

## Proteccion de Endpoints (JWT + RBAC)

### R7
CUANDO una peticion HTTP incluye un header `Authorization: Bearer <token>`, el
sistema DEBE extraer y validar el token JWT mediante una dependencia FastAPI
`get_current_user`. Si el token es valido, la dependencia DEBE inyectar un
objeto con los campos `user_id` (int) y `role` (str) en el endpoint.

### R8
SI una peticion HTTP a un endpoint protegido NO incluye el header
`Authorization: Bearer <token>`, o el token esta expirado, o la firma es
invalida, ENTONCES el sistema DEBE devolver status 401 con
`{"detail": "Not authenticated"}`.

### R9
SI una peticion HTTP a un endpoint protegido incluye un token JWT valido pero
con un formato de payload incorrecto (falta `sub`, `role` o `iat`), ENTONCES el
sistema DEBE devolver status 401 con un mensaje de error descriptivo.

### R10
El sistema DEBE proporcionar una dependencia `require_role(role: str)` que
verifique que el rol extraido del token coincide con el rol requerido. SI el rol
no coincide ENTONCES el sistema DEBE devolver status 403 con
`{"detail": "Insufficient permissions"}`.

### R11
MIENTRAS un usuario tiene rol `admin`, el sistema DEBE permitirle acceso a todos
los endpoints protegidos (`/api/config`, `/api/config/test/*`,
`/api/setup/session` y cualquier endpoint futuro).

### R12
MIENTRAS un usuario tiene rol `operator`, el sistema DEBE restringirle el
acceso exclusivamente a endpoints bajo `/api/weighing/*`. Cualquier intento de
acceder a `/api/config`, `/api/setup/*` u otros endpoints de administracion
DEBE devolver status 403.

---

## Bloqueo por Inactividad (Kiosk Mode)

### R13
CUANDO una peticion HTTP autenticada es procesada, el sistema DEBE verificar
que el tiempo transcurrido desde la emision del token (`iat`) no exceda el
`session_timeout_minutes` configurado. SI el timeout es excedido ENTONCES el
sistema DEBE devolver status 401 con
`{"detail": "Session expired due to inactivity"}`.

### R14
El sistema DEBE leer el valor `session_timeout_minutes` desde la seccion
`session` de `config.yaml`. SI la seccion `session` no existe en el archivo, el
sistema DEBE usar el valor por defecto de 15 minutos.

### R15
CUANDO un cliente HTTP autenticado con rol `admin` realiza
`PUT /api/setup/session` con body JSON `{"session_timeout_minutes": <int>}`,
el sistema DEBE validar que el valor sea un entero positivo (> 0), persistir el
cambio atomicamente en `config.yaml`, y devolver status 200 con el nuevo valor.

### R16
SI `PUT /api/setup/session` recibe un valor `session_timeout_minutes` <= 0 o
no entero, ENTONCES el sistema DEBE devolver status 422 con un mensaje de error
descriptivo.

### R17
El sistema DEBE proporcionar una dependencia `check_inactivity` que se ejecute
en cada peticion autenticada y aplique la logica de timeout de inactividad
(R13). Esta dependencia DEBE ejecutarse despues de `get_current_user` (R7).

---

## Base de Datos (MariaDB)

### R18
CUANDO el sistema arranca (lifespan de FastAPI), el sistema DEBE establecer una
conexion a MariaDB via SQLAlchemy usando las variables de entorno `DB_HOST`,
`DB_PORT` (3306), `DB_USER`, `DB_PASSWORD`, `DB_NAME`. La conexion DEBE usar el
driver PyMySQL.

### R19
CUANDO el sistema arranca, el sistema DEBE crear la tabla `users` en MariaDB si
esta no existe, usando el metadata de SQLAlchemy. La estructura de la tabla DEBE
ser la declarada en la seccion Persistencia de `design.md`.

### R20
CUANDO el sistema arranca y la tabla `users` esta vacia, el sistema DEBE crear
automaticamente un usuario administrador inicial (seed) con los siguientes
valores:
- `username`: `"admin"`
- `password`: valor de la variable de entorno `ADMIN_DEFAULT_PASSWORD` (si no
  existe, usar `"admin"` como fallback)
- `role`: `"admin"`
- `full_name`: `"Administrador"`
- `document`: `""`
- `is_active`: `True`
La contrasena DEBE almacenarse como hash bcrypt.

### R21
SI la conexion a MariaDB falla en el arranque, el sistema DEBE lanzar una
excepcion que impida que el servidor FastAPI inicie, y registrar el error via
logging.

---

## Modelo de Sesion (config.yaml)

### R22
El sistema DEBE incluir un dataclass congelado `SessionConfig` con el campo
`session_timeout_minutes: int`. Este dataclass DEBE vivir en `src/config.py`
junto al resto de dataclasses de configuracion.

### R23
La funcion `load_config` en `src/config.py` DEBE ser extendida para devolver
tambien `SessionConfig` (ademas de `SystemConfig`), leyendo la seccion `session`
de `config.yaml`. SI la seccion no existe, DEBE devolver `SessionConfig` con el
valor por defecto (15).

### R24
La escritura de `SessionConfig` en `config.yaml` DEBE mantener la atomicidad en
disco: escribir primero en archivo temporal y luego `os.replace()`, preservando
el resto de secciones del archivo (rs485, rs232, gsm, last_updated).

---

## Seguridad

### R25
La clave secreta JWT (`JWT_SECRET_KEY`) y la contrasena por defecto del admin
(`ADMIN_DEFAULT_PASSWORD`) DEBEN ser leidas exclusivamente de variables de
entorno. El sistema NO DEBE contener valores hardcodeados para estas claves en
el codigo fuente (excepto el fallback `"admin"` para `ADMIN_DEFAULT_PASSWORD`).
