# Arquitectura — Que significa "hacer un buen trabajo"

> Este documento define el estandar de calidad. Los agentes revisores
> evaluan codigo contra este archivo. Si no esta aqui, no es un requisito.

## Principios

1. **Capas claras.** El proyecto sigue el layout estandar de Go:
   - `cmd/<name>/` — punto de entrada del CLI (cobra).
   - `internal/domain/` — tipos y logica de negocio.
   - `internal/storage/` — persistencia (archivos, SQLite, etc.).
   No introducir capas sin una razon documentada en `feature_list.json`.

2. **Dependencias minimas.** cobra para CLI, stdlib para todo lo demas.
   Cualquier modulo externo se discute primero.

3. **Errores explicitos.** `(T, error)` siempre. Nunca `panic()` en librerias.
   Errores envueltos con `fmt.Errorf("...: %w", err)`.

4. **Interfaces pequenas.** Define la interfaz donde se consume, no donde
   se implementa. 1-3 metodos por interfaz.

5. **Tests en paralelo.** `t.Parallel()` en tests que no comparten estado.

## Flujo de datos

```
CLI (cobra) → dominio (structs/interfaces) → persistencia
```

## Tests

- `go test ./...` para todo.
- Tests unitarios en `*_test.go` junto al fuente.
- Sin mocks de filesystem. Usar `t.TempDir()` o `os.MkdirTemp()`.
