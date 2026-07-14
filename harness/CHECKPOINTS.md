# CHECKPOINTS — Evaluación del estado final

> En sistemas multi-agente no se evalúa el camino, se evalúa el destino.
> Estos son los checkpoints objetivos que un juez (humano o IA) puede usar
> para decidir si el proyecto está sano.

## C1 — El arnés está completo

- [ ] Existen los 4 archivos base: `harness/AGENTS.md`, `init.ps1` (o `init.sh` legacy),
      `harness/feature_list.json`, `harness/progress/current.md`.
- [ ] Existen los 3 docs: `harness/docs/architecture.md`, `harness/docs/conventions.md`,
      `harness/docs/verification.md`.
- [ ] `./init.ps1` (o `./init.sh` legacy) termina con exit code 0.

## C2 — El estado es coherente

- [ ] Como mucho una feature en `in_progress` en `harness/feature_list.json`.
- [ ] Toda feature `done` tiene tests asociados que pasan.
- [ ] `harness/progress/current.md` esta vacio o describe la sesion activa
      (no contiene basura de sesiones anteriores).

## C3 — El código respeta la arquitectura

- [ ] `src/` solo contiene los modulos previstos en `harness/docs/architecture.md`.
- [ ] No hay dependencias externas en `requirements.txt` (debe estar vacío
      o no existir).
- [ ] No hay `print()` sueltos para debug, ni TODOs sin contexto.

## C4 — La verificación es real

- [ ] `tests/` tiene al menos un test por módulo de `src/`.
- [ ] Los tests usan `tempfile.TemporaryDirectory()`, no mocks de fs.
- [ ] `python3 -m unittest discover -s tests -v` muestra > 0 tests
      y todos verdes.

## C5 — La base de datos está bajo control (si aplica)

- [ ] Si el proyecto usa BD SQL, existe `harness/database/.schema_dump.json`.
- [ ] `harness/docs/database.md` esta actualizado (generado por `schema_dump.py`).
- [ ] Las migraciones en `harness/database/migrations/` estan numeradas secuencialmente.
- [ ] Los cambios de schema estan documentados en `harness/specs/<feature>/design.md`
      bajo la sección `## Persistencia`.
- [ ] Si es proyecto legacy, existe `000_schema_inicial.sql` con el volcado inicial.

## C6 — La sesión se cerró bien

- [ ] No hay archivos sin trackear sospechosos (`*.tmp`, `__pycache__`
      fuera del `.gitignore`).
- [ ] `harness/progress/history.md` tiene una entrada por la ultima sesion.
- [ ] La última feature trabajada está reflejada en su estado correcto.

## C7 — Spec Driven Development

- [ ] Toda feature con `"sdd": true` en estado `spec_ready`, `spec-reviewed`,
      `in_progress`, `testing` o `done` tiene su carpeta `harness/specs/<name>/`
      con los 3 archivos: `requirements.md`, `design.md`, `tasks.md`.
- [ ] `requirements.md` usa EARS estricto (ver `harness/docs/specs.md`).
- [ ] Toda feature `done` con `"sdd": true` tiene todas sus tasks marcadas
      `[x]` en `tasks.md`.
- [ ] Cada `R<n>` de `requirements.md` esta cubierto por al menos un test
      concreto en `tests/`.

## C8 — Documentacion historica

- [ ] Toda feature `done` tiene `harness/progress/closure-<name>.md` con: resumen,
      archivos modificados, decisiones tecnicas, verificacion.
- [ ] Toda feature `blocked` tiene `harness/progress/blocked-<name>.md` con:
      contexto, sintoma, intentos, dependencias.
- [ ] Los closures documentan SOLID: si un principio se violo
      justificadamente, esta registrado en el closure.
- [ ] `harness/progress/history.md` tiene entrada por cada sesion cerrada.

---

**Cómo usar este archivo:** un agente revisor (`harness/.opencode/agents/reviewer.md`)
recorre cada checkbox, marca `[x]` o `[ ]`, y rechaza el cierre de sesion
si quedan boxes vacios en C1-C8.

## C10 — GitHub sync (si aplica)

- [ ] `harness/github.json` existe y tiene `repo` valido.
- [ ] Si `enabled: true`, `gh` CLI esta instalado y autenticado.
- [ ] Toda feature en `in_progress` o `done` tiene `github_issue` (URL valida).
- [ ] Toda feature `done` tiene su issue cerrado en GitHub.
- [ ] Las features `blocked` tienen un comentario en GitHub documentando el bloqueo.

## C11 — Bug workflow

- [ ] Todo bug en `triaged`, `in_progress` o `done` tiene `harness/progress/plan-bug-<name>.md` con diagnostico, causa raiz, fix propuesto.
- [ ] Todo bug `done` tiene `harness/progress/closure-<name>.md` con sintoma, causa raiz, fix aplicado, regression test.
- [ ] Cada bug `done` tiene un regression test que cubre el escenario de `reproduction`.
- [ ] El `reproduction` del bug coincide con lo que el test verifica.
- [ ] `./init.ps1` verde tras aplicar el fix.
