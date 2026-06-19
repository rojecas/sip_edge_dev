# Despliegue — {{PROJECT_NAME}}

> Guia de despliegue del proyecto. Cada proyecto derivado DEBE documentar
> sus entornos y pasos de despliegue aqui.
>
> Los agentes DEBEN leer este archivo antes de modificar configuracion de
> entorno, variables de conexion, o cualquier archivo que afecte el despliegue.

## Entornos

| Entorno | URL | Servidor | Stack | Notas |
|---------|-----|----------|-------|-------|
| Desarrollo local | {{DEV_URL}} | {{DEV_SERVER}} | {{DEV_STACK}} | {{DEV_NOTES}} |
| Staging | {{STAGING_URL}} | {{STAGING_SERVER}} | {{STAGING_STACK}} | {{STAGING_NOTES}} |
| Produccion | {{PROD_URL}} | {{PROD_SERVER}} | {{PROD_STACK}} | {{PROD_NOTES}} |

## Desarrollo local

### Requisitos

- {{REQUIREMENT_1}}
- {{REQUIREMENT_2}}
- {{REQUIREMENT_3}}

### Iniciar entorno

```bash
{{DEV_START_COMMAND}}
```

Esto levanta los siguientes servicios:

| Servicio | Puerto | Acceso |
|----------|--------|--------|
| {{SERVICE_1}} | {{PORT_1}} | {{URL_1}} |
| {{SERVICE_2}} | {{PORT_2}} | {{URL_2}} |

### Primera vez

1. {{FIRST_TIME_STEP_1}}
2. {{FIRST_TIME_STEP_2}}
3. Iniciar: {{DEV_START_COMMAND}}
4. Verificar con `./init.ps1`

### Comandos utiles

```bash
{{DEV_COMMAND_1}}
{{DEV_COMMAND_2}}
{{DEV_COMMAND_3}}
```

## Produccion

### Acceso

- {{PROD_ACCESS_INFO}}

### Despliegue de cambios

1. {{DEPLOY_STEP_1}}
2. {{DEPLOY_STEP_2}}
3. {{DEPLOY_STEP_3}}
4. Verificar en {{PROD_URL}}

### Base de datos

- {{PROD_DB_INFO}}

## URLs del sitio (si aplica)

| Ruta | Descripcion |
|------|-------------|
| / | {{ROOT_PAGE_DESC}} |
| <!-- /ruta --> | <!-- descripcion --> |

## Troubleshooting

### {{ERROR_SCENARIO_1}}

1. {{TS_STEP_1}}
2. {{TS_STEP_2}}
3. {{TS_STEP_3}}

### {{ERROR_SCENARIO_2}}

1. {{TS_STEP_1}}
2. {{TS_STEP_2}}
