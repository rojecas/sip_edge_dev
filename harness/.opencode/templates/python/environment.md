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

- Python 3.9+ (disponible como `python`)
- Sin aislamiento por contenedor

## Services

Ninguno detectado. Si tu proyecto usa servicios (BD, cache, colas), agregalos aqui.

Ejemplo con Docker:
| Service | Host access  | Container access |
|---------|-------------|------------------|
| PostgreSQL | 127.0.0.1:54320 | db:5432 |

## Init / Lifecycle

```bash
# Verificar entorno
./init.ps1

# Instalar dependencias (primera vez)
pip install -r requirements.txt

# Ejecutar tests
python -m unittest discover -s tests -v
```

---

## Template Docker (si usas contenedores)

Cambia `mode` a `docker`, rellena el nombre del servicio y descomenta:

```markdown
## Execution mode
**Mode:** docker
**Compose file:** compose.yml
**Service:** app

## Shell
Prefix ALL commands with: docker compose exec app
Ejemplo: docker compose exec app python -m unittest discover -s tests -v

## Runtime
- Python 3.9+ inside container
- Container image: python:3.12-slim

## Services
| Service | Host access | Container access |
|---------|------------|------------------|
| PostgreSQL | 127.0.0.1:54320 | db:5432 |

## Init / Lifecycle
docker compose up -d                                # start services
docker compose exec app pip install -r requirements.txt  # install deps
docker compose exec app python -m unittest discover -s tests -v  # run tests
```
