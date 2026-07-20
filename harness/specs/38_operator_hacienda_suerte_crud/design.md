# Design — Feature 38: Operator Hacienda/Suerte CRUD

## Resumen

Agregar dos pestañas ([Haciendas] y [Suertes]) a la vista kiosko para que operadores puedan listar, crear y editar haciendas y suertes (mismo acceso que administradores, **excepto eliminar**). Se modifican los guards en 2 PUT endpoints del backend (haciendas y suertes; POST ya usa `require_any_role`, DELETE permanece solo admin). En el frontend se reutilizan `AdminHaciendas` y `AdminSuertes` con una prop `allowDelete={false}` para ocultar los botones de eliminación.

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `src/haciendas.py` | 2 PUT endpoints: cambiar guard de `require_role("admin")` a `require_any_role`. POST ya usa `require_any_role`. DELETE se mantiene solo admin (sin cambios). |
| `frontend/src/components/AdminHaciendas.svelte` | Aceptar prop `allowDelete` (default `true`), ocultar botón eliminar si `false` |
| `frontend/src/components/AdminSuertes.svelte` | Aceptar prop `allowDelete` (default `true`), ocultar botón eliminar si `false` |
| `frontend/src/App.svelte` | Reemplazar modales por `<AdminHaciendas allowDelete={false} />` y `<AdminSuertes allowDelete={false} />`, limpiar imports sobrantes |

## Archivos a crear

Ninguno.

---

## Firmas nuevas

### Backend

PUT endpoints de haciendas y suertes cambian su guard:
```python
# Antes:
__admin: dict = Depends(require_role("admin"))
# Después:
__operator: dict = Depends(require_any_role("admin", "operator"))
```

POST ya usa `require_any_role`. DELETE se mantiene con `require_role("admin")` — sin cambios.

### Frontend — Prop `allowDelete`

`AdminHaciendas.svelte` y `AdminSuertes.svelte` aceptan nueva prop opcional:
```javascript
let { allowDelete = true } = $props();
```

Cuando `allowDelete === false`, el botón de eliminar en cada fila de la tabla no se renderiza.

**Uso en App.svelte:**
```svelte
<KioskLayout>
  ...
  {:else if currentRoute === "/kiosco/haciendas"}
    <AdminHaciendas allowDelete={false} />
  {:else if currentRoute === "/kiosco/suertes"}
    <AdminSuertes allowDelete={false} />
  ...
</KioskLayout>
```

---

## Excepciones

No se crean nuevas. DELETE devuelve 403 para operator (comportamiento existente, sin cambios).

---

## Alternativa descartada

### Dejar el botón de eliminar visible y que falle con 403
- **Descartada porque**: Mala UX. El operador haría clic, vería un error, y no entendería por qué. Mejor ocultar la acción que no está permitida.

---

## Persistencia

Sin cambios.

---

## Impacto en APIs existentes

| Endpoint | Cambio | Contrato |
|----------|--------|----------|
| `POST /api/haciendas` | Ya usa `require_any_role` ✅ | Sin cambios |
| `PUT /api/haciendas/{id}` | `require_role("admin")` → `require_any_role` | Sin cambios |
| `DELETE /api/haciendas/{id}` | **Sin cambios** (solo admin) | 403 para operator |
| `POST /api/suertes` | Ya usa `require_any_role` ✅ | Sin cambios |
| `PUT /api/suertes/{id}` | `require_role("admin")` → `require_any_role` | Sin cambios |
| `DELETE /api/suertes/{id}` | **Sin cambios** (solo admin) | 403 para operator |

---

## Análisis de impacto

### Feature 4 — farm_lot_crud
| Archivo | Impacto |
|---------|---------|
| `src/haciendas.py` — PUT endpoints | Guard ampliado a operator. Admin mantiene acceso. |

### Feature 13 — frontend_login_kiosk
| Archivo | Impacto |
|---------|---------|
| `KioskLayout.svelte` | Ya tiene 4 botones ✅ |
| `App.svelte` | Modales → AdminHaciendas/AdminSuertes con `allowDelete={false}` |

### Feature 16 — frontend_admin_masterdata
| Archivo | Impacto |
|---------|---------|
| `AdminHaciendas.svelte` | Nueva prop `allowDelete` (default `true`, sin romper admin) |
| `AdminSuertes.svelte` | Nueva prop `allowDelete` (default `true`, sin romper admin) |

### Feature 36 — hacienda_search_filter
Sin impacto directo.

---

## github_labels

`kiosko`, `operator`, `haciendas`, `suertes`, `permissions`
