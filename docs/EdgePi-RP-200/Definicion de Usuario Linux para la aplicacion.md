## Definicion de usuario para aplicacion

Crear el usuario con directorio home y shell bash
```
admin@SIP-Edge:~ $ sudo adduser sipedge
New password:
Retype new password:
passwd: password updated successfully
Changing the user information for sipedge
Enter the new value, or press ENTER for the default
        Full Name []: Analista de Pesaje Materia Extraña
        Room Number []:
        Work Phone []:
        Home Phone []:
        Other []:
chfn: name with non-ASCII characters: 'Analista de Pesaje Materia Extraña'
Is the information correct? [Y/n] Y

```
- User: sipedge
- password: sipedge1234

Añadir al usuario a los grupos requeridos
```
admin@SIP-Edge:~ $ sudo usermod -a -G dialout sipedge   # Acceso a puertos serie /dev/ttyACM*
sudo usermod -a -G video sipedge     # Para aceleración gráfica (DRM, framebuffer)
sudo usermod -a -G i2c sipedge       # Si usas algún dispositivo I2C
sudo usermod -a -G gpio sipedge      # Para control de GPIO (si accedes directamente)
sudo usermod -a -G tty sipedge       # Acceso general a terminales
sudo usermod -a -G plugdev sipedge   # Para dispositivos USB (módem 4G)
admin@SIP-Edge:~ $

```

3. Configurar auto-login para el usuario sipedge (modo kiosco)
Queremos que al encender el equipo, inicie sesión automáticamente con el usuario sipedge y lance la interfaz gráfica sin intervención.

Para la interfaz gráfica (LightDM en Raspberry Pi OS)
Edita /etc/lightdm/lightdm.conf:

```bash
sudo nano /etc/lightdm/lightdm.conf
Busca la sección [Seat:*] y descomenta/añade:

ini
[Seat:*]
autologin-user=sipedge
autologin-user-timeout=0
Si el archivo no existe, créalo con ese contenido.
```
