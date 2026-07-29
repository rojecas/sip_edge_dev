# Brainstorming: Balanza Virtual DINI ARGEO DFWLI-2

**Date Started:** 2026-06-24
**Status:** Paused
**Current Phase:** alignment (complete)
**Based On:** (none)
**Final Spec:** (pending — feature deferred)
**Last Updated:** 2026-06-24 21:37

## Original User Request

> Tengo el EdgeBox con todo el hardware que necesito, pero este se debe conectar a una balanza y la balanza esta en el laboratorio de Cañas del ingenio cliente que se encuentra a 40 km de distancia. Al no tener acceso a la balanza, debo simularla. Quiero hacer un microsideproyecto donde se cree una balanza virtual que se conecta a uno de los puertos seriales del pc del entorno de desarrollo local (este workstation)

---

## Phase A: Alignment Decision Log

### Q1: Alcance del proyecto — ¿dónde vive la balanza virtual?
**Options Presented:**
- A: Script standalone dentro de sip_edge (recomendado)
- B: Proyecto independiente
- C: Extension de src/scale.py con modo virtual
**Decision:** A — Script standalone dentro de sip_edge
**Rationale:** Simple, sin dependencias nuevas, vive en el mismo repo, se documenta como herramienta de desarrollo.
**Timestamp:** 2026-06-24

### Q2: Formato del archivo de lecturas y modo de interacción
**Options Presented:**
- A: CSV con peso muestra, mineral, vegetal
- B: CSV con solo un peso por linea
**Decision:** CSV con 3 pesos por medida (muestra, mineral, vegetal)
**Rationale:** El proceso de pesaje tiene 3 lecturas por medida
**Timestamp:** 2026-06-24

### Q3: Distribucion estadistica de los datos
**Decision:** 4 bloques de 50 medidas (A: baja contaminacion, B: media, C: alta con tendencia, D: outliers) + 1 bloque E de 50 medidas aleatorias uniformes = 250 medidas totales
**Rationale:** Validar las 12 herramientas estadisticas de sql_tools.py (basic_stats, percentiles, trend, moving_average, breakdowns, material_composition, shift/daily summaries, anomaly detection, thresholds checking)
**CSV Columnas:** status_muestra,peso_muestra,status_mineral,peso_mineral,status_vegetal,peso_vegetal,unit
**Timestamp:** 2026-06-24

### Q4: Mecanismo de simulación de estabilidad
**Decision:** La etiqueta ST/US en el CSV determina el comportamiento:
- ST → respuesta inmediata a REXT
- US → delay aleatorio 200ms–3s antes de responder
- La respuesta siempre se envia con status ST (la balanza virtual solo transmite cuando ya esta estable)
- Tecla 'p' en REPL retrocede un sub-paso (muestra←mineral←vegetal)
**Timestamp:** 2026-06-24

### Q5: Disparadores de envio de datos
**Decision:** Dos disparadores:
- Comando REXT por serial desde EdgeBox → con simulacion de estabilidad (delay si US)
- Tecla espacio/'d' desde teclado del PC → sin delay (simula boton PRINT de la balanza)
**Timestamp:** 2026-06-24

### Phase A → B Transition Pause [2026-06-24 21:37]
**Nota:** Se pausa el brainstorm de Balanza Virtual para priorizar Feature de Reset Individual.
**State:** Phase A completa. Pendiente: alignment summary confirmation, writing-plans.
**Status:** Paused

## Pause

**Timestamp:** 2026-06-24 21:37
**Reason:** Se prioriza Feature Reset Individual (mejora al flujo del kiosko). La Balanza Virtual se retomara despues.
