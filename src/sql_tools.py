"""Catalogo de 17 herramientas SQL parametrizadas invocables por el LLM."""

import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, time

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
            "description": "Obtiene estadisticas basicas (count, avg, min, max, std) de los pesajes en un rango de fechas, opcionalmente filtradas por tipo de material, tipo de cosecha, tipo de vehiculo y agrupacion por periodo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_material": {"type": "string", "description": "muestra, mineral, vegetal o null para peso total"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                    "agrupacion": {"type": "string", "description": "Agrupar resultados por: dia, semana, mes, turno (opcional)"},
                    "tipo_vehiculo": {"type": "string", "description": "Filtrar por: tractomula, vagon (opcional)"},
                    "periodo": {"type": "string", "description": "Shortcut de fecha: hoy, ayer, ultimos_7_dias, mes_actual, personalizado (opcional)"},
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
            "description": "Desglose de pesajes agregados por hacienda en un rango de fechas, con agrupacion opcional por periodo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                    "agrupacion": {"type": "string", "description": "Agrupar resultados por: dia, semana, mes, turno (opcional)"},
                    "tipo_vehiculo": {"type": "string", "description": "Filtrar por: tractomula, vagon (opcional)"},
                    "periodo": {"type": "string", "description": "Shortcut de fecha: hoy, ayer, ultimos_7_dias, mes_actual, personalizado (opcional)"},
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
            "description": "Resumen completo de un periodo personalizado entre dos fechas, con agrupacion opcional por periodo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "tipo_cosecha": {"type": "string", "description": "Filtro opcional por tipo de cosecha"},
                    "agrupacion": {"type": "string", "description": "Agrupar resultados por: dia, semana, mes, turno (opcional)"},
                    "tipo_vehiculo": {"type": "string", "description": "Filtrar por: tractomula, vagon (opcional)"},
                    "periodo": {"type": "string", "description": "Shortcut de fecha: hoy, ayer, ultimos_7_dias, mes_actual, personalizado (opcional)"},
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
    {
        "type": "function",
        "function": {
            "name": "get_weighing_notes",
            "description": "Obtiene las notas registradas en pesajes, filtrado opcionalmente por vagon y/o rango de fechas. Requiere al menos uno de vagon o fecha_inicio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vagon": {"type": "string", "description": "Filtro opcional por identificador de vagon"},
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin formato YYYY-MM-DD"},
                    "limit": {"type": "integer", "description": "Maximo de registros a retornar (default 20)"},
                },
            },
        },
    },
    # ── Nuevas tools (F33) ──────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_avg_weighing_time",
            "description": "Calcula el tiempo promedio entre pesajes consecutivos en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio en formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin en formato YYYY-MM-DD"},
                    "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"},
                    "periodo": {"type": "string", "description": "Shortcut: hoy, ayer, ultimos_7_dias, mes_actual, personalizado (opcional)"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_anomaly_rate",
            "description": "Calcula la tasa de anomalias (% de pesajes marcados como anomalos vs total).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio en formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin en formato YYYY-MM-DD"},
                    "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"},
                    "periodo": {"type": "string", "description": "Shortcut (opcional)"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_haciendas",
            "description": "Ranking descendente de haciendas por peso total en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Fecha inicio en formato YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fecha fin en formato YYYY-MM-DD"},
                    "limite": {"type": "integer", "description": "Numero maximo de haciendas (default 10)"},
                    "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"},
                    "periodo": {"type": "string", "description": "Shortcut (opcional)"},
                },
                "required": ["fecha_inicio", "fecha_fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_period_comparison",
            "description": "Compara dos periodos: delta absoluto y delta porcentual para count, peso_total, peso_promedio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {"type": "string", "description": "Inicio periodo actual YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "Fin periodo actual YYYY-MM-DD"},
                    "periodo_anterior_inicio": {"type": "string", "description": "Inicio periodo anterior YYYY-MM-DD"},
                    "periodo_anterior_fin": {"type": "string", "description": "Fin periodo anterior YYYY-MM-DD"},
                    "tipo_vehiculo": {"type": "string", "description": "tractomula o vagon (opcional)"},
                },
                "required": ["fecha_inicio", "fecha_fin", "periodo_anterior_inicio", "periodo_anterior_fin"],
            },
        },
    },
]


class SqlTools:
    """Catalogo de 17 herramientas SQL parametrizadas.

    Cada herramienta ejecuta consultas SQL directas contra la BD de pesajes
    y retorna resultados reales (sin alucinaciones del LLM).
    """

    def __init__(self, db_session_factory, agent_config=None) -> None:
        self._db_session_factory = db_session_factory
        self._agent_config = agent_config

    def _get_db(self) -> Session:
        """Obtiene una sesion de BD temporal."""
        return self._db_session_factory()

    # ------------------------------------------------------------------
    # Helpers (F33: shortcuts de fecha y filtro vehiculo)
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_date_shortcut(
        periodo: str | None = None,
        fecha_inicio: str | None = None,
        fecha_fin: str | None = None,
    ) -> tuple[str, str]:
        """Resuelve shortcuts de fecha a rangos (fecha_inicio, fecha_fin).

        Valores de periodo: 'hoy', 'ayer', 'ultimos_7_dias', 'mes_actual', 'personalizado'.
        Si periodo='personalizado', requiere fecha_inicio y fecha_fin explicitos.
        Si periodo es None, usa fecha_inicio/fecha_fin directamente.
        Lanza ToolExecutionError si faltan parametros.
        """
        if periodo is None:
            if not fecha_inicio or not fecha_fin:
                raise ToolExecutionError(
                    "Debe proporcionar fecha_inicio y fecha_fin, o un periodo valido"
                )
            return fecha_inicio, fecha_fin

        today = date.today()
        if periodo == "personalizado":
            if not fecha_inicio or not fecha_fin:
                raise ToolExecutionError(
                    "periodo='personalizado' requiere fecha_inicio y fecha_fin"
                )
            return fecha_inicio, fecha_fin
        elif periodo == "hoy":
            return today.isoformat(), today.isoformat()
        elif periodo == "ayer":
            yesterday = today - timedelta(days=1)
            return yesterday.isoformat(), yesterday.isoformat()
        elif periodo == "ultimos_7_dias":
            start = today - timedelta(days=6)
            return start.isoformat(), today.isoformat()
        elif periodo == "mes_actual":
            start = today.replace(day=1)
            return start.isoformat(), today.isoformat()
        else:
            raise ToolExecutionError(
                f"periodo invalido: '{periodo}'. "
                "Valores validos: hoy, ayer, ultimos_7_dias, mes_actual, personalizado"
            )

    @staticmethod
    def _apply_vehicle_filter(query, tipo_vehiculo: str | None):
        """Agrega filtro WHERE por tipo de vehiculo al query.

        'tractomula' -> Weighing.tractomula != ""
        'vagon' -> Weighing.vagon != ""
        None -> sin filtro.
        Lanza ToolExecutionError si el valor no es reconocido.
        """
        if tipo_vehiculo is None:
            return query
        if tipo_vehiculo == "tractomula":
            return query.filter(Weighing.tractomula != "")
        elif tipo_vehiculo == "vagon":
            return query.filter(Weighing.vagon != "")
        else:
            raise ToolExecutionError(
                f"tipo_vehiculo invalido: '{tipo_vehiculo}'. "
                "Valores validos: tractomula, vagon"
            )

    @staticmethod
    def _compute_period_label(fecha: date, hora: time, agrupacion: str) -> str:
        """Calcula la etiqueta de periodo para agrupacion.

        Args:
            fecha: objeto date del pesaje.
            hora: objeto time del pesaje.
            agrupacion: 'dia', 'semana', 'mes', o 'turno'.

        Returns:
            Etiqueta de periodo (string).
        """
        if agrupacion == "dia":
            return fecha.isoformat()
        elif agrupacion == "semana":
            iso = fecha.isocalendar()
            return f"{iso[0]}-W{iso[1]:02d}"
        elif agrupacion == "mes":
            return f"{fecha.year}-{fecha.month:02d}"
        elif agrupacion == "turno":
            h = hora.hour
            if 0 <= h < 6:
                return "manana"
            elif 6 <= h < 14:
                return "tarde"
            elif 14 <= h < 22:
                return "noche"
            else:
                return "madrugada"
        else:
            raise ToolExecutionError(
                f"agrupacion invalida: '{agrupacion}'. "
                "Valores validos: dia, semana, mes, turno"
            )

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

    # ------------------------------------------------------------------
    # Herramientas de estadisticas (T5)
    # ------------------------------------------------------------------

    def get_basic_stats(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        tipo_material: str | None = None,
        tipo_cosecha: str | None = None,
        agrupacion: str | None = None,
        tipo_vehiculo: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        """Count, avg, min, max, std de los pesajes en un rango."""
        if periodo:
            fecha_inicio, fecha_fin = self._resolve_date_shortcut(periodo, fecha_inicio, fecha_fin)
        fi = date.fromisoformat(fecha_inicio)
        ff = date.fromisoformat(fecha_fin)
        weight_expr = self._weight_column(tipo_material)
        db = self._get_db()
        try:
            if agrupacion:
                # Validar agrupacion (lanza si invalida)
                self._compute_period_label(fi, time(0, 0), agrupacion)
                # Query flat rows
                query = (
                    db.query(Weighing.fecha, Weighing.hora, weight_expr)
                    .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
                )
                if tipo_cosecha:
                    query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
                query = self._apply_vehicle_filter(query, tipo_vehiculo)
                rows = query.all()
                # Group by period
                groups: dict[str, list[float]] = defaultdict(list)
                for r in rows:
                    period_label = self._compute_period_label(r[0], r[1], agrupacion)
                    groups[period_label].append(float(r[2]))
                grupos = []
                for period_label in sorted(groups.keys()):
                    values = groups[period_label]
                    n = len(values)
                    avg_v = sum(values) / n if n > 0 else 0.0
                    min_v = min(values) if values else 0.0
                    max_v = max(values) if values else 0.0
                    if n > 1:
                        variance = sum((v - avg_v) ** 2 for v in values) / (n - 1)
                        std_v = variance ** 0.5
                    else:
                        std_v = 0.0
                    grupos.append({
                        "periodo": period_label,
                        "count": n,
                        "avg": round(avg_v, 2),
                        "min": round(min_v, 2),
                        "max": round(max_v, 2),
                        "std": round(std_v, 2),
                    })
                return {"agrupacion": agrupacion, "grupos": grupos}

            # Sin agrupacion — comportamiento original
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
            query = self._apply_vehicle_filter(query, tipo_vehiculo)
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
                rows_query = self._apply_vehicle_filter(rows_query, tipo_vehiculo)
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

    def get_breakdown_by_hacienda(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        tipo_cosecha: str | None = None,
        agrupacion: str | None = None,
        tipo_vehiculo: str | None = None,
        periodo: str | None = None,
    ) -> list[dict] | dict:
        """Desglose de pesajes por hacienda con JOIN."""
        if periodo:
            fecha_inicio, fecha_fin = self._resolve_date_shortcut(periodo, fecha_inicio, fecha_fin)
        fi = date.fromisoformat(fecha_inicio)
        ff = date.fromisoformat(fecha_fin)
        total_w = Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
        db = self._get_db()
        try:
            if agrupacion:
                # Validar agrupacion
                self._compute_period_label(fi, time(0, 0), agrupacion)
                # Query flat rows with hacienda info
                query = (
                    db.query(
                        Weighing.fecha, Weighing.hora,
                        Hacienda.id, Hacienda.codigo, Hacienda.nombre,
                        total_w,
                    )
                    .join(Hacienda, Weighing.hacienda_id == Hacienda.id)
                    .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
                )
                if tipo_cosecha:
                    query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
                query = self._apply_vehicle_filter(query, tipo_vehiculo)
                rows = query.all()
                # Group by (periodo, hacienda_id)
                groups: dict[str, dict[int, dict]] = defaultdict(
                    lambda: defaultdict(
                        lambda: {"codigo": "", "nombre": "", "count": 0, "total_weight": 0.0, "values": []}
                    )
                )
                for r in rows:
                    period_label = self._compute_period_label(r[0], r[1], agrupacion)
                    hid = r[2]
                    entry = groups[period_label][hid]
                    entry["codigo"] = r[3]
                    entry["nombre"] = r[4]
                    entry["count"] += 1
                    entry["total_weight"] += float(r[5])
                    entry["values"].append(float(r[5]))
                grupos = []
                for period_label in sorted(groups.keys()):
                    haciendas = []
                    for hid in sorted(groups[period_label].keys()):
                        entry = groups[period_label][hid]
                        vals = entry["values"]
                        avg_w = sum(vals) / len(vals) if vals else 0.0
                        haciendas.append({
                            "hacienda_id": hid,
                            "codigo": entry["codigo"],
                            "nombre": entry["nombre"],
                            "count": entry["count"],
                            "total_weight": round(entry["total_weight"], 2),
                            "avg_weight": round(avg_w, 2),
                        })
                    grupos.append({"periodo": period_label, "haciendas": haciendas})
                return {"agrupacion": agrupacion, "grupos": grupos}

            # Sin agrupacion — comportamiento original
            query = (
                db.query(
                    Hacienda.id,
                    Hacienda.codigo,
                    Hacienda.nombre,
                    func.count(Weighing.id).label("count"),
                    func.coalesce(func.sum(total_w), 0).label("total_weight"),
                    func.coalesce(func.avg(total_w), 0).label("avg_weight"),
                )
                .join(Hacienda, Weighing.hacienda_id == Hacienda.id)
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            query = self._apply_vehicle_filter(query, tipo_vehiculo)
            rows = query.group_by(Hacienda.id).order_by(func.sum(total_w).desc()).all()
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

    def get_custom_period_summary(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        tipo_cosecha: str | None = None,
        agrupacion: str | None = None,
        tipo_vehiculo: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        """Resumen completo de un periodo personalizado."""
        if periodo:
            fecha_inicio, fecha_fin = self._resolve_date_shortcut(periodo, fecha_inicio, fecha_fin)
        fi = date.fromisoformat(fecha_inicio)
        ff = date.fromisoformat(fecha_fin)
        total_w = Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
        db = self._get_db()
        try:
            if agrupacion:
                # Validar agrupacion
                self._compute_period_label(fi, time(0, 0), agrupacion)
                # Query flat rows
                query = (
                    db.query(Weighing.fecha, Weighing.hora, total_w, Weighing.hacienda_id)
                    .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
                )
                if tipo_cosecha:
                    query = query.filter(Weighing.tipo_cosecha == tipo_cosecha)
                query = self._apply_vehicle_filter(query, tipo_vehiculo)
                rows = query.all()
                # Group by period
                groups: dict[str, list[float]] = defaultdict(list)
                haciendas_per_group: dict[str, set] = defaultdict(set)
                for r in rows:
                    period_label = self._compute_period_label(r[0], r[1], agrupacion)
                    groups[period_label].append(float(r[2]))
                    haciendas_per_group[period_label].add(r[3])
                grupos = []
                for period_label in sorted(groups.keys()):
                    values = groups[period_label]
                    n = len(values)
                    avg_v = sum(values) / n if n > 0 else 0.0
                    grupos.append({
                        "periodo": period_label,
                        "count": n,
                        "peso_total": round(sum(values), 2),
                        "peso_promedio": round(avg_v, 2),
                        "muestra": 0.0,
                        "mineral": 0.0,
                        "vegetal": 0.0,
                        "haciendas_distintas": len(haciendas_per_group.get(period_label, set())),
                    })
                return {"agrupacion": agrupacion, "grupos": grupos}

            # Sin agrupacion — comportamiento original
            count_query = (
                db.query(func.count(Weighing.id))
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                count_query = count_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            count_query = self._apply_vehicle_filter(count_query, tipo_vehiculo)
            count = count_query.scalar() or 0
            row_query = (
                db.query(
                    func.coalesce(func.sum(Weighing.peso_muestra), 0).label("muestra"),
                    func.coalesce(func.sum(Weighing.peso_mineral), 0).label("mineral"),
                    func.coalesce(func.sum(Weighing.peso_vegetal_extrano), 0).label("vegetal"),
                    func.coalesce(func.avg(total_w), 0).label("avg_weight"),
                )
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                row_query = row_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            row_query = self._apply_vehicle_filter(row_query, tipo_vehiculo)
            row = row_query.first()
            total = float(row.muestra) + float(row.mineral) + float(row.vegetal)
            # Distinct haciendas
            hacienda_query = (
                db.query(func.count(func.distinct(Weighing.hacienda_id)))
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            if tipo_cosecha:
                hacienda_query = hacienda_query.filter(Weighing.tipo_cosecha == tipo_cosecha)
            hacienda_query = self._apply_vehicle_filter(hacienda_query, tipo_vehiculo)
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
        # R25: Usar umbrales desde AgentConfig si esta disponible
        max_veg = 0.5
        max_min = 0.3
        if self._agent_config is not None:
            max_veg = self._agent_config.max_vegetal_to_muestra
            max_min = self._agent_config.max_mineral_to_muestra
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
                    if ratio_veg > max_veg:
                        violations.append({
                            "record_index": i,
                            "tipo": "vegetal_ratio_alto",
                            "valor": round(ratio_veg, 4),
                            "umbral": max_veg,
                        })
                    if ratio_min > max_min:
                        violations.append({
                            "record_index": i,
                            "tipo": "mineral_ratio_alto",
                            "valor": round(ratio_min, 4),
                            "umbral": max_min,
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
    # Herramienta de notas (T8 — Feature 37)
    # ------------------------------------------------------------------

    def get_weighing_notes(
        self,
        vagon: str | None = None,
        fecha_inicio: str | None = None,
        fecha_fin: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Retorna notas de pesajes filtrados por vagon y/o rango de fechas.

        Requiere al menos uno de: vagon, fecha_inicio.
        """
        if not vagon and not fecha_inicio:
            raise ToolExecutionError(
                "Debe proporcionar al menos uno de: vagon, fecha_inicio"
            )
        db = self._get_db()
        try:
            query = db.query(
                Weighing.id,
                Weighing.fecha,
                Weighing.vagon,
                Weighing.tractomula,
                Weighing.notas,
            )
            if vagon:
                query = query.filter(Weighing.vagon == vagon)
            if fecha_inicio:
                fi = date.fromisoformat(fecha_inicio)
                query = query.filter(Weighing.fecha >= fi)
            if fecha_fin:
                ff = date.fromisoformat(fecha_fin)
                query = query.filter(Weighing.fecha <= ff)
            query = query.order_by(Weighing.id.desc()).limit(limit)
            rows = query.all()
            return [
                {
                    "id": r.id,
                    "fecha": r.fecha.isoformat() if r.fecha else None,
                    "vagon": r.vagon,
                    "tractomula": r.tractomula,
                    "notas": r.notas,
                }
                for r in rows
            ]
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Nuevas tools (F33)
    # ------------------------------------------------------------------

    def get_avg_weighing_time(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        tipo_vehiculo: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        """Tiempo promedio (minutos) entre pesajes consecutivos en el rango."""
        if periodo:
            fecha_inicio, fecha_fin = self._resolve_date_shortcut(
                periodo, fecha_inicio, fecha_fin
            )
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            query = (
                db.query(Weighing.fecha, Weighing.hora)
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            query = self._apply_vehicle_filter(query, tipo_vehiculo)
            rows = query.order_by(Weighing.fecha, Weighing.hora).all()
            if len(rows) < 2:
                return {
                    "avg_time_minutes": 0.0,
                    "count": len(rows),
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "message": "Datos insuficientes",
                }
            timestamps = [datetime.combine(r[0], r[1]) for r in rows]
            diffs = [
                (timestamps[i + 1] - timestamps[i]).total_seconds() / 60
                for i in range(len(timestamps) - 1)
            ]
            avg_minutes = sum(diffs) / len(diffs)
            return {
                "avg_time_minutes": round(avg_minutes, 2),
                "count": len(rows),
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            }
        finally:
            db.close()

    def get_anomaly_rate(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        tipo_vehiculo: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        """Tasa de anomalias (% de pesajes anomalos vs total)."""
        if periodo:
            fecha_inicio, fecha_fin = self._resolve_date_shortcut(
                periodo, fecha_inicio, fecha_fin
            )
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            wq = (
                db.query(func.count(Weighing.id))
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            wq = self._apply_vehicle_filter(wq, tipo_vehiculo)
            total_weighings = wq.scalar() or 0
            aq = (
                db.query(func.count(AnomalyLog.id))
                .filter(
                    func.date(AnomalyLog.created_at) >= fi,
                    func.date(AnomalyLog.created_at) <= ff,
                )
            )
            total_anomalies = aq.scalar() or 0
            rate = (
                total_anomalies / total_weighings * 100
                if total_weighings > 0
                else 0.0
            )
            return {
                "total_weighings": int(total_weighings),
                "total_anomalies": int(total_anomalies),
                "anomaly_rate_pct": round(rate, 2),
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            }
        finally:
            db.close()

    def get_top_haciendas(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        limite: int = 10,
        tipo_vehiculo: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        """Ranking descendente de haciendas por peso total."""
        if periodo:
            fecha_inicio, fecha_fin = self._resolve_date_shortcut(
                periodo, fecha_inicio, fecha_fin
            )
        if limite <= 0:
            raise ToolExecutionError(f"limite debe ser > 0: {limite}")
        db = self._get_db()
        try:
            fi = date.fromisoformat(fecha_inicio)
            ff = date.fromisoformat(fecha_fin)
            total_w = (
                Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
            )
            query = (
                db.query(
                    Hacienda.id,
                    Hacienda.codigo,
                    Hacienda.nombre,
                    func.sum(total_w).label("total_weight"),
                    func.count(Weighing.id).label("count"),
                )
                .join(Hacienda, Weighing.hacienda_id == Hacienda.id)
                .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
            )
            query = self._apply_vehicle_filter(query, tipo_vehiculo)
            rows = (
                query
                .group_by(Hacienda.id)
                .order_by(func.sum(total_w).desc())
                .limit(limite)
                .all()
            )
            return {
                "ranking": [
                    {
                        "hacienda_id": r.id,
                        "codigo": r.codigo,
                        "nombre": r.nombre,
                        "total_weight": round(float(r.total_weight or 0), 2),
                        "count": int(r.count),
                    }
                    for r in rows
                ],
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
            }
        finally:
            db.close()

    def get_period_comparison(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        periodo_anterior_inicio: str,
        periodo_anterior_fin: str,
        tipo_vehiculo: str | None = None,
        periodo: str | None = None,
    ) -> dict:
        """Comparacion (delta + delta%) entre dos periodos."""
        if periodo:
            fecha_inicio, fecha_fin = self._resolve_date_shortcut(
                periodo, fecha_inicio, fecha_fin
            )
        db = self._get_db()
        try:
            total_w = Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano

            def _period_summary(fi_str, ff_str):
                fi = date.fromisoformat(fi_str)
                ff = date.fromisoformat(ff_str)
                row_q = (
                    db.query(
                        func.count(Weighing.id).label("count"),
                        func.coalesce(func.sum(total_w), 0).label("peso_total"),
                        func.coalesce(func.avg(total_w), 0).label("peso_promedio"),
                    )
                    .filter(Weighing.fecha >= fi, Weighing.fecha <= ff)
                )
                row_q = self._apply_vehicle_filter(row_q, tipo_vehiculo)
                row = row_q.first()
                return {
                    "fecha_inicio": fi_str,
                    "fecha_fin": ff_str,
                    "count": int(row.count),
                    "peso_total": round(float(row.peso_total), 2),
                    "peso_promedio": round(float(row.peso_promedio), 2),
                }

            actual = _period_summary(fecha_inicio, fecha_fin)
            anterior = _period_summary(periodo_anterior_inicio, periodo_anterior_fin)

            delta_count = actual["count"] - anterior["count"]
            delta_total = actual["peso_total"] - anterior["peso_total"]
            delta_avg = actual["peso_promedio"] - anterior["peso_promedio"]

            if anterior["count"] > 0:
                pct_count = round(delta_count / anterior["count"] * 100, 2)
                pct_total = (
                    round(delta_total / anterior["peso_total"] * 100, 2)
                    if anterior["peso_total"] > 0
                    else None
                )
                pct_avg = (
                    round(delta_avg / anterior["peso_promedio"] * 100, 2)
                    if anterior["peso_promedio"] > 0
                    else None
                )
            else:
                pct_count = None
                pct_total = None
                pct_avg = None

            return {
                "periodo_actual": actual,
                "periodo_anterior": anterior,
                "delta": {
                    "count": delta_count,
                    "peso_total": round(delta_total, 2),
                    "peso_promedio": round(delta_avg, 2),
                },
                "delta_pct": {
                    "count": pct_count,
                    "peso_total": pct_total,
                    "peso_promedio": pct_avg,
                },
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
            "get_weighing_notes": self.get_weighing_notes,
            # Nuevas tools (F33)
            "get_avg_weighing_time": self.get_avg_weighing_time,
            "get_anomaly_rate": self.get_anomaly_rate,
            "get_top_haciendas": self.get_top_haciendas,
            "get_period_comparison": self.get_period_comparison,
        }
        if tool_name not in tool_map:
            raise ToolExecutionError(f"Herramienta desconocida: {tool_name}")
        try:
            return tool_map[tool_name](**arguments)
        except TypeError as e:
            raise ToolExecutionError(f"Parametros invalidos para {tool_name}: {e}") from e
        except Exception as e:
            raise ToolExecutionError(f"Error ejecutando {tool_name}: {e}") from e
