# Sesion en curso - 2026-07-13 - Despliegue EdgeBox #2

## Progreso
- Diagnostico inicial completado → /home/sipedge/diagnostico_inicial.md
- IP corregida: solo 192.168.1.42/24, DHCP desactivado
- Fase 1 (Usuarios): COMPLETADA
  - admin, sipedge, bkmngr creados
  - Grupos asignados (dialout, video, i2c, gpio, tty, plugdev, sudo)
  - Auto-login sipedge en LightDM
  - Clave SSH copiada a sipedge
  - Usuario pi bloqueado por seguridad

## Pendiente proxima sesion
- [ ] Fase 2 — Hardware: watchdog 30s, RTC, modem 4G, scripts red
- [ ] Fase 3 — Software Base: MariaDB, Python, repo, venv, .env, config.yaml
- [ ] Fase 4 — Servicios: sip-edge.service, quectel-init, cron backup
- [ ] Fase 5 — llama.cpp

## Estado EdgeBox #2
| Item | Valor |
|------|-------|
| IP | 192.168.1.42 |
| Usuario | sipedge (sudo) |
| SSH | `ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42` |
| SO | Debian 13 aarch64, kernel 6.18 |
| Disco libre | 21 GB |
