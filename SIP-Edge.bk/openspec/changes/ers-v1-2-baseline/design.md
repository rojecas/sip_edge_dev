## Context

Proyecto SIP-Edge: Sistema Inteligente de Pesaje y Control de Materia Extraña desplegado en EdgeBox RPi-200 (8GB RAM, 32GB eMMC, ARM Cortex-A72). Actualmente existe código Python base (`src/tools.py`, `src/agent.py`, `main.py`) y documentación ERS V1.2 que define el MVP.

Stack tecnológico definido: Python 3.11+ / FastAPI (async), MariaDB (InnoDB), llama.cpp + Qwen 2.5 3B (GGUF Q4_0), HTML5 + HTMX + WebSockets, módulo GSM para SMS.

## Goals / Non-Goals

**Goals:**
- Estructurar el proyecto en 8 capabilities con specs formales en OpenSpec
- Establecer trazabilidad entre requisitos ERS y artefactos de desarrollo
- Tener la baseline completa para comenzar implementación iterativa

**Non-Goals:**
- Modificar el código Python existente
- Implementar funcionalidades del Anexo F (Future Scope)
- Definir UI final (solo requisitos de interfaz)

## Decisions

1. **Separación por capabilities en lugar de capas**: Se estructuran los specs por dominio funcional (user-auth, weighing-scale, etc.) en lugar de por capa técnica (backend, frontend, DB). Esto alinea mejor con el desarrollo por cambios de OpenSpec y facilita la asignación de trabajo incremental.

2. **8 capabilities vs agrupación original del ERS**: El ERS agrupa en 6 módulos. Se desdobla en 8 capabilities separando `ui-kiosk` (experiencia de usuario) y `offline-operations` (resiliencia) como capacidades independientes, dado que cruzan múltiples módulos.

3. **Proposal como contrato vs ERS como fuente**: El ERS V1.2 se mantiene como documento fuente en `docs/`. Los specs de OpenSpec en `openspec/specs/` son la representación estructurada para el flujo de trabajo de cambios. El proposal de este cambio (ers-v1-2-baseline) actúa como contrato de trazabilidad entre ambos.

4. **Preservación de IDs de requisitos**: Se mantienen los IDs originales (RF-001 a RF-021, RNF-001 a RNF-008) en los escenarios de los specs para trazabilidad directa con el ERS.

## Risks / Trade-offs

- [Riesgo de desviación] Los specs de OpenSpec podrían desincronizarse del ERS si se actualiza uno sin el otro → Mitigación: Los cambios futuros deberán usar OpenSpec como fuente de verdad; el ERS queda como documento histórico de referencia.
- [Rendimiento] Qwen 2.5 3B consume ~2.2GB RAM, dejando ~5.8GB para el resto del sistema → Mitigación: Monitoreo continuo de RAM y umbral de 5.5GB como alerta preventiva.
- [Complejidad GSM] Dependencia de señal celular para notificaciones, sin feedback de entrega → Mitigación: Log de envíos con reintentos y reporte de fallos al Admin.
