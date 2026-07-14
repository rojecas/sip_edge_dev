# Sesion cerrada - 2026-07-14 - Despliegue EdgeBox #2 completado

## Resumen
EdgeBox #2 completamente desplegada. 5 fases ejecutadas, datos migrados,
verificacion post-reboot exitosa. Informe detallado en docs/informe_despliegue_edgebox2.md.

## Entregables
- [x] Fase 1 — Usuarios (admin, sipedge, bkmngr, grupos, auto-login)
- [x] Fase 2 — Hardware (watchdog 30s, RTC, 4G Tigo, SSD 119GB, WiFi, scripts)
- [x] Fase 3 — Software Base (MariaDB, Python, repo, venv, .env, config.yaml)
- [x] Fase 4 — Servicios (sip-edge systemd, cron, quectel-init)
- [x] Fase 5 — llama.cpp (bf2c86d, Qwen2.5 1.5B)
- [x] Reboot + verificacion post-arranque
- [x] DB migrada (12 users, 4221 weighings, 621 haciendas)
- [x] Emoji font + hostname + RTC + API key
- [x] SMS funcional con SMSC correcto

## Estado final EdgeBox #2
| Componente | Estado |
|------------|--------|
| IP | 192.168.1.42 |
| Hostname | SIP-Edge |
| SIP-Edge | active, /health 200 |
| 4G LTE | Tigo, 78%, IP dinamica |
| SMS | Funcional (envio + recepcion) |
| Watchdog | 30s |
| RTC | /dev/rtc0 + save-hwclock |
| SSD | 111 GB libre en /mnt/ssd |
| Disco | 19 GB libre eMMC |
| API Key | DeepSeek configurada |

## Lecciones
- send_sms.sh requiere SMSC explicito (+573003690025) y flag separado (sin =)
- hwclock en Debian 13 requiere util-linux-extra
- Emojis en kiosko requieren fonts-noto-color-emoji
- Modem index puede cambiar tras reset (0 -> 2 -> 0)
- Antena LTE se desconecta facil al manipular el chasis
