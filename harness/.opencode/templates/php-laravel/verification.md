# Verificacion — Como demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable, no con afirmaciones.

## Niveles de verificacion

### Nivel 1 — Tests (obligatorio)

Toda ruta, Service o Model con logica nueva tiene al menos un test que:

1. Cubre el camino feliz.
2. Cubre todos los caminos de error que la operacion puede producir (validacion fallida, 404, 422, 403, 500, etc.). Si una ruta o Service puede fallar de N formas distintas, hay al menos N tests de error.

Comando:
```bash
composer test
```
(o `php artisan test --parallel` si esta configurado)

### Nivel 2 — Formato y analisis estatico

```bash
./vendor/bin/pint --test     # PSR-12
composer lint                 # Laravel Pint + PHPStan si esta configurado
```

### Nivel 3 — Schema dump actualizado (obligatorio)

Si la feature toca la base de datos, despues de ejecutar migraciones:

```bash
python database/schema_dump.py       # regenera docs/database.md desde la BD real
```

El script lee la configuracion de `database/.schema_dump.json` (soporta SQLite y MySQL).
`init.ps1` verifica que `docs/database.md` no este mas viejo que la migracion mas reciente.

### Nivel 4 — Verificacion del harness

Antes de declarar `done`:
```bash
./init.ps1
```
Debe terminar con exit code 0 y todos los bloques [OK].
