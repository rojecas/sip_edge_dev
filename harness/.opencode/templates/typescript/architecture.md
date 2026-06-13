# Arquitectura — Que significa "hacer un buen trabajo"

> Este documento define el estandar de calidad. Los agentes revisores
> evaluan codigo contra este archivo. Si no esta aqui, no es un requisito.

## Principios

1. **Capas claras.** El proyecto tiene capas bien definidas:
   - `cli/` — comandos y parseo de argumentos (commander).
   - `domain/` — tipos, interfaces y logica de negocio pura.
   - `storage/` — persistencia (archivos, DB, lo que sea).
   No introducir capas sin una razon documentada en `feature_list.json`.

2. **Dependencias minimas.** Commander para CLI, vitest para testing.
   Cualquier dependencia nueva se discute primero (estado `blocked`).

3. **Errores explicitos.** Las funciones que pueden fallar lanzan errores
   tipados (`throw new DomainError(...)`), no devuelven `null`.

4. **Tipos estrictos.** `strict: true` en tsconfig. Nada de `any` sin
   justificacion explicita.

5. **Atomicidad.** Las escrituras en disco usan write-temp + rename
   (si aplica). Nunca dejar archivos a medio escribir.

## Flujo de datos

```
CLI (commander) → dominio (types/interfaces) → persistencia
```

- La capa CLI solo conoce el dominio.
- El dominio no conoce ni CLI ni persistencia.
- La persistencia solo conoce las interfaces del dominio.

## Tests

- `vitest` con TypeScript nativo (tsx).
- Sin mocks de sistema de archivos. Archivos reales en `os.tmpdir()`.
