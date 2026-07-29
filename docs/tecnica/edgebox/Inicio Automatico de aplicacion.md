
---
## Iniciar automáticamente la aplicación kiosco

Mediante un servicio systemd en el espacio de usuario (systemd --user) o un archivo .desktop en el autostart del usuario.

**Opción A:**

Archivo .desktop para LXDE (recomendada si usas escritorio)
Crea el archivo ~sipedge/.config/autostart/sipedge-app.desktop:

```bash
sudo -u sipedge mkdir -p /home/sipedge/.config/autostart
sudo -u sipedge nano /home/sipedge/.config/autostart/sipedge-app.desktop
Contenido:

ini
[Desktop Entry]
Type=Application
Name=sipedge App
Exec=/home/sipedge/sipedge_app.py
X-GNOME-Autostart-enabled=true
```

Asegúrate de que el script sea ejecutable: chmod +x /home/sipedge/sipedge_app.py.

**Opción B:**

Servicio systemd (si no usas X o quieres más control)
Crea un servicio como root:

```bash
sudo nano /etc/systemd/system/sipedge-app.service
```
Contenido:
```
ini
[Unit]
Description=sipedge Application
After=network-online.target multi-user.target
Wants=network-online.target

[Service]
User=sipedge
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/sipedge/.Xauthority
ExecStart=/home/sipedge/sipedge_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
```
Luego:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sipedge-app.service
sudo systemctl start sipedge-app.service
```

## 2. Ajustes adicionales de seguridad y usabilidad
Deshabilitar el protector de pantalla y suspensión
Para evitar que la pantalla se apague:

```bash
# Para el usuario sipedge, desactivar DPMS y screensaver
sudo -u sipedge bash -c "echo 'xset s off' >> /home/sipedge/.xinitrc"
sudo -u sipedge bash -c "echo 'xset -dpms' >> /home/sipedge/.xinitrc"
```
Si usas LightDM, puedes poner esos comandos en un script de inicio.

Restringir el acceso del usuario sipedge
No debe tener permiso sudo para comandos genéricos (solo los específicos que definiste).

No debe tener contraseña (opcional) si quieres que nadie pueda iniciar sesión manualmente con sipedge desde la consola. Para ello: sudo passwd -l sipedge (bloquea la contraseña). Pero con auto-login seguirá entrando. Si necesitas acceso ocasional, mejor déjala.

Limitar el uso de la shell: podrías cambiar la shell del usuario a un script que solo ejecute la aplicación, pero eso puede complicar el mantenimiento.

Asegurar que los puertos serie estén disponibles
Verifica que el usuario sipedge pueda leer/escribir en /dev/ttyACM*:

```bash
ls -la /dev/ttyACM*
# Debería mostrar crw-rw---- root dialout
```
Si no, crea una regla udev:

```bash
echo 'KERNEL=="ttyACM[0-9]*", GROUP="dialout", MODE="0660"' | sudo tee /etc/udev/rules.d/99-serial.rules
sudo udevadm trigger
```
## 3. Prueba y verificación
Reinicia el sistema: sudo reboot.

Debería iniciar sesión automáticamente como sipedge y ejecutar tu aplicación.

Desde tu aplicación, prueba:

Leer/escribir en /dev/ttyACM0 y /dev/ttyACM1.

Llamar a sudo /usr/local/bin/switch_network.sh eth.

Enviar un SMS con sudo /usr/local/bin/send_sms.sh.

Controlar el LED (si tu script de LED corre como servicio root, no necesita permisos especiales).

Si algo falla, revisa los logs: journalctl -u sipedge-app.service (si usaste servicio) o /var/log/lightdm/lightdm.log.

Estructura final recomendada de usuarios
Usuario	Rol	Grupos clave	Sudo (sin pass)
admin (o pi)