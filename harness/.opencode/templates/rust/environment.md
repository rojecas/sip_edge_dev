# Environment — {{PROJECT_NAME}}

> El agente DEBE leer este archivo **antes de ejecutar cualquier comando bash**.
> Describe DONDE y COMO se ejecutan los comandos, y que servicios estan disponibles.
> init.ps1 auto-detecta el contexto (Docker vs nativo) y avisa si hay discrepancias.

## Execution mode

**Mode:** native

No se detecto Docker. Todos los comandos se ejecutan directamente en el host.
Si usas Docker, cambia el modo a `docker` y completa la seccion correspondiente.

## Shell

Todos los comandos usan el shell del sistema. Sin prefijo de contenedor.

## Runtime

- Rust toolchain (rustc, cargo) en PATH
- Sin aislamiento por contenedor

## Services

Ninguno detectado. Si tu proyecto usa servicios (BD, cache), agregalos aqui.

## Init / Lifecycle

```bash
# Verificar entorno
./init.ps1

# Compilar
cargo build

# Ejecutar tests
cargo test
```

---

## Template Docker (si usas contenedores)

Cambia `mode` a `docker`, rellena y descomenta:

```markdown
## Execution mode
**Mode:** docker
**Compose file:** compose.yml
**Service:** app

## Shell
Prefix ALL commands with: docker compose exec app
Ejemplo: docker compose exec app cargo test

## Init / Lifecycle
docker compose up -d              # start services
docker compose exec app cargo test  # run tests
```
