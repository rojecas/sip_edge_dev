---
# Frontend Architecture — SIP-Edge

> Documento técnico fundacional.
> Captura el contexto, las restricciones de hardware, las decisiones arquitectónicas,
> las justificaciones técnicas y el plan de implementación del frontend para SIP-Edge.
> Una vez aprobado, cada feature SDD de frontend lo referencia como base.

---

## 1. Contexto del proyecto

### 1.1 Estado actual

SIP-Edge es un Sistema Inteligente de Pesaje y Control de Materia Extraña que opera
en una EdgeBox-RPI-200 (SeeedStudio) en una planta industrial en Colombia.

| Aspecto | Estado |
|---------|--------|
| Backend (FastAPI) | Completo. 40+ endpoints REST, WebSocket /ws/scale, auth JWT con RBAC. Sirve en puerto 8000. |
| Base de datos | MariaDB 11.8.6 con 9 tablas. |
| LLM (llama.cpp) | Operativo en puerto 8080, 3 cores dedicados. Modelos Qwen 2.5 1.5B / Gemma 4. |
| Hardware integrado | RS485 (bascula DINI ARGEO DFW06L), RS232 (PC externo), modem GSM Quectel EC25, RTC PCF8563, WDT. |
| Frontend | No existe. Solo una pagina HTML inline de login (src/login_page.py, 240 lineas) que muestra el token JWT en texto plano. |
| Features | 12 features implementadas y cerradas (status: done). |
| SDD specs | 12 specs completos en harness/specs/. |

### 1.2 Por que ahora el frontend

Las 12 features del backend estan completas y verificadas. El sistema tiene API REST completa,
WebSocket para lecturas de bascula en tiempo real, autenticacion JWT con roles, y toda la logica
de negocio implementada (pesaje, emergencia, respaldos, SMS, IA). Lo unico que falta es la
interfaz de usuario que los operadores y administradores usaran en el kiosco industrial.

---

## 2. Restricciones de hardware (vinculantes)

### 2.1 EdgeBox-RPI-200

| Componente | Detalle |
|------------|---------|
| CPU | Raspberry Pi CM4 — 4x Cortex-A72 @ 1.5 GHz (aarch64) |
| RAM | 8 GB LPDDR4 |
| Almacenamiento | 32 GB eMMC |
| SO | Debian 13 (Trixie) aarch64, kernel 6.12 |

### 2.2 Distribucion critica de CPU

Este es el factor mas restrictivo para la arquitectura del frontend:

| Core 0-2 | llama.cpp (taskset -c 0-2, 3 cores dedicados) |
| Core 3 | FastAPI + MariaDB + Chromium (kiosco) + SO + servicios |

1 core para todo lo que no es LLM. Cada ciclo de CPU que gaste el frontend server-side
se lo quita al backend y a la base de datos.

### 2.3 Pantalla

| Aspecto | Valor |
|---------|-------|
| Tamano | 27 pulgadas |
| Resolucion | Minimo 1680 px de ancho (asumimos 1920x1080) |
| Tactil | No | Se interactua con mouse y teclado.

### 2.4 Red

El frontend se sirve en localhost:8000. No hay trafico de red externo para las vistas
del kiosco; todo es intra-dispositivo.

---

## 3. Flujo de trabajo del kiosco (acordado)

### 3.1 Ciclo completo

`
ENCENDIDO DEL EQUIPO
       |
       v
Debian 13 arranca
  -> systemd: mariadb + sip-edge (FastAPI)
  -> systemd: Chromium --kiosk apunta a http://localhost:8000
       |
       v
SPA carga en Chromium
  -> No hay JWT en localStorage
  -> Muestra MODAL LOGIN (usuario + contrasena)
  -> "Olvido su contrasena" abre flujo de reset via SMS (PIN 4 digitos)
       |
       | Login exitoso (POST /api/auth/login)
       v
Segun el rol del usuario:
  OPERATOR -> /kiosco (Vista de pesaje)
  ADMIN    -> /admin (Dashboard)
       |
       | BOTON LOGOUT (esquina superior derecha, siempre visible)
       v
Vuelve al MODAL LOGIN
  "Sesion cerrada"
  Listo para el siguiente analista
`

### 3.2 Decisiones de flujo

| Decision | Justificacion |
|----------|---------------|
| Modal login, no pagina separada | El login es parte del SPA. No hay navegacion a /login. El kiosco nunca "sale" de la aplicacion. |
| Logout siempre visible | Boton "Cerrar sesion" en esquina superior derecha de TODAS las vistas. Permite al analista salir al finalizar su turno. |
| Control de inactividad dual | Frontend monitorea tiempo desde ultima interaccion. Backend chequea iat del JWT. Si expira, 401 y frontend forza modal login. |
| Sin cierre del navegador | Kiosco corre en modo --kiosk. No se puede cerrar Chromium accidentalmente. Solo Logout. |

### 3.3 Mapa de rutas del SPA

| Ruta | Rol | Descripcion |
|------|-----|-------------|
| / | — | Redirige: si hay JWT -> /kiosco (operator) o /admin (admin). Si no -> modal login. |
| /kiosco | operator | Formulario de pesaje multipaso (vista principal) |
| /kiosco/historial | operator | Historial de pesajes del operador actual |
| /admin | admin | Dashboard con acceso rapido a todas las secciones |
| /admin/config | admin | Configuracion del sistema (RS485, RS232, GSM, session, scale) |
| /admin/usuarios | admin | CRUD de usuarios |
| /admin/haciendas | admin | CRUD de haciendas y suertes |
| /admin/reportes | admin | Plantillas de reportes programados |
| /admin/anomalias | admin | Historial de anomalias detectadas |
| /admin/backup | admin | Estado y ejecucion de backups |
| /admin/agente | admin | Consola de consultas al agente IA |

---

## 4. Decisiones arquitectonicas

### ADR-01: SPA compilado vs SSR

| Opcion | Descripcion | Veredicto |
|--------|-------------|-----------|
| HTMX + Jinja2 (SSR) | Backend renderiza HTML en cada interaccion. Sin build step. | RECHAZADO |
| SPA compilado (Svelte/Preact) | Frontend se descarga una vez como JS estatico y corre en el browser. Backend solo sirve JSON. | SELECCIONADO |

Justificacion:
- El rendering HTML en el backend compite por el core 3 (el mismo del backend + MariaDB).
- Un SPA traslada el rendering al browser (Chromium), liberando el core 3.
- El SPA se descarga una vez al arrancar el kiosco (~50KB). Despues, solo peticiones JSON.
- El WebSocket de bascula se integra de forma nativa sin recargar nada.
- Dropdowns en cascada Hacienda->Suerte, modales y flujos multi-paso son instantaneos.

### ADR-02: Svelte 5 como framework SPA

| Opcion | Bundle (min+gz) | Runtime | Veredicto |
|--------|-----------------|---------|-----------|
| Svelte 5 | ~0 KB (compilado a JS puro) | Ninguno | SELECCIONADO |
| Preact | ~3 KB | Virtual DOM minimo | Alternativa viable |
| React | ~42 KB | Virtual DOM pesado | RECHAZADO |
| Vue | ~33 KB | Reactivo pesado | RECHAZADO |
| Alpine + HTMX | ~21 KB | SSR en backend | RECHAZADO (ADR-01) |

Justificacion:
- Svelte compila el componente a JS plano. No hay runtime ni virtual DOM.
- El bundle final de una app Svelte de ~30 componentes suele ser < 80 KB.
- En una EdgeBox donde cada KB de RAM y cada ciclo de CPU cuentan, Svelte es optimo.
- Reactividad nativa con , sin librerias adicionales.

### ADR-03: Sin servidor web adicional (no nginx)

| Opcion | Descripcion | Veredicto |
|--------|-------------|-----------|
| FastAPI sirve el SPA directamente | Backend monta src/static/ y sirve index.html en /. Mismo puerto 8000. | SELECCIONADO |
| Contenedor nginx separado | Nginx sirve estaticos y proxy inverso a FastAPI. | RECHAZADO |

Justificacion:
- FastAPI ya corre en el core 3. Anadir nginx es otro proceso, mas RAM, mas mantenimiento.
- Los assets del SPA son ~50 KB. uvicorn los sirve perfectamente.
- Al estar en el mismo puerto (8000), no hay CORS, ni problemas de proxy, ni puertos extra.
- Configuracion trivial: StaticFiles montado en el mismo proceso.

### ADR-04: Vite como build tool

Vite es el build tool estandar para Svelte. Produce dist/ con index.html, bundle.js, bundle.css.
Tree-shaking elimina codigo no usado. Hot Module Replacement en desarrollo.

### ADR-05: Sin librerias externas de UI

No se incluye Bootstrap, Material UI, Tailwind (inicialmente).
Para una app industrial con ~11 vistas especificas, un framework CSS generico anade
peso innecesario. Se usa CSS vanilla con variables y componentes reutilizables.
Si el proyecto crece, se evalua Tailwind CSS v4 con purga en el build.

### ADR-06: WebSocket nativo, no librerias

El WebSocket del kiosco se conecta a /ws/scale?token=<jwt>.
Se usa la API WebSocket nativa del browser. No se necesita Socket.IO ni ninguna otra libreria.

### ADR-07: Sin router externo complejo

Con 11 rutas planas, svelte-spa-router (~3 KB) es suficiente. O un ruteo casero con
history.pushState. No se necesita React Router.

---

## 5. Stack tecnologico completo

### 5.1 Desarrollo (tu maquina)

| Herramienta | Proposito |
|-------------|-----------|
| Node.js 22+ (LTS) | Entorno de ejecucion para build |
| npm 11+ | Gestor de paquetes |
| Vite 6+ | Build tool, dev server, HMR |
| Svelte 5 | Framework SPA (compilado) |
| svelte-spa-router | Ruteo client-side |

### 5.2 Produccion (EdgeBox)

| Componente | Que se despliega |
|------------|------------------|
| dist/index.html | Punto de entrada del SPA. Sirve en / |
| dist/bundle.js | Todo el JS compilado (~50-80 KB) |
| dist/bundle.css | Todo el CSS compilado (~5-15 KB) |
| FastAPI (existente) | Sirve los assets estaticos en src/static/ |

No se necesita: Node.js, npm, nginx, ni ninguna dependencia runtime en la EdgeBox.

### 5.3 Lo que NO se incluye

| Tecnologia | Motivo |
|------------|--------|
| React | 42 KB runtime innecesario para EdgeBox |
| Vue | 33 KB runtime innecesario |
| Axios | fetch nativo basta |
| lodash | JS moderno (2026) cubre 95% de los casos |
| moment.js / date-fns | Intl.DateTimeFormat nativo |
| Socket.IO | WebSocket nativo basta |
| Redux / Zustand | Svelte 5 tiene reactividad nativa con  |
| TypeScript | Opcional en desarrollo, pero bundle final debe ser JS |
| Bootstrap / Material UI | CSS vanilla + diseno propio = menos peso |

---

## 6. Plan de implementacion: 3 features SDD

Se separa en 3 features para facilitar el desarrollo, debug y despliegue incremental.

### Feature 13: frontend_login_kiosk (prioridad maxima)

Que incluye:
- Scaffold del proyecto Svelte 5 + Vite
- Integracion con FastAPI (montar src/static/)
- Modal de login + flujo de reset de contrasena via SMS (PIN 4 digitos)
- Almacenamiento de JWT en localStorage
- Interceptor 401 para forzar re-login
- Control de inactividad (comparar iat del JWT con hora local)
- Boton Logout (siempre visible en esquina superior derecha)
- Vista /kiosco: formulario multipaso de pesaje
  - Campos: Tractomula, Vagon, Guia
  - Dropdown Hacienda -> Suerte (carga dinamica desde API)
  - 3 campos de peso (muestra, mineral, vegetal) con botones Tara/Leer
  - WebSocket /ws/scale -> peso en vivo con indicador de estable (is_stable)
  - Boton Confirmar -> POST /api/weighings
  - Boton Reset -> modal de confirmacion -> POST /api/weighings/reset
- Vista /kiosco/historial: tabla de pesajes del operador actual
- Banner de emergencia: polling GET /api/emergency/status cada 5s
- Si modo manual activo: campos de peso se vuelven editables manualmente
- Modal de solicitud de emergencia (seleccionar supervisor + motivo)
- Instrucciones de configuracion de Chromium kiosk en EdgeBox

Depende de: features 2, 5, 6, 9 (backend ya implementado)

### Feature 14: frontend_admin (segunda prioridad)

Que incluye:
- Vista /admin: dashboard con cards de acceso rapido
- Configuracion del sistema (/admin/config): RS485, RS232, GSM, botones Test
- Configuracion de session timeout + scale timeout
- CRUD de usuarios (/admin/usuarios): tabla, crear, editar, desactivar
- CRUD de haciendas (/admin/haciendas): tabla, crear, editar, soft-delete
- CRUD de suertes (/admin/suertes): tabla filtrable por hacienda
- Backups (/admin/backup): tabla de ultimos 10, boton ejecutar

Depende de: feature 13 (comparte scaffold, auth, layout base)

### Feature 15: frontend_analytics (tercera prioridad)

Que incluye:
- Plantillas de reportes (/admin/reportes): CRUD con modal de configuracion
- Historial de anomalias (/admin/anomalias): tabla paginada, expandir reporte LLM
- Consola AI (/admin/agente): interfaz tipo chat con el agente inteligente

Depende de: feature 14 (comparte layout admin)

---

## 7. Integracion con FastAPI

### 7.1 Montaje de estaticos

En src/main.py se anade:

`python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="src/static"), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    from fastapi.responses import FileResponse
    if full_path.startswith(("api/", "ws/", "login", "health")):
        return JSONResponse({"detail": "Not found"}, status_code=404)
    return FileResponse("src/static/index.html")
`

### 7.2 Pipeline de build y deploy

`ash
# 1. En tu maquina (desarrollo)
cd frontend
npm run build   # produce dist/

# 2. Copiar a la EdgeBox
scp -i ~/.ssh/sip_edge_edgebox dist/* sipedge@192.168.1.42:/home/sipedge/sip_edge/src/static/

# 3. En la EdgeBox
sudo systemctl restart sip-edge
`

---

## 8. Configuracion del kiosco Chromium (EdgeBox)

### 8.1 Instalar Chromium

`ash
sudo apt update
sudo apt install -y chromium-browser
`

### 8.2 Crear script de inicio

`ash
cat > /home/sipedge/start-kiosk.sh << 'SCRIPT'
#!/bin/bash
# Esperar a que el backend este listo
for i in {1..30}; do
  curl -sf http://localhost:8000/health > /dev/null 2>&1 && break
  sleep 1
done

# Lanzar Chromium en modo kiosco
chromium-browser \
  --kiosk \
  --no-first-run \
  --disable-infobars \
  --check-for-update-interval=604800 \
  http://localhost:8000
SCRIPT
chmod +x /home/sipedge/start-kiosk.sh
`

### 8.3 Servicio systemd

`ash
sudo tee /etc/systemd/system/sip-edge-kiosk.service << 'EOF'
[Unit]
Description=SIP-Edge Kiosk Browser
After=sip-edge.service
Requires=sip-edge.service
PartOf=sip-edge.service

[Service]
Type=simple
User=sipedge
Environment=DISPLAY=:0
Environment=XDG_SESSION_TYPE=x11
ExecStart=/home/sipedge/start-kiosk.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sip-edge-kiosk.service
sudo systemctl start sip-edge-kiosk.service
`

### 8.4 Servidor grafico (si no existe)

`ash
sudo apt install -y xserver-xorg-core xinit x11-xserver-utils
# Anadir al final de ~/.profile:
# [[ -z  &&  -eq 1 ]] && startx
`

---

## 9. UI/UX Principles

### 9.1 Diseno para kiosco industrial

| Principio | Aplicacion |
|-----------|------------|
| Alto contraste | Fondo oscuro (#1a1a2e), texto claro (#e0e0e0), acentos (#e94560). Consistente con login existente. |
| Fuentes grandes | Minimo 16px labels, 20px inputs, 32px peso en vivo. |
| Botones Tactil | No | Se interactua con mouse y teclado.
| Una accion principal por vista | En kiosco: "Confirmar pesaje" es el boton grande y destacado. |
| Feedback inmediato | Cada accion muestra exito/error sin recargar pagina. |
| Confirmacion destructiva | Reset pesaje, logout, desactivar usuario -> modal de confirmacion. |
| Modo kiosco sin escapes | Sin barra de direcciones, sin cerrar ventana. Solo Logout desde la app. |

### 9.2 Paleta de colores

`css
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
`

---

## 10. Cronograma sugerido

| Fase | Contenido | Depende de |
|------|-----------|------------|
| Semana 1-2 | Spec + implementacion Feature 13 (frontend_login_kiosk) | — |
| Semana 2 | Configuracion EdgeBox: Chromium kiosk + deploy | Feature 13 |
| Semana 3-4 | Spec + implementacion Feature 14 (frontend_admin) | Feature 13 |
| Semana 5 | Spec + implementacion Feature 15 (frontend_analytics) | Feature 14 |
| Semana 5-6 | Pruebas en EdgeBox con hardware real, ajustes | Todo |

---

## 11. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Chromium kiosco consume mucha RAM | Alta | Medio | Monitorear con htop. 8GB deberia ser suficiente. Si es problema, cambiar a surf o uzbl. |
| SPA no responde bien en pantalla 27 (mouse) | Baja | Medio | Probar con el raton real. El diseno funciona igual con eventos de mouse. |
| Build de Svelte 5 requiere Node.js 22+ | Baja | Bajo | nvm en maquina de desarrollo. No afecta a EdgeBox. |
| Operador cierra Chromium con Alt+F4 | Media | Alto | --kiosk atrapa Alt+F4 en la mayoria de versiones. Si no, configurar watchdog que reinicie Chromium. |

---

## 12. Documentos relacionados

| Documento | Ubicacion |
|-----------|-----------|
| Especificaciones SDD del backend | harness/specs/ |
| Arquitectura general | harness/docs/architecture.md |
| Convenciones de codigo | harness/docs/conventions.md |
| Entorno (EdgeBox) | harness/docs/environment.md |
| Specs SDD frontend (futuros) | harness/specs/13_frontend_login_kiosk/ |
|  | harness/specs/14_frontend_admin/ |
|  | harness/specs/15_frontend_analytics/ |

---

> **Fin del documento.**
> Una vez aprobado por el humano, se procede a la creacion del primer spec SDD
> para la feature 13_frontend_login_kiosk.
