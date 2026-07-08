# Changelog — sip_edge

> All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-07-08

### Added
- Feature #13 — Frontend - Login, Kiosco de Pesaje y Logout: SPA con Svelte 5, modal login JWT, formulario multipaso de pesaje con WebSocket de báscula en vivo, historial de pesajes, emergencia y logout.
- Feature #14 — Frontend Admin - Dashboard y Navegación (14a): dashboard con cards de acceso rápido, sidebar de navegación lateral, enrutamiento RBAC, navegación directa por URL e interceptor 401.
- Feature #15 — Frontend Admin - Configuración y Backup (14b): panel de configuración del sistema (RS485, RS232, GSM) con pruebas, panel de backups con historial y ejecución.
- Feature #16 — Frontend Admin - CRUD de Datos Maestros (14c): CRUD completo de usuarios, haciendas (soft-delete) y suertes con paginación, auto-recarga y manejo de errores de red.
- Feature #18 — Campo tipo de cosecha en registro de pesaje: columna tipo_cosecha ENUM con 6 valores, select en formulario de kiosco y filtro en análisis estadísticos.
- Feature #21 — Paginación en endpoints y tablas de Usuarios y Backups: soporte de paginación en GET /api/users y GET /api/backup/status con controles de paginación en UI.
- Feature #24 — Reset Individual de Pesos en Kiosko de Pesaje: botón de reset individual para cada campo de peso (muestra, mineral, vegetal) en lugar de reset general.
- Feature #25 — Balanza Virtual DINI ARGEO DFWLI-2 para Desarrollo y Pruebas: herramienta standalone que simula protocolo DINI ARGEO vía puerto serial, con REPL interactivo, 5 datasets CSV y simulación de estabilidad.

### Fixed
- Bug #19 — Watchdog mal configurado: servicio reiniciado cada 30s por falta de sd_notify — implementado sd_notify() con systemd-healthcheck.
- Bug #20 — AdminSuertes.svelte no carga las suertes: corregido parsing de respuesta del endpoint GET /api/suertes (array plano vs paginado).
- Bug #22 — Campo phone no expuesto y document ambiguo: expuesto phone en API CRUD de usuarios y renombrado document a employee_code en BD, API y frontend.
- Bug #23 — Modo manual de emergencia no se activa vía SMS: corregida excepción silenciosa en activate() con guard callable y logging con contexto.

## [1.1.0] - 2026-06-17

### Added
- Feature #14 — Frontend - Panel de Administración: SPA administrativo con dashboard central, configuración del sistema (puertos RS485, RS232, GSM con pruebas), CRUD de usuarios, CRUD de haciendas y suertes (soft-delete), y panel de backups con historial y ejecución.

## [1.0.0] - 2026-06-16

### Added
- Feature #7 — Servicio de Notificaciones y Reportes SMS: envío de SMS vía módem GSM (Quectel EC25) con alertas de seguridad por intentos fallidos de login, reportes programados de resumen de turno y persistencia de configuración SMS.
- Feature #9 — Modo Manual de Emergencia: solicitud desde kiosco con autorización vía SMS, duración configurable, extensión/suspensión remota, persistencia ante cortes de energía y auditoría completa en BD.
- Feature #11 — Transmisión de Datos a PC vía RS232: envío de trama CSV de 15 campos al PC externo tras cada pesaje confirmado, con soporte para DEV_MODE y manejo de errores sin interrupción del flujo.
- Feature #12 — Restablecimiento de Contraseña vía SMS: generación de PIN numérico de 4 dígitos con expiración de 1 hora, enlace "Olvidó su contraseña" en login, modal de cambio de contraseña y dispatcher compartido de SMS entrantes.
- Feature #8 — Sistema Inteligente de Reportería y Detección de Anomalías (TinyLLM): reportes programados configurables, detección de anomalías en 3 capas (Z-Score, relacional, temporal), consultas ad-hoc por SMS con Function Calling y catálogo de 12 herramientas SQL parametrizadas.

## [0.1.0] - 2026-06-16

### Added
- Initial project scaffold.
