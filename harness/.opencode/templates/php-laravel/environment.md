# Environment — {{PROJECT_NAME}}

> El agente DEBE leer este archivo **antes de ejecutar cualquier comando bash**.
> Describe DONDE y COMO se ejecutan los comandos, y que servicios estan disponibles.
> init.ps1 auto-detecta el contexto (Docker vs nativo) y avisa si hay discrepancias.

## Execution mode

**Mode:** docker (recomendado para Laravel)
**Compose file:** compose.yml
**Service:** app

> Si no usas Docker, cambia a `native` y elimina los prefijos `docker compose exec app`.

## Shell

Prefix ALL commands with: `docker compose exec app`
Ejemplo: `docker compose exec app php artisan test`

## Runtime

- PHP 8.2+ (dentro del contenedor)
- Composer (dentro del contenedor)
- Extensiones comunes: pdo_mysql, redis, bcmath

## Services

| Service | Host access  | Container access |
|---------|-------------|------------------|
| MySQL   | 127.0.0.1:33060 | mysql:3306    |
| Redis   | 127.0.0.1:63790 | redis:6379    |

> Edita esta tabla segun tu compose.yml.

## Init / Lifecycle

```bash
# Arrancar servicios (primera vez o despues de apagar)
docker compose up -d

# Instalar dependencias PHP (primera vez)
docker compose exec app composer install

# Ejecutar migraciones
docker compose exec app php artisan migrate

# Ejecutar tests
docker compose exec app php artisan test

# Verificar formato
docker compose exec app ./vendor/bin/pint --test
```
