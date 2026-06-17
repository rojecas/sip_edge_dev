# Changelog — sip_edge

> All notable changes to this project will be documented in this file.

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
