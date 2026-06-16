# 📊 Informe de Requisitos Diferidos: Estado Actual vs. Roadmap de Crecimiento  
*Proyecto SIP-Edge – Análisis Técnico para Toma de Decisiones*  
*Fecha: 11-Feb-2026*

---

## 🔍 Resumen Ejecutivo

La transición de **ERS v1.0 → v1.1** representa una **reducción estratégica de alcance** para acelerar el MVP, eliminando 11 requisitos funcionales/no funcionales críticos que dependían de recursos limitados (RAM, almacenamiento) o dependencias externas no controlables. Este informe documenta:

- ✅ **Estado Actual (v1.2)**: MVP técnicamente viable en EdgeBox RPi-200 (8GB RAM / 32GB eMMC)
- ⏳ **Requisitos Diferidos**: 11 capacidades con justificación técnica de diferimiento
- 📈 **Roadmap de Crecimiento**: Fases 2.0 y 3.0 con criterios objetivos de activación
- ⚖️ **Matriz de Impacto**: Consumo estimado de recursos para cada funcionalidad futura

---

## 📌 Estado Actual: MVP v1.2 (Alcance Confirmado)

| Capacidad | Estado | Recursos Consumidos (Estimado) |
|-----------|--------|-------------------------------|
| Autenticación por credenciales + RBAC | ✅ Implementado | < 50MB RAM |
| Pesaje serial comando-respuesta | ✅ Implementado | PySerial: ~30MB RAM |
| TinyLLM (Qwen 2.5 3B GGUF Q4_0) | ✅ Implementado | ~2.1GB RAM (pico) |
| MariaDB (InnoDB) | ✅ Implementado | ~150MB RAM (base) + datos |
| Notificaciones SMS (módulo GSM) | ✅ Implementado | ~20MB RAM |
| **Total RAM Estimado (Pico)** | — | **~4.8GB** (margen 3.2GB) |
| **Almacenamiento eMMC** | — | **~8GB** ocupados (24GB libres) |

> 💡 **Conclusión Técnica**: El MVP v1.2 es **viable en hardware actual** con margen de seguridad para operación estable (>30% RAM libre).

---

## ⏳ Requisitos Diferidos: Matriz Técnica de Impacto

### Tabla 1: Requisitos Funcionales Diferidos (v1.0 → v1.2)

| ID Original | Nombre | Razón Técnica de Diferimiento | Impacto RAM Estimado | Impacto Almacenamiento | Dependencias Críticas |
|-------------|--------|-------------------------------|----------------------|------------------------|------------------------|
| **RF-001** | Integración Hikvision DS-K1T343 | API ISAPI no controlable por equipo de desarrollo. Riesgo operativo si falla (bloquea pesaje). | +15MB | Negligible | API Hikvision con SLA >99.5% |
| **RF-002** | Validación Biométrica Local (InsightFace) | Consumo RAM pico >1.2GB compite directamente con TinyLLM. Total excedería 8GB. | **+1.2GB** | +500MB (embeddings) | Webcam UVC + iluminación controlada |
| **RF-003** | Lógica de Doble Factor Implícito | Dependiente de RF-001 y RF-002. Sin biometría/Hikvision, el concepto "perímetro" es inviable. | N/A | N/A | Reactivación previa de RF-001/002 |
| **RF-014** | Bot Interactivo Telegram | Requiere internet estable. SMS garantiza operatividad 100% offline con módulo GSM. | +40MB | Negligible | Internet 4G/5G >95% uptime |
| **RF-023** | Enrolamiento Biométrico Local | Sin biometría activa (RF-002 diferido), el enrolamiento es innecesario. | +200MB (pico) | +500MB | Reactivación de RF-002 |
| **RF-024** | Vinculación Cuenta Telegram vía OTP | Depende de RF-014 (Telegram). | +10MB | Negligible | Reactivación de RF-014 |
| **RF-D01** | Dataset para Visión Artificial (Cámara Estéreo) | Requiere almacenamiento NVMe >512GB (no disponible en 32GB eMMC). | +300MB (pico) | **+512GB NVMe** | SSD M.2 2242 + cámara ToF/Stereo |

### Tabla 2: Requisitos No Funcionales Diferidos

| ID Original | Nombre | Razón de Diferimiento | Impacto en Diseño Actual |
|-------------|--------|------------------------|--------------------------|
| **RNF-002** | Prioridad de Procesamiento (`nice -10`) | Sin biometría activa, la priorización pierde sentido técnico. | No aplica en v1.2 |
| **RNF-003** | Tiempo de Inferencia <60s | Reemplazado por métrica más realista: latencia UI <200ms para operador. | Métrica obsoleta para MVP |
| **RNF-D01** | Almacenamiento Masivo para Dataset | Depende de RF-D01 (cámaras estéreo). | Reservar socket M.2 físicamente |

---

## 📈 Roadmap de Crecimiento: Fases Técnicas Validadas

### Fase 1.0 – MVP (Corriente – v1.2)
| Capability | Estado | Criterio de Éxito |
|------------|--------|-------------------|
| Autenticación por credenciales | ✅ Listo | Disponibilidad >98% durante 30 días |
| Pesaje serial comando-respuesta | ✅ Listo | Timeout <1500ms en 95% de transacciones |
| Agente IA para anomalías | ✅ Listo | Falsos positivos <5% en dataset validado |
| Notificaciones SMS | ✅ Listo | Entrega >90% en condiciones GSM reales |

> ⚠️ **Umbral para Avanzar a Fase 2.0**: Todas las métricas de éxito cumplidas + consumo RAM pico <5.5GB.

---

### Fase 2.0 – Expansión (+6 meses post-MVP)
| Capability | Prioridad | Recursos Adicionales Requeridos | Criterio de Activación |
|------------|-----------|---------------------------------|------------------------|
| **Biometría Facial Ligera (1:1)** | 🔶 Alta | • Webcam USB UVC<br>• Iluminación LED controlada<br>• +1.2GB RAM disponible | • RAM pico sistema base <5.5GB<br>• Iluminación instalada en puesto |
| **Telegram + SMS Híbrido** | 🔶 Alta | • Conexión internet estable<br>• +40MB RAM | • Uptime internet >90% en sitio<br>• Caso de uso validado para comandos naturales |
| **Monitoreo de Batería vía GPIO** | 🔶 Media | • GPIO libre en EdgeBox<br>• ADC externo (opcional) | • Disponibilidad de GPIO no usado por otros periféricos |

> 💡 **Arquitectura Recomendada para Fase 2.0**:  
> ```python
> # Patrón de abstracción para notificaciones híbridas
> class INotificationProvider(ABC):
>     @abstractmethod
>     async def send(self, recipient: str, message: str) -> bool: ...
> 
> class SMSProvider(INotificationProvider): ...
> class TelegramProvider(INotificationProvider): ...
> class HybridProvider(INotificationProvider):
>     # SMS como fallback automático si Telegram falla
>     def __init__(self, primary: TelegramProvider, fallback: SMSProvider): ...
> ```

---

### Fase 3.0 – Optimización (+12 meses post-MVP)
| Capability | Prioridad | Recursos Adicionales Requeridos | Criterio de Activación |
|------------|-----------|---------------------------------|------------------------|
| **Integración Hikvision (Lectura Asíncrona)** | 🔷 Media | • API ISAPI estable<br>• Cache local SQLite | • SLA API >99.5%<br>• Latencia <500ms en LAN |
| **Dataset para Visión Artificial** | 🔷 Baja | • SSD NVMe M.2 2242 (1TB)<br>• Cámara estéreo ToF<br>• +512GB almacenamiento | • Aprobación CAPEX<br>• Caso de uso validado para detección visual de materia extraña |

> ⚠️ **Nota Crítica para RF-D01**:  
> El socket M.2 del EdgeBox RPi-200 **debe reservarse físicamente** desde v1.2 para evitar conflictos futuros. No instalar módulos Wi-Fi/Bluetooth en este slot.

---

## ⚖️ Matriz de Decisión: ¿Cuándo Reactivar un Requisito Diferido?

| Criterio | Métrica Mínima | Método de Validación | Responsable |
|----------|----------------|----------------------|-------------|
| **Estabilidad del MVP** | Disponibilidad >98% durante 30 días consecutivos | Logs systemd + monitoreo heartbeat | DevOps |
| **Disponibilidad de RAM** | Consumo pico sistema base <5.5GB | `ps_mem.py` durante carga máxima | Ingeniero de Sistemas |
| **Caso de Negocio** | ROI cuantificado >15% (ej: reducción fraude) | Análisis pérdidas pre/post | Gerencia de Operaciones |
| **Hardware** | Presupuesto aprobado para componentes adicionales | Orden de compra validada | Gerencia Financiera |
| **Entorno** | Condiciones físicas cumplidas (iluminación, cobertura GSM) | Auditoría in situ | Ingeniero de Campo |

> ✅ **Regla de Oro**: Un requisito diferido **NO se reactiva** hasta que **TODOS** los criterios anteriores se cumplan simultáneamente.

---

## 🔧 Recomendaciones de Arquitectura para Facilitar el Crecimiento

### 1. Diseño con Extensiones en Mente (Desde v1.2)
| Capa | Patrón Recomendado | Beneficio Futuro |
|------|--------------------|------------------|
| **Notificaciones** | Interfaz `INotificationProvider` | Facilita migración SMS → Telegram híbrido en v2.0 |
| **Autenticación** | Plugin architecture (`IAuthMethod`) | Permite agregar biometría sin refactorizar core |
| **Almacenamiento** | Abstracción `IDataStore` | Facilita migración eMMC → NVMe en v3.0 |

### 2. Reservas Físicas de Hardware (Desde Instalación Inicial)
| Recurso | Acción Inmediata | Justificación |
|---------|------------------|---------------|
| **Socket M.2** | Dejar físicamente libre (no instalar Wi-Fi) | Requerido para NVMe en RF-D01 (v3.0) |
| **Puerto USB 2** | Dejar físicamente libre (no usar para hub) | Requerido para webcam en biometría v2.0 |
| **GPIO 12-15** | Documentar como reservados para monitoreo batería | Evita conflictos futuros con sensores |

### 3. Métricas de Monitoreo para Validar Crecimiento
Implementar desde v1.2:
```yaml
# metrics.yaml (ejemplo)
system:
  ram_peak_mb: 4800          # Alerta si >5500 (umbral v2.0)
  storage_used_gb: 8         # Alerta si >20 (umbral v3.0)
  serial_timeout_rate: 0.02  # Alerta si >0.05 (problema hardware)
  sms_delivery_rate: 0.92    # Alerta si <0.85 (problema GSM)
```

---

## ✅ Checklist de Acciones Inmediatas para MVP v1.2

```markdown
[ ] Reservar físicamente socket M.2 (no instalar módulos Wi-Fi/Bluetooth)
[ ] Reservar puerto USB 2 para webcam futura (no usar para hub)
[ ] Implementar interfaz INotificationProvider desde v1.2
[ ] Configurar monitoreo continuo de RAM pico (umbral 5.5GB)
[ ] Documentar en Anexo F todos los requisitos diferidos con criterios de reactivación
[ ] Validar benchmark de llama.cpp en hardware real (tokens/s, RAM pico)
```

---

## 📌 Conclusión Estratégica

El **MVP v1.2 es técnicamente sólido y viable** en el hardware actual, con margen de seguridad para operación estable. Los requisitos diferidos no representan "deuda técnica", sino **decisiones arquitectónicas intencionales** para:

1. ✅ Garantizar estabilidad operativa en entorno industrial
2. ✅ Reducir riesgo de bloqueos por dependencias externas (Hikvision)
3. ✅ Maximizar valor entregado con recursos limitados (8GB RAM)

El roadmap propuesto (Fases 2.0 y 3.0) es **realista y medible**, con criterios objetivos que evitan la tentación de "scope creep" prematuro. La clave para éxito a largo plazo es **respetar los umbrales de activación** antes de expandir funcionalidades.

> ℹ️ **Referencia Estándar**: Este informe sigue las prácticas de IEEE 1045-1992 (Guía para Requisitos de Software) y PMBOK® Guide (7ma ed.) para gestión progresiva de alcance (*progressive elaboration*).

¿Le gustaría que profundice en el diseño de la interfaz `INotificationProvider` para facilitar la migración a notificaciones híbridas en v2.0, o que prepare una matriz de riesgos técnicos para cada fase del roadmap?