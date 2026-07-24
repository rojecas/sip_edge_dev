# F43 — Corporate Branding: Design

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `frontend/public/logo-mayaguez.png` | Logo corporativo para servir como asset estático. Copia de `docs/logo-mayaguez.png`. |

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `frontend/src/app.css` | Reemplazar paleta de colores actual por variables corporativas. Añadir Montserrat en `body`. |
| `frontend/index.html` | Añadir `<link>` a Google Fonts Montserrat. |
| `frontend/src/components/AuthModal.svelte` | Añadir logo corporativo arriba del título. |
| `frontend/src/components/KioskLayout.svelte` | Reemplazar texto "Sip-Edge" por logo en header. |
| `frontend/src/components/AdminLayout.svelte` | Añadir logo en sidebar-header. Cambiar paleta del sidebar (fondo oscuro, acento amarillo). Fix visibilidad ⓘ. |
| `frontend/src/components/AboutModal.svelte` | Reemplazar placeholder `/static/favicon.png` por `/static/logo-mayaguez.png`. |

## Firmas nuevas

No se crean funciones, clases ni comandos nuevos. Todos los cambios son
declarativos (CSS) o de reemplazo de assets en componentes Svelte existentes.

## Excepciones

- `ExcepciónFontFamily`: El `input.weight-input` en `WeightField.svelte` usa
  `font-family: "Courier New", monospace` para mantener legibilidad numérica.
  Esta fuente NO se reemplaza por Montserrat.
- `ExcepciónIconos`: Los iconos emoji en sidebar (`📊`, `👥`, etc.) y
  LogoutButton (`🚪`) NO se ven afectados por la tipografía.

## Alternativa descartada

**Servir Montserrat desde archivo local en lugar de Google Fonts.**
Se descartó porque: (1) la licencia de Montserrat (SIL OFL) permite
auto-hospedaje, pero requiere descargar los 4 pesos WOFF2 y mantenerlos
en el repo (~80KB por archivo); (2) Google Fonts CDN ofrece caché
navegador, compresión y zero mantenimiento; (3) el EdgeBox tiene conexión
4G y la carga ocurre una sola vez al abrir el frontend. Si en el futuro
se requiere operación 100% offline, Montserrat se puede auto-alojar
como mejora.

## Análisis de impacto en features existentes

### Feature 13 — frontend_login_kiosk
| Archivo | Cambio | Impacto |
|---------|--------|---------|
| `frontend/index.html` | Google Fonts link | No rompe funcionalidad. |
| `frontend/src/app.css` | Paleta CSS + font-family | Todos los componentes existentes heredan los nuevos colores. Los tests visuales pueden fallar si comparan colores estáticos. |
| `AuthModal.svelte` | Logo en login | Estructural: añade `<img>` dentro del modal. No rompe flujo. |
| `KioskLayout.svelte` | Logo en header | El texto "Sip-Edge" se reemplaza por imagen. No afecta navegación. |
| `AboutModal.svelte` | Logo real en About | Reemplaza src de imagen existente. No rompe funcionalidad. |

### Feature 14 — frontend_admin_dashboard
| Archivo | Cambio | Impacto |
|---------|--------|---------|
| `AdminLayout.svelte` | Logo + paleta sidebar + fix ⓘ | Cambios CSS, no de lógica. La navegación, routing y RBAC no se tocan. |

### Feature 16 — frontend_admin_masterdata
| Archivo | Cambio | Impacto |
|---------|--------|---------|
| Ninguno directo | — | Los componentes de formulario heredan los estilos globales de `app.css`. No requieren cambios. |

### Feature 17 — frontend_analytics
| Archivo | Cambio | Impacto |
|---------|--------|---------|
| Ninguno directo | — | Los componentes heredan estilos globales. |

**Ruptura de compatibilidad:** No hay cambios de interfaz (firmas, props,
endpoints). Todos los cambios son CSS y assets. Los tests de frontend
que verifiquen colores específicos (ej. `var(--accent)` = `#e94560`)
fallarán; deberán actualizarse al nuevo valor #FDB814.

**Tests afectados:**
- `tests/` del backend: ninguno.
- Frontend: tests que verifiquen colores o valores de CSS custom properties.

**Plan de mitigación:** Actualizar valores de color en assertions de tests
frontend que comparen estilos.

## Contrato API

No hay cambios en la API. Esta feature es puramente frontend.

## Persistencia

No hay cambios en la base de datos.
