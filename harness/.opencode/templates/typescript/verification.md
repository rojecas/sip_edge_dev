# Verificacion — Como demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable, no con afirmaciones.

## Niveles de verificacion

### Nivel 1 — Tests unitarios (obligatorio)

Toda funcion exportada en `src/` tiene al menos un test que:

1. Cubre el camino feliz.
2. Cubre todos los caminos de error que la funcion puede producir (excepciones, valores limite, entradas invalidas). Si una funcion puede fallar de N formas distintas, hay al menos N tests de error.

Comando:
```bash
npm test
```

### Nivel 2 — Test de integracion del CLI (obligatorio para features de UI)

Las features que anaden comandos al CLI se verifican ejecutando el CLI real
con datos temporales:

```typescript
import { execSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";

const dir = mkdtempSync(tmpdir() + "/");
execSync(`npx tsx src/cli.ts add "hola" --body "mundo"`, {
  env: { ...process.env, DATA_FILE: dir + "/data.json" }
});
```

### Nivel 3 — Linter y formato

```bash
npm run lint       # ESLint
npm run format     # Prettier --check
```

### Nivel 4 — Verificacion del harness

Antes de declarar `done`:
```bash
./init.ps1
```
Debe terminar con exit code 0 y todos los bloques [OK].
