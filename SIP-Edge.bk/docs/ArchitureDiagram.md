```mermaid
graph TD
    subgraph "Capa de Presentación"
        UI[Navegador HTML/HTMX] <-->|WebSocket| API
        UI <-->|HTTP| API
    end

    subgraph "Capa de Aplicación Backend FastAPI"
        API[API Router / Controladores]
        
        subgraph "Servicios de Dominio"
            S_Auth[Servicio Autenticación]
            S_Weigh[Servicio Pesaje]
            S_Report[Servicio Reportes/Telegram]
        end
        
        subgraph "Gestores de Hardware Singletons"
            HW_Cam[Camera Manager]
            HW_Serial[Serial Manager]
        end

        subgraph "Motores IA"
            AI_Vision[Motor Biometría InsightFace]
            AI_LLM[Motor LLM Llama.cpp]
        end
    end

    subgraph "Capa de Datos"
        DB[(MariaDB)]
        VDB[(ChromaDB - Manuales)]
    end

    API --> S_Auth
    API --> S_Weigh
    API --> S_Report

    S_Auth --> HW_Cam
    S_Auth --> AI_Vision
    
    S_Weigh --> HW_Serial
    
    S_Report --> AI_LLM
    
    S_Weigh --> DB
    S_Report --> DB & VDB
