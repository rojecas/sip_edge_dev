# Spec Driven Development (SDD)

> Este proyecto sigue un flujo Kiro-style: requirements → design → tasks → code.
> El código no se escribe hasta que el spec está aprobado por un humano.

## Estructura

Cada feature nueva (`"sdd": true` en `feature_list.json`) tiene una carpeta
dedicada en cuanto deja `pending`:

```
specs/{NN}_{name}/
├── requirements.md   # QUÉ se necesita (EARS notation)
├── design.md         # CÓMO se construirá (decisiones técnicas)
└── tasks.md          # PASOS concretos a implementar
```

La carpeta se nombra `{NN}_{name}` donde `NN` es el `id` zero-padded a 2 digitos
y `name` coincide con el campo `name` de `feature_list.json`. Ejemplos:
`01_system_config`, `18_bug_workflow`.

> Nota: antes se usaba solo `<name>`. La convencion `{NN}_{name}` mantiene
> orden natural por id y facilita la navegacion.

## El campo `type` en `feature_list.json`

Cada entrada en `feature_list.json` DEBE tener un campo `"type"`:

- **`"feature"`** — funcionalidad nueva. Usa `acceptance` (criterios de
  verificación) y opcionalmente `"sdd": true` (spec requerido).
- **`"bug"`** — error documentado. Requiere `reproduction` (pasos para
  reproducir) y `affected_feature_ids` (IDs de features que impacta).

Los bugs NO pasan por SDD. Su flujo es independiente:
`untriaged -> triaged -> bug-fixer -> reviewer -> release-manager -> done`.

## Estados de una feature

| Estado         | Significado                                                    |
|----------------|----------------------------------------------------------------|
| `pending`      | Sin spec. El `spec_author` es el primero en actuar.            |
| `spec_ready`   | Spec drafted. Esperando aprobación humana. NO se toca código.  |
| `in_progress`  | Spec aprobado. `implementer` trabajando.                       |
| `done`         | Código verde, `reviewer` aprobó, sesión cerrada.               |
| `blocked`      | Atascado. Razón en `progress/current.md`.                      |

## La puerta de aprobación humana

El flujo automático se detiene **una vez**: cuando el `spec_author` termina
sus tres archivos, marca la feature como `spec_ready` y para. El humano
lee `specs/<feature>/` y dice "aprobado" (o pide cambios).

Solo entonces el `leader` transiciona `spec_ready → in_progress` y lanza
el `implementer`.

```
intake-agent → [spec_author] → spec_ready → ⏸ HUMANO → in_progress →
  [implementer → reviewer → release-manager (register)] → done
```

## requirements.md — EARS estricto

Las requirements se redactan en **EARS** (Easy Approach to Requirements
Syntax). Cada requirement es un párrafo numerado con uno de estos cinco
patrones:

| Patrón         | Plantilla                                                   |
|----------------|-------------------------------------------------------------|
| **Ubicuo**     | `El sistema DEBE <acción>.`                                 |
| **Evento**     | `CUANDO <disparador>, el sistema DEBE <acción>.`            |
| **Estado**     | `MIENTRAS <estado>, el sistema DEBE <acción>.`              |
| **Opcional**   | `DONDE <feature opcional>, el sistema DEBE <acción>.`       |
| **No deseado** | `SI <evento no deseado> ENTONCES el sistema DEBE <acción>.` |

Reglas duras:

- Cada requirement tiene un id estable: `R1`, `R2`, ...
- Cada requirement DEBE ser verificable por al menos un test concreto.
- No mezcles varios `DEBE` en un mismo requirement. Si hay más de uno, parte.
- Si una feature tiene **mas de 20 requirements (R1-R20+), dividir** en sub-features.
  Ejemplo: una feature de 41 requirements se divide en 14a (R1-R12), 14b (R13-R29), 14c (R30-R41).
- No uses verbos blandos ("podría", "puede", "soporta"). Solo `DEBE` / `NO DEBE`.

Ejemplo:

```markdown
## R1
CUANDO el usuario ejecuta `python -m src.cli recent`, el sistema DEBE
imprimir hasta 5 notas ordenadas por `created_at` descendente.

## R2
SI el flag `--limit` recibe un valor <= 0 ENTONCES el sistema DEBE
imprimir un mensaje de error en stderr y salir con código != 0.
```

## design.md — decisiones técnicas

Captura **antes** de tocar código:

- Qué archivos se crean / modifican.
- Qué firmas nuevas aparecen (funciones, clases, comandos).
- Que excepciones se reutilizan o se anaden.
- Que alternativa se descarto y por que (minimo una).
- `github_labels`: etiquetas adicionales para el issue de GitHub (opcional).

### Seccion obligatoria: Contrato API

Si la feature consume endpoints, `design.md` DEBE declarar la respuesta esperada:

### API: GET /api/haciendas
Respuesta: { items: Hacienda[], total: number, page: number, page_size: number, total_pages: number }

Esto evita que el implementer asuma array directo cuando el backend devuelve `{items: [...]}`.

NO es ingenieria desde primeros principios — apóyate en
`docs/architecture.md` y `docs/conventions.md`. El `design.md` documenta los
puntos donde tu feature roza la frontera de esas reglas.

### Sección obligatoria: Persistencia

Si la feature toca la base de datos (nueva tabla, nueva columna, nuevo índice,
nueva migración), `design.md` DEBE incluir una sección `## Persistencia` que
declare exactamente:

- **Tablas nuevas:** nombre, columnas (con tipo y constraints), índices, FK.
- **Tablas modificadas:** columnas añadidas/eliminadas/alteradas, nuevos índices.
- **Migraciones:** archivo(s) a crear y su orden.
- **Datos semilla:** si la feature requiere datos iniciales, declararlos aquí.

Formato de ejemplo:

```markdown
## Persistencia

### Tabla nueva: `task_lists`
| Columna      | Tipo             | Nullable | Default        | Notas               |
|------------- |----------------- |--------- |--------------- |-------------------- |
| id           | BIGINT UNSIGNED  | NO       | AUTO_INCREMENT | PK                  |
| user_id      | BIGINT UNSIGNED  | NO       |                | FK → users.id       |
| name         | VARCHAR(255)     | NO       |                |                     |
| created_at   | TIMESTAMP        | YES      | NULL           |                     |
| updated_at   | TIMESTAMP        | YES      | NULL           |                     |

Índices: `(user_id, created_at DESC)`

### Migraciones
1. `database/migrations/2026_01_01_000000_create_task_lists_table.php`

### Tabla modificada: `tasks`
Nueva columna: `task_list_id` BIGINT UNSIGNED NULL FK → task_lists.id

### Migraciones
2. `database/migrations/2026_01_01_000001_add_task_list_id_to_tasks.php`
```

El `implementer` escribe la migración **copiando exactamente lo declarado en el spec**.
El `reviewer` verifica que `docs/database.md` refleja los cambios tras ejecutar
la migración y el dump. Si hay discrepancias, rechaza.

## tasks.md — checklist ejecutable

Pasos discretos en orden, cada uno con checkbox. Cada task referencia al
menos un `R<n>` que cubre.

Ejemplo:

```markdown
- [ ] T1 — Añadir `cmd_recent` en `src/cli.py`. Cubre: R1, R3.
- [ ] T2 — Registrar subparser `recent` con flag `--limit`. Cubre: R1, R2.
- [ ] T3 — Añadir `test_recent_default_limit` en `tests/test_cli.py`. Cubre: R1.
- [ ] T4 — Añadir `test_recent_invalid_limit` en `tests/test_cli.py`. Cubre: R2.
```

El `implementer` marca `[x]` cada task al completarla.

Reglas adicionales:
- Cada T<n> que use funciones de framework (Svelte: `onMount`, React: `useEffect`, etc.) DEBE listar el import requerido como subtask.
- Si la task consume un endpoint API, DEBE incluir el contrato de respuesta esperado (ver Contrato API en design.md). El `reviewer`
rechaza si queda alguna `[ ]` sin justificación documentada.

## Trazabilidad (regla dura)

- Cada test en `tests/` debe poder mapearse a un `R<n>` de su spec.
- Cada `R<n>` debe tener al menos un test concreto.
- El `reviewer` comprueba esta correspondencia explícitamente y rechaza
  si falta.

El `implementer` documenta el mapa en `progress/impl_<name>.md`:

```markdown
## Trazabilidad
- R1 → `test_recent_default_limit`
- R2 → `test_recent_invalid_limit`
- R3 → `test_recent_custom_limit`
```

## Cuándo NO aplica SDD

Las features con `"sdd": false` o sin el campo `sdd` (las legacy 1–6) NO
tienen spec. SDD solo se aplica hacia adelante.
