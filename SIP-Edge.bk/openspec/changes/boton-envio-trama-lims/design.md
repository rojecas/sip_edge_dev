## Context

El laboratorio necesita integrarse con un sistema LIMS de agroindustria. Actualmente el sistema SIP-Edge tiene un puerto RS-485 para la báscula. Se agrega un puerto RS-232 independiente dedicado exclusivamente al envío de tramas al LIMS. La trama es un CSV plano con campos separados por coma, que el LIMS interpreta en su extremo.

El formulario de pesaje en kiosko recolecta: tipo de material (caña/materia extraña), peso, hacienda, suerte, guía y vagón. El botón "Enviar a LIMS" validará completitud antes de habilitarse.

## Goals / Non-Goals

**Goals:**
- Implementar driver serial RS-232 independiente para envío a LIMS
- Construir trama CSV con el formato específico solicitado
- Agregar botón "Enviar a LIMS" en UI de kiosko con validación de completitud
- Agregar configuración de puerto LIMS en interfaz Admin

**Non-Goals:**
- Recibir datos del LIMS (solo envío unidireccional)
- Implementar protocolo de confirmación/ACK desde LIMS
- Modificar el driver RS-485 de la báscula

## Decisions

1. **Driver serial independiente**: Se implementa como un driver separado del de la báscula, con su propia configuración en `config.yaml` (`lims.port`, `lims.baudrate`, `lims.parity`). Esto evita acoplamiento y permite operación simultánea.

2. **Trama como CSV plano sin formato binario**: El LIMS espera texto plano CSV. No se requiere delimitador de fin de línea especial ni checksum. Se envía como string ASCII terminado en CR+LF.

3. **Id autoincremental por sesión**: El Id de la trama se genera como secuencia autoincremental dentro del archivo de configuración o base de datos, para mantener consistencia incluso tras reinicios.

4. **Validación en frontend vía HTMX**: La habilitación del botón se maneja con un endpoint HTMX que verifica en cada cambio de formulario si todos los campos obligatorios están completos y retorna el estado del botón.

5. **Campos reservados en 0**: Los 7 campos "0" intermedios son fijos. Se envían tal cual sin modificación, ya que el LIMS espera esa posición exacta.

## Risks / Trade-offs

- [Pérdida de trama] Al ser envío unidireccional sin ACK, no hay confirmación de que el LIMS recibió la trama → Mitigación: Añadir log de envío con timestamp y opción de reintento manual.
- [Contención de puertos] RS-232 compartido con otro periférico futuro podría causar conflictos → Mitigación: Puerto dedicado y documentado exclusivamente para LIMS.
- [Secuencia de Id] Si el Id se reinicia (ej: formateo del sistema), el LIMS podría detectar duplicados → Mitigación: Iniciar desde el último Id disponible en BD + 1.

## Open Questions

- ¿El LIMS espera un terminador específico (CR, LF, CR+LF)?
- ¿El LIMS puede recibir tramas a alta velocidad si el operador envía varias en poco tiempo? ¿Hay rate limiting necesario?
- ¿Se debe almacenar la trama enviada en BD para trazabilidad?
