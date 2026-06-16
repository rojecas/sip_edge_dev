---

# INFORME TÉCNICO

## Implementación de Tool Calling en TinyLLMs y Evaluación de Rendimiento en Sistemas Edge

**Autor:** Román Jesús Castañeda
**Contexto:** Diseño de arquitectura de agente con TinyLLM en entorno edge (SBC tipo Raspberry Pi / Radxa)
**Objetivo:** Analizar viabilidad técnica, arquitectura alternativa a function calling nativo y evaluación de rendimiento percibido por el usuario.

---

# 1. Introducción

En el diseño de sistemas basados en LLM que utilizan herramientas externas (tools), muchos modelos comerciales ofrecen soporte nativo para *function calling*. Sin embargo, en entornos edge donde se emplean **TinyLLMs**, esta funcionalidad no está disponible.

El presente análisis aborda:

1. Cómo implementar tool calling sin soporte nativo.
2. Qué impacto tiene esta arquitectura en el rendimiento.
3. Cómo medir correctamente la experiencia de usuario.
4. Comparación estimada entre plataformas SBC.

---

# 2. Implementación de Tool Calling sin Soporte Nativo

## 2.1 Principio Fundamental

El *function calling nativo* no es una capacidad mágica del modelo, sino un patrón de orquestación.

Cuando el modelo no lo implementa, la arquitectura debe externalizar esa responsabilidad al orquestador.

---

## 2.2 Arquitectura Propuesta

Arquitectura recomendada:

```
Usuario
   ↓
Orquestador (Python)
   ↓
TinyLLM
   ↓ (salida estructurada JSON)
Parser / Validador
   ↓
Tool Router
   ↓
Ejecución de herramienta
   ↓
Resultado al modelo (si aplica)
```

### Principios clave:

* El LLM **nunca ejecuta funciones directamente**
* Solo genera una **decisión estructurada**
* El sistema valida y ejecuta externamente

---

## 2.3 Patrón de Implementación

### 1️⃣ Definición de contrato estricto de salida

El modelo debe responder únicamente en formato JSON estructurado:

```json
{
  "action": "nombre_tool",
  "arguments": {
    "parametro": "valor"
  }
}
```

Si no requiere herramienta:

```json
{
  "action": "none",
  "arguments": {}
}
```

---

### 2️⃣ Validación

Se debe:

* Extraer JSON
* Validar contra JSON Schema
* Manejar errores de formato
* Implementar fallback seguro

Esto reemplaza la validación automática de los SDKs comerciales.

---

### 3️⃣ Tool Router

El enrutador de herramientas:

* Verifica existencia
* Aplica control de permisos
* Registra auditoría
* Ejecuta función real

Este enfoque mejora:

* Seguridad
* Auditabilidad
* Control de errores
* Cumplimiento (ej. ISO 27001)

---

# 3. Métricas Relevantes de Rendimiento

Medir solo tokens/segundo es insuficiente.

Las métricas relevantes son:

---

## 3.1 TTFT – Time To First Token

Tiempo desde la consulta hasta el primer token generado.

Impacta percepción de inmediatez.

---

## 3.2 Tokens por segundo (Throughput)

Velocidad de generación una vez iniciada.

Impacta duración de respuestas largas.

---

## 3.3 Tool Loop Latency (Agent Step Latency)

Tiempo requerido para un ciclo completo:

1. Razonamiento
2. Generación de acción
3. Ejecución de tool
4. Recepción de resultado
5. Nueva iteración (si aplica)

Esta es la métrica más importante en agentes con herramientas.

---

## 3.4 Task Completion Time

Tiempo total hasta respuesta final.

Depende de:

```
(Task Time) ≈ (Latencia por ciclo × Número de ciclos) + latencia de tools
```

---

# 4. Impacto del Número de Ciclos

El principal factor de degradación en edge es el número de iteraciones.

Ejemplo: Consulta de clima

Enfoque fragmentado:

1. get_today
2. get_location
3. get_weather

→ 3 ciclos

Enfoque optimizado:

1. get_weather_tomorrow()

→ 1 ciclo

Reducir ciclos tiene mayor impacto que aumentar tokens/segundo.

---

# 5. Estimación Comparativa de Plataformas

## Supuestos

* TinyLLM 1.5B–3B
* Quantización Q4
* 40–60 tokens generados por paso

---

## 5.1 Raspberry Pi 5 (16GB)

Rendimiento estimado:

* 8–12 tokens/seg

Tiempo por ciclo:

* ~4–6 segundos

Escenario 3 tools:

* ~15–20 segundos totales

Experiencia:

* Funcional pero poco fluida si hay múltiples ciclos

---

## 5.2 Radxa Rock 5T (16GB)

Rendimiento estimado CPU:

* ~15–25 tokens/seg

Tiempo por ciclo:

* ~2–3 segundos

Escenario 3 tools:

* ~8–10 segundos totales

Experiencia:

* Aceptable en múltiples ciclos
* Fluida si se limita a 1–2 ciclos

---

# 6. Consideraciones Estratégicas

## 6.1 Hardware no es la única variable crítica

Mejorar tokens/segundo tiene impacto limitado si:

* El diseño del agente requiere múltiples iteraciones
* Las tools tienen alta latencia externa

---

## 6.2 Recomendación Arquitectónica

Para entornos edge industriales:

1. Diseñar herramientas de grano grueso (macro-tools)
2. Limitar a máximo 1–2 ciclos por solicitud
3. Centralizar lógica en backend
4. Usar el LLM solo para:

   * Interpretación
   * Decisión
   * Redacción final

---

# 7. Conclusiones

1. Es totalmente viable implementar tool calling sin soporte nativo.
2. La clave es arquitectura de orquestación externa.
3. La métrica crítica para UX es el Tool Loop Latency.
4. Reducir ciclos mejora más la experiencia que mejorar hardware.
5. Raspberry Pi 5 es viable para agentes simples (1 ciclo).
6. Radxa Rock 5T es más adecuado para agentes con múltiples iteraciones.
7. En aplicaciones industriales, el diseño de herramientas es más determinante que el modelo.

---

# 8. Recomendación para el Proyecto

Si el objetivo es:

* Sistema RAG multiusuario
* Agentes con tools
* Despliegue edge

Se recomienda:

* Implementar framework propio de tool routing
* Diseñar macro-tools
* Optimizar número de iteraciones
* Evaluar Radxa si se anticipan agentes complejos
* Mantener Raspberry Pi si se controla el número de ciclos

---

