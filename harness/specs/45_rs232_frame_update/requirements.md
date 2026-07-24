# Requirements — rs232_frame_update

## R1 — Separador de fecha `/`
El sistema DEBE formatear el campo fecha en la trama RS-232 usando `/` como
separador (YYYY/MM/DD) en lugar del guion isoformat (YYYY-MM-DD).

## R2 — Hora sin segundos
El sistema DEBE formatear el campo hora en la trama RS-232 sin segundos
(HH:MM) en lugar del formato isoformat completo (HH:MM:SS).

## R3 — Campo fijo `1`
El sistema DEBE insertar un campo fijo con valor `1` entre el campo vagon y
el campo numero_guia en la trama RS-232.

## R4 — Pesos con 2 decimales
El sistema DEBE formatear los 3 pesos (muestra, vegetal_extrano, mineral) con
exactamente 2 decimales (`.2f`) en lugar de 3 decimales (`.3f`).

## R5 — Reduccion de ceros de reserva
El sistema DEBE reducir los ceros de reserva de 7 a 5 en la trama RS-232.

## R6 — Aplicacion en POST /api/weighings
CUANDO se confirma un pesaje via POST /api/weighings, el sistema DEBE
transmitir la trama RS-232 con el nuevo formato de 14 campos.

## R7 — Aplicacion en POST /api/weighings/{id}/resend
CUANDO se reenvia un pesaje via POST /api/weighings/{id}/resend, el sistema
DEBE transmitir la trama RS-232 con el nuevo formato de 14 campos.

## R8 — Tests unitarios del nuevo formato
El sistema DEBE tener tests unitarios en tests/test_rs232.py que verifiquen
el nuevo formato: 14 campos, fecha con `/`, hora sin segundos, campo fijo `1`,
pesos con 2 decimales, y 5 ceros de reserva.

## R9 — Tests de integracion de transmision completa
El sistema DEBE tener tests de integracion que verifiquen la transmision
completa de la trama con el nuevo formato desde los endpoints POST
/api/weighings y POST /api/weighings/{id}/resend.

## Resumen de formato

| Posicion | Campo                | Formato    | Ejemplo        |
|----------|----------------------|------------|----------------|
| 1        | id                   | entero     | 42             |
| 2        | fecha                | YYYY/MM/DD | 2026/07/24     |
| 3        | hora                 | HH:MM      | 10:30          |
| 4        | vagon                | string     | ABC-123        |
| 5        | campo fijo           | 1          | 1              |
| 6        | numero_guia          | string     | G-789          |
| 7        | peso_muestra         | .2f        | 1.50           |
| 8        | reserva 1            | 0          | 0              |
| 9        | reserva 2            | 0          | 0              |
| 10       | reserva 3            | 0          | 0              |
| 11       | reserva 4            | 0          | 0              |
| 12       | reserva 5            | 0          | 0              |
| 13       | peso_vegetal_extrano | .2f        | 0.20           |
| 14       | peso_mineral         | .2f        | 0.80           |
