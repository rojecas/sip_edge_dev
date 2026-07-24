# Review — F43 corporate_branding

**Veredicto:** CHANGES_REQUESTED

## Trazabilidad requirements <-> tests

| R<n> | Cobertura | Test(s) |
|------|-----------|---------|
| R1 | [x] | R1: :root declara --color-primary como #FDB814 (×5 tests variables corporativas) |
| R2 | [x] | R2: --accent funcional se reasigna a var(--color-primary) (×4 tests) |
| R3 | [x] | R3: --success NO fue alterado (×3 tests variables semánticas) |
| R4 | [x] | R4: index.html incluye Google Fonts Montserrat |
| R5 | [x] | R5: app.css body usa Montserrat como font-family principal |
| R6 | [x] | R6: AuthModal muestra logo con src /static/logo-mayaguez.png |
| R7 | [x] | R7: KioskLayout usa logo en header-center |
| R8 | [x] | R8/R13: AdminLayout muestra logo 64x64 en sidebar-header |
| R9 | [~] | Solo verifica h2 "Ingenio Mayagüez S.A.". No testea versión, copyright ni disclaimer. |
| R10 | [x] | R10: AboutModal usa logo corporativo 64x64 |
| R11 | [ ] | **Sin test.** Favicon requirement no tiene test automatizado que lo verifique. |
| R12 | [~] | Variables CSS verificadas via T21, pero no hay test que renderice AdminLayout y verifique fondo .sidebar o active link. |
| R13 | [~] | Logo verificado, pero no se testea que .sidebar-title use color: var(--color-primary). |
| R14 | [~] | Cobertura indirecta vía variables CSS (T21). No hay test que verifique .btn-primary { background: var(--color-primary) }. |
| R15 | [~] | Cobertura indirecta vía variables CSS. No hay test que verifique input:focus { border-color: var(--color-primary) }. |
| R16 | [~] | Cobertura indirecta vía variables CSS. No hay test que verifique  { color: var(--color-primary) }. |
| R17 | [x] | 3 tests: botón ⓘ existe, está en header-right, abre AboutModal al click. |

## Tasks completas

- T1..T23: [x] todas completas.

## Skills consultados

- svelte5: [x] documentado en impl_43_corporate_branding.md.

## Impacto en features existentes

- [x] Sección presente en impl_43_corporate_branding.md con lista de componentes afectados y 0 regresiones.

## GitHub sync

- [x] Feature 43 tiene github_issue: https://github.com/rojecas/sip_edge/issues/28
- [x] Issue OPEN (correcto para status in_progress)
- [x] gh CLI confirma issue existe

## Arquitectura y convenciones

- [x] Feature puramente frontend (cero cambios en backend/API/BD).
- [x] Svelte 5 patterns correctos (\, \, \, \).
- [x] CSS con custom properties, sin breakpoints ni violaciones de convenciones.
- [x] Sin print(), TODO sin contexto, ni depuración hardcodeada.

## Checkpoints

- C1: [x] harness completo
- C2: [x] solo una feature en in_progress (la 43)
- C3: [x] código respeta arquitectura (sin dependencias externas)
- C4: [~] tests/ tiene módulo de tests; 21 tests nuevos pasan; 19 pre-existentes fallan (no relacionados con F43)
- C7: [x] spec SDD completo (requirements.md, design.md, tasks.md)
- C10: [x] GitHub sync OK (issue abierto)

## Release

- [ ] Feature no debe pasar a release hasta resolver R11.

## Cambios requeridos

### 1. R11 requiere test concreto (REQUERIDO — violación de regla dura)
R11 dice: *"CUANDO el navegador carga la aplicación, el favicon DEBE ser el isotipo de Mayaguez."*
No hay ningún test que verifique esto (ni existencia del archivo rontend/public/favicon.png, ni su contenido/dimensiones).
Añadir test en CorporateBranding.test.js que verifique:
- s.existsSync(resolve(__dirname, '../../../public/favicon.png')) — el archivo existe
- Opcional: verificar dimensiones (ej. 32×32 o 64×64 píxeles)

Cubre: R11.

### 2. R9 cobertura incompleta (RECOMENDADO)
El test de R10/R9 solo verifica el h2 "Ingenio Mayagüez S.A." pero no la versión, copyright ni disclaimer.
Añadir assertions para:
- document.querySelector('.about-subtitle')?.textContent contiene "SIP-Edge v1.0"
- document.querySelector('.about-copy')?.textContent contiene "© 2026 Ingenio Mayagüez S.A."
- document.querySelector('.about-disclaimer')?.textContent contiene "Sistema de uso exclusivo"

### 3. R12–R16 cobertura indirecta (RECOMENDADO)
Los requirements R12–R16 se cubren solo por la existencia de variables CSS en :root, pero no verifican que las reglas CSS que *usan* esas variables existan. Para mayor robustez, añadir tests que:
- Parseen pp.css y verifiquen .sidebar { background: var(--color-accent) } (R12)
- Parseen AdminLayout.svelte y verifiquen .sidebar-link.active { background: var(--color-primary) } (R12)
- Parseen pp.css y verifiquen .btn-primary { background: var(--color-primary) } (R14)
- Parseen pp.css y verifiquen input:focus { border-color: var(--color-primary) } (R15)
- Parseen pp.css y verifiquen  { color: var(--accent) } (R16)
