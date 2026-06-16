# Sesiones — Como documentar el trabajo

> Estandar de documentacion para sesiones de desarrollo. Define los
> artefactos que garantizan trazabilidad historica y permiten reconstruir
> decisiones tecnicas mucho tiempo despues.

## Artefactos obligatorios

### A1 — Plan de feature/bug

Se crea **antes** de tocar codigo.

- Si la feature tiene `"sdd": true`, el plan son los 3 archivos en
  `harness/specs/{NN}_{name}/` (`requirements.md`, `design.md`, `tasks.md`).
- Si es un bug (`"type": "bug"`), el plan es `harness/progress/plan-bug-<name>.md`
  (ver A1.2).
- Si no tiene SDD ni es bug, se crea `harness/progress/plan-<name>.md`
  (ver A1.1).

Contenido minimo del plan (features no-SDD):

- **Contexto:** que feature se aborda, cual es su `id` en
  `harness/feature_list.json`.
- **Diseno / solucion propuesta:** que archivos se crean o modifican, que
  firmas nuevas aparecen, que alternativas se descartaron.
- **Plan de verificacion:** escenarios concretos que se probaran.

#### A1.1 — Plan de bug (`harness/progress/plan-bug-<name>.md`)

Para items con `"type": "bug"`. Lo crea el `bug-fixer` durante la fase de diagnostico.

```markdown
# Plan bug — <bug name>

## Sintoma
<que falla, como se manifiesta, mensaje de error>

## Causa raiz
<que codigo o logica causa el fallo>

## Archivos implicados
- `src/xxx.py`: <que parte esta mal>
- `tests/test_xxx.py`: <test existente o nuevo>

## Fix propuesto
<que cambio corrige la causa raiz, por que>

## Plan de verificacion
- [ ] Regression test que cubre el escenario de `reproduction`
- [ ] `./init.ps1` verde
- [ ] Tests existentes no rotos
```

### A2 — Cierre (`harness/progress/closure-<name>.md`)

Se crea al marcar `"done"` en `feature_list.json`. Es el documento que
permite a un agente futuro (o a un humano) entender **que se hizo, por que
y como verificarlo**.

#### A2.1 — Cierre de feature

```markdown
# Cierre — <feature name>

## Resumen
<1-2 parrafos: que se implemento>

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
- [ ] Closure listo para release-manager

## Lecciones / pitfalls
- <algo que salio mal o que se aprendio>
```

#### A2.2 — Cierre de bug

```markdown
# Cierre — <bug name>

## Resumen
<1 parrafo: que bug se corrigio>

## Sintoma
<que fallaba>

## Causa raiz
<que causaba el fallo>

## Fix aplicado
<que cambio se hizo>

## Archivos modificados
| Archivo | Cambio |
|---------|--------|
| `src/foo.py` | Corregido metodo `bar()` |
| `tests/test_foo.py` | Regression test `test_xxx` |

## Verificacion
- [ ] `./init.ps1` verde
- [ ] Regression test `test_xxx` pasa
- [ ] Tests existentes no rotos
- [ ] Closure listo para release-manager

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
