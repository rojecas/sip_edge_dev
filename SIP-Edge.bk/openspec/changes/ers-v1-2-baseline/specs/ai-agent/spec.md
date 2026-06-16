## ADDED Requirements

### Requirement: Orquestador de consultas (AI Agent)
El sistema SHALL integrar un agente basado en Qwen 2.5 3B (GGUF) ejecutado mediante llama.cpp con capacidad de Function Calling para invocar herramientas predefinidas en Python.

#### Scenario: Agente responde a consulta
- **WHEN** el sistema envía una consulta al agente IA con contexto de pesaje
- **THEN** el agente procesa la consulta usando Function Calling e invoca la herramienta Python adecuada, retornando el resultado estructurado

### Requirement: Detección proactiva de anomalías
El sistema SHALL analizar estadísticamente los últimos 120 registros o las últimas 4 horas (lo que ocurra primero) para identificar desviaciones con Z-score > 3.

#### Scenario: Anomalía detectada
- **WHEN** un nuevo pesaje tiene un Z-score > 3 respecto a la ventana de análisis (120 registros o 4 horas)
- **THEN** el sistema marca el registro como anómalo y dispara una alerta para notificación SMS

#### Scenario: Pesaje normal sin anomalía
- **WHEN** un nuevo pesaje tiene un Z-score <= 3 respecto a la ventana de análisis
- **THEN** el sistema registra el peso sin marcarlo como anómalo

### Requirement: Análisis SQL estructurado con Function Calling
El agente SHALL resolver consultas cuantitativas invocando herramientas SQL parametrizadas, evitando alucinación de datos numéricos. No SHALL utilizar RAG ni pasar texto crudo al LLM para consultas sobre datos.

#### Scenario: Consulta de resumen por turno
- **WHEN** el agente recibe una solicitud de resumen cuantitativo (ej: "total de caña procesada en el turno de la mañana")
- **THEN** el agente invoca la herramienta SQL parametrizada correspondiente y retorna el resultado numérico sin alucinación
