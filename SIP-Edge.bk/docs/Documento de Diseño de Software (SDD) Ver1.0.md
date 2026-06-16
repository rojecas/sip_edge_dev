---

# 📄 Software Design Document (SDD)

## Sistema ERP Industrial con Agente IA Asíncrono

---

# 1. Introducción

## 1.1 Propósito

Este documento describe la arquitectura técnica del sistema ERP industrial que integra:

* Captura y registro de datos operativos.
* Motor de reglas deterministas.
* Servicio de análisis mediante TinyLLM.
* Interfaz de operador tipo kiosco.
* Generación de reportes vía SMS.
* Persistencia completa y trazabilidad auditada.

Complementa el ERS, los Requisitos Diferidos y los ADR aprobados.

---

## 1.2 Alcance

El sistema:

* Opera en Raspberry Pi industrial.
* Controla flujo de pesaje y validación.
* Ejecuta análisis estadísticos.
* Invoca IA de manera asíncrona.
* Mantiene trazabilidad completa de registros y eventos.

---

# 2. Arquitectura General

## 2.1 Estilo Arquitectónico

Arquitectura basada en:

* Monolito modular.
* Procesamiento asíncrono de tareas IA.
* Separación entre núcleo determinista y componente IA.
* Comunicación UI–Backend en tiempo real mediante WebSocket.

La IA es un componente auxiliar degradable.

---

## 2.2 Diagrama Conceptual de Componentes

```
[ UI Kiosco ]
        |
   REST + WebSocket
        |
[ Backend API ]
        |
  ---------------------------------
  |        |            |         |
[DB]  [Motor Reglas] [Gestor IA] [Logs]
                              |
                         [TinyLLM]
```

---

# 3. Vista Lógica

## 3.1 Módulos Principales

### 3.1.1 Módulo de Captura Operativa

* Lectura de báscula.
* Validación inicial.
* Flujo de confirmación.
* Registro de datos.

---

### 3.1.2 Motor de Reglas Deterministas

* Validación de umbrales.
* Cálculo estadístico básico.
* Detección primaria de anomalías.

Funciona independientemente del servicio IA.

---

### 3.1.3 Gestor de Servicio IA

* Gestión de estado global (UP / DEGRADED / DOWN / DISABLED).
* Control de fallos consecutivos.
* Circuit breaker.
* Timeout de inferencia.

---

### 3.1.4 Gestor de Tareas IA

* Creación de tareas.
* Control de concurrencia (máximo 1).
* Persistencia de resultados.
* Estados: PENDING / RUNNING / COMPLETED / FAILED.

---

### 3.1.5 Worker de Inferencia

* Invocación de TinyLLM.
* Aplicación de límites de tokens.
* Respuestas estructuradas.
* Sin memoria conversacional persistente.

---

### 3.1.6 Módulo de Comunicación en Tiempo Real

* Servidor WebSocket.
* Emisión de eventos de estado.
* Manejo de reconexión.

---

### 3.1.7 Persistencia y Auditoría

* Base de datos local.
* Logs técnicos.
* Logs informativos.
* Audit trail completo.
* Preparación para firma criptográfica de registros confirmados.

---

# 4. Vista de Procesos

## 4.1 Flujo Operativo Principal

1. Operador registra lectura.
2. Sistema valida con reglas deterministas.
3. Operador confirma registro.
4. Registro se almacena.
5. Si aplica, se genera tarea IA asíncrona.

La operación principal no depende de la IA.

---

## 4.2 Flujo de Tarea IA

1. Se crea tarea → PENDING.
2. Worker la toma → RUNNING.
3. Se emiten eventos WebSocket:

   * TASK_STARTED
   * STAGE_DB
   * STAGE_STATS
   * STAGE_LLM
4. Resultado → COMPLETED.
5. Persistencia del resultado.

Si ocurre error:

* Estado → FAILED.
* Evaluación de impacto en estado global IA.

---

# 5. Vista de Datos

## 5.1 Entidades Principales

### RegistroLectura

* id
* fecha
* operador
* valores
* estado_confirmado
* hash (si aplica)
* timestamp_confirmación

---

### IATask

* id
* tipo
* status
* created_at
* started_at
* completed_at
* result
* error_message

---

### IAServiceState

* state
* consecutive_failures
* last_success
* last_failure

---

### AuditLog

* usuario
* acción
* timestamp
* detalle

---

# 6. Control de Recursos

* Concurrencia máxima: 1 inferencia.
* Límite estricto de tokens de entrada y salida.
* Timeout máximo de inferencia.
* Sin almacenamiento de historial conversacional.
* Registro de tiempos de ejecución.

---

# 7. Experiencia de Usuario (UX)

* Procesamiento IA asíncrono.
* Indicador visual sobrio (spinner o barra indeterminada).
* Etapas perceptuales si ejecución > 2 segundos.
* Mensajes claros en caso de fallo.
* Sistema nunca bloquea flujo principal.

---

# 8. Riesgos Arquitectónicos Identificados

## 8.1 Riesgos Críticos

### 8.1.1 Error humano en confirmación de registro

Probabilidad: Alta
Impacto: Alto
Nivel: Crítico

Mitigación:

* Flujo de confirmación explícito.
* Registro solo tras confirmación.
* Audit trail completo.
* Firma solo de registros confirmados.

---

### 8.1.2 Saturación de CPU/RAM

Probabilidad: Media
Impacto: Alto
Nivel: Alto

Mitigación:

* Concurrencia 1.
* Worker aislado.
* Límites de tokens.
* Monitoreo de recursos.

---

### 8.1.3 Latencia excesiva del TinyLLM

Probabilidad: Media
Impacto: Alto
Nivel: Alto

Mitigación:

* Prompts cortos y estructurados.
* Timeout duro.
* Indicador visual.
* Registro de tiempos.

---

## 8.2 Riesgos Secundarios

* Fallos WebSocket.
* Crecimiento de datos.
* Tareas bloqueadas.
* Dependencia excesiva futura de IA.
* Trazabilidad insuficiente.

Todos con mitigaciones definidas en ADR correspondientes.

---

# 9. Estrategia de Evolución

La arquitectura permite:

* Ajustar límites de inferencia.
* Sustituir motor IA.
* Agregar nuevas tareas IA.
* Integrar firma criptográfica.
* Incorporar nuevos canales de comunicación.

Sin afectar el núcleo determinista.

---

# 10. Conclusión Arquitectónica

El sistema se diseña bajo los principios de:

* Resiliencia.
* Separación de responsabilidades.
* Degradabilidad controlada.
* Trazabilidad completa.
* Control estricto de recursos.

La IA es un componente auxiliar que agrega valor sin comprometer la estabilidad del sistema operativo principal.

---

Listo.

No lo analices ahora.
Solo guárdalo.

Mañana lo lees con cabeza fresca y verás cosas que hoy no ves.
Eso es parte del proceso.

Que descanses.
