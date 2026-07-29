# GitHub Integration — Sincronizacion de issues

> Documenta la integracion entre el flujo SDD local y GitHub Issues.

## Prerequisitos

1. **GitHub CLI (`gh`)** instalado y en PATH.
   - Instalar: `winget install GitHub.cli` (Windows) o `brew install gh` (macOS)
   - Verificar: `gh --version`
2. **Autenticacion:** `gh auth login`
3. **Repositorio:** El repo debe existir en GitHub y el usuario autenticado debe
   tener permisos para crear/cerrar issues.

## Configuracion

Editar `harness/github.json`:

```json
{
  "repo": "owner/repo",
  "enabled": true,
  "labels": ["enhancement"]
}
```

| Campo | Descripcion |
|-------|-------------|
| `repo` | Repositorio GitHub en formato `owner/repo` (ej. `rojecas/IIntranet`) |
| `enabled` | `true` para activar la sincronizacion automatica. `false` para desactivar. |
| `labels` | Etiquetas por defecto para los issues creados |

Si `enabled` es `false` o el archivo no existe, el flujo SDD funciona normalmente
sin GitHub.

## Flujo de sincronizacion

```
feature_list.json                          GitHub Issues
─────────────────                          ─────────────
status: pending          → (nada)
status: spec_ready       → (nada, espera aprobacion humana)
status: in_progress      → gh issue create  (leader dispara)
status: blocked          → gh issue comment (leader/implementer)
status: done             → gh issue close   (implementer dispara, con comentario)
```

### Creacion del issue

Cuando el leader transiciona `spec_ready → in_progress`, ejecuta:

```bash
python harness/scripts/github_sync.py create --feature-id 7
```

Esto:
1. Lee `harness/feature_list.json` para obtener titulo, descripcion, acceptance criteria
2. Ejecuta `gh issue create --repo owner/repo --title "[7] Titulo" --body "..." --label enhancement`
3. Guarda la URL del issue en `feature_list.json` → `"github_issue": "https://github.com/..."`
4. Es idempotente: si ya existe `github_issue`, no crea duplicado

### Cierre del issue

Cuando el implementer marca `done`, ejecuta:

```bash
python harness/scripts/github_sync.py close --feature-id 7 --closure-path harness/progress/closure-<name>.md
```

Esto:
1. Anade un comentario con resumen extraido del closure (archivos modificados, verificacion)
2. Cierra el issue con razon `completed`

### Comentario en bloqueo

Cuando una feature se bloquea:

```bash
python harness/scripts/github_sync.py comment --feature-id 7 --body "Bloqueado: gh CLI no disponible..."
```

## Verificacion

`./init.ps1` verifica que `gh` este disponible y autenticado si `harness/github.json`
tiene `"enabled": true`. Si falla, muestra instrucciones.

El leader verifica con `python harness/scripts/github_sync.py check` antes de
intentar crear issues.

## Troubleshooting

| Error | Causa | Solucion |
|-------|-------|---------|
| `gh CLI not found` | `gh` no instalado | `winget install GitHub.cli` |
| `gh is not authenticated` | No hay sesion | `gh auth login` |
| `feature has no github_issue` | El issue no se creo | Ejecutar `create --feature-id <n>` manualmente |
| `github.json not found` | Archivo de config no existe | Crear `harness/github.json` |
| `github.json: enabled: false` | Sync desactivada | Cambiar `enabled` a `true` |

## Anti-patrones

- NO crear issues manualmente en GitHub y esperar que el sync funcione al reves.
- NO modificar `github_issue` a mano en `feature_list.json`.
- NO ejecutar `close` sin haber creado el closure primero.
