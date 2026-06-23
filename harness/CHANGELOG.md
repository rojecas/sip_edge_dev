# Changelog — Harness-SDD

> ⚠️ **ESTE ES EL CHANGELOG DE LA FABRICA DEL HARNESS.**
> NO agregues entradas de features del proyecto aqui.
> Las features del proyecto se registran en `CHANGELOG.md` (raiz del proyecto).

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

## [1.13.1] - 2026-06-19

### Recibido desde fabrica Harness-SDD

### Fixed
- `harness/scripts/close.ps1` — Heuristica de `current.md` refinada: ahora filtra filas de tabla, headers de tabla, y placeholders de plantilla.
- `harness/scripts/close.ps1` — Git: chequeo de working tree limpio antes de pull. Comandos git con `EAP=Continue` local (PS 5.1).
- `harness/scripts/close.ps1` — Path de `init.ps1` corregido: `../../init.ps1` → `../init.ps1`.
- `.gitignore` — Anadido `harness/.session` (flag de runtime).
- `harness/.session` — `git rm --cached` (fuera del tracking).

## [1.14.0] - 2026-06-19

### Added
- harness/AGENTS.md — Seccion 1 paso 8: instruccion para leer y autodestruir recordatorios de sesion entre marcas \<!-- SESSION_REMINDER_START -->\ y \<!-- SESSION_REMINDER_END -->\.
- harness/AGENTS.md — Marcas \SESSION_REMINDER_*\ al final del archivo para recordatorios auto-limpiantes.
- harness/progress/next_session_reminder.md — Recordatorio para pruebas en EdgeBox (Features 14, 15, 16) y modo manual SMS.

### Changed
- harness/VERSION: 1.13.1 → 1.14.0 (minor)


## [1.13.0] - 2026-06-18

### Added
- `harness/docs/index.md` — Indice navegable de toda la documentacion del proyecto y del harness. Tablas de referencia cruzada con archivos, contenido y proposito. Mapa de conocimiento por tema con rutas "donde empezar / donde profundizar". Template con placeholders `{{PROJECT_NAME}}` y `{{..._DEEP_DIVE}}` para que cada proyecto lo adapte.
- `harness/docs/security.md` — Plantilla de postura de seguridad. Estructura: tabla resumen de estado (area, severidad, feature asociada), hallazgos documentados (archivo, problema, solucion, impacto), medidas ya implementadas, y roadmap (corto/mediano/largo plazo). Template con placeholders para que cada proyecto mantenga su propio analisis de seguridad.
- `harness/docs/deployment.md` — Guia de despliegue generica. Estructura: tabla de entornos (local, staging, produccion), instrucciones de desarrollo local (requisitos, inicio, primera vez, comandos utiles), pasos de despliegue a produccion, troubleshooting por escenario. Template con placeholders `{{DEV_URL}}`, `{{PROD_URL}}`, etc.
- `harness/docs/index.md` — Incluye seccion fija "Documentacion del harness" que lista todos los docs del harness con su contenido y proposito, mas secciones adaptables para docs del proyecto, artefactos de progreso y mapa de conocimiento.
- `harness/AGENTS.md` — Nuevas entradas en el mapa del repositorio (seccion 2) para `deployment.md`, `index.md` y `security.md`.

### Changed
- `harness/VERSION` — bump a 1.13.0

## [1.12.0] - 2026-06-18

### Added
- `harness/.opencode/agents/spec-author.md` — Nuevo paso 6: tras redactar los 3 archivos del spec, carga el skill `multi-reviewer` y ejecuta 6 revisores paralelos + arbiter sobre el spec completo. Incorpora los hallazgos antes de marcar `spec_ready`.
- `harness/.opencode/agents/bug-fixer.md` — Nuevo paso 4a en Fase 1 (diagnostico): carga el skill `systematic-debugging` y aplica su metodologia (hipotesis, reproduccion controlada, bisectriz) para determinar la causa raiz.
- `harness/.opencode/agents/intake-agent.md` — Nueva Fase 0 (descubrimiento) con 4 preguntas de contexto antes del formulario: problema, usuario/escenario, restricciones, edge cases. Alimenta los acceptance criteria y reduce specs bloqueados.
- `harness/.opencode/agents/implementer.md` — Paso 5 reescrito como ciclo rojo-verde-refactor: test que falla → minimo codigo → refactor. Orden estricto (test primero) que garantiza que cada test realmente prueba algo. Protocolo no-SDD tambien alineado.
- `harness/.opencode/agents/implementer.md` — Nuevo paso 8 (auto-revision) con checklist de 6 puntos antes de declarar `done`: cobertura R<n>, init.ps1 verde, sin debug prints, errores a stderr, convenciones, impacto documentado. Filtra rechazos evitables del reviewer. Protocolo no-SDD tambien incluye auto-revision.

### Changed
- `harness/VERSION` — bump a 1.12.0

## [1.11.0] - 2026-06-18

### Added
- `harness/docs/specs.md` — Nueva regla: maximo 20 requirements por feature. Si se excede, dividir en sub-features (ej: 14a, 14b, 14c).
- `harness/docs/specs.md` — Nueva seccion obligatoria en design.md: Contrato API. Declara el formato de respuesta esperado para que el implementer no asuma array directo cuando el backend devuelve `{items: [...]}`.
- `harness/docs/specs.md` — Nueva regla en tasks.md: cada task que use funciones de framework (Svelte: `onMount`, React: `useEffect`, etc.) DEBE listar el import requerido como subtask.
- `harness/AGENTS.md` — Nueva regla dura: "Gobierno de archivos compartidos". Si una implementacion modifica archivos creados por features anteriores, el implementer DEBE identificar features dependientes, re-ejecutar sus tests, y documentar el impacto. El reviewer DEBE verificar.
- `harness/AGENTS.md` — Nueva regla dura: "Consulta de skills obligatoria". Antes de implementar, el agente DEBE cargar y leer los skills relevantes al stack del proyecto. Si el skill contradice el codigo existente, priorizar el skill y documentar la desviacion.
- `harness/.opencode/agents/implementer.md` — Paso 1: ahora exige cargar skills del stack y documentar desviaciones. Nuevo paso 3: identificar features dependientes al modificar archivos compartidos.
- `harness/.opencode/agents/reviewer.md` — Nuevo paso 6: verificar que el implementer documento los skills consultados. Nuevo paso 7: verificar impacto en features existentes. Nuevas reglas duras correspondientes. Formato de veredicto actualizado con secciones de skills e impacto.

### Changed
- `harness/VERSION` — bump a 1.11.0

## [1.10.0] - 2026-06-15

### Changed
- `harness/.opencode/agents/bug-fixer.md` — Protocolo separado en 2 fases: F1 diagnostica y escribe plan-bug (sin implementar), F2 implementa fix + regression test tras aprobacion humana del plan.
- `harness/AGENTS.md` — §4.1 actualizado: flujo de bugs con dos pausas humanas (confirmar bug + aprobar plan).
- `harness/.opencode/agents/leader.md` — Caso F (`triaged`) actualizado: lanza bug-fixer en 2 fases separadas con pausa humana entre ellas para aprobar el plan.
- `harness/specs/18_bug_workflow/design.md` — Flujo de estados actualizado con 2 puertas humanas. Protocolo del bug-fixer dividido en Fase 1 y Fase 2. Tabla de GitHub sync actualizada.
- `harness/specs/18_bug_workflow/requirements.md` — R8 separado por fase (diagnostico vs implementacion). Nuevo R10b: prohibicion de implementar sin aprobacion humana del plan.
- `harness/CHECKPOINTS.md` — C11: nueva verificacion de que `plan-bug-<name>.md` fue aprobado por humano antes de implementar.

## [1.9.0] - 2026-06-15

### Added
- `README_harness.md` — Regla de ruta canonica: todo script operacional del harness reside en `harness/scripts/`.
- `README_harness.md` — Arboles de directorios actualizados (fabrica y proyecto scaffolded) reflejando la nueva ubicacion de scripts.
- `harness/.opencode/templates/changelog.md` — Template para el `CHANGELOG.md` del proyecto (formato keepachangelog).
- `harness/AGENTS.md` — Regla dura: CHANGELOGs diferenciados (fabrica vs proyecto). Tabla actualizada con proyecto-level CHANGELOG.md.
- `harness/feature_list.json` — Anadido `"type": "feature"` a las 7 features existentes (ids 12-18). Ahora toda entrada tiene `type` explicito.
- `demo/feature_list.json` — Anadido `"type": "feature"` a las 11 features existentes (ids 1-11).
- `harness/docs/specs.md` — Nueva seccion documentando el campo `type` con valores feature|bug y requisitos de cada uno.
- `harness/AGENTS.md` — Nueva regla dura: campo `type` explicito en feature_list.json.
- `harness/.opencode/agents/intake-agent.md` — Nuevo agente para crear features/bugs via conversacion con el humano.
- `harness/.opencode/agents/release-manager.md` — Nuevo agente con 2 modos: register (trackea cambios) y release (publica version).
- `harness/releases/tracker.json` — Estado de releases pendientes e historicos.
- `opencode.json` — Nuevos comandos `/new_feature_bug` y `/release`.
- `harness/AGENTS.md` — Regla dura: release-manager es el unico que toca version, changelog y GitHub sync.

### Changed
- `harness/.opencode/scripts/github_sync.py` → `harness/scripts/github_sync.py` — Unificado con el directorio canonico de scripts.
- `harness/.opencode/scripts/schema_dump.py` → `harness/scripts/schema_dump.py` — Idem.
- `harness/.opencode/scripts/validate_features.py` → `harness/scripts/validate_features.py` — Idem.
- `harness/init.sh` → `harness/scripts/init.sh` — Movido al directorio canonico de scripts (legacy Linux).
- `harness/init.ps1` — 4 referencias actualizadas de `harness/.opencode/scripts/` a `harness/scripts/`.
- `harness/init.ps1` — Referencia a `./scripts/close.ps1` corregida a `harness/scripts/close.ps1`.
- `opencode.json` — Comando `close` actualizado de `./scripts/close.ps1` a `harness/scripts/close.ps1`.
- `harness/AGENTS.md` — 2 referencias a `./scripts/close.ps1` corregidas a `harness/scripts/close.ps1`.
- `harness/.opencode/agents/leader.md` — 4 referencias a `harness/.opencode/scripts/github_sync.py` actualizadas.
- `harness/.opencode/agents/implementer.md` — Referencia a github_sync.py actualizada.
- `harness/.opencode/agents/bug-fixer.md` — Referencia a github_sync.py actualizada.
- `harness/docs/github.md` — 4 referencias a github_sync.py actualizadas.
- `harness/docs/database.md` — 2 referencias a schema_dump.py actualizadas.
- `harness/specs/18_bug_workflow/design.md` — 4 referencias a scripts actualizadas.
- `harness/specs/18_bug_workflow/tasks.md` — 2 referencias a scripts actualizadas.
- `harness/progress/closure-bug_workflow.md` — 2 referencias a scripts actualizadas.
- `harness/.opencode/templates/{python,typescript,php-laravel,rust,go,cpp-iot}/init.ps1` — 6 archivos: referencias a `harness/.opencode/scripts/` actualizadas a `harness/scripts/`.
- `harness/.opencode/templates/{python,typescript,php-laravel,rust,go}/database.md` — 5 archivos: referencias a `.opencode/scripts/` actualizadas a `harness/scripts/`.
- `harness/scripts/scaffold.ps1` — Copia `close.ps1` a `harness/scripts/` en vez de `scripts/` raiz. Copia `github_sync.py`, `validate_features.py` y `schema_dump.py` a `harness/scripts/`. Wrapper init.ps1 generado ahora usa `Push-Location` para proteger contra CWD incorrecto.
- `./init.ps1` — Wrapper raiz ahora cambia CWD a `$PSScriptRoot` via `Push-Location` para que `harness/init.ps1` resuelva correctamente sus rutas relativas.
- `harness/scripts/close.ps1` — 4 rutas internas corregidas: `$PSScriptRoot\..\harness\...` → `$PSScriptRoot\..\...` (eliminado `harness\` duplicado al estar en `harness/scripts/`).
- `harness/CHANGELOG.md` — Header de advertencia: "NO agregues entradas de features del proyecto aqui".
- `harness/scripts/scaffold.ps1` — `CHANGELOG.md` eliminado de `$copyAsIs` (ya no se copia el changelog de la fabrica al proyecto). Genera `CHANGELOG.md` del proyecto desde template. Genera `harness/releases/tracker.json`.
- `harness/.opencode/agents/leader.md` — Eliminadas todas las llamadas a `github_sync.py`. Agregado lanzamiento de `release-manager (register)` tras reviewer. Flujos simplificados.
- `harness/.opencode/agents/implementer.md` — Eliminado paso de changelog y github_sync. El implementer solo implementa.
- `harness/.opencode/agents/bug-fixer.md` — Eliminado paso de changelog y github_sync. El bug-fixer solo corrige.
- `harness/.opencode/agents/reviewer.md` — Eliminado checkbox de changelog. Ahora verifica solo codigo y tests.
- `harness/docs/sessions.md` — Closures A2.1 y A2.2: eliminados checkboxes de changelog y GitHub sync (los maneja release-manager).
- `harness/docs/specs.md` — Diagrama actualizado con intake-agent y release-manager.
- `harness/scripts/close.ps1` — Nuevo flag `-Release` para modo release.
- `README_harness.md` — Arboles actualizados con `releases/` directorio y 7 agentes.

### Removed
- `harness/.opencode/scripts/` — Directorio obsoleto (scripts movidos a `harness/scripts/`).
- `harness/Legacy_harness/` — Codigo muerto del harness anterior (contenia copias obsoletas de agentes, scripts y config de Claude).
- `harness/.opencode/node_modules/` — Dependencias npm no deberian estar versionadas en la fabrica.

---
## [1.8.0] - 2026-06-14

### Added
- `harness/.opencode/agents/bug-fixer.md` — Nuevo agente para diagnosticar y corregir bugs (type: bug). Protocolo: diagnostico → plan-bug → fix → regression test → github close → done.
- `harness/progress/impl_bug_workflow.md` — Trazabilidad R<n> → verificacion de la feature bug_workflow.
- `harness/progress/closure-bug_workflow.md` — Cierre documentado de la feature bug_workflow.
- `demo/feature_list.json` — Bug simulado `empty_title_validation` (id 12, type: bug) como demostracion del workflow.
- `demo/progress/closure-empty_title.md` — Cierre del bug demo.
- `harness/CHECKPOINTS.md` C11 — Verificaciones para bug workflow (plan-bug, closure, regression test, github sync para bugs).

### Changed
- `harness/feature_list.json` — `rules.valid_status` incluye `untriaged` y `triaged`. Feature 17 (github_integration) marcada `done` (ya estaba implementada). Feature 18 (bug_workflow) anadida y completada.
- `harness/.opencode/scripts/validate_features.py` — Soporta campo `type` (feature|bug, default feature). Valida `reproduction`, `affected_feature_ids` (ids existentes) para bugs. Relaja requisitos para bugs (sin sdd, sin acceptance). Ampliado `VALID_STATUSES`.
- `harness/.opencode/agents/leader.md` — Nuevos casos: E (bug untriaged), F (bug triaged), G (bug in_progress), H (sdd: false pending). Tabla de complejidad actualizada con columna de bugs. Reglas NO hacer actualizadas.
- `harness/.opencode/agents/implementer.md` — Modo no-SDD: protocolo alternativo sin carpeta `specs/`, crea `plan-<name>.md` desde `acceptance`.
- `harness/.opencode/agents/reviewer.md` — Protocolo de revision de bugs: verifica reproduction coverage, regresiones, GitHub sync. Formato de veredicto adaptado para bugs.
- `harness/docs/sessions.md` — A1.1 (plan-bug template), A2.1 (cierre de feature), A2.2 (cierre de bug con sintoma y causa raiz).
- `harness/init.ps1` — Seccion 3: omite verificacion de specs para items `type: bug`. Valida carpetas `specs/{NN}_{name}/` solo para features SDD.
- `harness/AGENTS.md` — Seccion 4.1: flujo para bugs (`untriaged → triaged → bug-fixer → done`). Nueva regla dura sobre bugs. Mapa actualizado con `bug-fixer.md`.
- `harness/.opencode/scripts/github_sync.py` — `build_issue_body()` detecta `type: bug` e incluye `reproduction` y `affected_feature_ids` en el cuerpo del issue.
- `harness/docs/specs.md` — Convencion de nombres de specs actualizada: `{NN}_{name}` donde NN es el id zero-padded a 2 digitos. Ejemplos: `01_system_config`, `18_bug_workflow`.
- `demo/src/cli.py` — `cmd_add` valida que el titulo no este vacio (fix del bug demo).
- `demo/tests/test_cli.py` — 2 regression tests para titulo vacio/whitespace.

### Fixed
- `harness/feature_list.json` — Feature 17 (github_integration) que estaba implementada desde v1.4.0 pero seguia marcada como `pending`.
- `harness/init.ps1` — Bug de parseo en PS 5.1 con caracteres Unicode (em-dash en strings). Reemplazados por ASCII `-`.

---

## [1.7.0] - 2026-06-14

### Added
- `harness/.session` — Fusible de proteccion de sesion. Contiene `open` o `closed`.
  `init.ps1` lo verifica al arrancar; si esta `open`, advierte que la sesion anterior
  no se cerro correctamente. `close.ps1` lo pone en `closed` al finalizar.
- `harness/init.ps1` — Nueva seccion 1.5 que lee `harness/.session` y reporta
  `[WARN]` si la sesion anterior quedo abierta, o `[OK]` si cerro correctamente.
- `harness/scripts/close.ps1` — Nuevo paso 4 que escribe `closed` en
  `harness/.session` tras completar la verificacion final.
- `harness/AGENTS.md` — Seccion 1 actualizada: el agente debe escribir `open` en
  `harness/.session` al iniciar trabajo real, y advertir al usuario si la sesion
  anterior no se cerro (paso 2).
- `harness/scripts/close.ps1` — Script de cierre de sesion limpio que ejecuta 3 pasos:
  verificacion de documentacion pendiente, sincronizacion con repositorio remoto
  (`git pull --rebase` + `git push`, o warning si no hay remote), y ejecucion de
  `init.ps1` como verificacion final. Soporta flags `-SkipDocs`, `-SkipGit`,
  `-SkipVerify`.
- `opencode.json` — Nuevo comando built-in `/close` que invoca `./scripts/close.ps1`
  en lugar de enviar un prompt largo al LLM. Mas rapido, cero tokens.
- `harness/scripts/scaffold.ps1` — Ahora copia `close.ps1` y `.session` al proyecto
  nuevo y propaga todos los comandos built-in desde el `opencode.json` de la fabrica
  (antes solo hardcodeaba `/init` y `/next`). Con fallback a comandos minimos si
  el archivo fuente no esta disponible.

## [1.6.4] - 2026-06-13

### Fixed
- `harness/scripts/scaffold.ps1` — No generaba `opencode.json` ni `.opencode/` en la raiz
  del proyecto nuevo. Ahora:
  - Se genera `opencode.json` con `instructions`, `command.init`, `command.next`,
    `permission` y `mcp` copiados del root `opencode.json` de la fabrica.
  - Se crea `.opencode/agents/` y `.opencode/skills/` en raiz copiando desde
    `harness/.opencode/agents/` y `harness/.opencode/skills/` para que opencode
    detecte los subagentes y skills por auto-descubrimiento.
  - Los directorios `.opencode/` en raiz se crean en el paso 3 (estructura).
- `harness/AGENTS.md` Seccion 8 — Estructura final del proyecto actualizada con
  `opencode.json` y `.opencode/` en raiz. Regla 1 y lecciones actualizadas.

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
