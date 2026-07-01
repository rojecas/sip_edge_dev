# Convenciones de codigo

> Homogeneidad extrema. La IA predice mejor cuando el repositorio se parece
> a si mismo en todas partes.

## Estilo Python

- **Version:** Python 3.9+ (sintaxis `list[str]` permitida).
- **Formato:** PEP 8. Lineas maximo 100 caracteres.
- **Imports:** stdlib primero, luego locales. Una linea por modulo.
- **Strings:** comillas dobles `"..."` siempre. Comillas simples solo
  para escapar comillas dobles dentro.
- **f-strings** para interpolacion. Nada de `.format()` ni `%`.

## Nombres

| Tipo                   | Convencion       | Ejemplo               |
|------------------------|------------------|-----------------------|
| Modulos                | `snake_case`     | `notes.py`            |
| Clases                 | `PascalCase`     | `Note`                |
| Funciones / variables  | `snake_case`     | `load_notes`          |
| Constantes             | `UPPER_SNAKE`    | `DEFAULT_NOTES_PATH`  |
| Privadas               | prefijo `_`      | `_atomic_write`       |

## Estructura de archivo

Cada archivo en `src/` empieza con:

```python
\"\"\"Una linea describiendo el proposito del modulo.\"\"\"
```

- Docstring de modulo obligatorio.
- Funciones publicas con docstring si tienen mas de 5 lineas.
- Sin comentarios `# TODO` sin contexto. Si hay TODO, incluye issue o feature id.

## Tests

- Un archivo `test_<modulo>.py` por cada modulo en `src/`.
- Clase `Test<Modulo>` con metodos `test_<funcion>_<escenario>`.
- Cada test cubre exactamente un escenario (feliz o error).


## YAML y Configuracion

- **Archivos YAML** (`compose.yml`, `config.yaml`): usar siempre UTF-8 sin BOM.
- **PowerShell y `${...}`** (ERROR COMUN): En PowerShell, las variables `${VAR:-default}` de Docker
  Compose son interpretadas como variables de PowerShell. Al escribir archivos YAML en PowerShell:

  ```powershell
  # MAL — PowerShell expande `${DB_USER:-sip_user}` a string vacio:
  @" ... ${DB_USER:-sip_user} ... "@

  # BIEN — usar here-string con comillas simples (no expande variables):
  @' ... ${DB_USER:-sip_user} ... '@

  # BIEN — escapar $ con backtick:
  @" ... `${DB_USER:-sip_user} ... "@

  # BIEN — usar [System.IO.File]::WriteAllText con here-string simple:
  [System.IO.File]::WriteAllText("ruta", @' ... ${DB_USER:-sip_user} ... '@)
  ```

  Verificar siempre que el YAML resultante preserve las variables `${...}` intactas.
  Un `docker compose config` sin errores confirma que el YAML es valido.
