# Manual de Administración — SIP-Edge

**SIP-Edge** (Sistema Inteligente de Pesaje) es una plataforma para el registro,
análisis y reporte de pesajes de caña de azúcar en centrales azucareros. Este
manual cubre las tareas administrativas esenciales.

> **Acceso:** El panel de administración está en `http://<ip-del-servidor>:8000`.
> En la EdgeBox: `http://192.168.1.42:8000`. En desarrollo local: `http://127.0.0.1:8000`.
> **Debe iniciar sesión con un usuario de rol `admin`.**

---

## 1. Gestión de Usuarios

### 1.1 Acceder al panel

Después de iniciar sesión, navegue a **Admin > Usuarios**. Verá una tabla con
todos los usuarios del sistema:

```
+------------------+------------------+---------------+------------+----------+------+
| Usuario          | Nombre Completo  | Cód. Empresa  | Teléfono   | Rol      | ...  |
+------------------+------------------+---------------+------------+----------+------+
| jperez           | Juan Pérez       | EMP001        | 57300...   | operator | Sí   |
| mlopez           | María López      | CORR012       | 57300...   | corr...  | Sí   |
| admin            | Administrador    | ADMIN01       | —          | admin    | Sí   |
+------------------+------------------+---------------+------------+----------+------+
```

La tabla incluye paginación (10, 20, 50 o 100 registros por página).

### 1.2 Crear un nuevo usuario

Haga clic en el botón **+ Nuevo Usuario**. Se abrirá un formulario con los
siguientes campos:

| Campo | Descripción | Requerido |
|-------|-------------|:---------:|
| **Usuario** | Nombre único para iniciar sesión | Sí |
| **Contraseña** | Contraseña de acceso | Sí |
| **Nombre Completo** | Nombre real del usuario | Sí |
| **Código Empresa** | Documento o código de empleado | Sí |
| **Teléfono** | Número celular (para recibir SMS de reportes y alertas) | Sí |
| **Rol** | Ver roles disponibles abajo | Sí |

Llene los campos y presione **Guardar**. Si el nombre de usuario ya existe, verá
el mensaje: _"Ya existe un usuario con este nombre. Elija otro nombre."_

### 1.3 Roles disponibles

| Rol | Permisos |
|-----|----------|
| **admin** | Acceso total: gestión de usuarios, configuración del sistema, reportes, kiosko de pesaje |
| **operator** | Solo kiosko de pesaje (registrar muestras en la báscula) |
| **corresponsal** | Solo consultas vía SMS (recibe reportes programados y alertas de anomalías) |

### 1.4 Editar un usuario existente

En la tabla, haga clic en el ícono ✏️ junto al usuario. El formulario de
edición permite modificar:

- Nombre Completo, Código Empresa, Teléfono, Rol
- Activar/desactivar (checkbox **Activo**)
- Cambiar contraseña (opcional: deje el campo **Nueva Contraseña** vacío si no desea cambiarla)

> **Nota:** El nombre de usuario (username) no se puede modificar una vez creado.

### 1.5 Desactivar un usuario

Haga clic en el ícono 🗑️ junto al usuario y confirme. La desactivación es un
**borrado lógico**: el usuario deja de poder iniciar sesión pero sus datos
permanecen en los registros históricos de pesajes.

Para reactivar, edite el usuario y marque el checkbox **Activo**.

### 1.6 Restablecer contraseña vía SMS

Los usuarios pueden solicitar el restablecimiento de contraseña enviando un SMS
al número del sistema con el comando:

```
reset password <usuario>
```

Ejemplo: `reset password jperez`

El sistema genera una nueva contraseña y la envía por SMS al teléfono registrado
del usuario. Solo funciona si el usuario tiene un teléfono registrado en el
sistema.

---

## 2. Plantillas de Reportes Programados

### 2.1 Acceder al panel

Navegue a **Admin > Reportes**. Verá la lista de plantillas configuradas:

```
+---------------------+----------------------+-----------------------------+------+
| Nombre              | Schedule             | Métricas                    | Act. |
+---------------------+----------------------+-----------------------------+------+
| Reporte Mañana      | 07:00, 08:00         | count, avg, min_max, trend  | Sí   |
| Resumen Diario      | 18:00                | count, breakdown_by_hacien. | Sí   |
+---------------------+----------------------+-----------------------------+------+
```

### 2.2 Crear una plantilla

Presione **+ Nueva Plantilla** y configure:

| Sección | Descripción |
|---------|-------------|
| **Nombre** | Identificador de la plantilla (ej. "Reporte Mañana") |
| **Horarios de envío** | Seleccione una o más horas del día (formato 24h) |
| **Métricas** | Marque las métricas que desea incluir (ver abajo) |
| **Destinatarios** | Busque y seleccione usuarios con rol admin o corresponsal. Solo reciben SMS los usuarios que tienen un número de teléfono registrado. |
| **Activo** | Checkbox para activar/desactivar la plantilla sin eliminarla |

Presione **Guardar**.

### 2.3 Métricas disponibles

| Métrica | Descripción | Ejemplo de salida |
|---------|-------------|-------------------|
| **Cantidad de pesajes** (`count`) | Total de registros del día | `Total pesajes: 47` |
| **Promedio de pesos** (`avg`) | Peso promedio en kg | `Peso promedio: 28.5 kg` |
| **Mínimo y máximo** (`min_max`) | Peso mínimo y máximo del día | `Min: 12.3 kg \| Max: 52.1 kg` |
| **Desglose por hacienda** (`breakdown_by_hacienda`) | Pesajes y kg agrupados por hacienda | `H1: 15p/430kg \| H2: 32p/912kg` |
| **Desglose por operador** (`breakdown_by_operator`) | Pesajes y kg agrupados por operador | `jperez: 20p/570kg \| mlopez: 27p/772kg` |
| **Composición de materia** (`composition`) | Proporciones Muestra/Mineral/Vegetal | `M=85% Min=10% Veg=5%` |
| **Cantidad de anomalías** (`anomaly_count`) | Total de anomalías detectadas hoy | `Anomalias hoy: 3` |
| **Tendencia** (`trend`) | Comparación del peso total vs día anterior | `Tendencia: sube 12.4% vs ayer` |
| **Desviación estándar** (`std`) | Variabilidad en los pesos del día | `Desviacion estandar: 8.23 kg` |

### 2.4 Editar y eliminar plantillas

- **Editar:** ✏️ Modifique cualquier campo de la plantilla.
- **Eliminar:** 🗑️ La plantilla se elimina permanentemente. Confirme en el diálogo.

### 2.5 Funcionamiento

Cada hora, en los horarios configurados, el sistema genera un reporte con las
métricas seleccionadas y lo envía por SMS a los destinatarios. El reporte tiene
el formato:

```
Reporte Resumen Mañana [2026-07-20]
====================================
Total pesajes: 47
Peso promedio: 28.5 kg
Tendencia: sube 12.4% vs ayer
```

---

## 3. Consultas vía SMS

### 3.1 Cómo funciona

El sistema procesa consultas en lenguaje natural enviadas por SMS al número del
EdgeBox. Las respuestas se generan usando inteligencia artificial local (modelo
LLM en el dispositivo), sin conexión a internet.

### 3.2 Ejemplos de consultas

| Consulta | Qué devuelve |
|----------|-------------|
| `estadísticas básicas de hoy` | Total de pesajes, promedio, mínimo y máximo del día actual |
| `resumen del turno mañana` | Pesajes registrados en la mañana (00:00–11:59) |
| `top 5 haciendas esta semana` | Las 5 haciendas con más kilos en la semana actual |
| `tasa de anomalías en julio` | Porcentaje de pesajes anómalos en julio de 2026 |
| `compara julio vs junio` | Comparación de totales entre dos meses |
| `notas del vagón V1234` | Notas registradas en los pesajes del vagón V1234 |
| `y ayer?` | **Seguimiento:** si preguntó por "hoy", ahora pregunta por "ayer" |
| `y la hacienda XYZ?` | **Seguimiento:** aplica el filtro de hacienda a la consulta anterior |

### 3.3 Comandos del sistema

Además de consultas de datos, el sistema reconoce los siguientes comandos:

| Comando | Efecto |
|---------|--------|
| `manual on` | Activa el modo manual de emergencia por tiempo predeterminado |
| `manual on ext 2h` | Extiende el modo manual 2 horas adicionales |
| `manual on ext 30m` | Extiende el modo manual 30 minutos adicionales |
| `manual off` | Desactiva el modo manual de emergencia |
| `reset password <usuario>` | Restablece la contraseña del usuario indicado |

### 3.4 Mensaje de ayuda

Si el sistema no reconoce su consulta o comando, responde con un mensaje
indicando la sintaxis correcta y los comandos disponibles.

### 3.5 Características del servicio SMS

- **Límite por mensaje:** Cada respuesta SMS se limita a 160 caracteres (hasta
  3 segmentos concatenados = 480 caracteres).
- **Conversaciones multiturno:** Puede hacer preguntas de seguimiento como
  _"y ayer?"_ o _"y de la hacienda Las Palmas?"_. El sistema mantiene el
  contexto de los mensajes anteriores.
- **Formato de fechas:** El sistema usa el formato `24 jun 2026` (sin barras)
  para evitar bloqueos del operador SMS.
- **Hora de referencia:** El sistema conoce la fecha actual y puede interpretar
  expresiones relativas como _"hoy"_, _"ayer"_, _"esta semana"_, _"este mes"_.
- **Usuarios corresponsales:** Si el remitente tiene rol `corresponsal`, solo
  puede hacer consultas de datos. Si intenta ejecutar comandos del sistema,
  recibe la respuesta: _"Solo puedo responder consultas sobre datos de pesaje."_
- **Despedida:** Al enviar _"gracias"_, _"bye"_ o similares, el sistema
  responde con un mensaje de despedida y cierra la conversación.

```
Remitente                        SIP-Edge
    |                                |
    |--- "estadísticas de hoy" ---->|
    |                                |--- "Hoy: 47 pesajes, promedio 28.5 kg..."
    |<------------------------------|
    |--- "y anomalías?" ----------->|
    |                                |--- "Anomalias hoy: 3"
    |<------------------------------|
    |--- "gracias" ---------------->|
    |                                |--- "Ha sido un gusto ayudarte. Conversacion finalizada."
    |<------------------------------|
```

---

## 4. Límites de Control (Configuración)

> Acceda a **Admin > Configuración** y ubique la sección **Límites de Control**.

Estos parámetros definen qué tan sensible es el sistema para detectar pesajes
anómalos. Ajuste estos valores según las características operativas de su
central.

### 4.1 Parámetros

| # | Parámetro | Valor por defecto | Rango | Descripción |
|---|-----------|:-----------------:|-------|-------------|
| 1 | **Umbral Z-Score** | 3.0 σ | 1.0 – 10.0 | Desviaciones estándar para considerar un pesaje como anómalo. **Más alto = menos sensible.** Un valor de 3.0 es el estándar estadístico para detectar outliers. |
| 2 | **Ventana de Análisis** | 120 registros | 30 – 500 | Cantidad de pesajes recientes que el sistema evalúa para detectar anomalías. Una ventana más grande da más contexto estadístico pero tarda más en adaptarse a cambios. |
| 3 | **Ventana Horaria** | 4 horas | 1 – 48 | Período de tiempo que cubre la ventana de análisis. Ajuste según la duración típica de un turno de pesaje. |
| 4 | **Ratio Máx. Vegetal/Muestra** | 0.5% | 0.01 – 1.0 | Proporción máxima permitida entre materia extraña vegetal y el peso de la muestra. Si se supera, el pesaje se marca como violación. |
| 5 | **Ratio Máx. Mineral/Muestra** | 0.3% | 0.01 – 1.0 | Igual que el anterior, pero para materia extraña mineral (piedras, tierra). |
| 6 | **Tasa Máx. de Cambio** | 0.5% | 0.01 – 1.0 | Cambio máximo permitido como fracción entre dos pesajes consecutivos. Valores cercanos a 1.0 permiten cambios más bruscos. |
| 7 | **Máx. Anomalías Consecutivas** | 3 alertas | 1 – 20 | Número de anomalías consecutivas necesarias para disparar una alerta SMS a los corresponsales. **Valores bajos = más alertas.** |

### 4.2 Cómo guardar

Después de modificar cualquier parámetro, presione el botón **Guardar
Configuración** al final de la página. Este botón guarda TODOS los cambios
pendientes: puertos seriales, módem GSM, límites de control y timeouts.

### 4.3 Otras secciones de configuración

La página **Configuración** también contiene:

| Sección | Propósito |
|---------|-----------|
| **Puerto RS485 (Báscula)** | Configurar el puerto serial de la báscula DINI ARGEO DFW06L |
| **Puerto RS232 (PC Externo)** | Configurar el puerto de transmisión a PC externo |
| **Módem GSM** | Índice del módem 4G (ModemManager) |
| **Timeouts** | Session Timeout (minutos de inactividad para cerrar sesión) y Scale Timeout (segundos de espera de la báscula) |

Cada sección de puerto serial incluye un botón **Test** naranja para verificar
la comunicación con el hardware.

---

## 5. Solución de Problemas Comunes

### 5.1 "No puedo iniciar sesión"

1. **Verifique el nombre de usuario y contraseña.** Distinga mayúsculas/minúsculas.
2. **¿El usuario está activo?** Pídale a otro administrador que revise en
   Admin > Usuarios si el checkbox **Activo** está marcado.
3. **¿La sesión expiró?** Por defecto, las sesiones expiran tras 15 minutos de
   inactividad. Vuelva a la página de inicio de sesión e intente de nuevo.
4. **Restablezca su contraseña:** Si tiene un teléfono registrado en el sistema,
   envíe un SMS al número del EdgeBox con el comando:
   ```
   reset password <su_usuario>
   ```
   Recibirá una nueva contraseña por SMS.

### 5.2 "No recibo SMS"

1. **Verifique que su teléfono esté registrado correctamente.** En Admin >
   Usuarios, revise la columna **Teléfono** de su usuario. El formato debe ser
   número completo (ej. `573001234567`), sin espacios ni guiones.
2. **Verifique que sea destinatario de la plantilla.** En Admin > Reportes,
   edite la plantilla y confirme que su usuario esté seleccionado en la lista de
   **Destinatarios**.
3. **Verifique cobertura celular.** El EdgeBox usa el módem 4G Quectel EC25.
   Si hay poca señal, los SMS pueden demorar o no entregarse.
4. **Reportes programados:** Los reportes solo se envían si la plantilla está
   **Activa** y tiene al menos un horario y una métrica configurados.

### 5.3 "El agente responde con fechas incorrectas"

Al consultar por SMS, siga estas recomendaciones:

1. **Use expresiones relativas** en lugar de fechas explícitas cuando sea
   posible: _"hoy"_, _"ayer"_, _"esta semana"_, _"este mes"_, _"julio"_.
2. **No use fechas con barras** (ej. `24/06/2026`). El operador SMS puede
   bloquear las barras. El sistema formatea sus respuestas como `24 jun 2026`.
3. **El año por defecto es 2026.** Si consulta _"24 de junio"_ sin especificar
   el año, el sistema asume 2026.
4. **Para comparar períodos**, sea explícito: _"compara julio 2026 vs junio
   2026"_. El sistema interpreta los nombres de meses en español
   (enero, febrero, ...).

### 5.4 "La báscula no se comunica"

1. En Admin > Configuración, sección **Puerto RS485 (Báscula)**, presione
   **Test RS485**. Si falla, revise:
   - Que el dispositivo (ej. `/dev/ttyACM0`) sea correcto.
   - Que los parámetros (baudrate, paridad, data bits, stop bits) coincidan con
     los de la báscula DFW06L.
   - Para la DFW06L, los valores típicos son: 115200 baud, 8N1.
2. Verifique que la báscula esté encendida y conectada al puerto RS485 del
   EdgeBox.

### 5.5 "El sistema está en modo manual"

Si un operador activó el modo manual de emergencia (por falla de hardware), el
sistema no leerá la báscula automáticamente. Para desactivarlo:

1. Envíe un SMS al número del sistema: `manual off`
2. O desde Admin > Configuración, verifique el estado del sistema.
3. El modo manual se activa/desactiva mediante el comando SMS `manual on` /
   `manual off`.

---

## Referencia Rápida

| Tarea | Ruta en la UI |
|-------|--------------|
| Crear usuario | Admin > Usuarios > **+ Nuevo Usuario** |
| Editar/desactivar usuario | Admin > Usuarios > ✏️ / 🗑️ |
| Ver/crear plantillas | Admin > Reportes > **+ Nueva Plantilla** |
| Ajustar límites de control | Admin > Configuración > sección **Límites de Control** |
| Probar puertos | Admin > Configuración > **Test RS485** / **Test RS232** / **Test GSM** |
| Consultas SMS | Enviar SMS al número del EdgeBox (lenguaje natural) |
| Restablecer contraseña | SMS: `reset password <usuario>` |
| Modo manual emergencia | SMS: `manual on` / `manual off` |

---

## Información del EdgeBox

| Dato | Valor |
|------|-------|
| **IP Ethernet** | 192.168.1.42 |
| **Acceso SSH** | `ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42` |
| **API** | `http://192.168.1.42:8000` |
| **Health check** | `http://192.168.1.42:8000/health` |
| **Base de datos** | MariaDB 11.8.6, base `sip_edge`, usuario `sip_user` |
| **Puerto báscula** | RS485 — `/dev/ttyACM0` |
| **Puerto PC externo** | RS232 — `/dev/ttyACM1` |

---

*SIP-Edge — Sistema Inteligente de Pesaje*
*Documento generado julio 2026*
