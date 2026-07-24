# Implementación — Correcciones F43 Corporate Branding (Review Feedback)

## Skills consultados

- **svelte5** — Reglas de Svelte 5: runes, mount(), stores. Verificado que no hay cambios en componentes, solo en tests.

## Resumen

Se corrigieron los tres hallazgos del reviewer en `harness/progress/review_43_corporate_branding.md`:

1. **R11 — Test de favicon** (REQUERIDO, regla dura): 3 tests nuevos que verifican existencia, formato PNG válido y dimensiones del favicon.
2. **R9 — Completar test AboutModal**: Se separó el test R9/R10 en dos tests independientes, agregando assertions para `.about-subtitle`, `.about-copy` y `.about-disclaimer`.
3. **R12-R16 — Fortalecer cobertura CSS**: 6 tests nuevos que verifican reglas CSS concretas en `app.css` y `AdminLayout.svelte`.

## Cambios realizados

### Archivo modificado

| Archivo | Cambio |
|---------|--------|
| `frontend/src/components/__tests__/CorporateBranding.test.js` | +10 tests nuevos. Añadido `existsSync` al import de `fs`. Lectura de `AdminLayout.svelte` para verificación de reglas CSS. |

### Detalle de tests nuevos (10)

#### T24 — Favicon corporativo (R11) — 3 tests
| Test | Descripción |
|------|-------------|
| `R11: frontend/public/favicon.png existe en disco` | `existsSync(faviconPath)` retorna `true` |
| `R11: favicon.png es un archivo PNG válido` | Verifica magic bytes PNG (`\x89PNG\r\n\x1a\n`) |
| `R11: favicon.png tiene dimensiones de ícono (16–64px)` | Lee IHDR chunk (bytes 16-23), verifica ancho/alto en rango 16-64, cuadrado |

#### T25 — Reglas CSS usan paleta corporativa (R12-R16) — 6 tests
| Test | Archivo verificado | Regla |
|------|-------------------|-------|
| `R12: .sidebar usa background: var(--color-accent)` | `AdminLayout.svelte` | `background: var(--color-accent)` |
| `R12: .sidebar-link.active usa background: var(--color-primary)` | `AdminLayout.svelte` | `background: var(--color-primary)` |
| `R13: .sidebar-title usa color: var(--color-primary)` | `AdminLayout.svelte` | `color: var(--color-primary)` |
| `R14: .btn-primary usa background: var(--color-primary)` | `app.css` | `background: var(--color-primary)` |
| `R15: input:focus usa border-color: var(--color-primary)` | `app.css` | `border-color: var(--color-primary)` |
| `R16: a usa color: var(--accent)` | `app.css` | `color: var(--accent)` |

#### Extensión R9 — 1 test adicional (separado de R10)
| Test | Descripción |
|------|-------------|
| `R9/R10: AboutModal muestra información corporativa completa` | Verifica razón social, versión "SIP-Edge v1.0", copyright "© 2026 Ingenio Mayagüez S.A.", disclaimer "Sistema de uso exclusivo" |

## Trazabilidad actualizada

| Requirement | Test(s) |
|-------------|---------|
| R1 | T21: 5 tests de variables corporativas en `:root` |
| R2 | T21: 4 tests de reasignación de variables funcionales |
| R3 | T21: 3 tests de variables semánticas sin modificar |
| R4 | T23: index.html incluye Google Fonts Montserrat |
| R5 | T23: app.css body usa Montserrat |
| R6 | T22: AuthModal logo |
| R7 | T22: KioskLayout logo |
| R8 | T22: AdminLayout logo 64x64 |
| R9 | T22: AboutModal muestra info corporativa (razón social, versión, copyright, disclaimer) |
| R10 | T22: AboutModal logo 64x64 |
| **R11** | **T24: 3 tests de favicon (existencia, PNG válido, dimensiones)** |
| **R12** | **T25: .sidebar background + .sidebar-link.active background** |
| **R13** | **T25: .sidebar-title color** |
| **R14** | **T25: .btn-primary background** |
| **R15** | **T25: input:focus border-color** |
| **R16** | **T25: a color** |
| R17 | T16/R17: 3 tests de ⓘ |

## Verificación

- `npm run build`: ✅ OK
- `npm test`: 211 passed / 19 failed (pre-existing) / 230 total
  - Los 10 tests nuevos pasan (3 favicon + 6 CSS + 1 R9 extendido)
  - Los 19 fallos son pre-existentes (AdminUsers emoji buttons, UserFormModal placeholder/encoding)
- `Copy-Item -Recurse frontend/dist → src/static/`: ✅ OK (assets/ preservado)

## Impacto

- Cero cambios en componentes Svelte, backend, API o base de datos.
- Solo se modificó el archivo de tests.
- Los tests pre-existentes de CorporateBranding (21) siguen pasando.

## Notas

- La verificación de dimensiones del favicon lee el chunk IHDR del PNG (bytes 16-23) usando `readUInt32BE`. Esto funciona en Node.js (vitest).
- Para la verificación de reglas CSS en `AdminLayout.svelte`, se lee el archivo fuente directamente (no es posible obtener estilos scoped de Svelte en jsdom).
