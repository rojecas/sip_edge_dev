# Convenciones de codigo

> Homogeneidad extrema. La IA predice mejor cuando el repositorio se parece
> a si mismo en todas partes.

## Estilo Go

- **Version:** Go 1.22+.
- **Formato:** `gofmt` (es el canon, no se discute).
- **Linter:** `golangci-lint run` con config default.
- **Manejo de errores:** `if err != nil { return ... }` sin excepciones.

## Nombres

| Tipo                   | Convencion       | Ejemplo               |
|------------------------|------------------|-----------------------|
| Paquetes               | `lowercase`      | `storage`, `domain`   |
| Tipos exportados       | `PascalCase`     | `Note`, `NoteStore`   |
| Funciones exportadas   | `PascalCase`     | `LoadNotes`           |
| Funciones no exportadas| `camelCase`      | `loadFromFile`        |
| Variables              | `camelCase`      | `notePath`            |
| Constantes             | `PascalCase`     | `DefaultLimit`        |

## Estructura de archivo

Cada archivo en `internal/`:

```go
// Package storage provides atomic JSON persistence for notes.
package storage
```

- Package doc en el archivo principal del paquete.
- `gofmt` es ley. No hay debates de estilo.
- `interface` se define donde se consume (aceptacion), no donde se implementa.
- `context.Context` como primer parametro en funciones que hacen I/O.

## Tests

- `*_test.go` en el mismo paquete (white-box) o `_test` (black-box).
- `t.Run("name", func(t *testing.T) { ... })` para sub-tests.
- `t.Parallel()` siempre que sea posible.
