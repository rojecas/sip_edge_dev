# Design — Frontend: Login, Kiosco de Pesaje y Logout

> Decisiones tecnicas detalladas para el SPA Svelte 5 + Vite que implementa
> el flujo completo del kiosco industrial. Referencia fundacional:
> `harness/docs/frontend-architecture.md` (ADR-01 a ADR-07).

---

## 1. Arquitectura general

```
Cliente (Chromium kiosco)              Servidor (FastAPI, puerto 8000)
┌──────────────────────────────┐      ┌──────────────────────────────────┐
│  SPA Svelte 5 (static JS)    │      │  src/main.py                     │
│  ┌────────────────────────┐  │      │  ┌────────────────────────────┐  │
│  │ AuthModal              │  │      │  │ StaticFiles("/static")     │  │
│  │ KioskForm              │  │──────│  │   └─ index.html            │  │
│  │ ScaleReader (WS)       │  │ WS   │  │   └─ bundle.js             │  │
│  │ HistoryTable           │  │◄────│  │   └─ bundle.css             │  │
│  │ EmergencyBanner        │  │──────│  ├────────────────────────────┤  │
│  │ EmergencyModal         │  │ REST │  │ /api/auth/*                │  │
│  │ InactivityGuard        │  │      │  │ /api/weighings/*           │  │
│  │ api.js (fetch wrapper) │  │      │  │ /api/emergency/*           │  │
│  │ router.js              │  │      │  │ /api/haciendas             │  │
│  └────────────────────────┘  │      │  │ /api/suertes               │  │
│  localStorage (JWT, role)   │      │  │ /ws/scale (WebSocket)       │  │
└──────────────────────────────┘      │  └────────────────────────────┘  │
                                      └──────────────────────────────────┘
```

### Rutas del SPA

| Ruta            | Componente     | Rol     | Descripcion                      |
|-----------------|----------------|---------|----------------------------------|
| `/`             | Redireccion    | —       | Redirige segun JWT o muestra login |
| `/kiosco`       | `KioskForm`    | operator | Formulario de pesaje             |
| `/kiosco/historial` | `HistoryTable` | operator | Historial del operador actual   |
| `/admin`        | `AdminPlaceholder` | admin  | Placeholder para Feature 14      |

---

## 2. Scaffold del proyecto Svelte 5 + Vite

```
sip_edge/
├── frontend/                     # NUEVO: proyecto Svelte 5 + Vite
│   ├── package.json
│   ├── vite.config.js
│   ├── svelte.config.js
│   ├── index.html                # Entry point del SPA
│   └── src/
│       ├── main.js               # Punto de entrada Svelte
│       ├── App.svelte            # Componente raiz: router + layout
│       ├── app.css               # Estilos globales + variables CSS
│       ├── stores/
│       │   └── auth.js           # Store reactivo de autenticacion
│       ├── lib/
│       │   ├── api.js            # Fetch wrapper con JWT + 401 interceptor
│       │   ├── ws.js             # WebSocket /ws/scale manager
│       │   ├── router.js         # Ruteo SPA (svelte-spa-router o manual)
│       │   ├── inactivity.js     # Control de inactividad (iat check)
│       │   └── constants.js      # URLs de API, colores, timeouts
│       └── components/
│           ├── AuthModal.svelte          # Modal de login + reset password
│           ├── ResetPinModal.svelte      # Modal ingreso PIN (olvido contrasena)
│           ├── ResetPasswordModal.svelte # Modal cambio de contrasena
│           ├── LogoutButton.svelte       # Boton "Cerrar sesion" fijo
│           ├── KioskLayout.svelte        # Layout base para vistas de kiosco
│           ├── AdminLayout.svelte        # Layout base para vistas admin (placeholder)
│           ├── KioskForm.svelte          # Formulario de pesaje multipaso
│           ├── ScaleReader.svelte        # Indicador de peso en vivo + estabilidad
│           ├── WeightField.svelte        # Componente reutilizable: campo peso + botones Tara/Leer
│           ├── ConfirmModal.svelte       # Modal generico de confirmacion
│           ├── HistoryTable.svelte       # Tabla de historial de pesajes
│           ├── EmergencyBanner.svelte    # Banner de modo manual emergency
│           ├── EmergencyModal.svelte     # Modal de solicitud de emergencia
│           ├── InactivityGuard.svelte    # Componente de control de inactividad
│           └── AdminPlaceholder.svelte   # Placeholder para vista /admin
│
├── src/
│   └── static/                   # NUEVO: destino del build del frontend
│       ├── index.html            # Copiado desde frontend/dist/
│       ├── bundle.js
│       ├── bundle.css
│       └── assets/
│
└── src/
    └── main.py                   # MODIFICADO: montar StaticFiles + catch-all route
```

---

## 3. Archivos modificados en `src/`

| Archivo | Cambio |
|---------|--------|
| `src/main.py` | **MODIFICADO**: Importar `StaticFiles`, montar en `/static`, anadir catch-all route `/{full_path:path}` que sirve `src/static/index.html` para rutas no-API. El orden de rutas importa: las rutas API/WS/login/health van primero. |

No se modifican otros archivos de `src/` ni de `tests/`. Esta feature es
exclusivamente frontend SPA + integracion estatica.

---

## 4. Manejo del JWT en localStorage

### Flujo de autenticacion

```
1. SPA carga → leer localStorage("sip_edge_token")
2. Si no existe → AuthModal visible (login)
3. Login exitoso → guardar { token, role } en localStorage
   → localStorage.setItem("sip_edge_token", access_token)
   → localStorage.setItem("sip_edge_role", role)
4. Cada peticion → api.js agrega Authorization: Bearer <token>
5. HTTP 401 → api.js elimina token, redirige a login
6. Logout → localStorage.removeItem("sip_edge_token" | "sip_edge_role")
7. Inactividad → comparar iat del JWT con Date.now()
   → si (now - iat) > session_timeout_minutes → logout automatico
```

### Store reactivo `stores/auth.js`

```javascript
// store reactivo que contiene:
// { token: string|null, role: string|null, user: string|null }
// Exporta: login(), logout(), isAuthenticated(), getToken(), getRole()
```

---

## 5. Fetch wrapper (`lib/api.js`)

```javascript
/**
 * Wrapper sobre fetch que:
 * - Agrega automáticamente Authorization: Bearer <token> desde localStorage
 * - Intercepta HTTP 401 → llama a auth.logout() y redirige a login
 * - Parsea JSON automáticamente
 * - Lanza errores con mensaje del backend
 *
 * Funciones exportadas:
 *   api.get(url)          → GET request
 *   api.post(url, body)   → POST request
 *   api.put(url, body)    → PUT request
 *   api.del(url)          → DELETE request
 */
```

---

## 6. Integracion WebSocket `/ws/scale` (`lib/ws.js`)

```javascript
/**
 * Módulo WebSocket manager:
 * - Conecta a /ws/scale?token=<jwt>
 * - Reconexión automática hasta 5 intentos (intervalo 2s)
 * - Store reactivo scaleStore: { net_weight, is_stable, unit, connected }
 * - Callback onMessage para actualizar componentes
 * - Cierra conexión al hacer logout
 */
```

### Formato del mensaje WebSocket (desde backend)

```json
{
  "type": "scale_reading",
  "data": {
    "net_weight": 150.500,
    "is_stable": true,
    "unit": "kg"
  }
}
```

---

## 7. Control de inactividad (`lib/inactivity.js`)

Basado en frontend-architecture.md seccion 3.1:

1. Al autenticarse, decodificar el payload del JWT (base64) y extraer `iat`.
2. Obtener `session_timeout_minutes` del payload o valor por defecto (30 min).
3. En cada navegacion, calcular: `(Date.now()/1000 - iat) > session_timeout * 60`.
4. Si supera el timeout → eliminar token → mostrar modal login con mensaje
   "Sesion expirada por inactividad".
5. El backend tambien chequea `iat` via `check_inactivity` dependency.

Este es un mecanismo dual (frontend + backend) para robustez.

---

## 8. API calls consumidas por el SPA

| Metodo | Endpoint | Proposito | Componente |
|--------|----------|-----------|------------|
| POST | `/api/auth/login` | Login | `AuthModal` |
| POST | `/api/auth/verify-reset-pin` | Verificar PIN reset | `ResetPinModal` |
| POST | `/api/auth/complete-reset` | Cambiar contrasena | `ResetPasswordModal` |
| GET | `/api/haciendas?page=1&page_size=100` | Listar haciendas activas (paginado) | `KioskForm` |
| GET | `/api/suertes?hacienda_id=X` | Listar suertes por hacienda | `KioskForm` |
| POST | `/api/weighings` | Persistir pesaje | `KioskForm` (Confirmar) |
| POST | `/api/weighings/reset` | Limpiar formulario | `KioskForm` (Reset) |
| GET | `/api/weighings?page=1&page_size=20&start_date=&end_date=` | Listar pesajes paginados del operador | `HistoryTable` |
| GET | `/api/emergency/status` | Estado modo manual (polling 5s) | `EmergencyBanner` |
| GET | `/api/emergency/admins` | Listar supervisores | `EmergencyModal` |
| POST | `/api/emergency/request` | Solicitar modo manual | `EmergencyModal` |
| WS | `/ws/scale?token=<jwt>` | Peso en vivo | `ScaleReader` |

---

## 9. Arquitectura de componentes Svelte

### Arbol de componentes

```
App.svelte
├── AuthModal.svelte                    [visible solo si no autenticado]
│   ├── ResetPinModal.svelte            [modal "Olvido su contrasena" paso 1]
│   └── ResetPasswordModal.svelte       [modal "Olvido su contrasena" paso 2]
│
├── InactivityGuard.svelte              [siempre montado, chequea iat]
│
├── {#if role === "operator"}
│   KioskLayout.svelte
│   ├── LogoutButton.svelte             [esquina superior derecha]
│   ├── EmergencyBanner.svelte          [arriba, condicional]
│   │   └── EmergencyModal.svelte       [modal solicitud]
│   ├── {currentRoute === "/kiosco"}
│   │   └── KioskForm.svelte
│   │       ├── ScaleReader.svelte      [peso en vivo + estabilidad]
│   │       ├── WeightField.svelte x3   [muestra, mineral, vegetal]
│   │       └── ConfirmModal.svelte     [confirmacion reset]
│   └── {currentRoute === "/kiosco/historial"}
│       └── HistoryTable.svelte
│
├── {#if role === "admin"}
│   AdminLayout.svelte
│   ├── LogoutButton.svelte             [esquina superior derecha]
│   └── AdminPlaceholder.svelte         ["Panel de Administracion - Proximamente"]
```

### Responsabilidades de cada componente

| Componente | Responsabilidad |
|------------|-----------------|
| `App.svelte` | Store auth, routing condicional (login vs app), montar InactivityGuard |
| `AuthModal.svelte` | Formulario login, enlace "Olvido su contrasena" |
| `ResetPinModal.svelte` | Modal PIN 4 digitos, dispara verify-reset-pin |
| `ResetPasswordModal.svelte` | Modal nueva contrasena, dispara complete-reset |
| `LogoutButton.svelte` | Boton fijo + modal confirmacion, llama auth.logout() |
| `KioskLayout.svelte` | Layout con header (usuario, logout, emergency banner) + slot para contenido |
| `AdminLayout.svelte` | Layout admin placeholder |
| `KioskForm.svelte` | Formulario completo: campos texto, dropdowns, pesos, botones Confirmar/Reset |
| `ScaleReader.svelte` | Indicador peso en vivo, indicador estabilidad, subscripcion WebSocket |
| `WeightField.svelte` | Input numerico + botones Tara/Leer, prop: `fieldName`, bind:value |
| `ConfirmModal.svelte` | Modal generico con titulo, mensaje, botones Confirmar/Cancelar. Props: `show`, `title`, `message`, `onConfirm`, `onCancel` |
| `HistoryTable.svelte` | Tabla responsive con datos de pesajes, controles de paginacion, filtro por rango de fechas, columna de acciones (opcional) |
| `EmergencyBanner.svelte` | Banner condicional + polling 5s + boton "Solicitar" |
| `EmergencyModal.svelte` | Dropdown supervisores, campo motivo, boton enviar |
| `InactivityGuard.svelte` | Timer que chequea iat periodicamente, llama logout si expirado |
| `AdminPlaceholder.svelte` | Pagina placeholder para Feature 14 |

---

## 10. Paleta de colores (consistente con login existente)

```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-input: #0f3460;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0b0;
  --accent: #e94560;
  --accent-hover: #c73652;
  --success: #51cf66;
  --error: #ff6b6b;
  --warning: #ffd43b;
  --border: #333;
}
```

Identica a la paleta definida en `frontend-architecture.md` seccion 9.2 y
consistente con `src/login_page.py` (los estilos inline del login actual).

---

## 11. Integracion con FastAPI (`src/main.py`)

Se modifica `src/main.py` para:

1. **Importar** `StaticFiles` y `FileResponse`:
   ```python
   from fastapi.staticfiles import StaticFiles
   from fastapi.responses import FileResponse, JSONResponse
   ```

2. **Montar StaticFiles** (despues de la definicion de `app` pero antes de
   las rutas catch-all):
   ```python
   import os
   static_dir = os.path.join(os.path.dirname(__file__), "static")
   if os.path.isdir(static_dir):
       app.mount("/static", StaticFiles(directory=static_dir), name="static")
   ```

3. **Anadir catch-all route** (AL FINAL, despues de todas las rutas API):
   ```python
   @app.api_route("/{full_path:path}", methods=["GET"])
   async def serve_spa(full_path: str):
       if full_path.startswith(("api/", "ws/", "login", "health")):
           return JSONResponse({"detail": "Not found"}, status_code=404)
       return FileResponse(os.path.join(static_dir, "index.html"))
   ```

   > **Orden critico**: Las rutas `/api/...`, `/ws/...`, `/login`, `/health`
   > se registran ANTES que la catch-all. FastAPI respeta el orden de
   > registro. Las rutas API/WS nunca deben caer en la catch-all.

4. **Mantener endpoint `/login` existente** (para compatibilidad). No
   eliminarlo. El SPA lo reemplazara visualmente.

---

## 12. Pipeline de build y deploy

### Desarrollo (maquina local)

```bash
# En frontend/
cd frontend
npm install          # Una vez
npm run dev          # Vite dev server con HMR (puerto 5173)
```

### Produccion

```bash
# 1. Build
cd frontend
npm run build        # produce frontend/dist/

# 2. Copiar a src/static/
Copy-Item -Path "frontend/dist/*" -Destination "src/static/" -Recurse -Force

# 3. En EdgeBox (o via Docker)
sudo systemctl restart sip-edge
```

### Pipeline CI (recomendado)

```
git push → build frontend → Copy-Item a src/static/ → docker compose restart
```

---

## 13. Alternativa descartada: HTMX + Jinja2 (SSR)

**Alternativa:** Usar HTMX con Jinja2 templates renderizados en el servidor,
donde cada interaccion del usuario genera una peticion HTTP y el backend
devuelve HTML parcial.

**Descartada por:**
1. **CPU**: Rendering HTML en backend compite por el core 3 (el mismo de
   FastAPI + MariaDB). El frontend-architecture.md ADR-01 documenta que
   solo 1 core esta disponible para todo lo que no es LLM.
2. **WebSocket**: HTMX no tiene soporte nativo para WebSocket. El peso en
   vivo de la bascula requeriria polling HTTP cada ~200ms, generando
   trafico extra y latencia.
3. **Experiencia de usuario**: Los dropdowns en cascada Hacienda→Suerte,
   modales multi-paso, y actualizaciones en tiempo real son mas lentos y
   complejos con SSR.
4. **Bundle**: Svelte 5 compila a ~50-80 KB sin runtime, una transferencia
   unica. HTMX + Alpine.js + Jinja2 requieren ~21 KB mas overhead de
   servidor por cada request.

**Beneficio de la alternativa elegida (Svelte 5 SPA):**
- Cero rendering server-side del HTML de la UI.
- WebSocket nativo para peso en vivo.
- Interacciones instantaneas sin recargar.
- Bundle pequeno que se descarga una vez al arrancar el kiosco.

---

## 14. Dependencias npm

| Paquete | Version | Proposito |
|---------|---------|-----------|
| `svelte` | ^5.x | Framework SPA |
| `@sveltejs/vite-plugin-svelte` | ^5.x | Plugin Vite para Svelte |
| `vite` | ^6.x | Build tool |
| `svelte-spa-router` | ^4.x | Ruteo client-side (opcional, si no se implementa router manual) |

Sin dependencias de UI, sin librerias de WebSocket, sin librerias de
autenticacion. Todo con API nativas del browser.

---

## 15. Persistencia

Esta feature NO modifica la base de datos. Toda la persistencia es
client-side (localStorage para JWT y rol) o via API existente en el backend.

---

## 16. github_labels

```
frontend, svelte, kiosk, login, weighing
```

---

## 17. Pagination and Date Filter Design

### 17.1 API Response Format (Backend Contract)

Todos los endpoints de listado que devuelven multiples registros DEBEN
soportar el siguiente formato de respuesta paginada:

```json
{
  "items": [ ... ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

### 17.2 Query Parameters

| Parametro | Tipo | Default | Descripcion |
|-----------|------|---------|-------------|
| `page` | int | 1 | Numero de pagina (1-indexed) |
| `page_size` | int | 20 | Registros por pagina (max 100) |
| `sort_by` | string | "fecha" | Columna de ordenamiento |
| `sort_order` | string | "desc" | "asc" o "desc" |
| `start_date` | string (date) | null | Filtro fecha inicio (YYYY-MM-DD) |
| `end_date` | string (date) | null | Filtro fecha fin (YYYY-MM-DD) |

### 17.3 Modificaciones al backend

Se deben modificar los siguientes archivos de `src/`:

**`src/weighings.py`**: El endpoint `GET /api/weighings` debe:
1. Aceptar query params: `page` (int, default 1), `page_size` (int, default 20),
   `start_date` (string, opcional), `end_date` (string, opcional),
   `sort_by` (string, default "fecha"), `sort_order` (string, default "desc")
2. Filtrar por `usuario_id` si el rol es "operator"
3. Filtrar por rango de fechas si `start_date` y/o `end_date` estan presentes
4. Paginar los resultados y devolver formato `{items, total, page, page_size, total_pages}`

**`src/haciendas.py`**: El endpoint `GET /api/haciendas` debe:
1. Aceptar query params: `page` (int, default 1), `page_size` (int, default 100),
   `sort_by` (string, default "nombre"), `sort_order` (string, default "asc")
2. Paginar los resultados y devolver formato `{items, total, page, page_size, total_pages}`

### 17.4 Frontend: HistoryTable pagination controls

El componente `HistoryTable.svelte` debe incluir:
- Selector de rango de fechas (dos inputs `type="date"`) encima de la tabla
- Boton "Filtrar" que dispara la busqueda con los parametros
- La tabla muestra la pagina actual de resultados
- Controles de paginacion debajo de la tabla:
  - "Anterior" / "Siguiente" botones
  - "Pagina X de Y"
  - Selector de page_size (10, 20, 50)
- Estado de carga durante la peticion
- Mensaje "No se encontraron registros" si la busqueda filtrada da 0 resultados

### 17.5 Frontend: Haciendas dropdown

El dropdown de Haciendas en `KioskForm.svelte` debe:
- Cargar la primera pagina de haciendas al montar el componente
- Si hay mas paginas, cargarlas en segundo plano para tener el listado completo
- Opcionalmente, implementar busqueda incremental mientras el usuario escribe
- Manejar estados de carga y error
