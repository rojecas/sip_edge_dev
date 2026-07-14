# Sesion en curso - 2026-07-14 - Despliegue EdgeBox #2 completado

## Resumen
EdgeBox #2 completamente desplegada y operativa. Las 5 fases ejecutadas,
verificacion post-reboot exitosa. Informe detallado en docs/informe_despliegue_edgebox2.md.

## Fases completadas
- [x] Fase 1 — Usuarios (admin, sipedge, bkmngr, grupos, auto-login, bloqueo pi)
- [x] Fase 2 — Hardware (watchdog 30s, RTC PCF8563, 4G Tigo, SSD 119GB, WiFi)
- [x] Fase 3 — Software Base (MariaDB 11.8.6, Python 3.13.5, repo, venv, .env, config.yaml)
- [x] Fase 4 — Servicios (sip-edge systemd, cron backup, quectel-init)
- [x] Fase 5 — llama.cpp (bf2c86d, Qwen2.5 1.5B)
- [x] Reboot + verificacion post-arranque

## Estado final EdgeBox #2
| Componente | Estado |
|------------|--------|
| IP | 192.168.1.42 |
| Hostname | edgebox |
| SIP-Edge | active, /health 200 |
| 4G LTE | Tigo, 78%, 10.81.172.147 |
| SMS | Funcional |
| Watchdog | 30s |
| RTC | /dev/rtc0 detectado |
| Disco | 19 GB eMMC + 111 GB SSD |
| SSH | sipedge@192.168.1.42 (key + password) |

## Pendientes menores
- [ ] save-hwclock.service
- [ ] Hostname -> SIP-Edge (opcional)
- [ ] DEEPSEEK_API_KEY
- [ ] Modelos GGUF adicionales
- [ ] Binarios llama.cpp restantes
