# Indice de documentacion — {{PROJECT_NAME}}

> Indice navegable de toda la documentacion del proyecto. Cada proyecto
> derivado DEBE mantener este indice actualizado al anadir o modificar docs.
>
> La documentacion se distribuye en dos ubicaciones:
> - `docs/` (raiz): documentacion tradicional del proyecto.
> - `harness/docs/`: documentacion del harness, orientada a agentes IA.

## Documentacion del harness (harness/docs/)

| Archivo | Contenido | Para que sirve |
|---------|-----------|----------------|
| harness/docs/architecture.md | Principios SOLID, capas, flujo de datos | Antes de implementar |
| harness/docs/conventions.md | Estilo de codigo, nombres, manejo de errores | Antes de escribir codigo |
| harness/docs/specs.md | Proceso SDD: EARS, 3 archivos, puerta humana | Antes de redactar specs |
| harness/docs/sessions.md | Estandar A1/A2/A3: planes, closures, bloqueos | Antes de documentar trabajo |
| harness/docs/verification.md | Niveles de verificacion: unitaria, integracion, smoke | Antes de marcar done |
| harness/docs/database.md | Schema, migraciones, backups | Antes de tocar BD |
| harness/docs/environment.md | Stack, servicios, comandos, credenciales locales | Antes de ejecutar comandos |
| harness/docs/deployment.md | Despliegue a produccion: entornos, pasos, troubleshooting | Antes de deployar |
| harness/docs/security.md | Postura de seguridad: hallazgos, roadmap | Antes de tocar auth, BD o datos sensibles |
| harness/docs/github.md | Integracion GitHub Issues | Antes de usar github_sync.py |
| harness/docs/index.md | Este indice | Para navegar la documentacion |

## Documentacion del proyecto (docs/)

> Cada proyecto derivado debe listar aqui sus documentos especificos.

| Archivo | Contenido | Para que sirve |
|---------|-----------|----------------|
| docs/README.md | Descripcion general del proyecto | Primer contacto con el proyecto |
| <!-- docs/tu-doc.md --> | <!-- descripcion --> | <!-- proposito --> |

## Artefactos de progreso (harness/progress/)

| Archivo | Contenido |
|---------|-----------|
| harness/progress/current.md | Sesion actual (template cuando no hay sesion activa) |
| harness/progress/history.md | Bitacora de sesiones anteriores |
| harness/progress/closure-*.md | Cierres de features/bugs completados |
| harness/progress/blocked-*.md | Registros de features bloqueadas |
| harness/progress/plan-*.md | Planes de features no-SDD |
| harness/progress/plan-bug-*.md | Planes de diagnostico de bugs |

## Mapa de conocimiento por tema

| Tema | Donde empezar | Donde profundizar |
|------|---------------|-------------------|
| Arquitectura general | harness/docs/architecture.md | {{ARCHITECTURE_DEEP_DIVE}} |
| Stack tecnologico | harness/docs/environment.md | {{STACK_DEEP_DIVE}} |
| Base de datos | harness/docs/database.md | {{DB_DEEP_DIVE}} |
| Seguridad | harness/docs/security.md | {{SECURITY_DEEP_DIVE}} |
| Despliegue | harness/docs/deployment.md | {{DEPLOYMENT_DEEP_DIVE}} |
| SDD workflow | harness/docs/specs.md | harness/AGENTS.md |
| Features / backlog | harness/feature_list.json | harness/specs/ |
| Convenciones de codigo | harness/docs/conventions.md | {{CONVENTIONS_DEEP_DIVE}} |
