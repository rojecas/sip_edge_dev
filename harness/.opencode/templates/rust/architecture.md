# Arquitectura — Que significa "hacer un buen trabajo"

> Este documento define el estandar de calidad. Los agentes revisores
> evaluan codigo contra este archivo. Si no esta aqui, no es un requisito.

## Principios

1. **Capas claras.** El proyecto tiene modulos bien definidos:
   - `cli/` — parseo de argumentos (clap).
   - `domain/` — structs, traits y logica de negocio.
   - `storage/` — persistencia (archivos, SQLite, etc.).
   No introducir capas sin una razon documentada en `feature_list.json`.

2. **Dependencias minimas.** clap para CLI, serde para serializacion,
   thiserror para errores. Cualquier crate nuevo se discute primero.

3. **Errores explicitos.** `Result<T, E>` siempre. Nada de `unwrap()` en
   codigo de produccion. Usar `thiserror` para errores de dominio.

4. **Ownership claro.** Preferir borrows sobre clones. Si se clona, comentar
   por que.

5. **Tests inline.** Tests unitarios en el mismo archivo con `#[cfg(test)]`.

## Flujo de datos

```
CLI (clap) → dominio (structs/traits) → persistencia
```

## Tests

- `cargo test` para todo.
- Tests de integracion en `tests/`.
- Sin mocks de filesystem. Usar `tempfile` crate o `std::env::temp_dir()`.
