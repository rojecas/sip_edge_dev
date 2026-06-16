## 1. Proyecto y Estructura

- [ ] 1.1 Crear estructura de directorios del proyecto (backend, frontend, scripts, tests)
- [ ] 1.2 Inicializar entorno Python con dependencias (FastAPI, SQLAlchemy, llama.cpp bindings, pyserial, etc.)
- [ ] 1.3 Configurar MariaDB con esquema inicial y migraciones
- [ ] 1.4 Configurar systemd para servicios críticos con Restart=always y watchdog 30s

## 2. Autenticación y Usuarios (user-auth)

- [ ] 2.1 Implementar modelo de usuario en SQLAlchemy con hash bcrypt
- [ ] 2.2 Implementar endpoints de login/logout con sesiones
- [ ] 2.3 Implementar middleware RBAC con restricción por rol
- [ ] 2.4 Implementar interfaz Admin de CRUD de usuarios
- [ ] 2.5 Implementar bloqueo temporal por intentos fallidos (3 intentos / 5 min)

## 3. Pesaje y Báscula (weighing-scale)

- [ ] 3.1 Implementar driver de comunicación serial con timeout configurable
- [ ] 3.2 Implementar comando-respuesta para botones de control (Tara, Peso Mineral, etc.)
- [ ] 3.3 Implementar interfaz Admin para configuración de puerto y baudrate en caliente

## 4. Persistencia de Datos (data-persistence)

- [ ] 4.1 Implementar modelo de registro de pesaje con transacciones atómicas (commit/rollback)
- [ ] 4.2 Implementar CRUD de haciendas con borrado lógico
- [ ] 4.3 Implementar CRUD de suertes vinculadas a hacienda con carga en cascada

## 5. Agente IA (ai-agent)

- [ ] 5.1 Integrar llama.cpp con Qwen 2.5 3B (GGUF Q4_0) como proceso separado
- [ ] 5.2 Implementar orquestador con Function Calling para herramientas Python
- [ ] 5.3 Implementar detector de anomalías estadísticas (Z-score >3, ventana 120 registros / 4h)
- [ ] 5.4 Implementar herramientas SQL parametrizadas para consultas cuantitativas

## 6. Notificaciones SMS (sms-notification)

- [ ] 6.1 Implementar gestor de comandos AT para módulo GSM
- [ ] 6.2 Implementar envío de reportes programados (06:00, 14:00, 22:00 configurables)
- [ ] 6.3 Implementar alertas de seguridad por intentos no autorizados

## 7. Administración y Configuración (admin-config)

- [ ] 7.1 Implementar persistencia de configuración en config.yaml con carga al inicio
- [ ] 7.2 Implementar rutina diaria de respaldo automático (dump.sql.gz, rotación 30 días)
- [ ] 7.3 Implementar exportación a USB/SD con verificación CRC32
- [ ] 7.4 Implementar modo manual de emergencia vía SMS (MANUAL_ON, timeout 15 min)

## 8. Interfaz de Usuario (ui-kiosk)

- [ ] 8.1 Implementar layout kiosko con feedback visual por colores
- [ ] 8.2 Implementar formulario de pesaje con campo readonly y cascada hacienda-suerte
- [ ] 8.3 Implementar actualizaciones en tiempo real vía WebSockets (HTMX)

## 9. Operación Offline y Resiliencia (offline-operations)

- [ ] 9.1 Implementar cola de SMS para envío diferido cuando no hay señal GSM
- [ ] 9.2 Implementar watchdog de servicios con notificación de reinicios
- [ ] 9.3 Implementar monitoreo de consumo RAM con alerta al superar 5.5GB
