# 🤖 Protocolo de Inicio (Bootstrapping)

## 🎯 Propósito del Archivo
Este documento define el **Proceso de Arranque (Bootstrapping)** para cualquier nuevo proyecto generado por los agentes de IA. Asegura que cada proyecto tenga una estructura de directorios consistente y disponga de todas las herramientas necesarias desde el primer momento.

## 📋 Reglas Generales de Creación de Proyectos
Al crear un nuevo proyecto, los agentes deben:

1.  **Consultar `_agents/constitution.md`**:
    *   Leer la Constitución del Agente para entender los estándares, licencias y pautas éticas.
    *   **Nota**: La constitución actual está en blanco. Se debe crear este archivo.

2.  **Generar Estructura Estándar**:
    Crear la siguiente jerarquía de directorios:
    ```
    nombre-del-proyecto/
    ├── .claude/               # Configuración de Claude AI
    ├── _agents/               # Agentes personalizados del proyecto
    │   └── constitution.md    # (A crear) Constitución del Proyecto
    ├── _docs/                 # Documentación del proyecto
    │   ├── architecture.md    # Arquitectura
    │   └── requirements.md    # Requisitos
    ├── src/                   # Código fuente
    │   └── main.py            # Punto de entrada
    └── .env                   # Variables de entorno
    ```

## 🚀 Prompt de Ejecución

Para generar un nuevo proyecto, ejecuta el siguiente comando en tu terminal:

```bash
./bootstrap-project.sh <nombre-del-proyecto>
```

O, si estás usando un agente específico:

"Hola Antigravity, crea un nuevo proyecto llamado `<nombre-del-proyecto>` con la estructura estándar definida en `_agents/readme.md`."

## 🛠️ Herramientas Disponibles

El sistema incluye las siguientes herramientas para la gestión y desarrollo de proyectos:

*   **`_agents/constitution.md`**: Plantilla para definir la constitución del agente.
*   **`_docs/architecture.md`**: Plantilla para la documentación de arquitectura.
*   **`_docs/requirements.md`**: Plantilla para la documentación de requisitos.
*   **`bootstrap-project.sh`**: Script para automatizar la creación de proyectos.