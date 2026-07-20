# Design — Feature 38: Operator Hacienda/Suerte CRUD

## Resumen

Agregar dos pestañas ([Haciendas] y [Suertes]) a la vista kiosko para que operadores tengan el **mismo acceso** que los administradores a la gestión de haciendas y suertes. Se modifican los guards de rol en 6 endpoints del backend (POST, PUT, DELETE). En el frontend se reutilizan los componentes completos `AdminHaciendas` y `AdminSuertes` existentes, embebidos dentro de `KioskLayout`.

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | 6 endpoints: cambiar `require_role("admin")` → `require_any_role("admin", "operator")` en POST, PUT, DELETE de haciendas y suertes |
| `frontend/src/components/KioskLayout.svelte` | Agregar 2 botones de navegación ("Haciendas", "Suertes") |
| `frontend/src/App.svelte` | Agregar 2 condiciones de ruta que rendericen `<AdminHaciendas />` y `<AdminSuertes />` dentro de `<KioskLayout>` |

## Archivos a crear

Ninguno. Se reutilizan `AdminHaciendas.svelte` y `AdminSuertes.svelte` completos.

---

## Firmas nuevas

### Backend

No hay firmas nuevas. Solo cambia el decorador `Depends` en 6 endpoints existentes:

```python
# Antes (solo admin):
__admin: dict = Depends(require_role("admin"))

# Después (admin + operator):
__operator: dict = Depends(require_any_role("admin", "operator"))
```

Endpoints afectados en `src/haciendas.py`:
- `create_new_hacienda` (POST) — línea ~284
- `update_hacienda` (PUT) — línea ~310
- `delete_hacienda` (DELETE) — línea ~335
- `create_new_suerte` (POST) — línea ~350
- `update_suerte` (PUT) — línea ~376
- `delete_suerte` (DELETE) — línea ~401

### Frontend — Reutilización de componentes admin completos

`AdminHaciendas.svelte` y `AdminSuertes.svelte` son componentes autónomos que contienen tabla paginada, modales de creación/edición, y botones de acción. No dependen de `AdminLayout` — este solo les da un contenedor con sidebar. Son perfectamente reutilizables dentro de `KioskLayout`.

**Uso en App.svelte:**
```svelte
{#if $authStore.isOperator}
  <KioskLayout>
    {#if currentRoute === "/kiosco/historial"}
      <HistoryTable />
    {:else if currentRoute === "/kiosco/haciendas"}
      <AdminHaciendas />
    {:else if currentRoute === "/kiosco/suertes"}
      <AdminSuertes />
    {:else}
      <KioskForm />
    {/if}
  </KioskLayout>
```

---

## Excepciones

No se crean nuevas excepciones. Los endpoints ya manejan 404, 409, y 422.

---

## Alternativa descartada

### Alternativa: Solo permitir creación (POST) — spec anterior
- **Descartada porque**: El requisito real es que los operadores tengan el **mismo acceso** que los administradores a haciendas y suertes. Limitar solo a creación obliga al operador a contactar al admin para corregir errores (ej. código mal escrito) o eliminar registros obsoletos, rompiendo el flujo de trabajo.

### Alternativa: Componentes nuevos (KioskHaciendas/KioskSuertes)
- **Descartada porque**: Duplica cientos de líneas de código (tabla, paginación, modales, validación). `AdminHaciendas` y `AdminSuertes` ya contienen toda la funcionalidad requerida.

---

## Persistencia

No se requieren nuevas tablas, columnas, índices o migraciones. La feature reutiliza las tablas `haciendas` y `suertes` existentes (Feature 4).

---

## Impacto en APIs existentes

| Endpoint | Cambio | Contrato |
|----------|--------|----------|
| `POST /api/haciendas` | Guard: `admin` → `admin + operator` | Sin cambios |
| `PUT /api/haciendas/{id}` | Guard: `admin` → `admin + operator` | Sin cambios |
| `DELETE /api/haciendas/{id}` | Guard: `admin` → `admin + operator` | Sin cambios |
| `POST /api/suertes` | Guard: `admin` → `admin + operator` | Sin cambios |
| `PUT /api/suertes/{id}` | Guard: `admin` → `admin + operator` | Sin cambios |
| `DELETE /api/suertes/{id}` | Guard: `admin` → `admin + operator` | Sin cambios |

`GET` endpoints ya son accesibles a operator (usan `require_role("admin", "operator")`).

---

## Análisis de impacto en features existentes

### Feature 4 — farm_lot_crud
| Archivo | Impacto | Compatibilidad |
|---------|---------|---------------|
| `src/haciendas.py` — 6 endpoints | Guards ampliados a operator | **Compatible.** Admin mantiene acceso. |

**Tests afectados**: Tests que verifican 403 para operator en POST/PUT/DELETE deben cambiar a 201/200/204.

### Feature 13 — frontend_login_kiosk
| Archivo | Impacto | Compatibilidad |
|---------|---------|---------------|
| `KioskLayout.svelte` | +2 botones nav | Compatible |
| `App.svelte` | +2 condiciones ruta | Compatible |

### Feature 16 — frontend_admin_masterdata
| Componente | Impacto | Compatibilidad |
|-----------|---------|---------------|
| `AdminHaciendas.svelte` | Reutilizado en kiosko sin cambios | Compatible |
| `AdminSuertes.svelte` | Reutilizado en kiosko sin cambios | Compatible |

### Feature 36 — hacienda_search_filter
Sin impacto directo. F38 habilita la navegación a `/kiosco/haciendas` desde F36.

---

## github_labels

`kiosko`, `operator`, `haciendas`, `suertes`, `permissions`
