# Closure Bug: AdminSuertes.svelte — carga de suertes al seleccionar una hacienda

## Síntoma
Al seleccionar una hacienda en el dropdown de AdminSuertes.svelte, se mostraba el mensaje "No hay suertes registradas para esta hacienda." aunque la hacienda tuviera suertes en la BD. La API `GET /api/suertes?hacienda_id=483` devolvía las 6 suertes correctamente.

## Causa raíz
El endpoint `GET /api/suertes` en el backend (`src/haciendas.py:331`) usa `response_model=List[SuerteResponse]` y retorna un **array JSON plano** (`[{...}, {...}]`). Sin embargo, `loadSuertes()` en el frontend asumía que la respuesta tenía formato `{items: [...]}` (como el endpoint `/api/haciendas` que retorna `PaginatedResponse`). Al ser `result` un array directo, `result.items` era `undefined`, y `undefined || []` producía un array vacío, disparando el mensaje de "No hay suertes".

## Archivos modificados
- `frontend/src/components/AdminSuertes.svelte` (1 línea modificada)

## Fix aplicado
**Cambio:** En `loadSuertes()`, línea 83:
```javascript
// Antes (roto):
suertes = result.items || [];

// Después (corregido):
suertes = Array.isArray(result) ? result : (result.items || []);
```

Este cambio maneja ambos formatos de respuesta:
- Si el backend retorna un array plano (`List[SuerteResponse]`), se usa directamente.
- Si el backend retorna un objeto paginado (`{items: [...], total: ...}`), se extrae `.items`.

## Regression test
No se pudo añadir un test automatizado porque el proyecto frontend no tiene framework de testing configurado (no hay vitest, jest ni playwright en `package.json`). La verificación se realizó mediante `npm run build`.

## Resultado de verificación
- `npm run build` (frontend/): **OK** — 150 modules transformed, build completed in 1.61s, sin errores.
- Build artifacts copiados a `src/static/`: **OK** — index.html, assets/index-BYiE8AiO.js, assets/index-U0tXq8yR.css
- `harness/init.ps1`: Entorno verificado OK (salvo timeout en tests por Docker).
