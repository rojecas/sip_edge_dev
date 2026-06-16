### Piloto del agente de IA con TinyLLM sin soporte nativo de *function calling*

 Estrategia basada en **simulación controlada del ciclo completo**, medición de latencias por componentes críticos y validación de la calidad de las respuestas.

---
#Plan de la implementacion y evaluacion

## 🧪 Estrategia para el Piloto del Agente IA

### 1. **Entorno de Prueba Aislado**
- **Hardware**: Usar el mismo EdgeBox RPi-200 donde correrá el MVP, pero en un entorno de desarrollo (no producción).
- **Software**: 
  - Python 3.11+ con `asyncio`
  - `llama-cpp-python` para cargar el modelo Qwen 2.5 3B (GGUF Q4_0)
  - Base de datos simulada (SQLite en memoria) con datos históricos de pesajes (últimos 170 registros).
  - Herramientas (*tools*) mockeadas o reales, pero sin dependencias externas (ej: sin puerto serial real, sin GSM).

### 2. **Arquitectura del Piloto**
Implementar un **Orquestador de Herramientas** que:
- Recibe un prompt en lenguaje natural.
- Utiliza un **prompt estructurado** (few-shot) para que el TinyLLM genere una “llamada a herramienta” en formato JSON.
- Interpreta el JSON y ejecuta la herramienta correspondiente (ej: `query_sql`, `detect_anomalies`).
- Vuelve a enviar el resultado al LLM para que genere una respuesta final en lenguaje natural.

Ejemplo de flujo:
```
Usuario: "¿Cuál fue el peso promedio de la Hacienda San José en la última hora?"
→ Prompt estructurado al LLM → 
LLM genera: {"tool": "query_sql", "params": {"hacienda": "San José", "timeframe": "last_hour"}}
→ Orquestador ejecuta consulta SQL real → 
Resultado: 452.3 kg → 
Enviar resultado al LLM para respuesta final → 
LLM responde: "El peso promedio fue de 452.3 kg en la última hora."
```

### 3. **Herramientas a Implementar en el Piloto**
- `query_sql`: Consulta parametrizada a la base de datos sintética.
- `detect_anomalies`: Ejecuta detección de anomalías (Z-score >3) sobre los datos de prueba.
- `get_last_records`: Devuelve los últimos N registros (simula historial).

---

## 📏 Métricas y Forma de Medición

### 1. **Latencia Total del Ciclo (E2E)**
- **Qué medir**: Tiempo desde que el usuario envía el prompt hasta que recibe la respuesta final.
- **Cómo medir**: Usar `time.perf_counter()` en puntos clave:
  ```python
  start = time.perf_counter()
  # 1. Procesamiento del LLM para generar tool call
  # 2. Ejecución de la herramienta
  # 3. Procesamiento del LLM para respuesta final
  end = time.perf_counter()
  latency_e2e = end - start
  ```
- **Objetivo**: < 10 segundos para el 95% de las consultas (considerando modelo 3B en CPU ARM).

### 2. **Desglose por Fase**
- **Tiempo de inferencia del LLM (prompt → tool call)**.
- **Tiempo de ejecución de la herramienta** (ej: consulta SQL).
- **Tiempo de inferencia del LLM (resultado → respuesta natural)**.

### 3. **Precisión de la Llamada a Herramientas**
- **Qué medir**: Porcentaje de veces que el LLM genera un JSON válido y llama a la herramienta correcta.
- **Cómo medir**: 
  - Conjunto de 50 prompts predefinidos (ej: “dame el último peso”, “detecta anomalías”).
  - Validación manual/automática de que la herramienta ejecutada corresponde a la intención.

### 4. **Uso de Recursos**
- **RAM pico** durante la inferencia (`psutil.Process().memory_info().rss`).
- **CPU usage** durante el ciclo.

### 5. **Calidad de la Respuesta Final**
- **Evaluación humana o automática** (usando métricas como BLEU o ROUGE contra respuestas esperadas).
- **Satisfacción subjetiva** en una escala 1-5 (si es posible con usuarios reales).

---

## 🛠️ Implementación Paso a Paso del Piloto

### Fase 1: Preparación del Entorno
1. **Cargar el modelo GGUF** con `llama-cpp-python`.
2. **Crear base de datos sintética** con `sqlite3` y datos de pesajes realistas (120 registros).
3. **Implementar herramientas mock** que simulen consultas SQL y detección de anomalías.

### Fase 2: Orquestador Básico
1. **Diseñar prompt estructurado** que guíe al LLM a generar JSON para tool calling.
   Ejemplo:
   ```
   Eres un asistente que puede usar herramientas. Responde en JSON con formato:
   {"tool": "nombre_herramienta", "params": {"param1": "valor1"}}
   ```
2. **Implementar parser de JSON** y mapeo a funciones Python.

### Fase 3: Ejecución de Pruebas
1. **Script automatizado** que envía los 50 prompts predefinidos y registra:
   - Latencia total y por fase.
   - Correctitud de la herramienta llamada.
   - Uso de RAM/CPU.
2. **Validación manual** de al menos el 20% de las respuestas.

### Fase 4: Análisis y Ajuste
1. **Identificar cuellos de botella**: ¿Es la inferencia del LLM? ¿La ejecución de herramientas?
2. **Ajustar prompts** para mejorar precisión.
3. **Optimizar herramientas** (ej: índices en SQLite para consultas rápidas).

---

## 📊 Reporte del Piloto

Entregar un informe con:
1. **Latencia promedio E2E** y percentiles (p50, p95, p99).
2. **Precisión de tool calling** (% de aciertos).
3. **Consumo de recursos** (RAM pico, CPU promedio).
4. **Lista de errores comunes** (ej: JSON mal formado, herramienta incorrecta).
5. **Recomendaciones** para producción:
   - ¿Es necesario fine-tuning del prompt?
   - ¿Se requiere cache de consultas?
   - ¿Debe implementarse un timeout por fase?

---

## 🚨 Consideraciones Clave para el Piloto

- **El modelo GGUF Q4_0 es lento en CPU**: Espera latencias de 2–5 segundos por inferencia en ARM Cortex-A72.
- **Sin soporte nativo de function calling**: Dependerás de prompts ingenierizados, lo que añade variabilidad.
- **Prueba con carga concurrente** (aunque sea baja, ej: 2–3 solicitudes simultáneas) para ver estabilidad.

---

## ✅ Checklist de Acciones Inmediatas

```markdown
[ ] Configurar EdgeBox RPi-200 con Python 3.11 y llama-cpp-python
[ ] Descargar modelo Qwen 2.5 3B GGUF Q4_0
[ ] Dataset sintético de 170 registros de pesajes en formato SQLite
[ ] Implementar 3 herramientas mock (SQL, anomalías, historial)
[ ] Diseñar prompt estructurado para tool calling
[ ] Escribir script de medición con time.perf_counter() y psutil
[ ] Ejecutar 50 prompts predefinidos y recolectar métricas
[ ] Analizar resultados y ajustar prompt/herramientas
[ ] Documentar hallazgos y decidir viabilidad para MVP
```

---

Esta estrategia te permitirá **validar el rendimiento real del Agente IA en el hardware objetivo**, identificar riesgos tempranos y ajustar el diseño antes de la integración completa en el SIP-Edge. ¿Te gustaría que detalle alguno de los componentes, como el prompt estructurado o el script de medición?