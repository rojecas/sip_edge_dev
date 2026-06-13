# Convenciones de codigo

> Homogeneidad extrema. La IA predice mejor cuando el repositorio se parece
> a si mismo en todas partes.

## Estilo Rust

- **Edition:** 2021+.
- **Formato:** `cargo fmt` sin personalizacion.
- **Linter:** `cargo clippy` con reglas default. `#[allow(clippy::...)]`
  solo con justificacion.
- **Strings:** `&str` en parametros, `String` en structs que poseen datos.

## Nombres

| Tipo                   | Convencion       | Ejemplo               |
|------------------------|------------------|-----------------------|
| Modulos                | `snake_case`     | `note_storage`        |
| Structs / Enums        | `PascalCase`     | `Note`, `NoteError`   |
| Funciones / metodos    | `snake_case`     | `load_notes`          |
| Constantes             | `UPPER_SNAKE`    | `DEFAULT_NOTES_PATH`  |
| Traits                 | `PascalCase`     | `NoteStore`           |

## Estructura de archivo

Cada archivo en `src/`:

```rust
//! Una linea describiendo el proposito del modulo.
```

- Doc comments `///` en funciones publicas.
- `pub` explicito. Nada publico por accidente.
- `#[derive(Debug)]` en todo struct publico.

## Tests

- Tests unitarios en modulo `#[cfg(test)] mod tests { ... }` al final del archivo.
- Tests de integracion en `tests/`.
- Cada test: `#[test] fn test_<funcion>_<escenario>() { ... }`.
