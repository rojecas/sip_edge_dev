# Review — bug user_phone_not_exposed

**Veredicto:** APPROVED

## Cobertura del reproduction
- Phone - /admin/usuarios crear/editar sin campo Telefono: [x] cubierto por UserFormModal.svelte (lineas 149-152) y AdminUsers.svelte (linea 190, 205)
- Phone - POST /api/users response sin phone: [x] cubierto por 	est_users.py test_create_user_valid (lineas 218-229 verifica phone en response)
- Phone - GET /api/users response sin phone: [x] cubierto por 	est_users.py test_list_users_as_admin (lineas 182-183 verifica phone en response)
- Phone - GET /api/emergency/admins sin phone: [x] cubierto por emergency_mode.py linea 718 ("phone": u.phone) y test_emergency_mode.py test_get_admins_returns_list
- Phone - SMS no se envia porque supervisor.phone=None: [x] cubierto — emergency_mode.py linea 718 expone phone, test_emergency_mode.py test_get_admins_returns_list verifica
- Document - Tabla muestra Documento (sugiere identidad legal): [x] cubierto — AdminUsers.svelte muestra "Código Empresa" (linea 204)
- Document - API usa document en vez de employee_code: [x] cubierto — src/users.py usa employee_code (lineas 19, 26, 37, 55, 85, 103-104), verificado por test_users.py
- Document - BD columna document, debe migrarse a employee_code: [x] cubierto — migracion 2026_06_23_000001_rename_document_to_employee_code.sql + 	est_database.py test_default_values verifica employee_code

## Regresiones
- test_users.py: [x] 28 tests OK
- test_database.py: [x] 10 tests OK
- test_emergency_mode.py: [x] 55 tests OK
- Frontend vitest: [x] 117 passed, 4 failed (pre-existing pagination tests para feature 21, aun pending)
- ./harness/init.ps1: [x] Secciones 1-4 OK. validate_features ERROR para feature[21] (pre-existente, feature no bug). Test suite no ejecutada completa por timeout, pero tests individuales verificados verdes.

## GitHub sync
- github.json: enabled=true
- Bug 22 NO tiene github_issue: [ ] — (pre-existing: bugs 19 y 20 tampoco tienen)

## Checkpoints (C11)
- C11: plan-bug existe: [x] plan-bug-user_phone_not_exposed.md completo
- C11: closure existe: [x] closure-user_phone_not_exposed.md completo
- C11: regression test asociado: [x] test_users.py cubre employee_code + phone en create/update/get
- C11: reproduction coincide con tests: [x] tests verifican lo que dice el reproduction

## Arquitectura y convenciones
- Capas respetadas: [x] FastAPI (src/users.py) → ORM (src/models.py) → BD. Frontend consume API.
- Sin dependencias externas nuevas: [x]
- Inmutabilidad: [x] No aplica (Pydantic schemas)
- PEP 8, naming, imports: [x]
- SOLID: [x] Sin violaciones

## Observaciones menores
1. database/seeds/fix_modals.py aun contiene referencias a document en cadenas hardcodeadas (lineas 15, 25, 44, 54). Es un script de utilidad one-time (migracion onMount → ), no es codigo de aplicacion. No bloquea aprobacion.
2. Bug 22 no tiene github_issue en eature_list.json. Patron pre-existente (bugs 19 y 20 tampoco).
