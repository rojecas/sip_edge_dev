# Changelog — Harness-SDD

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
  `harness/init.ps1` — `schema_dump.py` al fallar mostraba traceback de Python en
  consola a pesar del `$null =`. Ahora se usa `$ErrorActionPreference = "SilentlyContinue"`
  durante la llamada para suprimir los `NativeCommandError` de PS 5.1.
- `harness/.opencode/templates/python/init.ps1` y `harness/init.ps1` — `python -m unittest`
  producia `NativeCommandError` en la salida. Mismo fix con `SilentlyContinue`.
- `harness/.opencode/scripts/validate_features.py` — `Path.read_text()` no manejaba BOM
  UTF-8 que escribe `Set-Content -Encoding UTF8` en PS 5.1, causando `Expecting value: line 1
  column 1 (char 0)`. Ahora usa `encoding="utf-8-sig"`.
- `harness/scripts/scaffold.ps1` — `Set-Content -Encoding UTF8` escribia BOM UTF-8 en todos
  los archivos generados (feature_list.json, docs, init.ps1, etc.). Reemplazado por
  `Write-FileNoBom` que usa `[System.IO.File]::WriteAllText` con `UTF8Encoding($false)`.

## [1.6.2] - 2026-06-13

### Fixed
- `harness/AGENTS.md` Seccion 8 — `docs/` y `specs/` ya no se listan como directorios
  en raiz del proyecto scaffolded. Ambos viven bajo `harness/` (estructura final y
  regla 1 corregidas; lecciones actualizadas).
- `harness/scripts/scaffold.ps1` — Ya no crea `docs/` ni `specs/` en raiz del target.
  Solo crea `src/`, `tests/`, `scripts/` (o `src/`, `include/`, `lib/`, `test/` para cpp-iot).

## [1.6.1] - 2026-06-13

### Removed
- `opencode.json` — Comando `/scaffold` eliminado. El scaffold ahora se hace
  exclusivamente via `harness/scripts/scaffold.ps1` en terminal.

## [1.6.0] - 2026-06-13

### Added
- `harness/scripts/scaffold.ps1` — Script interactivo que automatiza las 4 preguntas
  iniciales y todo el proceso de scaffold (crear directorios, copiar archivos AS-IS,
  renderizar templates del stack, generar wrapper init.ps1, y verificar con init.ps1).
  Soporta los 6 stacks: python, typescript, php-laravel, rust, go, cpp-iot.
  Para cpp-iot genera ademas `platformio.ini` y `.clang-format`.

## [1.5.0] - 2026-06-13

### Added
- `harness/AGENTS.md` — Seccion 8 "Scaffold de proyectos nuevos" con reglas,
  estructura final del proyecto, lecciones capturadas y tabla de errores comunes.
  Incluye: directorios a crear en raiz (`src/`, `tests/`, `scripts/`, `specs/`),
  ubicacion de `feature_list.json` en `harness/`, compatibilidad PS 5.1
  (`Join-Path` sin `-LiteralPath`), y cuidado con `Copy-Item`.

## [1.4.2] - 2026-06-12

### Fixed
- `harness/init.ps1` — `2>&1` en PS5.1 producia `RemoteException` que contaminaba la salida.
  Se capturo el output en variables locales con `$null = & cmd 2>&1` o `$result = & cmd 2>&1`
  segun el caso, y solo se muestra si hay error.
- `harness/init.ps1` — `schema_dump.py` al fallar mostraba traceback crudo de Python en
  consola. Ahora se redirige stderr a `$null` y solo se muestra el `[WARN]` correspondiente.
- `harness/init.ps1` — `validate_features.py` se ejecutaba sin captura de output,
  mostrando su prefijo `[validate_features]` inconsistente con el resto del script.
  Ahora se captura en variable y se muestra como `[OK]` solo si pasa, o se muestra
  el error si falla.
- `harness/init.ps1` — `python -m unittest` con salida 5 ("no tests found") se trataba
  como error. Ahora se acepta exit code 5 como exit code valido (no hay tests = no hay
  error).
- `harness/.opencode/templates/python/init.ps1` — mismos 3 problemas que `harness/init.ps1`.
  Aplicados los mismos parches: captura de validate_features, supresion de traceback de
  schema_dump, y manejo de exit code 5 en tests.
- `harness/.opencode/templates/typescript/init.ps1`,
  `harness/.opencode/templates/php-laravel/init.ps1`,
  `harness/.opencode/templates/rust/init.ps1`,
  `harness/.opencode/templates/go/init.ps1` — mismos problemas de validate_features
  (output raw) y schema_dump (traceback). Aplicados los parches correspondientes.

## [1.4.1] - 2026-06-12

### Fixed
- `harness/scripts/setup_wizard.ps1` — el dispatcher buscaba el wizard del stack solo
  en `.opencode/templates/`. En proyectos derivados el `.opencode/` vive bajo `harness/`,
  por lo que el wizard no se encontraba. Ahora busca en `harness/.opencode/templates/`
  primero y luego en `.opencode/templates/` como fallback.
- `harness/.opencode/templates/php-laravel/init.ps1` — seccion 0 duplicada: la deteccion
  de proyecto nuevo y llamada al wizard estaba tanto en el wrapper raiz como en el
  `harness/init.ps1`, causando doble ejecucion. Se movio esa logica exclusivamente al
  wrapper raiz, dejando `harness/init.ps1` solo con verificacion del estado de Laravel.

---

## [1.4.0] - 2026-06-12

### Added
- **Integracion GitHub Issues** en el flujo SDD. Sincroniza `feature_list.json` con GitHub:
  issues se crean al transicionar a `in_progress`, se cierran con comentario al marcar `done`.
- `harness/github.json` — configuracion de repo, habilitacion y labels
- `harness/.opencode/scripts/github_sync.py` — script con comandos `check`, `create`, `close`, `comment`
- `harness/docs/github.md` — documentacion de la integracion (prerequisitos, flujo, troubleshooting)
- `harness/CHECKPOINTS.md` C10 — verificacion de GitHub sync
- `harness/init.ps1` seccion 4.5 — verificacion de `gh` CLI y autenticacion

### Changed
- `harness/feature_list.json` — nueva feature `github_integration` (id 17, pending, sdd: true)
- `harness/AGENTS.md` — nuevas entradas en mapa (`harness/github.json`, `harness/docs/github.md`,
  `harness/.opencode/scripts/github_sync.py`); nueva regla dura de sincronizacion GitHub
- `harness/.opencode/scripts/validate_features.py` — validacion del campo `github_issue` (formato URL)
- `harness/.opencode/agents/leader.md` — Caso B: crea issue en GitHub al transicionar a `in_progress`
- `harness/.opencode/agents/implementer.md` — Paso 8: cierra issue en GitHub al marcar `done`
- `harness/.opencode/agents/reviewer.md` — Paso 5: verifica GitHub sync (issue existe, cerrado si done)
- `harness/docs/specs.md` — `github_labels` opcional documentado en `design.md`
- `harness/docs/sessions.md` — A2 template incluye verificacion de GitHub issue cerrado
- `harness/VERSION` — bump a 1.4.0

---

## [1.3.0] - 2026-06-12

### Changed
- **Coherencia de paths:** Todos los archivos del harness referencian rutas con prefijo `harness/`.
  Las plantillas y los agentes ahora son consistentes con la fabrica.
- `harness/.opencode/templates/python/init.ps1` — `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/typescript/init.ps1` — `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/php-laravel/init.ps1` — `$baseFiles`, script paths, DB paths, wizard path prefijados con `harness/`
- `harness/.opencode/templates/rust/init.ps1` — `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/go/init.ps1` — `$baseFiles`, script paths, DB paths prefijados con `harness/`
- `harness/.opencode/templates/cpp-iot/init.ps1` — `$baseFiles`, script paths, doc paths prefijados con `harness/`
- `harness/.opencode/agents/leader.md` — paths de archivos del harness prefijados con `harness/`
- `harness/.opencode/agents/implementer.md` — paths de archivos del harness prefijados con `harness/`
- `harness/.opencode/agents/spec-author.md` — paths de archivos del harness prefijados con `harness/`
- `harness/.opencode/agents/reviewer.md` — paths de archivos del harness prefijados con `harness/`
- `harness/AGENTS.md` — corregidos `progress/closure-*`, `progress/blocked-*`, `specs/<name>/` sin prefijo `harness/`
- `harness/CHECKPOINTS.md` — todos los paths de harness prefijados con `harness/` (C1-C8)
- `harness/docs/sessions.md` — paths de artefactos prefijados con `harness/progress/` y `harness/specs/`
- `harness/VERSION` — bump a 1.3.0

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
- `harness/docs/sessions.md` — estandar de documentacion con 3 artefactos
  obligatorios: A1 (plan de feature/bug), A2 (closure al marcar `done`),
  A3 (registro de bloqueo al marcar `blocked`). Templates incluidos.
- `harness/CHECKPOINTS.md` C8 — "Documentacion historica": verifica que toda
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

## [1.0.0] - 2026-06-11

### Added
- SDD workflow completo (EARS notation, 3-file spec, human approval gate)
- 4 sub-agentes: `leader`, `spec-author`, `implementer`, `reviewer`
- 6 templates de stack: `python`, `typescript`, `php-laravel`, `rust`, `go`, `cpp-iot`
- `setup_wizard.ps1` dispatcher generico con deteccion de stack
- `init.ps1` con verificacion de entorno, archivos base, validacion de features y tests
- `validate_features.py` — validador de `feature_list.json`
- `CHECKPOINTS.md` (C1-C6) — criterios de evaluacion
- Demo `notes-cli` con 7 features completadas y 27 tests
