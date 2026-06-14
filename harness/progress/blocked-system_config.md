# Bloqueo — system_config

- **Feature:** system_config (id: 1)
- **Estado:** `blocked`
- **Fecha:** 2026-06-13

## Contexto

Feature aprobada (`spec_ready`), transicionada a `in_progress`. Al intentar sincronizar con GitHub, `gh` CLI requiere autenticacion.

## Sintoma

```
To get started with GitHub CLI, please run:  gh auth login
Alternatively, populate the GH_TOKEN environment variable with a GitHub API authentication token.
```

## Intentos

1. `gh` CLI no instalado en contenedor → resuelto (anadido a `Dockerfile`)
2. `gh` CLI instalado (v2.94.0) pero no autenticado → requiere token

## Dependencias

- Autenticar `gh` con `gh auth login` (interactivo) o
- Establecer `GH_TOKEN` en el entorno del contenedor (compose.yml, variable de entorno)
- O deshabilitar `github.json` (`"enabled": false`)
