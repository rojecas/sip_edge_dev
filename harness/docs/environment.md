# Environment — sip_edge

> El agente DEBE leer este archivo **antes de ejecutar cualquier comando bash**.
> Describe DONDE y COMO se ejecutan los comandos, y que servicios estan disponibles.
> init.ps1 auto-detecta el contexto (Docker vs nativo) y avisa si hay discrepancias.

## Execution mode

**Mode:** docker
**Compose file:** compose.yml
**Service:** backend

## Shell

Prefix ALL commands with: docker compose exec backend
Ejemplo: docker compose exec backend python -m unittest discover -s tests -v

## Runtime

- Python 3.11 inside container
- Container image: python:3.11-slim (build via Dockerfile)

## Services

| Service   | Host access      | Container access |
|-----------|-----------------|------------------|
| MariaDB   | 127.0.0.1:3306  | mariadb:3306     |
| Backend   | 127.0.0.1:8000  | (N/A)            |

## Init / Lifecycle

```bash
# Start all services
docker compose up -d

# Verify environment
./init.ps1

# Install dependencies (inside container)
docker compose exec backend pip install -r requirements.txt

# Run tests
docker compose exec backend python -m unittest discover -s tests -v

# Access backend API
# http://127.0.0.1:8000
```
