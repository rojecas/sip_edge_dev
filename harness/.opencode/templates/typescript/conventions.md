# Convenciones de codigo

> Homogeneidad extrema. La IA predice mejor cuando el repositorio se parece
> a si mismo en todas partes.

## Estilo TypeScript

- **Version:** Node.js 20 LTS, TypeScript 5.x.
- **Formato:** Prettier con config default (2 spaces, single quotes, trailing commas).
- **Linter:** ESLint con `@typescript-eslint` recommended.
- **Strings:** backticks solo cuando hay interpolacion; comillas simples para strings fijos.

## Nombres

| Tipo                   | Convencion       | Ejemplo               |
|------------------------|------------------|-----------------------|
| Archivos               | `kebab-case`     | `note-storage.ts`     |
| Clases / Interfaces    | `PascalCase`     | `Note`, `INoteStore`  |
| Funciones / variables  | `camelCase`      | `loadNotes`           |
| Constantes             | `UPPER_SNAKE`    | `DEFAULT_NOTES_PATH`  |
| Tipos                  | `PascalCase`     | `NoteId`, `NoteInput` |

## Estructura de archivo

Cada archivo en `src/`:

```typescript
/** Una linea describiendo el proposito del modulo. */
```

- JSDoc en funciones exportadas.
- `export` explicito, no `export default`.
- Sin `any`. Si es inevitable, comentar por que.

## Tests

- Un archivo `*.test.ts` por modulo, junto al fuente o en `tests/`.
- `describe` + `it` anidados: `describe('NoteStore', () => { it('loads empty on missing file', ...) })`.
- Cada test cubre exactamente un escenario.
