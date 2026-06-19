# Design — Frontend Admin: Configuración y Backup

> Feature 15 (14b) — Panel de configuración del sistema y backups. Código
> fuente existente del desarrollo de feature 14. Esta feature verifica y
> corrige el funcionamiento de AdminConfig y AdminBackup.

---

## 1. Arquitectura general

```
App.svelte
└── AdminLayout.svelte         [de Feature 14 / 14a]
    ├── Sidebar                [de Feature 14 / 14a]
    └── Slot de contenido      [segun currentRoute]
        ├── AdminConfig.svelte [/admin/config, Feature 15]
        ├── AdminBackup.svelte [/admin/backup, Feature 15]
        └── ... otros          [features 20 / 14c]
```

## 2. Archivos a verificar (ya existen)

| Archivo                             | Proposito                                    |
|-------------------------------------|----------------------------------------------|
| `frontend/src/components/AdminConfig.svelte`  | Formulario de configuracion RS485, RS232, GSM + timeouts |
| `frontend/src/components/AdminBackup.svelte`  | Panel de backups con historial y ejecucion   |

## 3. Archivos a modificar (si es necesario)

| Archivo                             | Posible correccion                            |
|-------------------------------------|-----------------------------------------------|
| `frontend/src/components/AdminBackup.svelte` | Problema conocido: extraer `.items` de respuesta API |
| `frontend/src/lib/constants.js`     | Endpoints de config y backup (verificar)      |

## 4. Backend: NO se modifican archivos en `src/` ni `tests/`

Todos los endpoints ya existen. Esta feature es frontend-only.

## 5. Detalle de componentes a verificar

### 5.1 AdminConfig.svelte

Formulario dividido en 3 secciones con bordes/cards:
1. **RS485**: path (text) + 4 selects (baudrate, parity, data_bits, stop_bits) + boton Test
2. **RS232**: misma estructura que RS485 + boton Test
3. **GSM**: modem_index (number) + boton Test
4. **Timeouts**: session_timeout (number) + scale_timeout (number 1-10)

Comportamiento a verificar:
- Carga `GET /api/config` al montar
- Guardado de configuracion (PUT /api/config)
- Guardado individual de timeouts (PUT /api/setup/session, PUT /api/setup/scale)
- Tests de puertos con resultado inline (verde/rojo)
- Estados: loading, submitting, success, error

### 5.2 AdminBackup.svelte

Tabla con historial de backups + botones:
- Carga `GET /api/backup/status` al montar
- Tabla con columnas: ID, Archivo, Tamano, Checksum Local, Copia USB, Checksum USB, Error, Fecha
- Boton "Ejecutar Backup" → POST /api/backup/run con deshabilitado 30s
- Boton "Refrescar" → recarga GET /api/backup/status
- Manejo de errores: 4xx/5xx no deshabilita boton
- Problema conocido: verificar que se extrae `.items` correctamente de la respuesta

## 6. Estado actual del codigo

El codigo existe y compila. Problemas conocidos del closure de feature 14:
- AdminBackup puede no extraer `.items` correctamente de la respuesta API
- Verificar que el manejo de errores HTTP 422 preserva los cambios del formulario

## 7. Persistencia

Esta feature NO modifica la base de datos.

## 8. github_labels

```
frontend, svelte, admin, config, backup, serial
```
