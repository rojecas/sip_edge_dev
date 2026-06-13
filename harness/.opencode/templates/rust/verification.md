# Verificacion — Como demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable, no con afirmaciones.

## Niveles de verificacion

### Nivel 1 — Tests (obligatorio)

Toda funcion publica tiene al menos un test que:

1. Cubre el camino feliz.
2. Cubre todos los caminos de error que la funcion puede producir (variantes de error, valores limite, entradas invalidas). Si una funcion puede fallar de N formas distintas, hay al menos N tests de error.

Comando:
```bash
cargo test
```

### Nivel 2 — Formato y linter

```bash
cargo fmt --check    # Formato
cargo clippy          # Linter
```

### Nivel 3 — Verificacion del harness

Antes de declarar `done`:
```bash
./init.ps1
```
Debe terminar con exit code 0 y todos los bloques [OK].
