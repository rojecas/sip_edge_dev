# Sesión F37 + F33 — 2026-07-20

## Feature 37 — notas_muestras
### Estado final: done (Issue #25)

Ciclo: spec-author → spec-validator → humano (cambio R7/R8: columna → modal) → implementer → reviewer → testing → release-manager

Bugs corregidos en testing:
1. Notas no persistían — `NotesField.svelte` sin `$bindable()` en prop `notas`
2. Hacienda no reseteaba — `HaciendaCodeInput` sin `resetKey`
3. Historial sin orden por hora — `order_by` solo `fecha`, agregado `hora DESC`

## Feature 33 — sql_tools_v2
### Estado final: done (Issue #26)

Ciclo: spec-author → spec-validator → humano (setup card + tooltips) → implementer → reviewer → testing → release-manager

Entregado:
- 4 tools nuevas + 3 modificadas + shortcuts fecha + filtro vehículo
- Setup: card "Límites de Control" con 7 parámetros + tooltips
- `check_thresholds()` lee de AgentConfig
- Desviación estándar en reportes SMS

Fixes post-implementación:
1. `llm_client.py` simulado usaba fechas hardcodeadas → `periodo: "mes_actual"`
2. Circuit breaker cooldown 30s → 5s para LLM local
3. `fecha_inicio`/`fecha_fin` opcionales en 3 tools (schema + firmas)
4. `prepend_today()` inyecta fecha real en cada consulta
5. `scale.py` no crashea si falta puerto serial (Docker sin hardware)
6. `llm_url` en EB2 corregido: `http://localhost:8080` (sin `/v1` duplicado)

## Infraestructura
- EB2: `AI_PRIMARY_BACKEND=local` (qwen2.5-1.5b), `llm_timeout=120s`
- llama-server con `taskset -c 0-2 -t 3` (3 cores, core 3 libre)
- Docker local: `DEV_MODE=false`, `AI_PRIMARY_BACKEND=remote` (DeepSeek)
- `compose.yml`: defaults actualizados

## Datos de prueba
- Script `generate_historical_weighings.py` actualizado: rangos personalizables, anomalías, notas contextuales
- 7,137 pesajes generados (2026-04-01 a 2026-07-19), 618 anómalos, 3,985 con notas

## Archivos modificados
src/: sql_tools.py, main.py, llm_client.py, agent_orchestrator.py, scale.py, config.py, report_templates.py, sms_service.py
frontend/: AdminConfig.svelte, NotesField.svelte, HaciendaCodeInput.svelte, KioskForm.svelte
tests/: test_sql_tools.py, test_config.py, test_report_templates.py, test_sms_service.py
scripts/: generate_historical_weighings.py (reescrito)
docs/: admin_manual.md (nuevo)
harness/: specs/33_sql_tools_v2/, specs/37_notas_muestras/ (actualizado)

## Pendiente
- F32 (sample_imaging), F34 (alert_monitor), F35 (sms_scheduling_v2)
- Mejorar desempeño LLM local en CM4