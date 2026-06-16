# Design — Password Reset via SMS

> Feature #12 — Decisiones técnicas para el restablecimiento remoto de contraseña vía SMS.

---

## 1. Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `src/password_reset.py` | Módulo con `PasswordResetService`, parser de SMS, y endpoints de API |
| `src/sms_incoming.py` | Módulo con `IncomingSmsDispatcher` para polling compartido de SMS entrantes |
| `database/migrations/2026_06_16_000001_add_password_reset_fields.py` | Migración para agregar columnas a `users` |
| `harness/progress/impl_12_password_reset_sms.md` | Trazabilidad R<n> ↔ tests (creado por implementer) |

---

## 2. Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Agregar columnas `force_password_change`, `reset_pin`, `reset_pin_expires_at` al modelo `User` |
| `src/users.py` | Excluir `reset_pin` y `reset_pin_expires_at` del schema `UserResponse` |
| `src/main.py` | Inicializar `IncomingSmsDispatcher` y `PasswordResetService` en lifespan; registrar routers |
| `src/emergency_mode.py` | Refactorizar: eliminar `_poll_incoming_sms()` y `_poll_mmcli_sms()`; registrar `process_incoming_sms` como handler en `IncomingSmsDispatcher` |

---

## 3. Firmas nuevas

### `src/sms_incoming.py` — Dispatcher compartido

```python
class SmsHandler(Protocol):
    def __call__(self, sender_phone: str, text: str) -> bool:
        """Procesa un SMS entrante. Retorna True si el SMS fue manejado."""

class IncomingSmsDispatcher:
    def __init__(self, modem_index: int, dev_mode: bool = False) -> None: ...
    def register_handler(self, handler: SmsHandler) -> None: ...
    def enqueue_incoming_sms(self, sender_phone: str, text: str) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

### `src/password_reset.py` — Servicio y endpoints

```python
class PasswordResetError(Exception):
    """Error base del módulo de reset de contraseña."""

class InvalidPinError(PasswordResetError):
    """PIN inválido o expirado."""

class PasswordResetService:
    def __init__(self, db_session_factory, sms_service, dispatcher: IncomingSmsDispatcher) -> None: ...
    def handle_incoming_sms(self, sender_phone: str, text: str) -> bool: ...
    def generate_and_send_pin(self, username: str, sender_phone: str) -> bool: ...

class VerifyResetPinRequest(BaseModel):
    username: str = Field(min_length=1)
    pin: str = Field(min_length=4, max_length=4)

class CompleteResetRequest(BaseModel):
    reset_token: str = Field(min_length=1)
    new_password: str = Field(min_length=1)
    confirm_password: str = Field(min_length=1)

class VerifyResetPinResponse(BaseModel):
    reset_token: str
    token_type: str = "bearer"
```

### Funciones auxiliares en `src/auth.py`

```python
def create_reset_token(user_id: int) -> str: ...
    """Crea un JWT con expiración de 5 minutos para reset de contraseña."""
```

---

## 4. Nuevos endpoints API

### `POST /api/auth/verify-reset-pin`

- **Body:** `VerifyResetPinRequest` (`{ username, pin }`)
- **Response 200:** `VerifyResetPinResponse` (`{ reset_token, token_type }`)
- **Response 401:** `{ "detail": "Invalid username or PIN" }` — mensaje genérico
- **Lógica:**
  1. Buscar usuario por username (case-insensitive)
  2. Si no existe → 401
  3. Si `reset_pin` es nulo → 401
  4. Si `reset_pin_expires_at` es pasado o nulo → 401
  5. Si PIN no coincide con hash → 401
  6. Si todo OK: limpiar `reset_pin`, `reset_pin_expires_at`, emitir `reset_token` JWT (5 min)
- **Auth:** Sin autenticación previa (accesible desde pantalla de login)

### `POST /api/auth/complete-reset`

- **Body:** `CompleteResetRequest` (`{ reset_token, new_password, confirm_password }`)
- **Response 200:** `{ "message": "Password updated successfully" }`
- **Response 401:** Si token inválido/expirado
- **Response 422:** Si `new_password != confirm_password`
- **Lógica:**
  1. Decodificar y validar `reset_token` JWT
  2. Extraer `user_id` del `sub`
  3. Verificar que usuario existe
  4. Validar `new_password == confirm_password` y longitud ≥ 1
  5. Actualizar `password_hash` con bcrypt de `new_password`
  6. Poner `force_password_change = False`
  7. Limpiar `reset_pin`, `reset_pin_expires_at`
- **Auth:** Solo el `reset_token` JWT (no requiere token de sesión)

---

## 5. Procesamiento de SMS entrantes

### Problema detectado

La feature #9 (emergency_mode) ya implementa polling de SMS entrantes vía mmcli en
`EmergencyModeService._poll_incoming_sms()`. Si la feature #12 crea un segundo polling
independiente, ambos servicios competirán por leer y eliminar los mismos SMS, causando
condiciones de carrera y pérdida de mensajes.

### Solución: `IncomingSmsDispatcher` compartido

Se extrae la lógica de polling mmcli de `EmergencyModeService` a un nuevo
`IncomingSmsDispatcher` en `src/sms_incoming.py`:

1. **Dispatcher** ejecuta un único bucle asyncio que cada 15 segundos consulta mmcli.
2. Cada handler registrado recibe `(sender_phone, text)` y retorna `True` si procesó el SMS.
3. Si ningún handler procesa el SMS, se elimina sin acción (no se logea como error).
4. Al finalizar, el SMS se elimina de módem.

### Orden de registro de handlers

1. `EmergencyModeService.process_incoming_sms` — primero (comandos "manual on/off")
2. `PasswordResetService.handle_incoming_sms` — segundo (comando "reset password")

Si un handler retorna `True`, el dispatcher saltea los handlers restantes para ese SMS.

### Modo desarrollo

`IncomingSmsDispatcher` soporta cola interna (`enqueue_incoming_sms`) para simular
SMS entrantes en tests y dev mode, mismo patrón que `EmergencyModeService`.

---

## 6. Manejo de errores / excepciones

| Excepción | Módulo | Disparo |
|-----------|--------|---------|
| `PasswordResetError` | `password_reset.py` | Error base |
| `InvalidPinError` | `password_reset.py` | PIN inválido, expirado o nulo |

Ninguna excepción nueva en `auth.py` — se reutilizan `HTTPException` con códigos
estándar (401, 422).

---

## 7. Persistencia

### Tabla modificada: `users`

| Columna               | Tipo MariaDB           | Nullable | Default | Descripción                           |
|-----------------------|------------------------|----------|---------|---------------------------------------|
| `force_password_change` | `BOOLEAN`            | NO       | `FALSE` | Se activa al generar PIN              |
| `reset_pin`           | `VARCHAR(128)`         | SÍ       | `NULL`  | Hash bcrypt del PIN de 4 dígitos      |
| `reset_pin_expires_at` | `TIMESTAMP(0)`       | SÍ       | `NULL`  | Momento UTC de expiración del PIN     |

### Migraciones

1. `database/migrations/2026_06_16_000001_add_password_reset_fields.py`

```sql
ALTER TABLE users
  ADD COLUMN force_password_change BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN reset_pin VARCHAR(128) DEFAULT NULL,
  ADD COLUMN reset_pin_expires_at TIMESTAMP(0) DEFAULT NULL;
```

### Modelo SQLAlchemy (src/models.py)

```python
force_password_change = Column(Boolean, nullable=False, default=False, server_default="0")
reset_pin = Column(String(128), nullable=True, default=None)
reset_pin_expires_at = Column(TIMESTAMP, nullable=True, default=None)
```

### NOTA sobre UserResponse (src/users.py)

El schema `UserResponse` usa `from_attributes = True`. Para evitar exponer
`reset_pin` y `reset_pin_expires_at`, se DEBE agregar explícitamente solo los
campos permitidos o usar `exclude` en la configuración del modelo Pydantic.

---

## 8. Consideraciones de seguridad

- **PIN hasheado:** `reset_pin` almacena hash bcrypt, NO texto plano. Misma función
  `hash_password` de `auth.py`.
- **Single-use:** El PIN se invalida (`reset_pin = NULL`) tras verificación exitosa
  o al completar el reset. No puede reutilizarse.
- **Reset token JWT corto:** 5 minutos de expiración. Misma clave `JWT_SECRET_KEY`
  y algoritmo `HS256` que los tokens de sesión.
- **Mensaje genérico en errores:** El endpoint `verify-reset-pin` retorna siempre
  `"Invalid username or PIN"` para no revelar qué campo es incorrecto.
- **No exponer campos sensibles:** `reset_pin` y `reset_pin_expires_at` excluidos
  de `GET /api/users` y `GET /api/users/{id}`.

---

## 9. Alternativa descartada

### Alternativa: PIN en texto plano + expiración en lógica de aplicación

Se consideró almacenar el PIN directamente (sin hash) junto con un timestamp de
expiración, confiando en que la BD es segura.

**Descartada por:** Viola el principio de mínimo privilegio. Cualquier leak de la
BD (backup, dumping, SQLi) expondría todos los PINs activos. El costo de aplicar
bcrypt es negligible (4 dígitos = 10,000 combinaciones) comparado con el beneficio
de seguridad.

---

## 10. github_labels

```json
["password-reset", "auth", "sms", "security"]
```
