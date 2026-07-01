# AGENTS.md â€” Mapa de navegacion para agentes de IA

> Este archivo es el **punto de entrada** para cualquier agente que trabaje en este
> repositorio. NO es una biblia de reglas: es un **mapa**. Lee solo lo que
> necesites cuando lo necesites (divulgacion progresiva).

---

## 1. Antes de empezar (obligatorio)

1. Ejecuta `./init.ps1` y verifica que termina sin errores. Si falla, **para**
   y resuelve el entorno antes de tocar codigo.
2. Si `init.ps1` reporto `[WARN]` en la seccion 1.5 (`.session = open`), advierte
   al usuario: "La sesion anterior no se cerro correctamente. Revisa
   harness/progress/current.md". Pregunta si desea continuar o ejecutar
   `./scripts/close.ps1` primero.
3. Escribe `open` en `harness/.session` para activar el fusible de proteccion.
   El script `./scripts/close.ps1` lo pondra en `closed` al finalizar.
4. Lee `harness/progress/current.md` para entender en que estado quedo la ultima sesion.
5. Lee `harness/feature_list.json`. Toda feature nueva (`"sdd": true`) pasa por
   **Spec Driven Development** â€” ver `harness/docs/specs.md` y S4 de este archivo.
6. Lee `harness/docs/specs.md` antes de tocar cualquier spec o feature `sdd: true`.
7. Lee `harness/docs/sessions.md` para conocer el estandar de documentacion
   (planes, cierres, bloqueos).
8. **Session reminder:** Revisa si hay contenido entre las marcas
   <!-- SESSION_REMINDER_START -->
<!-- SESSION_REMINDER_END --> al final
   de este archivo. Si hay contenido, presentalo al usuario y luego BORRA todo
   el contenido entre esas marcas (pero deja las marcas vacias).
   Si no hay contenido, continua normalmente.

## 2. Mapa del repositorio

### Fabrica de harnesses (`harness/`)

| Archivo / carpeta                      | Que contiene                                                                | Cuando leerlo |
|----------------------------------------|-----------------------------------------------------------------------------|---------------|
| `harness/feature_list.json`            | Features de la fabrica (wizards pendientes)                                 | Siempre, al empezar |
| `harness/VERSION`                      | Version semver de la fabrica (ej. `1.1.0`)                                  | Para saber que features del harness tiene este proyecto |
| `harness/CHANGELOG.md`                 | Registro de cambios de la fabrica                                            | Para ver el delta entre versiones |
| `harness/progress/current.md`          | Estado de la sesion actual                                                  | Siempre, al empezar |
| `harness/progress/history.md`          | Bitacora append-only de sesiones de la fabrica                              | Si necesitas contexto historico |
| `harness/docs/architecture.md`         | Principios de arquitectura (generico, stack-agnostic)                       | Antes de implementar |
| `harness/docs/conventions.md`          | Patrones de convenciones (generico, stack-agnostic)                         | Antes de escribir codigo |
| `harness/docs/specs.md`                | Proceso SDD: EARS notation, los 3 archivos, puerta de aprobacion humana     | Antes de redactar o leer un spec |
| `harness/docs/verification.md`         | Como verificar que tu trabajo funciona                                      | Antes de declarar una tarea como `done` |
| `harness/docs/database.md`             | Convencion de capa de persistencia (generico)                               | Antes de tocar BD |
| `harness/docs/environment.md`          | Template con placeholders para describir el entorno                         | Al adaptar a un proyecto |
| `harness/docs/sessions.md`             | Estandar de documentacion: planes, cierres y bloqueos                       | Antes de crear o cerrar cualquier artefacto de progreso |
| `harness/docs/deployment.md`           | Guia de despliegue: entornos, pasos, troubleshooting (template)             | Antes de modificar configuracion de entorno o deployar |
| `harness/docs/security.md`             | Postura de seguridad: hallazgos, estado, roadmap (template)                 | Antes de tocar auth, BD o datos sensibles |
| `harness/docs/index.md`                | Indice navegable de toda la documentacion (template)                        | Para ubicar documentacion por tema |
| `harness/CHECKPOINTS.md`               | Criterios objetivos de "estado final correcto"                              | Para auto-evaluarte |
| `harness/.opencode/agents/`            | Definiciones de subagentes (`leader`, `spec-author`, `implementer`, `reviewer`, `bug-fixer`, `intake-agent`, `release-manager`) | Si orquestas trabajo |
| `harness/.opencode/templates/`         | Templates por stack (python, typescript, rust, go, cpp-iot, php-laravel)   | Al hacer scaffold |
| `harness/scripts/`                     | Scripts operacionales: `close.ps1`, `github_sync.py`, `validate_features.py`, `schema_dump.py`, `setup_wizard.ps1` | Durante cierre de sesion o sync |
| `harness/releases/tracker.json`        | Estado de releases pendientes e historicos                                   | Al hacer release |
| `harness/database/`                    | `.schema_dump.json`, `migrations/`, `backups/` (solo si el proyecto usa BD) | Antes de escribir migraciones |
| `harness/github.json`                  | Configuracion de integracion con GitHub (repo, enabled, labels)              | Al configurar GitHub sync |
| `harness/docs/github.md`               | Documentacion de la integracion GitHub Issues                                 | Antes de usar github_sync.py |
| `harness/scripts/github_sync.py`       | Script de sincronizacion con GitHub (create, close, comment, check)       | Al transicionar features |
| `harness/scripts/setup_wizard.ps1`     | Dispatcher generico de wizard por stack                                     | Durante scaffold |
| `harness/scripts/close.ps1`            | Cierre de sesion limpio (docs, git, verificacion)                            | Al terminar sesion |

### Demo (`demo/`)

| Archivo / carpeta          | Que contiene                                      | Cuando leerlo |
|----------------------------|--------------------------------------------------|---------------|
| `demo/feature_list.json`   | Features de la demo notes-cli (11 features)       | Para referencia didactica |
| `demo/src/`                | Codigo de la aplicacion demo (storage, notes, cli)| Para referencia didactica |
| `demo/tests/`              | Tests de la demo                                  | Para referencia didactica |
| `demo/specs/cli_recent/`   | Spec SDD de ejemplo                               | Para referencia didactica |
| `demo/progress/`           | Historial de sesiones de la demo                  | Para referencia didactica |

## 3. Reglas duras (no negociables)

- **Una sola feature a la vez.** No mezcles cambios de varias tareas en la misma sesion.
- **No declares una tarea `done` sin verificacion.** Ejecuta `./init.ps1` y
   asegurate de que el bloque correspondiente pasa al 100%.
- **No saltes la fase de spec.** Toda feature con `"sdd": true` debe pasar
  por `spec_author` y obtener aprobacion humana antes de tocar codigo.
- **No saltes la puerta de aprobacion humana.** El leader detiene el flujo
  en `spec_ready` y espera.
- **Documenta lo que haces** en `harness/progress/current.md` mientras trabajas.
- **Deja el repositorio limpio** antes de cerrar la sesion (ver S5).
- **Crea harness/progress/closure-<name>.md` al marcar `done`.** Ninguna feature se
  cierra sin un documento de cierre que capture archivos modificados, decisiones
  tecnicas y verificacion. Ver `harness/docs/sessions.md` A2.
- **Crea harness/progress/blocked-<name>.md` al marcar `blocked`.** Documenta
  contexto, sintoma, intentos y dependencias. Ver `harness/docs/sessions.md` A3.
- **Respeta SOLID.** El reviewer rechaza codigo que viole S, O, L, I, D sin
  justificacion documentada. Ver `harness/docs/architecture.md`.
- **Versiona los cambios de la fabrica.** Si modificas cualquier archivo bajo
  `harness/docs/`, `harness/AGENTS.md`, `harness/CHECKPOINTS.md`, o templates,
  DEBES actualizar `harness/VERSION` (semver) y `harness/CHANGELOG.md` con
  el detalle de archivos modificados. Ver `harness/CHANGELOG.md`.
- **Si no sabes algo, busca en `harness/docs/`** antes de inventarlo.
- **Antes de escribir SQL, queries o migraciones, lee `harness/docs/database.md`.**
- **Antes de ejecutar comandos bash, lee `harness/docs/environment.md`.**
- **Sincroniza con GitHub.** Si `harness/github.json` tiene `enabled: true`, el leader DEBE crear
  el issue al transicionar a `in_progress` y el implementer DEBE cerrarlo al marcar `done`. Si gh falla, la feature se bloquea.
- **Cada item en `feature_list.json` DEBE tener campo `type`** con valores `"feature"` o `"bug"`.
- **El release-manager es el unico que toca version, changelog y GitHub sync.**
- **Gobierno de archivos compartidos.** Si una implementacion modifica archivos que fueron creados por features anteriores (src/, stores/, lib/, components/ compartidos, etc.), el implementer DEBE:
  1. Identificar que features consumen esos archivos (revisar depends_on en eature_list.json, rastrear imports en el codigo fuente).
  2. Re-ejecutar los tests de las features afectadas.
  3. Documentar el impacto en harness/progress/impl_<name>.md bajo la seccion 'Impacto en features existentes'.
  El reviewer DEBE verificar que este analisis existe y que no hay regresiones en features dependientes.
- **Consulta de skills obligatoria.** Antes de implementar un cambio, el agente DEBE cargar y leer los skills relevantes al stack del proyecto (ej: svelte5, 
eact18, laravel). Si el skill contiene reglas que contradicen el codigo existente, el agente DEBE priorizar el skill y documentar la desviacion en harness/progress/impl_<name>.md. El reviewer DEBE verificar que los skills relevantes fueron consultados.

## 4. Flujo de trabajo (SDD)

```
pending -> [spec-author] -> spec_ready -> HUMANO -> in_progress -> [implementer -> reviewer] -> done
```

1. El leader detecta la primera feature `pending` con `"sdd": true`.
2. El leader lanza `spec-author`, que crea
   `harness/specs/<name>/{requirements,design,tasks}.md` y marca el status como
   `spec_ready`.
3. **Pausa.** El humano lee el spec en `harness/specs/<name>/` y aprueba (o pide cambios).
4. Una vez aprobado, el leader cambia el status a `in_progress` y lanza `implementer`.
5. El implementer ejecuta `tasks.md` una a una, marcanbolas `[x]`.
6. El reviewer verifica trazabilidad `R<n>` <-> test y tasks completas;
   aprueba o rechaza.
7. Si aprueba, el leader lanza `release-manager (register)`, que cierra el issue de GitHub
   y marca `done`.

### 4.1 Flujo de trabajo (bugs)

```
untriaged -> HUMANO -> triaged -> [bug-fixer -> reviewer -> release-manager] -> done
```

1. El humano o `intake-agent` crea un item con `"type": "bug"` y status `untriaged`.
2. El leader presenta el bug al humano para confirmacion.
3. Si el humano confirma, el leader cambia a `triaged` y lanza `bug-fixer`.
4. El bug-fixer diagnostica, escribe `plan-bug-<name>.md`, implementa fix + regression test.
5. El reviewer verifica cobertura del reproduction, regresiones, y `./init.ps1` verde.
6. El release-manager cierra el issue y marca `done`.

## 5. Cierre de sesion (lifecycle)

Antes de terminar:

1. Ejecuta `./init.ps1` â€” todo verde.
2. Si la tarea esta acabada: crea harness/progress/closure-<name>.md` siguiendo
   `harness/docs/sessions.md` A2. Marca `status: "done"` en `harness/feature_list.json`.
3. Mueve el resumen de `harness/progress/current.md` al final de `harness/progress/history.md`.
4. Vacia `harness/progress/current.md` dejando solo la plantilla.
5. No dejes archivos temporales, ni prints de debug, ni TODOs sin contexto.
6. Ejecuta `harness/scripts/close.ps1` para el cierre formal de sesion.

## 6. Si te bloqueas

1. Crea harness/progress/blocked-<name>.md` siguiendo `harness/docs/sessions.md` A3.
2. Marca la feature como `"blocked"` en `harness/feature_list.json`.
3. Documenta el bloqueo en `harness/progress/current.md`.
4. Si la herramienta no hace lo que esperas, **no inventes un workaround**:
   para la sesion y reporta el bloqueo.

## 7. Versionado de la fabrica

Cada cambio en los archivos de la fabrica (`harness/docs/`, `harness/AGENTS.md`,
`harness/CHECKPOINTS.md`, templates, scripts del harness) DEBE quedar
registrado con un bump de version y una entrada en `harness/CHANGELOG.md`.

### Semver para la fabrica

| Bump | Cuando usarlo | Ejemplo |
|------|--------------|---------|
| **MAJOR** (X.0.0) | Cambio incompatible: reestructuracion de carpetas, nuevo formato de `feature_list.json`, cambio de motor de BD | `1.1.0` â†’ `2.0.0` |
| **MINOR** (0.X.0) | Nuevas features del harness: nuevo doc, nueva regla, nuevo template, nuevo script | `1.1.0` â†’ `1.2.0` |
| **PATCH** (0.0.X) | Correcciones: typos, bugs en scripts, ajustes menores sin nuevo comportamiento | `1.1.0` â†’ `1.1.1` |

### Procedimiento

1. Bump `harness/VERSION`.
2. Anadir entrada en `harness/CHANGELOG.md` con secciones `Added`, `Changed`, `Removed`.
3. Cada item del changelog DEBE listar los archivos concretos modificados.
4. Registrar la sesion en `harness/progress/history.md`.

## 8. Scaffold de proyectos nuevos

> Al crear un proyecto nuevo a partir de esta fabrica, sigue estas reglas.
> Fueron capturadas de sesiones anteriores donde el scaffold fallo.

### Estructura final de un proyecto scaffolded

```
<proyecto>/
â”œâ”€â”€ opencode.json             # config de opencode (instrucciones, comandos, agentes, skills)
â”œâ”€â”€ .opencode/                # agentes y skills (copia de harness/.opencode/agents/ y skills/)
â”‚   â”œâ”€â”€ agents/               # leader, spec-author, implementer, reviewer, bug-fixer, intake-agent, release-manager
â”‚   â””â”€â”€ skills/               # sdd-workflow
â”œâ”€â”€ src/                      # codigo fuente del proyecto
â”œâ”€â”€ tests/                    # tests del proyecto
â”œâ”€â”€ scripts/                  # setup_wizard.ps1
â””â”€â”€ harness/                  # la fabrica autocontenida
    â”œâ”€â”€ init.ps1              # verificacion de entorno
    â”œâ”€â”€ feature_list.json     # features del proyecto (NO en raiz)
    â”œâ”€â”€ AGENTS.md, VERSION, CHANGELOG.md, CHECKPOINTS.md, github.json
    â”œâ”€â”€ .opencode/            # agentes, scripts, skills, templates
    â”œâ”€â”€ docs/                 # architecture, conventions, specs, sessions, etc.
    â”œâ”€â”€ specs/                # specs SDD (requirements, design, tasks)
    â”œâ”€â”€ progress/             # current.md, history.md, closure-*, blocked-*
    â”œâ”€â”€ scripts/              # close.ps1, github_sync.py, validate_features.py, schema_dump.py
    â”œâ”€â”€ releases/             # tracker.json
    â””â”€â”€ database/             # .schema_dump.json, migrations/, backups/, seeds/
```

### Reglas al ejecutar el scaffold

1. **Solo tres directorios de proyecto en raiz:** `src/`, `tests/`, `scripts/`.
   Los directorios `docs/`, `progress/`, `specs/` viven dentro de `harness/`.
   Si el usuario quiere un `docs/` propio, que lo cree el manualmente.
   **El scaffold DEBE crear `opencode.json` y `.opencode/` en raiz** para que
   opencode detecte los subagentes y las skills (el contenido se copia de
   `harness/.opencode/agents/` y `harness/.opencode/skills/`).

2. **`feature_list.json` va en `harness/`**, no en la raiz del proyecto.
   El template `harness/init.ps1` espera `harness/feature_list.json`.
   `validate_features.py` por defecto busca en `harness/feature_list.json`.
   Mantenerlo ahi evita parchear los scripts.

3. **Al copiar `harness/` desde la fabrica, usar `Copy-Item -Recurse`**
   para directorios completos. Al copiar archivos individuales dentro de
   directorios, asegurarse de que el directorio destino existe como
   `-PathType Container` (no como archivo). `Copy-Item` puede tratar
   un directorio como archivo si el destino no existe.

4. **Verificar SIEMPRE con `./harness/init.ps1`** al terminar el scaffold.
   No declarar el scaffold como terminado hasta que todos los bloques
   esten `[OK]`.

### Lecciones capturadas (no repetir)

| Error | Causa | Correccion |
|-------|-------|-----------|
| `progress/`, `docs/` y `specs/` duplicados en raiz | El scaffold creaba esos dirs en raiz, pero el contenido real iba en `harness/` | Solo crear `src/`, `tests/`, `scripts/` en raiz |
| `feature_list.json` en raiz causa `[FAIL]` en init.ps1 | Template espera `harness/feature_list.json` | Poner `feature_list.json` en `harness/` |
| `validate_features.py` busca `harness/feature_list.json` por defecto | Script asume que base es `harness/` | Mantener `feature_list.json` en `harness/` |
| Directorios copiados como archivos | `Copy-Item` sin `-Recurse` en directorio | Usar `Copy-Item -Recurse` para dirs; si no, copiar archivo por archivo |
| opencode no detecta subagentes ni skills en proyecto nuevo | scaffold no generaba `opencode.json` ni `.opencode/` en raiz | Generar `opencode.json` en raiz y copiar agents + skills a `.opencode/` |

## 9. Actualizar un proyecto derivado

Cuando un proyecto creado a partir de esta fabrica necesita recibir las
mejoras del harness:

1. Leer `harness/VERSION` del proyecto (ej. `1.1.0`).
2. Leer `harness/CHANGELOG.md` de la fabrica desde la version del proyecto
   hasta la version actual de la fabrica (ej. `1.1.0` â†’ `1.2.0`).
3. **El delta entre versiones es la lista exacta de cambios a aplicar.**
4. Para cada entrada del delta:
   - Leer los archivos modificados listados en el changelog.
   - Adaptar el cambio al stack y convenciones del proyecto (PHP/CI, PHP/ZOOM, Python, etc.).
   - Si un cambio no aplica (ej. una regla sobre BD cuando el proyecto no usa BD), documentarlo en el CHANGELOG del proyecto como `### Skipped`.
5. Actualizar `harness/VERSION` del proyecto a la version de la fabrica.
6. Actualizar `harness/CHANGELOG.md` del proyecto con una entrada que
   liste los cambios aplicados y los saltados.
7. Ejecutar `./harness/init.ps1` en el proyecto â€” todo verde.
8. Registrar la sesion de actualizacion en `harness/progress/history.md`.

<!-- SESSION_REMINDER_START -->
<!-- SESSION_REMINDER_END -->



