## Configuración de Puertos Industriales RS232 / RS485
El primer paso es identificar correctamente los puertos. La documentación de SeeedStudio para el EdgeBox-RPI-200 especifica el mapeo de los puertos serie:

RS232: /dev/ttyACM1
RS485: /dev/ttyACM0

Sigue estos pasos para verificar, configurar y probar la comunicación.

Paso 1: Verificar la existencia de los dispositivos

Ejecuta el siguiente comando para listar los dispositivos serie y confirmar que los puertos están presentes:

```Bash
admin@SIP-Edge:~ $ ls -la /dev/ttyACM*
crw-rw---- 1 root dialout 166, 0 Apr  5 17:31 /dev/ttyACM0
crw-rw---- 1 root dialout 166, 1 Apr  5 17:31 /dev/ttyACM1
```

### 2. Configurar permisos de usuario

Para poder comunicarte con los puertos sin ser root, añade tu usuario (por ejemplo, sipedge) al grupo dialout:

```Bash
sudo usermod -a -G dialout sipedge
```

Es necesario cerrar la sesión y volver a iniciarla para que los cambios de grupo surtan efecto.

### 3. Configurar parámetros de comunicación (velocidad, paridad, bits de parada)

Para aplicaciones industriales, la velocidad de 115200 baudios es un estándar. Puedes configurar los parámetros temporalmente con stty o permanentemente en tu script/aplicación.

Configuración temporal con stty (por ejemplo, para RS232):

```Bash
# Configura /dev/ttyACM1 a 115200 baud, 8 bits de datos, sin paridad, 1 bit de parada
stty -F /dev/ttyACM1 115200 cs8 -cstopb -parenb -echo
```
	- 115200: Velocidad en baudios.
	- cs8: 8 bits de datos.
	- cstopb: 1 bit de parada (el '-' significa 'no', por lo que se desactivan 2 bits de parada).
	- parenb: Sin bit de paridad.
	- echo: Desactiva el eco local, útil para comunicación con dispositivos externos.

Configuración en un script de Python:
La configuración se maneja directamente al abrir el puerto. Para RS485, es posible que necesites parámetros adicionales para controlar la dirección de transmisión, pero para empezar, la configuración es similar.

```Bash
#!/usr/bin/env python3
import serial

# Para RS232
ser232 = serial.Serial('/dev/ttyACM1', 115200, timeout=1, bytesize=8, parity='N', stopbits=1)
# Para RS485
ser485 = serial.Serial('/dev/ttyACM0', 115200, timeout=1, bytesize=8, parity='N', stopbits=1)

print(f"RS232 abierto: {ser232.is_open}")
print(f"RS485 abierto: {ser485.is_open}")

# Ejemplo de escritura en RS232
ser232.write(b'1234567890')

# No olvides cerrar los puertos al finalizar
# ser232.close()
# ser485.close()
```
Nota: El manual oficial de EdgeBox-RPI-200 utiliza este ejemplo en Python para verificar la comunicación serie.

### 4. Prueba de Comunicación con un Dispositivo Externo

Conecta un dispositivo externo (por ejemplo, un PLC, un sensor, o un adaptador USB a RS232/485 en tu PC) al puerto correspondiente del EdgeBox.

En tu PC, abre un monitor serial (como PuTTY, screen o minicom) en el puerto del adaptador.

En el EdgeBox, usa echo y cat para una prueba rápida:

Enviar datos desde el EdgeBox: En una terminal, ejecuta

```Bash
echo "Hola desde EdgeBox" > /dev/ttyACM1
```
 
 . Deberías ver el mensaje en el monitor serial de tu PC.

Recibir datos en el EdgeBox: En una terminal, ejecuta cat /dev/ttyACM1. Escribe un mensaje en el monitor serial de tu PC y deberías verlo aparecer en la terminal del EdgeBox. Presiona Ctrl+C para salir.

