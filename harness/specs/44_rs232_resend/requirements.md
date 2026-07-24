# Requirements — rs232_resend (EARS)

> Feature: Reenvío de Datos RS232 desde Kiosko
> Dependencias: F6 (weighing_capture), F11 (rs232_transmission)
> Límite: 9 requirements (por debajo del límite de 20)
>
> **Nota spec-validator (2026-07-23):** Corregidos R1-R5 y R9-R10; ver requirements.old.md.
>
> **Nota líder (2026-07-23):** Eliminado R5 original ("enviado_pc=true → no mostrar Reenviar").
> Verificado en `src/rs232.py:68`: `ser.write()` sin handshaking — `enviado_pc=true` solo
> significa que el EdgeBox escribió bytes al UART sin error de SO, NO que el PC los recibió.
> Si el PC está apagado o el software cerrado, el write al UART igual tiene éxito.
> Por tanto, el botón siempre debe cambiar a "Reenviar Datos" tras confirmar (Opción A).

---

## R1
CUANDO `POST /api/weighings` retorna HTTP 201 exitoso, el sistema DEBE
reemplazar el botón "Confirmar Medidas" por un botón "Reenviar Datos"
habilitado en el kiosko, en todos los casos sin evaluar `enviado_pc`.

## R2
CUANDO el operador presiona el botón "Reenviar Datos" en el kiosko, el
sistema DEBE invocar `POST /api/weighings/{id}/resend`.

## R3
El sistema DEBE permitir que el operador presione "Reenviar Datos" cualquier
cantidad de veces, invocando `POST /api/weighings/{id}/resend` en cada presión.

## R4
CUANDO el operador presiona Tara o Leer (READ) en cualquiera de los 3 campos
de peso (Muestra, Mineral, Vegetal), el sistema DEBE restaurar el botón
principal a "Confirmar Medidas" para el siguiente pesaje.

## R5
El sistema DEBE exponer un endpoint `POST /api/weighings/{id}/resend` con
las siguientes responsabilidades:
- Leer el registro de pesaje existente por `{id}`.
- Cargar la `Hacienda` y `Suerte` asociadas para construir la trama.
- Construir la trama CSV con `_build_frame_data()`.
- Transmitir la trama por el puerto RS232 configurado con `_send_rs232_frame()`.
- Actualizar `enviado_pc = True` en el registro.
- Incrementar `resend_count` en 1.
- NO re-ejecutar detección de anomalías.
- Devolver el registro actualizado como `WeighingResponse`.
- Devolver HTTP 404 si el `{id}` no existe.
- Devolver HTTP 404 si un operator intenta reenviar un pesaje de otro usuario.

## R6
La tabla `weighings` DEBE tener una columna `resend_count` de tipo
`INTEGER NOT NULL DEFAULT 0`.

## R7
CUANDO `POST /api/weighings/{id}/resend` transmite exitosamente, el sistema
DEBE incrementar `resend_count` en exactamente 1.

## R8
CUANDO un usuario autenticado con rol `admin` visualiza el historial de
pesajes en `HistoryTable`, el sistema DEBE mostrar un botón 🔄
en cada fila donde `enviado_pc = false`.

## R9
El botón 🔄 en `HistoryTable` NO DEBE ser visible para usuarios con rol
`operator`.
