# Bitacora historica de la fabrica (append-only)

> Cada vez que se cierra una sesion del harness, su resumen se anade aqui.
> No edites entradas anteriores. Solo anades al final.

---

## 2026-06-11 — Setup wizard integrado

- **Agente:** implementer
- **Cambios:** `scripts/setup_wizard.ps1` generico con deteccion de stack y delegacion a `.opencode/templates/<stack>/setup_wizard.ps1`. `init.ps1` Docker-aware. Scaffold copia `setup_wizard.ps1`.
- **Resultado:** 5 features pendientes (wizards python, typescript, rust, go, cpp-iot).
- **Lecciones:** 6 reglas duras aprendidas (PowerShell here-strings, UTF-8 BOM, TCP port checks, evitar `docker compose run`, no redirigir stderr de Docker).

## 2026-06-12 — Mejora de documentacion historica (v1.2.0)

- **Agente:** implementer
- **Cambios:** `harness/docs/architecture.md` (seccion SOLID), `harness/docs/sessions.md` (nuevo: estandar de planes, closures, bloqueos), `harness/AGENTS.md` (reglas duras ampliadas, S5/S6 reescritas), `harness/progress/current.md` (template con tabla indice), `harness/CHECKPOINTS.md` (C8: documentacion historica)
- **Resultado:** Inspirado en el sistema CCMT legacy de `plans/` + `handoffs/`, se adopto un sistema de 3 artefactos por feature: plan (antes), closure (al hacer `done`), registro de bloqueo (al `blocked`). Arquitectura reforzada con principios SOLID y checklist de evaluacion para el reviewer.
- **Lecciones:** Version y Changelog deben actualizarse como parte del cierre de sesion. El harness de cada proyecto derivado debe recibir las mismas actualizaciones.
