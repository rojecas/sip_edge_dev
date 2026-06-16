# Closure — emergency_mode

> Feature 9 — Modo Manual de Emergencia  
> Fecha: 2026-06-15  
> Agente: implementer  
> Estado del cierre: implementacion completada, T20 pendiente (EdgeBox)

---

## Resumen

Implementado el modulo completo de Modo Manual de Emergencia segun el spec en
`harness/specs/09_emergency_mode/`. Se completaron las tareas T1-T19. T20
(verificacion en EdgeBox) queda pendiente por requerir acceso al hardware real.

## Archivos creados / modificados

### Creados
- `src/emergency_mode.py` — Modulo completo (700+ lineas)
- `tests/test_emergency_mode.py` — 53 tests
- `database/migrations/2026_06_16_000001_create_emergency_mode_log.sql` — Migracion MariaDB
- `harness/progress/impl_emergency_mode.md` — Mapa de trazabilidad

### Modificados
- `src/models.py` — + `EmergencyModeLog` model, + `phone` column en User, + `manual_entry` en Weighing
- `src/main.py` — + imports, + EmergencyModeService en lifespan, + emergency_router
- `src/weighings.py` — + `manual_entry` en schemas y endpoint
- `harness/specs/09_emergency_mode/tasks.md` — T1-T19 marcados [x]
- `harness/progress/current.md` — Actualizado con feature en curso

## Verificacion

| Nivel | Estado | Detalle |
|-------|--------|---------|
| N1 — Tests unitarios | PASS | 53/53 emergencia, 300/300 total |
| N2 — CLI | N/A | Feature REST, no CLI |
| N3 — init.ps1 | PASS | Todos [OK] |
| N4 — EdgeBox | PENDIENTE | Ver abajo |

## Pendiente: Verificacion EdgeBox (Nivel 4 / T20)

Para completar T20 se necesita acceso SSH a la EdgeBox (192.168.1.42).
Comandos a ejecutar:

```bash
# 1. Copiar migracion
scp -i ~/.ssh/sip_edge_edgebox database/migrations/2026_06_16_000001_create_emergency_mode_log.sql sipedge@192.168.1.42:/tmp/

# 2. Ejecutar migracion en MariaDB
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "mysql -u sip_user -psip_pass sip_edge < /tmp/2026_06_16_000001_create_emergency_mode_log.sql"

# 3. Deploy y reinicio
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "cd /home/sipedge/sip_edge && git pull && sudo systemctl restart sip-edge"

# 4. Smoke test
curl http://192.168.1.42:8000/health

# 5. Verificar endpoints de emergencia
curl -H "Authorization: Bearer <token>" http://192.168.1.42:8000/api/emergency/status
curl -H "Authorization: Bearer <token>" http://192.168.1.42:8000/api/emergency/admins
```

## Decisions tecnicas

1. **Phone en User model**: Necesario para enviar SMS al supervisor (R4) y
   verificar emisor de SMS (R17). Columna nullable, retrocompatible.

2. **manual_entry en Weighing**: Flag booleano para distinguir pesajes manuales
   de los capturados via bascula. Facilita auditoria.

3. **Dev mode SMS polling**: Cola interna para tests. Produccion usa mmcli.

4. **Datetime timezone-aware**: Uso consistente de UTC con tzinfo. Compatibilidad
   con SQLite mediante normalizacion en restore_from_db().

## Estado final

Feature 9 implementada y verificada en Docker local (Niveles 1-3). Lista para
review y posterior despliegue en EdgeBox (Nivel 4). No se marca `done` — espera
la aprobacion del reviewer y release-manager.
