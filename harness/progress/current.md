# Sesión — 2026-07-24

## F45 — rs232_frame_update (done)

- **src/rs232.py:43-54** — nuevo formato de 14 campos (fecha `/`, hora HH:MM, campo fijo `1`, pesos `.2f`, 5 ceros)
- **tests/test_rs232.py** — 12 tests (4 nuevos), todos pasan
- **src/llm_client.py** — `thinking: disabled` para compatibilidad DeepSeek v4
- **src/main.py** — `deepseek-chat` → `deepseek-v4-flash`
- Agentes: unificados a `deepseek-v4-pro`

## F43 — corporate_branding (done, cerrada 2026-07-23)

- frontend/src/app.css, index.html, AuthModal, KioskLayout, AdminLayout, AboutModal
- Logo Mayagüez, favicon, tests

## Archivos modificados
- src/rs232.py, src/llm_client.py, src/main.py, tests/test_rs232.py
- .opencode/agents/*.md (modelos actualizados)
- harness/feature_list.json (F45 registrada y cerrada)
- harness/specs/45_rs232_frame_update/ (spec completo)
