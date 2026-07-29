# SIP-Edge — Sistema Inteligente de Pesaje y Control de Materia Extraña

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Svelte](https://img.shields.io/badge/Svelte-5-ff3e00.svg)](https://svelte.dev)
[![License](https://img.shields.io/badge/license-proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.4.0-brightgreen.svg)](CHANGELOG.md)

**Plataforma de _edge computing_ para laboratorios de control de calidad agroindustrial.**
Opera 100% offline en hardware ARM de bajo consumo. Inteligencia artificial local para
consulta de datos en lenguaje natural, detección automática de anomalías y comunicación
bidireccional vía SMS.

---

## ¿Qué hace SIP-Edge?

```
    ┌──────────┐      RS485       ┌──────────────┐      RS232      ┌───────────┐
    │ Báscula  │─────────────────▶│  EdgeBox ARM │────────────────▶│ PC externo│
    │ DINI     │    (lectura      │  (SIP-Edge)  │   (trama CSV)  │ (sistema  │
    │ ARGEO    │     automática)  │              │                │  legacy)  │
    └──────────┘                  └──────┬───────┘                └───────────┘
                                        │
                                   SMS (4G)
                                        │
                             ┌──────────┴──────────┐
                             │  Supervisores y      │
                             │  corresponsales       │
                             │  "¿cómo va el turno?" │
                             └──────────────────────┘
```

1. Un operador pesa en la báscula — el peso se captura automáticamente (sin teclear).
2. El sistema persiste el registro en base de datos y transmite la trama al PC externo.
3. Una IA local analiza el pesaje en 3 capas y detecta anomalías en tiempo real.
4. Supervisores consultan datos en **lenguaje natural** vía SMS, sin comandos ni formatos.
5. Reportes programados llegan automáticamente a los destinatarios configurados.

---

## Stack Tecnológico

| Capa | Tecnología | Notas |
|------|-----------|-------|
| **Backend** | Python 3.13 + FastAPI + uvicorn | API REST + WebSocket para báscula en vivo |
| **Frontend** | Svelte 5 + Vite | SPA en modo kiosco industrial (Chromium) |
| **Base de datos** | MariaDB 11.8 | ORM SQLAlchemy 2.0 |
| **IA Local** | llama.cpp + Qwen 2.5 1.5B | 16 herramientas SQL parametrizadas |
| **Comunicación** | ModemManager + Quectel EC25 | SMS bidireccional vía red 4G |
| **Hardware** | EdgeBox-RPI-200 (CM4, 8 GB RAM) | Bajo consumo (~15W), sin ventilador |
| **SO** | Debian 13 (Trixie) aarch64 | systemd, watchdog por hardware |
| **Desarrollo** | Docker Compose | Backend + MariaDB + phpMyAdmin |

---

## Requisitos

### Hardware
- EdgeBox-RPI-200 o Raspberry Pi CM4 con 4+ GB RAM
- Báscula DINI ARGEO DFW06L (o compatible con protocolo RS485)
- Módem 4G Quectel EC25 (o compatible con ModemManager)
- Pantalla táctil (7" o 10") para kiosco

### Software
- Debian 13 aarch64
- Python 3.13+
- MariaDB 11.8+
- llama.cpp + modelo Qwen 2.5 1.5B (GGUF, ~1.1 GB)
- ModemManager + SIM con plan de datos y SMS

### Dependencias Python
```
fastapi>=0.115        pyserial>=3.5          sqlalchemy>=2.0
uvicorn>=0.34         httpx>=0.28            pymysql>=1.1
python-jose>=3.3      bcrypt>=4.2            pydantic>=2.10
pyyaml>=6.0           python-dotenv>=1.0     websockets>=14
```

---

## Despliegue Rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/rojecas/sip_edge.git /home/sipedge/sip_edge
cd /home/sipedge/sip_edge

# 2. Configurar variables de entorno
cp .env.example .env
nano .env   # editar credenciales DB, secretos JWT

# 3. Instalar dependencias
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar hardware
sudo cp deploy/99-scale-ports.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules

# 5. Crear base de datos y ejecutar migraciones
sudo mysql -e "CREATE DATABASE IF NOT EXISTS sip_edge"
sudo mysql -e "CREATE USER IF NOT EXISTS sip_user@localhost IDENTIFIED BY 'password'"
sudo mysql -e "GRANT ALL ON sip_edge.* TO sip_user@localhost"
python database/migrations/run_all.py

# 6. Generar build del frontend (solo si se modificó)
cd frontend && npm install && npm run build && cd ..

# 7. Iniciar
sudo systemctl enable --now sip-edge
```

### Docker Compose (desarrollo local)

```bash
docker compose up -d
# Backend: http://localhost:8000
# phpMyAdmin: http://localhost:8080
```

---

## Estructura del Proyecto

```
sip_edge/
├── src/                   ← Backend (31 módulos Python)
│   ├── main.py            ← Punto de entrada FastAPI
│   ├── auth.py            ← Autenticación JWT + RBAC
│   ├── scale.py           ← Integración serial RS485
│   ├── weighings.py       ← Captura y persistencia de pesajes
│   ├── rs232.py           ← Transmisión RS232 a PC externo
│   ├── agent_orchestrator.py ← Orquestador IA central
│   ├── sms_*.py           ← Servicio SMS (envío, recepción, persistencia)
│   ├── emergency_mode.py  ← Modo manual de emergencia
│   ├── backup.py          ← Sistema de respaldos
│   ├── models.py          ← Modelos SQLAlchemy (12 tablas)
│   └── tools/             ← Herramientas (balanza virtual, datasets)
├── frontend/              ← SPA Svelte 5 (kiosco + admin)
├── tests/                 ← Suite de tests (28 archivos, ~15,000 líneas)
├── docs/                  ← Documentación
│   ├── cliente/           ← Entregables (informes, ERS, SDD, manuales)
│   ├── tecnica/           ← Guías de configuración y despliegue
│   └── referencia/        ← Manuales de hardware
├── database/              ← Migraciones + seeds
├── scripts/               ← Herramientas (backup, generación datos, diagnóstico)
├── deploy/                ← Reglas udev para puertos seriales
├── compose.yml            ← Docker Compose (desarrollo)
├── Dockerfile             ← Imagen de producción
└── requirements.txt       ← Dependencias Python
```

---

## Seguridad

| Control | Implementación |
|---------|---------------|
| **Autenticación** | JWT con firma HMAC-SHA256. Hash bcrypt para contraseñas. |
| **RBAC** | 3 roles: admin (total), operator (solo pesaje), corresponsal (solo consultas SMS) |
| **Bloqueo por inactividad** | Timeout configurable. Forza logout del kiosco. |
| **Inyección SQL** | ORM parametrizado (SQLAlchemy). Nunca SQL crudo desde input de usuario. |
| **Alucinación IA** | Arquitectura Function Calling estricta: el LLM nunca genera valores numéricos. Solo parafrasea resultados reales de la BD. Temperatura 0.1. |
| **Credenciales** | Secretos en `.env` (permisos 600). `config.yaml` para parámetros no sensibles. |

---

## Operación Diaria

### Panel de Administración (`/admin`)
- **Dashboard:** acceso rápido a todas las secciones
- **Usuarios:** crear, editar, activar/desactivar
- **Haciendas/Suertes:** CRUD con borrado lógico
- **Configuración:** puertos RS485/RS232/GSM, timeouts, prueba de conectividad
- **Backups:** historial, ejecución manual, exportación USB/SD
- **Reportes:** plantillas programadas con métricas seleccionables
- **Anomalías:** historial de detecciones con detalle Z-Score
- **Consola IA:** interfaz tipo chat para consultas directas

### Kiosco de Pesaje (`/kiosco`)
- Login con credenciales o flujo de olvido de contraseña (PIN SMS)
- Formulario multipaso: Tara → Leer Muestra → Confirmar
- Peso en vivo vía WebSocket desde la báscula
- Resets individuales por campo de peso
- Notas de muestra colapsables
- Historial de pesajes del operador
- Banner de emergencia con solicitud al supervisor

### Consultas SMS
```
Operador:  "¿cómo va el turno de hoy?"
SIP-Edge: "Turno mañana 22 jul: 47 pesajes, 523.8 kg total. Promedio 11.1 kg/pesaje."

Operador:  "¿y ayer?"
SIP-Edge: "Ayer 21 jul: 51 pesajes, 567.3 kg total."

Operador:  "¿cuál fue el promedio de mineral en hacienda 131 esta semana?"
SIP-Edge: "Promedio mineral hacienda 131, 15-21 jul: 0.187 kg/muestra."
```

### Comandos SMS del Sistema
| Comando | Acción |
|---------|--------|
| `manual on` | Activar modo manual de emergencia (supervisor) |
| `manual off` | Desactivar modo manual |
| `extender N` | Extender modo manual N minutos |
| `reset password <usuario>` | Iniciar restablecimiento de contraseña (admin) |

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Líneas de código (back + front + tests) | ~25,000 |
| Endpoints REST | 45+ |
| Tablas de base de datos | 12 |
| Herramientas SQL (IA) | 16 |
| Capas de detección de anomalías | 3 |
| Modelo LLM | Qwen 2.5 1.5B Q4_K_M (1.1 GB) |
| Velocidad de inferencia | ~3.6 t/s generación, ~7.7 t/s prompt |
| RAM del modelo | ~1.1 GB |
| Latencia consulta SMS | 5-15 segundos |

---

## Documentación

Ver `docs/cliente/` para la documentación entregable completa:
- **Informes 01-06** — Hardware, entorno, backend, frontend, IA, trazabilidad
- **ERS v1.2, v1.3, v1.4** — Especificación de Requisitos de Software
- **SDD Rev1.1** — Documento de Diseño de Software
- **Manual de Instalación** — Despliegue paso a paso en un EdgeBox nuevo
- **Manual de Administración** — Operación diaria del sistema

Ver `docs/tecnica/` para guías de configuración del EdgeBox, modem, y herramientas.

---

## Licencia

Software propietario. Desarrollado para Ingenio Mayagüez S.A., 2026.
Todos los derechos reservados. Prohibida su reproducción total o parcial sin autorización.
