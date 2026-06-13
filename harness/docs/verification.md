# Verificacion â€” Como demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable, no con afirmaciones.

## Niveles de verificacion

### Nivel 1 â€” Tests unitarios (obligatorio)

Toda funcion publica en `src/` tiene al menos un test en `tests/` que:

1. Cubre el camino feliz.
2. Cubre todos los caminos de error que la funcion puede producir (excepciones, valores limite, entradas invalidas). Si una funcion puede fallar de N formas distintas, hay al menos N tests de error.

Comando:
```bash
python -m unittest discover -s tests -v
```

### Nivel 2 â€” Test de integracion del CLI (obligatorio para features de UI)

Las features que anaden comandos al CLI se verifican ejecutando el CLI real
contra un archivo temporal:

```python
import subprocess, tempfile, os
with tempfile.TemporaryDirectory() as d:
    env = {**os.environ, "DATA_FILE": os.path.join(d, "data.json")}
    out = subprocess.check_output(
        ["python", "-m", "src.cli", "add", "hola", "--body", "mundo"],
        env=env, text=True
    )
    assert "1" in out
```

### Nivel 3 â€” Verificacion del harness

Antes de declarar `done`:
```bash
./init.ps1
```
Debe terminar con exit code 0 y todos los bloques [OK].
