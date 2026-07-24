# F43 — Corporate Branding: Tasks

> **Leyenda:** `[x]` = ya implementado, `[ ]` = pendiente.

---

## Assets

- [x] T1 — Copiar `docs/logo-mayaguez.png` a `frontend/public/logo-mayaguez.png`.
  Cubre: R6, R7, R8, R10.

## Favicon (ya implementado)

- [x] T2 — Favicon desde `ingeniomayaguez.com` en `frontend/public/favicon.png`.
  Cubre: R11.

## Paleta CSS Corporativa

- [x] T3 — Declarar variables CSS corporativas en `:root` en `frontend/src/app.css`
  (`--color-primary: #FDB814`, `--color-accent: #32373c`, `--color-gray: #f4f4f4`,
  etc.). Cubre: R1.

- [x] T4 — Reasignar variables funcionales existentes (`--accent`, `--bg-primary`,
  `--bg-secondary`, `--bg-input`, `--text-primary`, `--text-secondary`, `--border`)
  a los nuevos valores corporativos. Preservar `--success`, `--error`, `--warning`.
  Cubre: R2, R3.

## Tipografía Montserrat

- [x] T5 — Añadir `<link rel="preconnect">` y `<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">`
  a `frontend/index.html`. Cubre: R4.

- [x] T6 — Cambiar `font-family` del `body` en `app.css` a
  `"Montserrat", system-ui, -apple-system, sans-serif`. Cubre: R5.

## Logo en Vistas

- [x] T7 — En `AuthModal.svelte`: añadir `<img src="/static/logo-mayaguez.png">`
  centrado arriba del título `<h1>SIP-Edge</h1>`, con altura máxima 64px y
  espaciado inferior. Ajustar `.modal-title` para que no tenga margen superior
  extra. Cubre: R6.

- [x] T8 — En `KioskLayout.svelte`: reemplazar el `<span class="app-name">Sip-Edge</span>`
  por `<img src="/static/logo-mayaguez.png">` con altura máxima 48px centrado.
  Mantener la clase `.app-name` para el posicionamiento absoluto.
  Cubre: R7.

- [x] T9 — En `AdminLayout.svelte`: en el `sidebar-header`, añadir logo
  (64x64px) centrado antes del título "SIP-Edge Admin". Ajustar espaciado.
  Cubre: R8, R13.

## Modal About

- [x] T10 — AboutModal.svelte ya existe con copyright, disclaimer y versión.
  Cubre: R9.

- [x] T11 — En `AboutModal.svelte`: reemplazar el `<img src="/static/favicon.png">`
  por `<img src="/static/logo-mayaguez.png">` con `width="64"` `height="64"`.
  Cubre: R10.

## Sidebar Admin

- [x] T12 — En `AdminLayout.svelte`: cambiar estilos del `.sidebar`:
  fondo `var(--color-accent)` (#32373c), borde derecho visible.
  `.sidebar-link.active` con background `var(--color-primary)` (#FDB814)
  y texto blanco. `.sidebar-link:hover` con fondo `var(--color-accent-hover)`.
  `.sidebar-title` en color `var(--color-primary)`.
  Cubre: R12.

## Componentes de Formulario

- [x] T13 — En `app.css`: asegurar que `.btn-primary` y estilos equivalentes
  usen `background: var(--color-primary)`.
  Cubre: R14.

- [x] T14 — En `app.css`: asegurar que `input:focus`, `select:focus`,
  `textarea:focus` usen `border-color: var(--color-primary)`.
  Cubre: R15.

- [x] T15 — En `app.css`: asegurar que los enlaces `a` usen
  `color: var(--color-primary)`. Cubre: R16.

## Fix ⓘ en Admin

- [x] T16 — En `AdminLayout.svelte`: diagnosticar por qué el botón `.sidebar-about`
  (ⓘ) no es visible. Ajustar CSS para que quede dentro del flujo de
  `.header-right` y no sea solapado por el `LogoutButton` (que tiene
  `position: fixed`). Posible solución: añadir `position: relative; z-index: 1`
  al `.header-right` y al `.admin-header`, o ajustar el z-index del logout.
  Cubre: R17.

## Tests

- [x] T17 — Verificar que los tests de frontend existentes pasan tras los
  cambios de paleta. Si algún test compara valores de color (ej.
  `expect(getComputedStyle(el).getPropertyValue('--accent').trim()).toBe('#e94560')`),
  actualizarlo a `#FDB814`. Cubre: R1, R2.

- [x] T18 — Verificar que el logo se renderiza correctamente en AuthModal,
  KioskLayout y AdminLayout en modo desarrollo (`npm run dev`).
  Cubre: R6, R7, R8.

- [x] T19 — Verificar que Montserrat se carga y aplica en el frontend
  (inspeccionar `font-family` en computed styles). Cubre: R4, R5.

- [x] T20 — Verificar que el botón ⓘ en AdminLayout es visible y al
  clickearlo abre el AboutModal. Cubre: R17.

- [x] T21 — Añadir test automatizado que verifica que las CSS custom properties
  corporativas están definidas en `:root` y las variables funcionales
  reasignadas correctamente (R1, R2). Verificar que las variables semánticas
  (`--success`, `--error`, `--warning`) no fueron alteradas (R3).
  Cubre: R1, R2, R3.

- [x] T22 — Añadir test automatizado que verifica que el logo corporativo se
  renderiza en AuthModal (R6), KioskLayout (R7) y AdminLayout (R8, R13),
  y que AboutModal usa `/static/logo-mayaguez.png` en lugar del placeholder
  (R10). Cubre: R6, R7, R8, R10, R13.

- [x] T23 — Añadir test automatizado que verifica que Montserrat se carga como
  `font-family` del `body` (R5) y que el `link` de Google Fonts está presente
  en `index.html` (R4). Cubre: R4, R5.
