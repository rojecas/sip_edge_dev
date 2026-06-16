# Verificacion Ã¢â‚¬â€ Como demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable, no con afirmaciones.

## Niveles de verificacion

### Nivel 1 Ã¢â‚¬â€ Tests unitarios (obligatorio)

Toda funcion publica en `src/` tiene al menos un test en `tests/` que:

1. Cubre el camino feliz.
2. Cubre todos los caminos de error que la funcion puede producir (excepciones, valores limite, entradas invalidas). Si una funcion puede fallar de N formas distintas, hay al menos N tests de error.

Comando:
```bash
python -m unittest discover -s tests -v
```

### Nivel 2 Ã¢â‚¬â€ Test de integracion del CLI (obligatorio para features de UI)

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

### Nivel 3 Ã¢â‚¬â€ Verificacion del harness

Antes de declarar `done`:
```bash
./init.ps1
```
Debe terminar con exit code 0 y todos los bloques [OK].

### Nivel 4 — Verificación en EdgeBox (hardware real)

> Obligatorio para features que toquen hardware (puertos seriales, modem GSM, RTC, WDT, etc.)

Las features que involucran hardware DEBEN verificarse en la EdgeBox-RPI-200
**después del despliegue**. Este nivel valida que el código funciona con el
hardware real en el entorno de producción.

Comandos:

```bash
# 1. Actualizar código y reiniciar servicio
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "cd /home/sipedge/sip_edge && git pull && sudo systemctl restart sip-edge"

# 2. Ejecutar tests de hardware (si existen)
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "cd /home/sipedge/sip_edge && source venv/bin/activate && python -m unittest discover -s tests_hardware -v"

# 3. Smoke test rápido: health check de la API
curl http://192.168.1.42:8000/health
```

SI el comando `git pull` no trae cambios, DEBE ejecutarse al menos el smoke
test de health check y los tests_hardware para confirmar que el servicio
funciona correctamente tras el reinicio.

SI este nivel falla, la feature se considera `blocked` hasta que se resuelva
la incompatibilidad con el hardware real.

Combinación con Nivel 3: `./init.ps1` se ejecuta siempre en local (Docker).
Nivel 4 se ejecuta después del despliegue en EdgeBox. Ambos DEBEN pasar
antes de declarar `done`.
