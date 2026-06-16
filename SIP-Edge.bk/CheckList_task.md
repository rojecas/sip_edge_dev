# 📋 Checklist del Piloto de Rendimiento: Agente SIP-Edge

Este documento establece la hoja de ruta técnica para medir la viabilidad de un modelo **Qwen 2.5 3B** en un entorno **EdgeBox RPi-200**.

---

## 🏗️ Fase 1: La Base (Infraestructura y Datos)
*Configuración del entorno de hardware y los datos de cimiento.*

- [x] **Configurar EdgeBox RPi-200:** Instalación de OS y Python 3.11.
- [x] **Motor de Inferencia:** Instalación de `llama-cpp-python` o `llama.cpp-server` con soporte para aceleración CPU (ARM NEON).
- [x] **Carga del Modelo:** Descargar y verificar integridad de `Qwen 2.5 3B GGUF Q4_0`.
- [x] **Dataset de Pesajes:** Base de datos SQLite (`materia_prima.db`) con 170 registros históricos para pruebas de consulta reales.

---

## 🧠 Fase 2: El Relleno (Lógica y Control del Agente)
*Desarrollo de las capacidades del modelo y restricciones de salida.*

- [ ] **Definición de Schemas (Pydantic/JSON):** Definir la estructura exacta de entrada y salida para las 3 herramientas:
    - `sql_query`: Consultas de pesajes.
    - `anomaly_detection`: Lógica estadística Z-score.
    - `sms_notification`: Simulación de alertas.
- [ ] **Implementación de Herramientas (Python):** Escribir el código que ejecuta las funciones anteriores y devuelve texto al LLM.
- [ ] **Diseño de Gramática GBNF:** Crear el archivo de gramática para forzar al modelo a responder **únicamente** en formato JSON válido (evita errores de parsing).
- [ ] **Ingeniería de Prompt Estructurado:** Diseño del *System Prompt* con técnica *Few-shot* (ejemplos de entrada/salida) y delimitadores claros.

---

## 📏 Fase 3: El Molde (Instrumentación de Medición)
*Preparación del laboratorio de pruebas.*

- [ ] **Configuración Determinística:** Fijar `temperature=0` y `seed` en la inferencia para que las pruebas sean comparables.
- [ ] **Dataset de Evaluación (Golden Set):** Preparar los 50 prompts de prueba que cubran los Requisitos Funcionales (RF-001 a RF-021).
- [ ] **Script de Monitoreo:** Desarrollar el script de medición que capture:
    - `time.perf_counter()`: Latencia (TTFT y tiempo total).
    - `psutil`: Consumo de RAM (Peak) y carga de CPU.
    - **Validador de Acierto:** Comparación entre herramienta esperada y herramienta ejecutada.

---

## 🚀 Fase 4: El Horneado (Ejecución y Recolección)
*Puesta en marcha del experimento.*

- [ ] **Ejecución Automatizada:** Correr el loop de los 50 prompts sin intervención humana.
- [ ] **Captura de Logs:** Almacenar cada interacción en un archivo `resultados_piloto.csv` incluyendo:
    - Prompt de entrada.
    - Pensamiento del modelo (Thought).
    - Acción ejecutada.
    - Métricas de tiempo y hardware.
    - ¿Éxito o Fallo de sintaxis?

---

## ⚖️ Fase 5: Control de Calidad (Análisis y Viabilidad)
*Evaluación de los resultados para la toma de decisiones.*

- [ ] **Análisis de Latencia vs. UX:** Determinar si los tiempos de respuesta cumplen con el **RNF-001** (Latencia de UI < 200ms para el operador, aunque el agente tarde más en segundo plano).
- [ ] **Análisis de Error:** Identificar si los fallos son por el modelo (lógica) o por el prompt (instrucciones).
- [ ] **Ajuste y Re-test:** Realizar una segunda vuelta de ajustes si la precisión es menor al 80%.
- [ ] **Informe de Viabilidad MVP:** Decisión final: *¿Es capaz el Qwen 3B de manejar el sistema SIP-Edge de forma autónoma en el EdgeBox?*

---

### Notas Técnicas Adicionales:
*   **Prioridad:** El foco principal es la **RAM**. Con 8GB en la RPi-200, debemos asegurar que el modelo (~2.1GB) + el OS + MariaDB no causen *swapping* en la eMMC.
*   **Seguridad:** Validar que el agente no intente ejecutar SQL destructivo (`DELETE`, `DROP`).

--- 
*Este listado servirá como hoja de ruta para la implementación del script de medición.*