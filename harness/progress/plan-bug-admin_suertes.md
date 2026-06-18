# Plan Bug: AdminSuertes.svelte no carga las suertes al seleccionar una hacienda

## Síntoma
Al seleccionar una hacienda en el dropdown de AdminSuertes.svelte, se muestra el mensaje "No hay suertes registradas para esta hacienda." aunque la hacienda sí tiene suertes en la BD. La API `GET /api/suertes?hacienda_id=483` devuelve 6 suertes correctamente.

## Causa raíz
La función `loadSuertes()` en `AdminSuertes.svelte` asume que la respuesta del endpoint `/api/suertes` tiene formato `{items: [...]}` (como el endpoint `/api/haciendas` que sí retorna paginado). Sin embargo, el endpoint `/api/suertes` en el backend retorna una **lista plana** (`List[SuerteResponse]`), es decir, un array JSON directo:

```python
@suertes_router.get("", response_model=List[SuerteResponse])
```

Por lo tanto, `result` es un array directo `[{...}, {...}]`, y `result.items` es `undefined`. La línea `suertes = result.items || []` produce `[]`, lo que dispara el mensaje de "No hay suertes".

## Archivos implicados
- `frontend/src/components/AdminSuertes.svelte` (único archivo a modificar)

## Fix propuesto
Cambiar la línea que parsea la respuesta en `loadSuertes()` para que maneje tanto arrays directos como objetos con `.items`:

```javascript
suertes = Array.isArray(result) ? result : (result.items || []);
```

Esto permite que el frontend funcione correctamente sin importar si el backend retorna un array plano o un objeto paginado.

## Plan de verificación
1. `npm run build` en `frontend/` debe compilar sin errores.
2. Verificar que el fix maneja ambos formatos de respuesta (array directo y `{items: [...]}`).
3. Ejecutar `harness/init.ps1` para verificar que no hay regresiones.
