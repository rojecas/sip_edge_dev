## [1.12.0] - 2026-06-18

### Added
- harness/AGENTS.md — Nueva regla dura: "Gobierno de archivos compartidos".
  Si una implementacion modifica archivos creados por features anteriores, el
  implementer DEBE identificar features dependientes, re-ejecutar sus tests,
  y documentar el impacto. El reviewer DEBE verificar.
- harness/AGENTS.md — Nueva regla dura: "Consulta de skills obligatoria".
  Antes de implementar, el agente DEBE cargar y leer los skills relevantes
  al stack del proyecto. Si el skill contradice el codigo existente, el
  agente DEBE priorizar el skill y documentar la desviacion.
- .opencode/agents/implementer.md — Paso 1 del protocolo SDD ahora exige
  cargar skills del stack. Paso 3 exige identificar features dependientes
  al modificar archivos compartidos. Nuevas reglas duras sobre shared files
  y skills.
- .opencode/agents/reviewer.md — Nuevo paso 6: verificar que el implementer
documento los skills consultados. Nuevo paso 7: verificar impacto en
features existentes. Nuevas reglas duras correspondientes.
- harness/docs/verification.md — Nuevo Nivel 5: verificacion manual de UI para SPA frontend.
  Estandariza la verificacion en local (Docker) y remoto (EdgeBox) con tabla de escenarios.
  documento los skills consultados. Nuevo paso 7: verificar impacto en
  features existentes. Nuevas reglas duras correspondientes.

### Changed
- harness/VERSION — bump a 1.12.0

## [1.11.0] - 2026-06-18

### Added
- .opencode/skills/svelte5/SKILL.md — Nuevo skill de Svelte 5 con reglas duras:
  runes (/ solo en .svelte.js), mount() vs new App(),
  patron storeName para svelte/store, onMount imports, checklist del implementer.
- harness/docs/specs.md — Nueva regla: maximo 20 requirements por feature.
  Si se excede, dividir en sub-features (ej: 14a, 14b, 14c).
- harness/docs/specs.md — Nueva seccion obligatoria en design.md: Contrato API.
  El implementer debe saber si la respuesta es array directo o {items: [...]}.
- harness/docs/specs.md — Nueva regla en tasks.md: cada task que use funciones
  de framework (onMount, useEffect, etc.) DEBE listar el import requerido.

### Changed
- harness/VERSION — bump a 1.11.0
## [1.10.0] - 2026-06-15

### Added
- harness/docs/verification.md — Nuevo Nivel 4 de verificación en EdgeBox (hardware real).
  Obligatorio para features que toquen hardware (puertos seriales, modem GSM, RTC, WDT).
  Incluye comandos SSH para deploy + tests_hardware + smoke test de health check.
  Si falla, la feature se marca como locked.
- harness/docs/environment.md — Nuevos comandos SSH para ejecutar tests de hardware en
  EdgeBox post-deploy, smoke test de health check y logs del servicio tras reinicio.
- harness/docs/sessions.md — Templates A2.1 (feature closure) y A2.2 (bug closure)
  actualizados con checkbox de verificación Nivel 4 EdgeBox (si aplica hardware).

### Changed
- harness/VERSION — bump a 1.10.0

---
# Changelog â€” Harness-SDD

> Registro de cambios en la fabrica de harnesses. Cada entrada describe
> que archivos se modificaron y por que.

## Como usar este archivo

### Al modificar la fabrica (trabajando en Harness-SDD)

1. Determinar el nuevo numero de version segun semver:
   - **MAJOR** (X.0.0): cambio incompatible (ej. estructura de archivos radicalmente distinta)
   - **MINOR** (0.X.0): nuevas features del harness (nuevos docs, reglas, templates)
   - **PATCH** (0.0.X): correcciones (typos, bugs en scripts del harness)
2. Actualizar `harness/VERSION`.
3. Anadir entrada `[X.Y.Z]` en este archivo con secciones `### Added`, `### Changed`,
   `### Removed` documentando cada archivo modificado y el proposito del cambio.
4. Registrar la sesion en `harness/progress/history.md`.

### Al actualizar el harness de un proyecto derivado

1. Leer `harness/VERSION` del proyecto para saber de que version de la fabrica deriva.
2. Leer este CHANGELOG desde la version del proyecto hasta la actual.
3. Las entradas entre ambas versiones son el **delta** de cambios a aplicar.
4. Aplicar cada cambio del delta, adaptandolo al stack del proyecto.
5. Actualizar `harness/VERSION` y `harness/CHANGELOG.md` del proyecto con la
   nueva version y los cambios aplicados.
6. Registrar la sesion de actualizacion en `harness/progress/history.md`.

---

## [1.6.3] - 2026-06-13

### Fixed
- `harness/.opencode/templates/{python,typescript,php-laravel,rust,go}/init.ps1` y
  `harness/init.ps1` â€” `schema_dump.py` al fallar mostraba traceback de Python en
  consola a pesar del `$null =`. Ahora se usa `$ErrorActionPreference = "SilentlyContinue"`
  durante la llamada para suprimir los `NativeCommandError` de PS 5.1.
- `harness/.opencode/templates/python/init.ps1` y `harness/init.ps1` â€” `python -m unittest`
  producia `NativeCommandError` en la salida. Mismo fix con `SilentlyContinue`.
- `harness/.opencode/scripts/validate_features.py` â€” `Path.read_text()` no manejaba BOM
  UTF-8 que escribe `Set-Content -Encoding UTF8` en PS 5.1, causando `Expecting value: line 1
  column 1 (char 0)`. Ahora usa `encoding="utf-8-sig"`.
- `harness/scripts/scaffold.ps1` â€” `Set-Content -Encoding UTF8` escribia BOM UTF-8 en todos
  los archivos generados (feature_list.json, docs, init.ps1, etc.). Reemplazado por
  `Write-FileNoBom` que usa `[System.IO.File]::WriteAllText` con `UTF8Encoding($false)`.

## [1.6.2] - 2026-06-13

### Fixed
- `harness/AGENTS.md` Seccion 8 â€” `docs/` y `specs/` ya no se listan como directorios
  en raiz del proyecto scaffolded. Ambos viven bajo `harness/` (estructura final y
  regla 1 corregidas; lecciones actualizadas).
- `harness/scripts/scaffold.ps1` â€” Ya no crea `docs/` ni `specs/` en raiz del target.
  Solo crea `src/`, `tests/`, `scripts/` (o `src/`, `include/`, `lib/`, `test/` para cpp-iot).

## [1.6.1] - 2026-06-13

### Removed
- `opencode.json` â€” Comando `/scaffold` eliminado. El scaffold ahora se hace
  exclusivamente via `harness/scripts/scaffold.ps1` en terminal.

## [1.6.0] - 2026-06-13

### Added
- `harness/scripts/scaffold.ps1` â€” Script interactivo que automatiza las 4 preguntas
  iniciales y todo el proceso de scaffold (crear directorios, copiar archivos AS-IS,
  renderizar templates del stack, generar wrapper init.ps1, y verificar con init.ps1).
  Soporta los 6 stacks: python, typescript, php-laravel, rust, go, cpp-iot.
  Para cpp-iot genera ademas `platformio.ini` y `.clang-format`.

## [1.5.0] - 2026-06-13

### Added
- `harness/AGENTS.md` â€” Seccion 8 "Scaffold de proyectos nuevos" con reglas,
  estructura final del proyecto, lecciones capturadas y tabla de errores comunes.
  Incluye: directorios a crear en raiz (`src/`, `tests/`, `scripts/`, `specs/`),
  ubicacion de `feature_list.json` en `harness/`, compatibilidad PS 5.1
  (`Join-Path` sin `-LiteralPath`), y cuidado con `Copy-Item`.

## [1.4.2] - 2026-06-12

### Fixed
- `harness/init.ps1` â€” `2>&1` en PS5.1 producia `RemoteException` que contaminaba la salida.
  Se capturo el output en variables locales con `$null = & cmd 2>&1` o `$result = & cmd 2>&1`
  segun el caso, y solo se muestra si hay error.
- `harness/init.ps1` â€” `schema_dump.py` al fallar mostraba traceback crudo de Python en
  consola. Ahora se redirige stderr a `$null` y solo se muestra el `[WARN]` correspondiente.
- `harness/init.ps1` â€” `validate_features.py` se ejecutaba sin captura de output,
  mostrando su prefijo `[validate_features]` inconsistente con el resto del script.
  Ahora se captura en variable y se muestra como `[OK]` solo si pasa, o se muestra
  el error si falla.
- `harness/init.ps1` â€” `python -m unittest` con salida 5 ("no tests found") se trataba
  como error. Ahora se acepta exit code 5 como exit code valido (no hay tests = no hay
  error).
- `harness/.opencode/templates/python/init.ps1` â€” mismos 3 problemas que `harness/init.ps1`.
  Aplicados los mismos parches: captura de validate_features, supresion de traceback de
  schema_dump, y manejo de exit code 5 en tests.
- `harness/.opencode/templates/typescript/init.ps1`,
  `harness/.opencode/templates/php-laravel/init.ps1`,
  `harness/.opencode/templates/rust/init.ps1`,
  `harness/.opencode/templates/go/init.ps1` â€” mismos problemas de validate_features
  (output raw) y schema_dump (traceback). Aplicados los parches correspondientes.

## [1.4.1] - 2026-06-12

### Fixed
- `harness/scripts/setup_wizard.ps1` â€” el dispatcher buscaba el wizard del stack solo
  en `.opencode/templates/`. En proyectos derivados el `.opencode/` vive bajo `harness/`,
  por lo que el wizard no se encontraba. Ahora busca en `harness/.opencode/templates/`
  primero y luego en `.opencode/templates/` como fallback.
- `harness/.opencode/templates/php-laravel/init.ps1` â€” seccion 0 duplicada: la deteccion
  de proyecto nuevo y llamada al wizard estaba tanto en el wrapper raiz como en el
  `harness/init.ps1`, causando doble ejecucion. Se movio esa logica exclusivamente al
  wrapper raiz, dejando `harness/init.ps1` solo con verificacion del estado de Laravel.

---

## [1.4.0] - 2026-06-12

### Added
- **Integracion GitHub Issues** en el flujo SDD. Sincroniza `feature_list.json` con GitHub:
  issues se crean al transicionar a `in_progress`, se cierran con comentario al marcar `done`.
- `harness/github.json` â€” configuracion de repo, habilitacion y labels
- `harness/.opencode/scripts/github_sync.py` â€” script con comandos `check`, `create`, `close`, `comment`
- `harness/docs/github.md` â€” documentacion de la integracion (prerequisitos, flujo, troubleshooting)
- `harness/CHECKPOINTS.md` C10 â€” verificacion de GitHub sync
- `harness/init.ps1` seccion 4.5 â€” verificacion de `gh` CLI y autenticacion

### Changed
- `harness/feature_list.json` â€” nueva feature `github_integration` (id 17, pending, sdd: true)
- `harness/AGENTS.md` â€” nuevas entradas en mapa (`harness/github.json`, `harness/docs/github.md`,
  `harness/.opencode/scripts/github_sync.py`); nueva regla dura de sincronizacion GitHub
- `harness/.opencode/scripts/validate_features.py` â€” validacion del campo `github_issue` (formato URL)
- `harness/.opencode/agents/leader.md` â€” Caso B: crea issue en GitHub al transicionar a `in_progress`
- `harness/.opencode/agents/implementer.md` â€” Paso 8: cierra issue en GitHub al marcar `done`
- `harness/.opencode/agents/reviewer.md` â€” Paso 5: verifica GitHub sync (issue existe, cerrado si done)
- `harness/docs/specs.md` â€” `github_labels` opcional documentado en `design.md`
- `harness/docs/sessions.md` â€” A2 template incluye verificacion de GitHub issue cerrado
- `harness/VERSION` â€” bump a 1.4.0

---

## [1.3.0] - 2026-06-12

### Changed
- **Coherencia de paths:** Todos los archivos del harness referencian rutas con prefijo `harness/`.
  Las plantillas y los agentes ahora son consistentes con la fabrica.
- `harness/.opencode/templates/python/init.ps1` â€” `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/typescript/init.ps1` â€” `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/php-laravel/init.ps1` â€” `$baseFiles`, script paths, DB paths, wizard path prefijados con `harness/`
- `harness/.opencode/templates/rust/init.ps1` â€” `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/go/init.ps1` â€” `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/cpp-iot/init.ps1` â€” `$baseFiles`, script paths, doc paths prefijados con `harness/`
- `harness/.opencode/agents/leader.md` â€” paths de archivos del harness prefijados con `harness/`
- `harness/.opencode/agents/implementer.md` â€” paths de archivos del harness prefijados con `harness/`
- `harness/.opencode/agents/spec-author.md` â€” paths de archivos del harness prefijados con `harness/`
- `harness/.opencode/agents/reviewer.md` â€” paths de archivos del harness prefijados con `harness/`
- `harness/AGENTS.md` â€” corregidos `progress/closure-*`, `progress/blocked-*`, `specs/<name>/` sin prefijo `harness/`
- `harness/CHECKPOINTS.md` â€” todos los paths de harness prefijados con `harness/` (C1-C8)
- `harness/docs/sessions.md` â€” paths de artefactos prefijados con `harness/progress/` y `harness/specs/`
- `harness/VERSION` â€” bump a 1.3.0

### Fixed
- Inconsistencia: las plantillas referenciaban `.opencode/scripts/`, `database/.schema_dump.json` en raiz,
  pero la fabrica los tiene bajo `harness/`. Ahora todas las referencias son `harness/.opencode/scripts/`,
  `harness/database/.schema_dump.json`, etc.
- Inconsistencia: `$baseFiles` de plantillas omitian `harness/VERSION`, `harness/docs/specs.md`,
  `harness/docs/sessions.md`. Ahora los incluyen.
- Inconsistencia: agentes referenciaban `docs/specs.md`, `feature_list.json` sin prefijo. Ahora usan `harness/docs/specs.md`,
  `harness/feature_list.json`.

---

## [1.2.0] - 2026-06-12

### Added
- **Principios SOLID** en `harness/docs/architecture.md`: S, O, L, I, D con
  checklist de evaluacion para el reviewer. Adaptable por stack.
- `harness/docs/sessions.md` â€” estandar de documentacion con 3 artefactos
  obligatorios: A1 (plan de feature/bug), A2 (closure al marcar `done`),
  A3 (registro de bloqueo al marcar `blocked`). Templates incluidos.
- `harness/CHECKPOINTS.md` C8 â€” "Documentacion historica": verifica que toda
  feature `done` tenga closure y toda `blocked` tenga registro.

### Changed
- `harness/AGENTS.md`: lectura obligatoria de `sessions.md` (S1). Nuevas reglas
  duras en S3 (closure, bloqueo, SOLID). Secciones S5 y S6 reescritas con
  protocolo paso a paso.
- `harness/progress/current.md`: template reestructurado con tabla indice de
  features y seccion de bloqueos activos.
- `harness/docs/architecture.md`: seccion SOLID insertada entre principios
  universales y capa de persistencia.

---

## [1.1.0] - 2026-06-12

### Added
- Seguimiento de cambios de BD: `harness/database/` con `.schema_dump.json`, `migrations/`, `backups/`
- `schema_dump.py` en `harness/.opencode/scripts/` (soporta SQLite y MySQL)
- `docs/database.md` como guia generica de persistencia (auto-generado cuando hay BD, manual para no-SQL)
- `CHECKPOINTS.md` C5: "La base de datos esta bajo control"
- `harness/VERSION` + `harness/CHANGELOG.md` (versionado de la fabrica misma)

### Changed
- **Refactor estructural:** fabrica en `harness/`, demo `notes-cli` en `demo/`
- `init.ps1` raiz ahora es un wrapper que delega en `harness/init.ps1`
- `harness/init.ps1`: paths actualizados, valida `harness/feature_list.json` y `demo/feature_list.json`
- `harness/AGENTS.md`: mapa actualizado con rutas `harness/` + seccion `demo/`
- `validate_features.py`: acepta path como argumento opcional
- `opencode.json`: instrucciones y scaffold apuntan a `harness/`

### Removed
- `database/` en raiz (conflicto con frameworks). Ahora en `harness/database/`.

---

## [1.7.0-sync] - 2026-06-14

### Added (from factory [1.7.0])
- `harness/.session` â€” Fusible de proteccion de sesion. Contiene `open` o `closed`.
  `init.ps1` lo verifica al arrancar; si esta `open`, advierte que la sesion anterior
  no se cerro correctamente. `close.ps1` lo pone en `closed` al finalizar.
- `harness/init.ps1` â€” Nueva seccion 1.5 que lee `harness/.session` y reporta
  `[WARN]` si la sesion anterior quedo abierta, o `[OK]` si cerro correctamente.
- `scripts/close.ps1` â€” Script de cierre de sesion limpio que ejecuta 3 pasos:
  verificacion de documentacion pendiente, sincronizacion con repositorio remoto
  (`git pull --rebase` + `git push`, o warning si no hay remote), y ejecucion de
  `init.ps1` como verificacion final. Soporta flags `-SkipDocs`, `-SkipGit`,
  `-SkipVerify`. Al finalizar escribe `closed` en `harness/.session`.
- `opencode.json` â€” Nuevos comandos built-in: `/close` (invoca `./scripts/close.ps1`)
  y `/proyect_init` (genera/actualiza AGENTS.md).
- `.opencode/agents/` y `.opencode/skills/` en raiz del proyecto â€” Copiados desde
  `harness/.opencode/` para que opencode detecte subagentes y skills por
  auto-descubrimiento.

### Changed (from factory [1.7.0] + [1.6.4])
- `harness/AGENTS.md` â€” Seccion 1 actualizada con pasos 2-3 sobre `.session` y
  `close.ps1`. Seccion 8 actualizada con `opencode.json` y `.opencode/` en la
  estructura final del proyecto. Nueva leccion capturada sobre opencode y
  auto-descubrimiento de subagentes.

### Version
- `harness/VERSION` â†’ 1.7.0 (sincronizado con la fabrica)

### Nota
Los cambios locales del proyecto ([1.7.0] spec naming convention, [1.7.1] Docker
detection fix) se preservan como historico y continuan aplicados.

---

## [1.9.1] - 2026-06-15

### Changed
- `harness/AGENTS.md` Seccion 8 â€” Eliminado `init.ps1` wrapper raiz del arbol de estructura final y reglas asociadas. Removida leccion sobre `Join-Path -LiteralPath` en wrapper raiz.
- `opencode.json` â€” Comando `/init` actualizado de `./init.ps1` a `./harness/init.ps1`.

### Removed
- `init.ps1` (raiz) â€” Wrapper que delegaba en `harness/init.ps1`. Ahora se invoca directamente `./harness/init.ps1`.

---

## [1.9.0] - 2026-06-15

### Added (from factory [1.8.0] + [1.9.0])
- `harness/.opencode/agents/bug-fixer.md` â€” Nuevo agente para diagnosticar y corregir bugs.
- `harness/.opencode/agents/intake-agent.md` â€” Nuevo agente para crear features/bugs via conversacion.
- `harness/.opencode/agents/release-manager.md` â€” Nuevo agente con modos register y release.
- `harness/releases/tracker.json` â€” Estado de releases pendientes e historicos.
- `harness/.opencode/templates/changelog.md` â€” Template de CHANGELOG.md para el proyecto.
- `harness/scripts/` â€” Directorio canonico de scripts operacionales.
- `harness/scripts/validate_features.py` â€” Validador con soporte de campo `type` (feature|bug), `untriaged`/`triaged`.
- `harness/scripts/github_sync.py` â€” Sincronizacion GitHub con soporte de bugs.
- `harness/scripts/close.ps1` â€” Cierre de sesion en directorio canonico (migrado desde `scripts/`).
- `harness/scripts/schema_dump.py` â€” Migrado desde `harness/database/`.
- `harness/docs/specs.md` â€” Nueva seccion documentando campo `type` y flujo de bugs.
- `harness/docs/sessions.md` â€” Anadidos A1.1 (plan-bug) y A2.2 (cierre de bug).
- `harness/CHECKPOINTS.md` â€” C11 para bug workflow.
- `opencode.json` â€” Nuevos comandos `/new_feature_bug` y `/release`.

### Changed
- `harness/feature_list.json` â€” Anadido `"type": "feature"` a todas las features existentes. `valid_status` incluye `untriaged` y `triaged`.
- `harness/init.ps1` â€” Referencias actualizadas de `harness/.opencode/scripts/` a `harness/scripts/`. Nueva seccion 3 con verificacion de specs que omite items type:bug.
- `harness/AGENTS.md` â€” Corregidas referencias de scripts. Anadido flujo de bugs (4.1). Anadidos intake-agent y release-manager al mapa. Nuevas reglas: campo `type`, release-manager exclusivo.
- `harness/docs/specs.md` â€” Diagrama actualizado con intake-agent y release-manager.
- `.opencode/agents/leader.md` â€” Anadidos casos E-H (bugs y no-SDD). Eliminadas llamadas a github_sync. Anadido release-manager step.
- `.opencode/agents/implementer.md` â€” Anadido protocolo no-SDD. Eliminado github_sync y changelog.
- `.opencode/agents/reviewer.md` â€” Anadido protocolo de revision de bugs. Checklist C11.
- `opencode.json` â€” Comando `close` actualizado a `harness/scripts/close.ps1`.

### Removed
- `harness/database/schema_dump.py` â€” Movido a `harness/scripts/schema_dump.py`.

### Si no aplica (cambios de fabrica saltados)
- Scaffold y templates de stacks no Python (typescript, php-laravel, rust, go, cpp-iot) â€” sip_edge usa stack Python, no aplican.
- Demo notes-cli y sus features â€” sip_edge no tiene demo.

## [1.7.1] - 2026-06-13

### Fixed
- `harness/init.ps1` â€” Seccion 6 (tests) no detectaba entornos Docker y ejecutaba
  `python -m unittest` nativamente, fallando cuando las dependencias estan solo en el
  contenedor. Ahora detecta `$hasCompose` y ejecuta via
  `docker compose exec -T backend python -m unittest discover -s tests -v`.

## [1.7.0] - 2026-06-13

### Added
- `harness/docs/specs.md`: ConvenciÃ³n de naming para specs con prefijo numÃ©rico `<id>_<name>` (ej. `01_system_config`). Permite identificar orden de implementaciÃ³n en revisiÃ³n histÃ³rica.

### Changed
- `harness/.opencode/agents/spec-author.md`: Actualizadas rutas de spec para usar `<id>_<name>` en lugar de `<name>`. El agente crea carpetas como `01_system_config/`.

---

## [1.0.0] - 2026-06-11

### Added
- SDD workflow completo (EARS notation, 3-file spec, human approval gate)
- 4 sub-agentes: `leader`, `spec-author`, `implementer`, `reviewer`
- 6 templates de stack: `python`, `typescript`, `php-laravel`, `rust`, `go`, `cpp-iot`
- `setup_wizard.ps1` dispatcher generico con deteccion de stack
- `init.ps1` con verificacion de entorno, archivos base, validacion de features y tests
- `validate_features.py` â€” validador de `feature_list.json`
- `CHECKPOINTS.md` (C1-C6) â€” criterios de evaluacion
- Demo `notes-cli` con 7 features completadas y 27 tests



