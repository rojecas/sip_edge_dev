# Requirements — rs232_transmission (EARS)

> Feature: Transmisión de Datos a PC vía RS232
> Covers: RF-022

---

## R1
CUANDO el analista oprime el boton [confirmar medida] en el kiosco de pesaje y el endpoint `POST /api/weighings`
retorna status 201), el sistema DEBE invocar la función `send_frame()` con los
datos del pesaje para transmitir la trama RS232 al PC externo.

## R2
CUANDO `send_frame()` construye la trama CSV, el sistema DEBE generar
exactamente 15 campos separados por coma en el orden literal:

```
Id,Fecha,Hora,Vagon,Guía,Peso_muestra,0,0,0,0,0,0,0,Peso_vegetal,Peso_mineral
```

Los siete ceros consecutivos (posiciones 7 a 13) son un padding fijo y NO DEBEN
ser reemplazados por ningún otro valor.

## R3
CUANDO `send_frame()` construye la trama CSV, el sistema DEBE usar el valor del
campo `vagon` del `frame_data` sin modificación, respetando mayúsculas,
minúsculas, dígitos y cualquier carácter alfanumérico tal cual fue ingresado en
el registro de pesaje.

## R4
CUANDO `send_frame()` se ejecuta, el sistema DEBE cargar la configuración del
puerto RS232 (path, baudrate, parity, data_bits, stop_bits) desde `config.yaml`
usando `load_config()` y utilizar esos parámetros para abrir el puerto serial.

## R5
CUANDO el envío de la trama RS232 es exitoso (la función `send_frame()` retorna
sin lanzar excepción), el sistema DEBE establecer `enviado_pc = True` en el
registro `Weighing` correspondiente y persistir el cambio en la base de datos.

## R6
SI ocurre cualquier excepción durante la ejecución de `send_frame()` (puerto no
disponible, error de escritura, timeout, error de permisos) ENTONCES el sistema
DEBE registrar el error a través de `logging.error()`, NO DEBE relanzar la
excepción, y el registro de pesaje DEBE permanecer como confirmado en la base de datos.

## R7
MIENTRAS la variable de entorno `DEV_MODE` esté definida como `true`, `1` o
`yes` (case-insensitive), la función `send_frame()` DEBE omitir toda operación
de E/S serial y retornar inmediatamente sin error, para permitir pruebas en
entornos sin hardware RS232 real.

## R8
La trama CSV DEBE terminar con los caracteres `\r\n` (CRLF) según el estándar
de transmisión RS232.

## R9
CUANDO `send_frame()` construye la trama CSV, el sistema DEBE usar el valor del
campo `numero_guia` del `frame_data` como valor del campo `Guía` en la trama,
sin modificación.

## R10
CUANDO `send_frame()` construye la trama CSV, el sistema DEBE usar el valor del
campo `pesos.muestra` del `frame_data` como valor del campo `Peso_muestra`, el
campo `pesos.vegetal_extrano` como `Peso_vegetal`, y el campo `pesos.mineral`
como `Peso_mineral`, todos formateados con tres decimales.
