import sqlite3
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from typing import Optional

# Herramienta 1: Consultar Pesajes
class QueryWeighingData(BaseModel):
    """Consulta registros históricos de pesaje en la base de datos."""
    hacienda_id: Optional[int] = Field(None, description="ID de la hacienda para filtrar.")
    suerte_id: Optional[int] = Field(None, description="ID de la suerte/lote.")
    limit: int = Field(10, description="Número de registros a recuperar (máximo 50).")

# Herramienta 2: Detección de Anomalías
class DetectAnomalies(BaseModel):
    """Ejecuta análisis estadístico Z-score sobre los pesajes recientes."""
    n_records: int = Field(120, description="Cantidad de registros recientes a analizar.")
    threshold: float = Field(3.0, description="Umbral de desviación (Z-score). Por defecto 3.0.")

# Herramienta 3: Notificación SMS
class SendSMSAlert(BaseModel):
    """Envía una alerta o reporte vía SMS a un rol específico."""
    recipient_role: str = Field(..., description="Rol del destinatario: 'Gerente' o 'Administrador'.")
    message: str = Field(..., description="Contenido del mensaje SMS (máx 160 caracteres).")
    
class SIPEdgeTools:
    def __init__(self, db_path="materia_prima.db"):
        self.db_path = db_path

    def query_weighing_data(self, hacienda_id=None, suerte_id=None, limit=10):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM registros WHERE 1=1"
        params = []
        
        if hacienda_id:
            query += " AND hacienda_id = ?"
            params.append(hacienda_id)
        if suerte_id:
            query += " AND suerte_id = ?"
            params.append(suerte_id)
            
        query += f" ORDER BY fecha_hora DESC LIMIT {min(limit, 50)}"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df.to_dict(orient="records")

    def detect_anomalies(self, n_records=120, threshold=3.0):
        conn = sqlite3.connect(self.db_path)
        # Traemos el peso neto para analizar
        df = pd.read_sql_query(f"SELECT id, peso_neto FROM registros ORDER BY fecha_hora DESC LIMIT {n_records}", conn)
        conn.close()
        
        if df.empty: return "No hay datos suficientes."

        # Lógica Z-Score
        df['z_score'] = (df['peso_neto'] - df['peso_neto'].mean()) / df['peso_neto'].std()
        anomalies = df[df['z_score'].abs() > threshold]
        
        if anomalies.empty:
            return "No se detectaron anomalías en los últimos registros."
        return anomalies.to_dict(orient="records")

    def send_sms_alert(self, recipient_role, message):
        # En el piloto, solo simulamos el envío (mock)
        # Aquí irían los comandos AT para el módulo EC25-AUXGR
        print(f"\n[MÓDULO GSM] Enviando SMS a {recipient_role}: {message}")
        return {"status": "success", "sent_to": recipient_role}