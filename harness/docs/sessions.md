# Sesiones — Como documentar el trabajo

> Estandar de documentacion para sesiones de desarrollo. Define los
> artefactos que garantizan trazabilidad historica y permiten reconstruir
> decisiones tecnicas mucho tiempo despues.

## Artefactos obligatorios

### A1 — Plan de feature/bug

Se crea **antes** de tocar codigo. Si la feature tiene `"sdd": true`, el
plan son los 3 archivos en `harness/specs/<name>/` (`requirements.md`, `design.md`,
`tasks.md`). Si no tiene SDD, se crea `harness/progress/plan-<name>.md`.

Contenido minimo:

- **Contexto:** que feature o bug se aborda, cual es su `id` en
  `harness/feature_list.json`.
- **Diagnostico** (solo bugs): sintoma, causa raiz, archivos implicados.
- **Diseno / solucion propuesta:** que archivos se crean o modifican, que
  firmas nuevas aparecen, que alternativas se descartaron.
- **Plan de verificacion:** escenarios concretos que se probaran.
- **Draft de codigo:** opcional, util para bugs donde la solucion no es
  obvia.

### A2 — Cierre de feature (`harness/progress/closure-<name>.md`)

Se crea al marcar `"done"` en `feature_list.json`. Es el documento que
permite a un agente futuro (o a un humano) entender **que se hizo, por que
y como verificarlo**.

Contenido obligatorio:

```markdown
# Cierre — <feature name>

## Resumen
<1-2 parrafos: que se implemento/corrigio>

## Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `src/foo.py` | Anadido metodo `bar()` |
| `tests/test_foo.py` | 3 tests nuevos |

## Decisiones tecnicas
- <decision 1 y por que>
- <decision 2 y por que>
- <alternativa descartada y razon>

## Verificacion
- [ ] `./init.ps1` verde
- [ ] <test especifico 1>
- [ ] <test especifico 2>
- [ ] Trazabilidad R<n> ↔ tests (si SDD)
- [ ] GitHub issue cerrado (si `harness/github.json` enabled)

## Lecciones / pitfalls
- <algo que salio mal o que se aprendio>
```

### A3 — Registro de bloqueo (`harness/progress/blocked-<name>.md`)

Se crea al marcar `"blocked"` en `feature_list.json`. Documenta el estado
del bloqueo para que otro agente o un humano pueda retomar.

Contenido obligatorio:

```markdown
# Bloqueo — <feature name>

## Contexto
<que se estaba implementando, en que fase>

## Sintoma
<que fallo, mensaje de error, comportamiento observado>

## Intentos realizados
- <intento 1: que se hizo, resultado>
- <intento 2: que se hizo, resultado>

## Dependencias para desbloquear
- <que se necesita: decision externa, fix de otra feature, tooling, etc.>

## Archivos relevantes
- <archivos ya modificados o bajo investigacion>
```

## Prohibiciones

- NO borrar closures, planes ni registros de bloqueo. Son historicos.
- NO mezclar el cierre de dos features en un solo archivo.
- NO marcar `done` sin haber creado el closure correspondiente.
- NO marcar `blocked` sin haber creado el registro de bloqueo.
