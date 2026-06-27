"""Catalogo de 12 herramientas SQL parametrizadas invocables por el LLM."""

import logging
from datetime import date, datetime, time

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.models import AnomalyLog, Hacienda, User, Weighing

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Se lanza cuando una herramienta SQL falla."""


TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_basic_stats",
            "description": "Obtiene estadisticas basicas (count, avg, min, max, std) de los pesajes en un rango de fechas, opcionalmente filtradas por tipo de material y tipo de cosecha.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_material": {"type": "string", "description": "muestra, mineral, vegetal o null para peso total"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_percentiles",
            "description": "Calcula el percentil especifico del peso en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "percentil": {"type": "number", "description": "Percentil deseado (0-100)"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha_inicio", "fecha_fin", "percentil"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_moving_average",
            "description": "Calcula el promedio movil de los ultimos N pesajes para un tipo de material.",
            "parameters": {
                "type": "object",
                "properties": {
                    "window_size": {"type": "integer", "description": "Numero de registros en la ventana"},
                    "tipo_material": {"type": "string", "description": "muestra, mineral, vegetal o null para peso total"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["window_size"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend",
            "description": "Calcula la pendiente de regresion lineal simple sobre los pesos en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_material": {"type": "string", "description": "muestra, mineral, vegetal o null para peso total"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_breakdown_by_hacienda",
            "description": "Desglose de pesajes agregados por hacienda en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_breakdown_by_operator",
            "description": "Desglose de pesajes agregados por operador en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_material_composition",
            "description": "Calcula la proporcion de muestra, mineral y vegetal en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_shift_summary",
            "description": "Reporte completo de un turno especifico (fecha + turno).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha": {"type": "string", "description": "Fecha formato YYYY-MM-DD"},
                    "turno": {"type": "string", "description": "Turno: manana (00:00-06:00), tarde (06:00-14:00), noche (14:00-22:00), madrugada (22:00-24:00)"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha", "turno"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_daily_summary",
            "description": "Resumen agregado de un dia completo (00:00-23:59).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha": {"type": "string", "description": "Fecha formato YYYY-MM-DD"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_custom_period_summary",
            "description": "Resumen completo de un periodo personalizado entre dos fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_anomalies",
            "description": "Detecta anomalias en el registro de pesajes usando Z-Score en una ventana movil.",
            "parameters": {
                "type": "object",
                "properties": {
                    "window_size": {"type": "integer", "description": "Numero de registros en la ventana"},
                    "z_threshold": {"type": "number", "description": "Umbral de Z-Score para considerar anomalia"},
                },
                "required": ["window_size", "z_threshold"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_thresholds",
            "description": "Evalua los pesajes recientes contra los umbrales de materiales configurados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "window_size": {"type": "integer", "description": "Numero de registros a evaluar"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                },
                "required": ["window_size"],
            },
        },
    },
]


class SqlTools:
    """Catalogo de 12 herramientas SQL parametrizadas.

    Cada herramienta ejecuta consultas SQL directas contra la BD de pesajes
    y retorna resultados reales (sin alucinaciones del LLM).
    """

    def __init__(self, db_session_factory) -> None:
        self._db_session_factory = db_session_factory

    def _get_db(self) -> Session:
        """Obtiene una sesion de BD temporal."""
        return self._db_session_factory()

    # ------------------------------------------------------------------
    # Herramientas de estadisticas (T5)
    # ------------------------------------------------------------------

    def get_basic_stats(self, fecha_inicio: str, fecha_fin: str, tipo_material: str | None = None, tipo_cosecha: str | None = None) -> dict:
        """Count, avg, min, max, std de los pesajes en un rango."""
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            weight_expr = self._weight_column(tipo_material)
            query = (
                db.query(
                    func.count(Weighing.id).label("count"),
                    func.coalesce(func.avg(weight_expr), 0).label("avg"),
                    func.coalesce(func.min(weight_expr), 0).label("min"),
                    func.coalesce(func.max(weight_expr), 0).label("max"),
                )
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            row = query.first()
            # Calculate std separately
            total = float(row.count)
            if total > 1:
                mean = float(row.avg)
                rows_query = (
                    db.query(weight_expr)
                    .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
                )
                if tipo_cosecha:
                    rows_query = rows_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
                rows = rows_query.all()
                variance = sum((float(r[0]) - mean) ** 2 for r in rows) / (total - 1)
                std = variance ** 0.5
            else:
                std = 0.0
            return {
                "count": int(row.count),
                "avg": round(float(row.avg), 2),
                "min": round(float(row.min), 2),
                "max": round(float(row.max), 2),
                "std": round(std, 2),
            }
        finally:
            db.close()

    def get_percentiles(self, fecha_inicio: str, fecha_fin: str, percentil: float, tipo_cosecha: str | None = None) -> dict:
        """Calcula el percentil especifico de peso total."""
        if not 0 <= percentil <= 100:
            raise ToolExecutionError(f"Percentil debe estar entre 0 y 100: {percentil}")
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            total_weight = (
                Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
            )
            query = (
                db.query(total_weight)
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            rows = query.order_by(total_weight).all()
            values = [float(r[0]) for r in rows]
            if not values:
                return {"percentil": percentil, "valor": 0.0, "count": 0}
            n = len(values)
            k = (percentil / 100.0) * (n - 1)
            f = int(k)
            c_idx = min(f + 1, n - 1)
            if f == c_idx:
                result = values[f]
            else:
                result = values[f] + (k - f) * (values[c_idx] - values[f])
            return {"percentil": percentil, "valor": round(result, 2), "count": n}
        finally:
            db.close()

    def get_moving_average(self, window_size: int, tipo_material: str | None = None, tipo_cosecha: str | None = None) -> dict:
        """Promedio movil de los ultimos N pesajes."""
        if window_size <= 0:
            raise ToolExecutionError(f"window_size debe ser > 0: {window_size}")
        db = self._get_db()
        try:
            weight_expr = self._weight_column(tipo_material)
            query = (
                db.query(weight_expr)
                .order_by(Weighing.id.desc())
                .limit(window_size)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            rows = query.all()
            values = [float(r[0]) for r in rows]
            if not values:
                return {"window_size": window_size, "moving_average": 0.0, "count": 0}
            avg = sum(values) / len(values)
            return {"window_size": window_size, "moving_average": round(avg, 2), "count": len(values)}
        finally:
            db.close()

    def get_trend(self, fecha_inicio: str, fecha_fin: str, tipo_material: str | None = None, tipo_cosecha: str | None = None) -> dict:
        """Pendiente de regresion lineal simple."""
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            weight_expr = self._weight_column(tipo_material)
            query = (
                db.query(Weighing.id, weight_expr)
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            rows = query.order_by(Weighing.id).all()
            n = len(rows)
            if n < 2:
                return {"pendiente": 0.0, "count": n, "interpretacion": "Datos insuficientes"}
            x_vals = list(range(n))
            y_vals = [float(r[1]) for r in rows]
            sum_x = sum(x_vals)
            sum_y = sum(y_vals)
            sum_xy = sum(x_vals[i] * y_vals[i] for i in range(n))
            sum_x2 = sum(x * x for x in x_vals)
            denominator = n * sum_x2 - sum_x * sum_x
            if denominator == 0:
                slope = 0.0
            else:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
            interpretation = "estable" if abs(slope) < 0.1 else ("creciente" if slope > 0 else "decreciente")
            return {
                "pendiente": round(slope, 4),
                "count": n,
                "promedio": round(sum_y / n, 2) if n > 0 else 0.0,
                "interpretacion": interpretation,
            }
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Herramientas de desglose (T6)
    # ------------------------------------------------------------------

    def get_breakdown_by_hacienda(self, fecha_inicio: str, fecha_fin: str, tipo_cosecha: str | None = None) -> list[dict]:
        """Desglose de pesajes por hacienda con JOIN."""
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            query = (
                db.query(
                    Hacienda.id,
                    Hacienda.codigo,
                    Hacienda.nombre,
                    func.count(Weighing.id).label("count"),
                    func.coalesce(func.sum(
                        Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
                    ), 0).label("total_weight"),
                    func.coalesce(func.avg(
                        Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
                    ), 0).label("avg_weight"),
                )
                .join(Hacienda, Weighing.hacienda_id == Hacienda.id)
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            rows = query.group_by(Hacienda.id).order_by(func.sum(
                Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
            ).desc()).all()
            return [
                {
                    "hacienda_id": r.id,
                    "codigo": r.codigo,
                    "nombre": r.nombre,
                    "count": int(r.count),
                    "total_weight": round(float(r.total_weight), 2),
                    "avg_weight": round(float(r.avg_weight), 2),
                }
                for r in rows
            ]
        finally:
            db.close()

    def get_breakdown_by_operator(self, fecha_inicio: str, fecha_fin: str, tipo_cosecha: str | None = None) -> list[dict]:
        """Desglose de pesajes por operador con JOIN."""
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            query = (
                db.query(
                    User.id,
                    User.username,
                    User.full_name,
                    func.count(Weighing.id).label("count"),
                    func.coalesce(func.sum(
                        Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
                    ), 0).label("total_weight"),
                )
                .join(User, Weighing.usuario_id == User.id)
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            rows = query.group_by(User.id).order_by(func.sum(
                Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
            ).desc()).all()
            return [
                {
                    "user_id": r.id,
                    "username": r.username,
                    "full_name": r.full_name,
                    "count": int(r.count),
                    "total_weight": round(float(r.total_weight), 2),
                }
                for r in rows
            ]
        finally:
            db.close()

    def get_material_composition(self, fecha_inicio: str, fecha_fin: str, tipo_cosecha: str | None = None) -> dict:
        """Proporcion muestra/mineral/vegetal en el rango de fechas."""
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            query = (
                db.query(
                    func.coalesce(func.sum(Weighing.peso_muestra), 0).label("muestra"),
                    func.coalesce(func.sum(Weighing.peso_mineral), 0).label("mineral"),
                    func.coalesce(func.sum(Weighing.peso_vegetal_extrano), 0).label("vegetal"),
                )
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            row = query.first()
            muestra = float(row.muestra)
            mineral = float(row.mineral)
            vegetal = float(row.vegetal)
            total = muestra + mineral + vegetal
            return {
                "muestra": round(muestra, 2),
                "mineral": round(mineral, 2),
                "vegetal": round(vegetal, 2),
                "total": round(total, 2),
                "pct_muestra": round(muestra / total * 100, 1) if total > 0 else 0.0,
                "pct_mineral": round(mineral / total * 100, 1) if total > 0 else 0.0,
                "pct_vegetal": round(vegetal / total * 100, 1) if total > 0 else 0.0,
            }
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Herramientas de resumen (T7)
    # ------------------------------------------------------------------

    def get_shift_summary(self, fecha: str, turno: str, tipo_cosecha: str | None = None) -> dict:
        """Reporte completo de un turno especifico."""
        SHIFT_HOURS = {
            "manana": ("00:00", "06:00"),
            "tarde": ("06:00", "14:00"),
            "noche": ("14:00", "22:00"),
            "madrugada": ("22:00", "23:59"),
        }
        if turno not in SHIFT_HOURS:
            raise ToolExecutionError(f"Turno desconocido: {turno}. Valores validos: {list(SHIFT_HOURS.keys())}")
        start, end = SHIFT_HOURS[turno]
        db = self._get_db()
        try:
            fd = date.fromisoformat(fecha)
            t_start = time.fromisoformat(start)
            t_end = time.fromisoformat(end)
            # Query with time constraints
            count_query = (
                db.query(func.count(Weighing.id))
                .filter(
                    Weighing.fecha == fd,
                    Weighing.hora >= t_start,
                    Weighing.hora <= t_end,
                )
            )
            if tipo_cosecha:
                count_query = count_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            count = count_query.scalar() or 0
            row_query = (
                db.query(
                    func.coalesce(func.sum(Weighing.peso_muestra), 0).label("muestra"),
                    func.coalesce(func.sum(Weighing.peso_mineral), 0).label("mineral"),
                    func.coalesce(func.sum(Weighing.peso_vegetal_extrano), 0).label("vegetal"),
                )
                .filter(
                    Weighing.fecha == fd,
                    Weighing.hora >= t_start,
                    Weighing.hora <= t_end,
                )
            )
            if tipo_cosecha:
                row_query = row_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            row = row_query.first()
            total = float(row.muestra) + float(row.mineral) + float(row.vegetal)
            return {
                "fecha": fecha,
                "turno": turno,
                "horario": f"{start}-{end}",
                "count": int(count),
                "peso_total": round(total, 2),
                "muestra": round(float(row.muestra), 2),
                "mineral": round(float(row.mineral), 2),
                "vegetal": round(float(row.vegetal), 2),
            }
        finally:
            db.close()

    def get_daily_summary(self, fecha: str, tipo_cosecha: str | None = None) -> dict:
        """Resumen agregado de un dia completo."""
        db = self._get_db()
        try:
            fd = date.fromisoformat(fecha)
            count_query = (
                db.query(func.count(Weighing.id))
                .filter(Weighing.fecha == fd)
            )
            if tipo_cosecha:
                count_query = count_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            count = count_query.scalar() or 0
            row_query = (
                db.query(
                    func.coalesce(func.sum(Weighing.peso_muestra), 0).label("muestra"),
                    func.coalesce(func.sum(Weighing.peso_mineral), 0).label("mineral"),
                    func.coalesce(func.sum(Weighing.peso_vegetal_extrano), 0).label("vegetal"),
                )
                .filter(Weighing.fecha == fd)
            )
            if tipo_cosecha:
                row_query = row_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            row = row_query.first()
            total = float(row.muestra) + float(row.mineral) + float(row.vegetal)
            avg_weight = round(total / count, 2) if count > 0 else 0.0
            return {
                "fecha": fecha,
                "count": int(count),
                "peso_total": round(total, 2),
                "peso_promedio": avg_weight,
                "muestra": round(float(row.muestra), 2),
                "mineral": round(float(row.mineral), 2),
                "vegetal": round(float(row.vegetal), 2),
            }
        finally:
            db.close()

    def get_custom_period_summary(self, fecha_inicio: str, fecha_fin: str, tipo_cosecha: str | None = None) -> dict:
        """Resumen completo de un periodo personalizado."""
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            count_query = (
                db.query(func.count(Weighing.id))
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                count_query = count_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            count = count_query.scalar() or 0
            row_query = (
                db.query(
                    func.coalesce(func.sum(Weighing.peso_muestra), 0).label("muestra"),
                    func.coalesce(func.sum(Weighing.peso_mineral), 0).label("mineral"),
                    func.coalesce(func.sum(Weighing.peso_vegetal_extrano), 0).label("vegetal"),
                    func.coalesce(func.avg(
                        Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
                    ), 0).label("avg_weight"),
                )
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                row_query = row_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            row = row_query.first()
            total = float(row.muestra) + float(row.mineral) + float(row.vegetal)
            # Distinct haciendas
            hacienda_query = (
                db.query(func.count(func.distinct(Weighing.hacienda_id)))
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                hacienda_query = hacienda_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            hacienda_count = hacienda_query.scalar() or 0
            return {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "count": int(count),
                "peso_total": round(total, 2),
                "peso_promedio": round(float(row.avg_weight), 2),
                "muestra": round(float(row.muestra), 2),
                "mineral": round(float(row.mineral), 2),
                "vegetal": round(float(row.vegetal), 2),
                "haciendas_distintas": int(hacienda_count),
            }
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Herramientas de anomalias (T8)
    # ------------------------------------------------------------------

    def detect_anomalies(self, window_size: int, z_threshold: float) -> list[dict]:
        """Consulta anomaly_log para obtener anomalias recientes detectadas."""
        db = self._get_db()
        try:
            rows = (
                db.query(AnomalyLog)
                .order_by(AnomalyLog.created_at.desc())
                .limit(window_size)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "record_id": r.record_id,
                    "layer": r.layer,
                    "z_score": float(r.z_score) if r.z_score is not None else None,
                    "metric_value": float(r.metric_value),
                    "threshold": float(r.threshold),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        finally:
            db.close()

    def check_thresholds(self, window_size: int, tipo_cosecha: str | None = None) -> dict:
        """Evalua los ultimos N pesajes contra los umbrales configurados."""
        db = self._get_db()
        try:
            query = (
                db.query(
                    Weighing.peso_muestra,
                    Weighing.peso_mineral,
                    Weighing.peso_vegetal_extrano,
                )
                .order_by(Weighing.id.desc())
                .limit(window_size)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            rows = query.all()
            if not rows:
                return {"window_size": window_size, "count": 0, "violations": []}
            violations = []
            for i, (muestra, mineral, vegetal) in enumerate(rows):
                m, mi, v = float(muestra), float(mineral), float(vegetal)
                if m > 0:
                    ratio_veg = v / m
                    ratio_min = mi / m
                    if ratio_veg > 0.5:
                        violations.append({
                            "record_index": i,
                            "tipo": "vegetal_ratio_alto",
                            "valor": round(ratio_veg, 4),
                            "umbral": 0.5,
                        })
                    if ratio_min > 0.3:
                        violations.append({
                            "record_index": i,
                            "tipo": "mineral_ratio_alto",
                            "valor": round(ratio_min, 4),
                            "umbral": 0.3,
                        })
            return {
                "window_size": window_size,
                "count": len(rows),
                "violations": violations,
                "total_violations": len(violations),
            }
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Dispatcher central (T9)
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """Ejecuta la tool por nombre y retorna el resultado.

        Lanza ToolExecutionError si la tool no existe o los parametros son invalidos.
        """
        tool_map = {
            "get_basic_stats": self.get_basic_stats,
            "get_percentiles": self.get_percentiles,
            "get_moving_average": self.get_moving_average,
            "get_trend": self.get_trend,
            "get_breakdown_by_hacienda": self.get_breakdown_by_hacienda,
            "get_breakdown_by_operator": self.get_breakdown_by_operator,
            "get_material_composition": self.get_material_composition,
            "get_shift_summary": self.get_shift_summary,
            "get_daily_summary": self.get_daily_summary,
            "get_custom_period_summary": self.get_custom_period_summary,
            "detect_anomalies": self.detect_anomalies,
            "check_thresholds": self.check_thresholds,
        }
        if tool_name not in tool_map:
            raise ToolExecutionError(f"Herramienta desconocida: {tool_name}")
        try:
            return tool_map[tool_name](**arguments)
        except TypeError as e:
            raise ToolExecutionError(f"Parametros invalidos para {tool_name}: {e}") from e
        except Exception as e:
            raise ToolExecutionError(f"Error ejecutando {tool_name}: {e}") from e

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _weight_column(tipo_material: str | None):
        """Retorna la columna de peso segun el tipo de material."""
        if tipo_material == "muestra":
            return Weighing.peso_muestra
        elif tipo_material == "mineral":
            return Weighing.peso_mineral
        elif tipo_material == "vegetal":
            return Weighing.peso_vegetal_extrano
        else:
            return Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
