# Convenciones de codigo

> Homogeneidad extrema. La IA predice mejor cuando el repositorio se parece
> a si mismo en todas partes.

## Estilo PHP

- **Version:** PHP 8.2+.
- **Formato:** PSR-12. Pint como formatter (`./vendor/bin/pint`).
- **Strict types:** `declare(strict_types=1)` en la primera linea
  despues del `<?php`.
- **Strings:** comillas simples para strings fijos; comillas dobles solo
  cuando hay interpolacion o `\n`.
- **Arrays:** sintaxis corta `[]`.

## Nombres

| Tipo                   | Convencion       | Ejemplo                    |
|------------------------|------------------|----------------------------|
| Modelos                | `PascalCase`     | `Note`, `TaskList`         |
| Controladores          | `PascalCase`     | `NoteController`           |
| Servicios              | `PascalCase`     | `NoteService`              |
| Metodos                | `camelCase`      | `findById`, `createNote`   |
| Tablas                 | `snake_case`     | `notes`, `task_lists`      |
| Migraciones            | `snake_case`     | `create_notes_table`       |
| Tests                  | `camelCase`      | `it_creates_a_note`        |
| Rutas                  | `kebab-case`     | `/api/note-lists`          |

## Estructura de archivo

Cada archivo PHP:
```php
<?php

declare(strict_types=1);

namespace App\Models;

final class Note extends Model
{
    // ...
}
```

- `final` por defecto en clases concretas.
- `readonly` en propiedades que no cambian tras construccion.
- Sin comentarios `// TODO` sin contexto.

## Tests (Pest)

- Archivos `tests/Feature/*Test.php` para tests de integracion.
- Archivos `tests/Unit/*Test.php` para tests unitarios.
- Cada test usa `it()` o `test()` de Pest:

```php
it('creates a note and returns its id', function () {
    $response = $this->post('/notes', ['title' => 'Test']);
    $response->assertCreated();
});
```
