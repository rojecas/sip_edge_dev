# Requirements — Password Reset via SMS

> Feature #12 — Restablecimiento remoto de contraseña vía SMS.
> EARS estricto. Cada `R<n>` es verificable por al menos un test.

---

## R1 — Recepción del comando SMS

CUANDO el sistema recibe un SMS entrante cuyo texto coincide exactamente con el patrón
`"reset password <username>"` (sin importar mayúsculas/minúsculas, espacios iniciales/finales
permitidos), el sistema DEBE buscar un usuario activo cuyo `username` coincida ignorando
mayúsculas/minúsculas.

---

## R2 — Usuario no existe

SI el usuario indicado en el comando `"reset password <username>"` no existe en la base
de datos ENTONCES el sistema DEBE enviar un SMS de error al número de teléfono del remitente
indicando que el usuario no fue encontrado. El sistema NO DEBE generar ningún PIN.

---

## R3 — Usuario sin teléfono registrado

SI el usuario existe pero su campo `phone` es nulo o cadena vacía ENTONCES el sistema
DEBE enviar un SMS de error al número de teléfono del remitente indicando que el usuario
no tiene un teléfono registrado. El sistema NO DEBE generar ningún PIN.

---

## R4 — Generación de PIN

CUANDO el usuario existe y tiene un teléfono registrado no vacío, el sistema DEBE generar
un PIN numérico aleatorio de exactamente 4 dígitos (rango 1000–9999, inclusivo).

---

## R5 — Persistencia del PIN

CUANDO se genera un PIN para un usuario, el sistema DEBE:
- Almacenar el hash bcrypt del PIN en la columna `reset_pin` del usuario.
- Establecer `reset_pin_expires_at` a la hora actual UTC más 1 hora exacta.
- Establecer `force_password_change` a `True`.

---

## R6 — Envío del PIN por SMS

CUANDO el PIN ha sido almacenado exitosamente, el sistema DEBE enviar un SMS al número
de teléfono del usuario conteniendo el PIN generado en texto plano y las instrucciones
para restablecer la contraseña.

---

## R7 — Endpoint de verificación de PIN

CUANDO un cliente HTTP envía una solicitud `POST /api/auth/verify-reset-pin` con los
campos `username` (string) y `pin` (string de 4 dígitos), el sistema DEBE:
1. Verificar que el `username` existe en la base de datos.
2. Verificar que `reset_pin` del usuario no es nulo.
3. Verificar que el `pin` ingresado coincide con el hash bcrypt almacenado en `reset_pin`.
4. Verificar que `reset_pin_expires_at` es posterior a la hora actual UTC.

---

## R8 — Emisión de reset_token

CUANDO todas las verificaciones de R7 son exitosas, el sistema DEBE:
- Invalidar el PIN estableciendo `reset_pin = NULL` y `reset_pin_expires_at = NULL`.
- Emitir un `reset_token` JWT firmado con expiración de 5 minutos.
- Retornar el `reset_token` en la respuesta HTTP.

---

## R9 — Rechazo de PIN inválido

SI alguna de las verificaciones de R7 falla (username no existe, reset_pin es nulo,
PIN incorrecto, o PIN expirado) ENTONCES el sistema DEBE retornar un error HTTP 401
con un mensaje genérico y NO DEBE emitir ningún `reset_token`. El sistema NO DEBE
revelar si el usuario existe o el PIN es correcto/incorrecto.

---

## R10 — Endpoint de cambio de contraseña

CUANDO un cliente HTTP envía una solicitud `POST /api/auth/complete-reset` con los
campos `reset_token` (string JWT), `new_password` (string, min 1 carácter) y
`confirm_password` (string), el sistema DEBE validar que el `reset_token` JWT es
válido, no ha expirado, y que el `sub` del token corresponde a un usuario existente.

---

## R11 — Actualización de contraseña

CUANDO el `reset_token` es válido y `new_password` es igual a `confirm_password`
(ambos con longitud >= 1), el sistema DEBE:
- Actualizar `password_hash` con el hash bcrypt de `new_password`.
- Establecer `force_password_change = False`.
- Limpiar `reset_pin = NULL` y `reset_pin_expires_at = NULL`.
- Retornar HTTP 200 indicando éxito.

---

## R12 — Rechazo de cambio inválido

SI el `reset_token` es inválido o ha expirado ENTONCES el sistema DEBE retornar
HTTP 401 y NO DEBE modificar la contraseña.

SI `new_password` y `confirm_password` no coinciden ENTONCES el sistema DEBE retornar
HTTP 422 con detalle descriptivo y NO DEBE modificar la contraseña.

---

## R13 — Columnas en base de datos

La tabla `users` DEBE incluir las siguientes columnas:

| Columna                | Tipo          | Default | Nullable | Descripción                          |
|------------------------|---------------|---------|----------|--------------------------------------|
| `force_password_change` | Boolean       | `false` | NO       | Se activa al generar PIN             |
| `reset_pin`            | VARCHAR(128)  | —       | SÍ       | Hash bcrypt del PIN                  |
| `reset_pin_expires_at` | TIMESTAMP     | —       | SÍ       | Fecha/hora de expiración del PIN     |

---

## R14 — Protección de campos sensibles

El endpoint `GET /api/users` y `GET /api/users/{id}` NO DEBEN incluir los campos
`reset_pin` ni `reset_pin_expires_at` en sus respuestas.

---

## R15 — Enlace "Olvidó su contraseña" en login

El sistema DEBE incluir en la página de login un enlace o botón con el texto
"Olvidó su contraseña" que, al hacer clic, muestre un modal con los campos:
`username` (texto) y `pin` (4 dígitos numéricos).

---

## R16 — Modal de cambio de contraseña

CUANDO la verificación del PIN es exitosa (R7 + R8), el sistema DEBE transicionar
a un segundo modal con los campos: `new_password` (contraseña nueva) y
`confirm_password` (confirmación). Al enviar, el sistema DEBE llamar al endpoint
`POST /api/auth/complete-reset` con el `reset_token` obtenido en R8.

---

## Mapa de trazabilidad: Acceptance → Requirements

| Acceptance Criteria               | Requirements cubiertos |
|-----------------------------------|------------------------|
| RF-NUEVO 1: SMS "reset password"  | R1, R4, R5, R6         |
| RF-NUEVO 2: Validar usuario/tel   | R2, R3                 |
| RF-NUEVO 3: Generar PIN 4 dígitos | R4, R5, R6             |
| RF-NUEVO 4: Modal usuario + PIN   | R15                    |
| RF-NUEVO 5: Modal cambio password | R7, R8, R9, R10, R11, R12, R16 |
| RF-NUEVO 6: Columnas en users     | R13, R14               |
| RF-NUEVO 7: Rechazo sin teléfono  | R3                     |
