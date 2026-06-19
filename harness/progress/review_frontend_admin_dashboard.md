# Review — feature 14 (frontend_admin_dashboard)

**Veredicto:** CHANGES_REQUESTED

## Trazabilidad requirements <-> tests

| Requirement | Cobertura | Estado |
|-------------|-----------|--------|
| R1 — Dashboard con 5 cards | Solo code review (T1). **Sin test concreto en tests/.** | ❌ |
| R2 — Card Configuracion → /admin/config | Solo code review (T1). **Sin test concreto en tests/.** | ❌ |
| R3 — Card Usuarios → /admin/usuarios | Solo code review (T1). **Sin test concreto en tests/.** | ❌ |
| R4 — Card Haciendas → /admin/haciendas | Solo code review (T1). **Sin test concreto en tests/.** | ❌ |
| R5 — Card Suertes → /admin/suertes | Solo code review (T1). **Sin test concreto en tests/.** | ❌ |
| R6 — Card Backup → /admin/backup | Solo code review (T1). **Sin test concreto en tests/.** | ❌ |
| R7 — Sidebar en todas las rutas /admin/* | Solo code review (T2). **Sin test concreto en tests/.** | ❌ |
| R8 — Solo admin accede a /admin/* | Solo code review (T3, T4, T6). Backend test 	est_auth.py::test_operator_denied_access_to_config verifica RBAC a nivel API (403), pero NO verifica el comportamiento frontend descrito en R8 (redireccion a /kiosco). **Sin test concreto del frontend en tests/.** | ❌ |
| R9 — Navegacion directa por hash a sub-rutas | Solo code review (T3, T7). **Sin test concreto en tests/.** | ❌ |
| R10 — HTTP 401 redirige a login | Solo code review (T5). Backend tests verifican 401 a nivel API, pero NO verifican el comportamiento frontend descrito en R10 (modal login con mensaje). **Sin test concreto del frontend en tests/.** | ❌ |

**Conclusion:** Ningun R<n> tiene un test concreto en 	ests/ que lo verifique. Todos se basan unicamente en code review. Esto viola la regla del protocolo: *"localiza al menos un test concreto en tests/ que lo verifique. Si falta cobertura para algun R<n>, rechaza."*

## Tasks completas

| Task | Estado | Nota |
|------|--------|------|
| T1 | ✅ [x] | Verificar AdminDashboard.svelte |
| T2 | ✅ [x] | Verificar AdminLayout.svelte |
| T3 | ✅ [x] | Verificar App.svelte routing condicional |
| T4 | ✅ [x] | Verificar RBAC |
| T5 | ✅ [x] | Verificar interceptor 401 |
| T6 | ✅ [x] | Verificar auth.js store |
| T7 | ✅ [x] | Verificar router.js store |
| T8 | ✅ [x] | npm run build |
| T9 | ✅ [x] | Copiar dist a src/static/ |
| T10 | ✅ [x] | ./init.ps1 (con FAIL pre-existente) |
| T11 | ✅ [x] | Trazabilidad documentada |

Todas las tasks estan marcadas [x]. OK.

## Svelte 5 compliance

| Regla | Estado |
|-------|--------|
| main.js usa mount(App, {target}), NO 
ew App() | ✅ |
| Ningun .js usa $state/$derived (solo .svelte) | ✅ |
| Stores usan writable/derived de svelte/store | ✅ |
| Templates usan $storeName para reactividad | ✅ |
| AdminLayout usa $props() + {@render children?.()} | ✅ |
| App.svelte usa $state para currentRoute | ✅ |

Svelte 5 reglas cumplidas correctamente.

## Impacto en features existentes

- [x] Seccion 'Impacto en features existentes' documentada en impl_frontend_admin_dashboard.md
- [x] Dependencia con Feature 13 reconocida (stores compartidos: auth.js, api.js, router.js)
- [x] No se modificaron archivos de features anteriores (solo verificacion)

OK.

## Skills consultados

- [x] svelte5 skill consultado y documentado en seccion "Svelte 5 compliance (skill checklist)"

## ./init.ps1

**Estado: FAIL en seccion 5**

La seccion 5 (validate_features.py) falla porque harness/feature_list.json contiene caracteres Latin-1 (como ñ, ó) que no son UTF-8 validos, causando un UnicodeDecodeError.

Esto viola la regla dura: *"Nunca apruebes con ./init.ps1 en rojo."*

Nota: el implementer documento que es un error pre-existente y no relacionado con Feature 14, pero la regla no hace excepciones.

## GitHub sync

GitHub sync esta habilitado (harness/github.json: "enabled": true), pero Feature 14 **no tiene campo github_issue** en harness/feature_list.json. Esto viola el protocolo: *"verifica que la feature tiene github_issue"*.

## Checkpoints

- C1: [x] El arnés está completo
- C2: [ ] ./init.ps1 tiene FAIL en seccion 5
- C3: [x] Código respeta la arquitectura
- C4: [ ] Sin tests concretos en tests/ para R1-R10
- C5: [x] BD bajo control (no aplica)
- C6: [ ] Sesion aun abierta (.session = open)
- C7: [ ] Cada R<n> no tiene test concreto en tests/
- C8: [ ] Sin closure creado (feature aun en in_progress)

## Release

- [ ] La feature NO esta lista para release-manager.

## Cambios requeridos

1. **Anadir tests** — Cada R<n> (R1-R10) necesita al menos un test concreto en 	ests/ que lo verifique. Dado que son tests de frontend Svelte 5, se recomienda:
   - Opcion A: Configurar Vitest + @testing-library/svelte en el frontend y escribir tests para cada componente.
   - Opcion B: Escribir tests de integracion que rendericen el SPA via Playwright/Puppeteer y verifiquen el comportamiento del DOM descrito en cada R<n>.
   - Opcion C (minima): Si no se puede configurar un framework de testing frontend, documentar formalmente por que no es posible y que metodo alternativo de verificacion se uso (con aprobacion del humano).

2. **Resolver ./init.ps1 FAIL** — Corregir la codificacion de harness/feature_list.json a UTF-8 valido para que alidate_features.py pueda procesarlo. Esto es pre-existente pero bloquea el paso del init.

3. **Agregar github_issue a Feature 14** — Crear el issue en GitHub y agregar "github_issue": "https://github.com/rojecas/sip_edge/issues/N" en harness/feature_list.json para Feature 14.
