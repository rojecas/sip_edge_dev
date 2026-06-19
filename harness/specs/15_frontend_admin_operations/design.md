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
| `frontend/src/components/AdminBackup.svelte` | Field name mismatch: backend ingles vs frontend español (ver seccion 7) |
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
- Problema conocido: field name mismatch (español vs ingles) entre frontend y backend
  — ver seccion 7 para detalle

## 6. Contrato API

Todos los endpoints ya existen en el backend. La respuesta esperada se documenta
para que el implementer verifique el mapeo correcto en el frontend.

### GET /api/config
```
Respuesta: {
  rs485:     { path: string, baudrate: int, parity: string, data_bits: int, stop_bits: float },
  rs232:     { path: string, baudrate: int, parity: string, data_bits: int, stop_bits: float },
  gsm:       { modem_index: int },
  last_updated: string (ISO 8601),
  session_timeout_minutes?: int,
  scale_timeout_seconds?: int
}
```

### PUT /api/config
```
Request:  { rs485: {...}, rs232: {...}, gsm: {...} }
Respuesta 200: mismo schema que GET /api/config
Respuesta 422: { detail: string }
```

### POST /api/config/test/{port}
```
port ∈ { rs485, rs232, gsm }
Respuesta ok:    { status: "ok" }
Respuesta fail:  { status: "fail", detail: string }
Respuesta 404:   { detail: string } (port invalido)
```

### PUT /api/setup/session
```
Request:  { session_timeout_minutes: int (gt: 0) }
Respuesta 200: { session_timeout_minutes: int }
```

### PUT /api/setup/scale
```
Request:  { timeout_seconds: int (ge: 1, le: 10) }
Respuesta 200: { timeout_seconds: int }
```

### GET /api/backup/status
```
Respuesta: BackupLog[] (array directo, NO `{items: [...]}`)
BackupLog: {
  id: int,
  filename: string,
  file_size: int | null,
  local_checksum: string | null,
  usb_copied: bool,
  usb_checksum: string | null,
  error_message: string | null,
  created_at: string (ISO 8601)
}
NOTA: El backend retorna array directo, no objeto paginado.
El AdminBackup.svelte usa `result.items || result || []` para cubrir ambos formatos.
```

### POST /api/backup/run
```
Respuesta 202: { status: "accepted", message: "Backup started" }
```

## 7. Estado actual del codigo

El codigo existe y compila. Problemas conocidos del desarrollo de feature 14:

- **AdminBackup — field name mismatch (CRITICO):** El componente AdminBackup.svelte
  espera campos en español (`archivo`, `tamano`, `checksum_local`, `copia_usb`,
  `checksum_usb`, `error`, `fecha`) pero el backend retorna campos en ingles
  (`filename`, `file_size`, `local_checksum`, `usb_copied`, `usb_checksum`,
  `error_message`, `created_at`). Esto causa que todas las columnas de la tabla
  muestren "—" aunque existan registros de backup.
- Verificar que el manejo de errores HTTP 422 preserva los cambios del formulario
  en AdminConfig.svelte.

## 8. Persistencia

Esta feature NO modifica la base de datos.

## 9. github_labels

```
frontend, svelte, admin, config, backup, serial
```
