# Arquitectura — Que significa "hacer un buen trabajo"

> Este documento define el estandar de calidad. Los agentes revisores
> evaluan codigo contra este archivo. Si no esta aqui, no es un requisito.

## Principios

1. **Capas claras.** El proyecto sigue la estructura estandar de Laravel:
   - `app/Models/` — modelos Eloquent (capa de datos).
   - `app/Http/Controllers/` — controladores (entrada HTTP/CLI).
   - `app/Services/` — logica de negocio pura (sin dependencia HTTP).
   - `app/Jobs/` — trabajos asincronos.
   No introducir capas adicionales sin una razon documentada en
   `feature_list.json`.

2. **PHP 8.2+ con strict_types.** `declare(strict_types=1)` en todo archivo.
   Tipos de retorno y parametros siempre declarados.

3. **Eloquent como unica capa de datos.** Sin queries raw dentro de
   controladores. Si un query es complejo, va en un Service o en un
   Query Scope del Model.

4. **Errores explicitos.** Excepciones de dominio (`DomainException`,
   `NotFoundException`) desde Services. Nunca devolver `null` por
   "no encontrado".

5. **Artesania de datos.** Cada Model tiene su Factory para tests.
   Las migraciones son la fuente de verdad del schema.

## Flujo de datos

```
HTTP Request → Controller → Service → Model (Eloquent) → DB
       ↑                                  |
       └──── Response ←──────────────────┘
```

- El Controller solo orquesta: valida, llama al Service, retorna respuesta.
- El Service contiene la logica de negocio. No conoce HTTP.
- El Model solo sabe de su tabla y relaciones.

## Tests

- **Pest** como framework de testing (mas expresivo que PHPUnit).
- Factories para datos de prueba.
- `RefreshDatabase` trait en tests que tocan BD.
- Sin mocks de Eloquent. Base de datos SQLite en memoria (`:memory:`).
