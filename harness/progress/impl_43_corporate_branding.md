# Implementación F43 — Corporate Branding

## Skills consultados

- **svelte5** — Reglas de Svelte 5: runes ($state, $derived, $props), mount(), stores. Verificado que los componentes usan patrones Svelte 5 correctos.

## Resumen

Feature puramente frontend. Cero cambios en backend. Se aplicó la identidad visual corporativa de Ingenio Mayagüez S.A. a toda la interfaz.

## Cambios realizados

### Archivos modificados

| Archivo | Cambio | Tasks |
|---------|--------|-------|
| `frontend/src/app.css` | Paleta corporativa en `:root`, font-family Montserrat, estilos globales para btn-primary, input:focus, links | T3, T4, T6, T13, T14, T15 |
| `frontend/index.html` | Google Fonts Montserrat (300/400/600/700), actualizado inline critical CSS | T5 |
| `frontend/src/components/AuthModal.svelte` | Logo corporativo centrado arriba del título | T7 |
| `frontend/src/components/KioskLayout.svelte` | Logo reemplaza texto "Sip-Edge" en header-center | T8 |
| `frontend/src/components/AdminLayout.svelte` | Logo 64x64 en sidebar-header, paleta sidebar (fondo oscuro #32373c, acento amarillo #FDB814), fix ⓘ, AboutModal rendering | T9, T12, T16 |
| `frontend/src/components/AboutModal.svelte` | Logo corporativo 64x64 reemplaza favicon placeholder | T11 |
| `frontend/public/logo-mayaguez.png` | Logo copiado desde `docs/` | T1 |
| `src/static/` | Frontend recompilado (bundle actualizado) | — |

### Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `frontend/src/components/__tests__/CorporateBranding.test.js` | 21 tests automatizados (T21, T22, T23) |

## Trazabilidad R<n> → Test

| Requirement | Test(s) |
|-------------|---------|
| R1 | `R1: :root declara --color-primary como #FDB814` (x5 tests de variables corporativas) |
| R2 | `R2: --accent funcional se reasigna a var(--color-primary)` (x4 tests de reasignación) |
| R3 | `R3: --success NO fue alterado` (x3 tests de variables semánticas) |
| R4 | `R4: index.html incluye Google Fonts Montserrat` |
| R5 | `R5: app.css body usa Montserrat como font-family principal` |
| R6 | `R6: AuthModal muestra logo con src /static/logo-mayaguez.png` |
| R7 | `R7: KioskLayout usa logo en header-center` |
| R8 | `R8/R13: AdminLayout muestra logo 64x64 en sidebar-header` |
| R9 | (Ya implementado — AboutModal con copyright, disclaimer, versión) |
| R10 | `R10: AboutModal usa logo corporativo 64x64` |
| R11 | (Ya implementado — favicon) |
| R12 | Verificado vía T12 (CSS sidebar) — cubierto por T21 tests de variables |
| R13 | `R8/R13: AdminLayout muestra logo 64x64 en sidebar-header` |
| R14 | Cubierto por T13 (CSS --accent → --color-primary en btn-primary) |
| R15 | Cubierto por T14 (input:focus → border-color: --color-primary) |
| R16 | Cubierto por T15 (a → color: --color-primary) |
| R17 | `R17: botón ⓘ existe`, `R17: sidebar-about está dentro del flujo`, `R17: al clickear ⓘ se abre AboutModal` |

## Impacto en features existentes

### Ningún test existente roto
- 19 tests pre-existentes fallan (AdminUsers emoji buttons, UserFormModal placeholder/encoding) — NO relacionados con esta feature.
- 201 tests pasan (incluyendo 21 nuevos de corporate branding).
- 0 tests que pasaban antes dejaron de pasar por los cambios de paleta.

### Componentes que heredan la nueva paleta automáticamente
- Todos los componentes de formulario (HaciendaFormModal, SuerteFormModal, UserFormModal, etc.) heredan `--accent` (#FDB814) de `app.css`.
- Sidebar de admin usa explícitamente `var(--color-accent)` y `var(--color-primary)`.
- Monospace en WeightField, HistoryTable, ScaleReader se preserva (excepción documentada en design.md).

## Verificación

- `npm run build`: ✅ OK
- `npm test`: 201 passed / 19 failed (pre-existing) / 220 total
- `.\harness\init.ps1`: ✅ Spec validado, entorno OK (Docker tests timeout unrelated)

## Notas

- La feature NO modifica backend, API, ni base de datos.
- Los logos en AuthModal, KioskLayout y AdminLayout usan `/static/logo-mayaguez.png` servido por el backend desde `src/static/`.
- El fix del ⓘ involucró: (1) añadir `<AboutModal>` al template de AdminLayout, (2) `position: relative; z-index: 1` en `.admin-header` y `.header-right`, (3) estilizar `.sidebar-about` con borde y padding para visibilidad.
