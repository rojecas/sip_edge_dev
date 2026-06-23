# Recordatorio para la proxima sesion

> Leer al iniciar la sesion. Este archivo contiene tareas pendientes
> y contexto necesario para continuar el trabajo.

---

## 1. Estado del repositorio

El working tree tiene cambios sin commit. NO esta sincronizado con origin/master.
Ejecutar antes de empezar:

    git status
    git diff --stat

## 2. Pruebas en entorno remoto (EdgeBox-RPI-200)

Pendiente de realizar. Requiere acceso SSH a la EdgeBox:

    ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42

### Features a probar

| Feature | Nombre | Hardware relevante |
|---------|--------|-------------------|
| 14 | frontend_admin_dashboard | Pantalla (navegacion admin) |
| 15 | frontend_admin_operations | Config RS485/RS232, Backup |
| 16 | frontend_admin_masterdata | CRUD Usuarios/Haciendas/Suertes |

### Flujo de pruebas

1. Hacer git pull en EdgeBox + reiniciar servicio
2. Ingresar al SPA via http://192.168.1.42:8000
3. Loguear como admin/admin
4. Probar:

   - [ ] /admin/dashboard — navegacion
   - [ ] /admin/config — configuracion RS485/RS232/GSM
   - [ ] /admin/usuarios — CRUD completo
   - [ ] /admin/haciendas — CRUD con paginacion
   - [ ] /admin/suertes — CRUD filtrado por hacienda
   - [ ] /admin/backup — historial y ejecucion

## 3. Modo manual de emergencia (SMS)

Se requiere probar el flujo de emergencia via SMS.

### Pre-requisitos
- Modem 4G Quectel EC25 activo (mmcli -m 0)
- Plan de datos activo
- Numero de admin configurado en users.phone

### Flujo a probar
1. Desde el kiosco: solicitar modo manual
2. Verificar que llega SMS al admin
3. Responder con 'manual on' desde el celular
4. Verificar que el modo manual se activa
5. Pesar con peso editable
6. Extender con SMS 'manual on ext 30m'
7. Desactivar con 'manual off'

### Comandos utiles
`ash
# Estado del modem
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 \"mmcli -m 0\"

# Logs del servicio
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 \"sudo journalctl -u sip-edge -n 50 --no-pager\"

# Tests de hardware
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 \
  \"cd /home/sipedge/sip_edge && source venv/bin/activate && python -m unittest discover -s tests_hardware -v\"

# Smoke test
curl http://192.168.1.42:8000/health
`

### Feature 9 — emergency_mode
- RF-020a a RF-020k: flujo completo de modo manual
- Requiere: modem GSM activo + usuarios con telefono registrado

## 4. Feature 21 — pagination_users_backups

Creada en status 'pending'. Cuando se retome:
1. Lanzar spec-author para redactar requirements + design + tasks
2. Aprobacion humana
3. Implementer
4. Reviewer + release-manager

## 5. Git antes de terminar

Recordar:
1. Hacer commit de los cambios
2. Push a origin/master
3. Ejecutar close.ps1
