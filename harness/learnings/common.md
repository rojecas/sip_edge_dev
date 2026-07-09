# Lecciones Comunes — Para TODOS los agentes
> Leer AL INICIAR cualquier tarea que involucre escritura de archivos.

## 1. Herramientas disponibles
NO existe tool `write` ni `edit`. Las unicas herramientas de escritura son:
- `bash` con PowerShell cmdlets: `Set-Content`, `Add-Content`, `Out-File`
- `bash` con Python: `open()`, `json.dump()`

Para leer: `read`, `glob`, `grep`, `bash`.
Para lanzar subagentes: `task`.

## 2. Modificar archivos JSON
**NUNCA** uses regex (`-replace`) para modificar JSON. El formato es fragile y el regex puede:
- Afectar multiples entradas simultaneamente
- Comerse contenido entre dos coincidencias
- Romper la indentacion o estructura

**Siempre usa Python:**
```powershell
python -c "
import json
with open('archivo.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
# modificar data...
with open('archivo.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
"
```

## 3. Reemplazos de texto con -replace
Si DEBES usar `-replace`:
1. Primero verifica cuantas ocurrencias hay: `Select-String -Path "archivo" -Pattern "texto"`
2. Asegurate de que el patron sea UNICO e inequivoco
3. Opcional: haz backup primero (`Copy-Item -Path "archivo" -Destination "archivo.bak"`)

## 4. Line endings al escribir archivos (Windows/Linux)
El repositorio usa LF en git, pero Windows convierte a CRLF en checkout.
Al escribir archivos desde Python:
- Usar newline='' para preservar los line endings existentes.
- NUNCA concatenar strings con \n manuales sin verificar cuantos \n
  ya existen alrededor del punto de insercion (error comun: duplicar blanks).
- Si el archivo queda con multiples lineas en blanco, limpiar con:
  re.sub(b'\n{4,}', b'\n\n\n', content) para LF.
- Antes de escribir, verifica con git show HEAD:archivo el formato original.

## 5. Subagentes y la carpeta learnings
Los subagentes (implementer, reviewer, spec-author, bug-fixer) NO leen
AGENTS.md al ser lanzados. El agente lider DEBE incluir en cada prompt:
  "Lee harness/learnings/common.md y harness/learnings/<tu_rol>.md
   antes de empezar."
