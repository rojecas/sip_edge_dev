# Arquitectura — Que significa "hacer un buen trabajo"

> Este documento define el estandar de calidad. Los agentes revisores
> evaluan codigo contra este archivo. Si no esta aqui, no es un requisito.

## Principios

1. **Capas claras.** El proyecto tiene capas bien definidas y acotadas.
   No introducir capas adicionales (servicios, repositorios, ORMs) hasta que
   haya una razon concreta documentada en `feature_list.json`.

2. **Sin dependencias externas.** Solo stdlib de Python. Si una feature
   requiere una dependencia, primero se discute (estado `blocked`).

3. **Errores explicitos.** Las funciones que pueden fallar lanzan excepciones
   nombradas, no devuelven `None`.

4. **Inmutabilidad por defecto.** Dataclasses con `frozen=True`.
   Modificar = crear una nueva instancia.

5. **Atomicidad en disco.** Toda escritura se hace primero en un archivo
   temporal y luego `os.replace()`. Nunca dejar el archivo a medio escribir.

## Flujo de datos

```
CLI (argparse) → modelo de dominio → persistencia (JSON)
```

- La capa CLI solo conoce el modelo de dominio.
- El modelo de dominio no conoce ni CLI ni persistencia.
- La persistencia solo conoce el modelo de dominio.

## Tests

- `unittest` con `tempfile.TemporaryDirectory()` para tests de archivos.
- Sin mocks de sistema de archivos. Siempre archivos reales en temp dirs.
