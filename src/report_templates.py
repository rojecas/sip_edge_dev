"""Gestion CRUD de plantillas de reporte programado y generacion de reportes."""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import AnomalyLog, Hacienda, ReportTemplate, ReportTemplateUser, User, Weighing

logger = logging.getLogger(__name__)


class TemplateNotFoundError(Exception):
    """Se lanza cuando se intenta modificar/eliminar una plantilla que no existe."""


METRIC_HANDLERS: dict[str, callable] = {}  # Se registran abajo


def _register_metric(name: str):
    """Decorador para registrar un handler de metrica."""
    def decorator(fn):
        METRIC_HANDLERS[name] = fn
        return fn
    return decorator


class ReportTemplateService:
    """Servicio de gestion CRUD de plantillas de reporte programado.

    Permite crear, modificar, eliminar y listar plantillas, y generar
    reportes con solo las metricas seleccionadas (SQL directo, sin LLM).
    """

    def __init__(self, db_session_factory) -> None:
        self._db_session_factory = db_session_factory

    def _get_db(self) -> Session:
        return self._db_session_factory()

    # ------------------------------------------------------------------
    # CRUD (T16)
    # ------------------------------------------------------------------

    def create(self, data: dict) -> ReportTemplate:
        """Crea una nueva plantilla de reporte.

        Almacena destinatarios en la tabla pivote report_template_users
        en vez de como JSON en la columna recipients.
        """
        db = self._get_db()
        try:
            template = ReportTemplate(
                name=data["name"],
                schedule=json.dumps(data.get("schedule", [])),
                metrics=json.dumps(data.get("metrics", [])),
                is_active=data.get("is_active", True),
            )
            db.add(template)
            db.flush()  # Necesario para obtener template.id

            # Insertar filas en la tabla pivote para cada user_id
            user_ids = data.get("user_ids", [])
            for uid in user_ids:
                rtu = ReportTemplateUser(template_id=template.id, user_id=uid)
                db.add(rtu)

            db.commit()
            db.refresh(template)
            return template
        finally:
            db.close()

    def update(self, template_id: int, data: dict) -> ReportTemplate:
        """Actualiza una plantilla existente.

        Si se pasa user_ids, reemplaza las filas en la tabla pivote
        (borra existentes + inserta nuevas).

        Raises:
            TemplateNotFoundError: si la plantilla no existe.
        """
        db = self._get_db()
        try:
            template = db.query(ReportTemplate).filter(
                ReportTemplate.id == template_id
            ).first()
            if template is None:
                raise TemplateNotFoundError(f"Plantilla {template_id} no encontrada")

            if "name" in data:
                template.name = data["name"]
            if "schedule" in data:
                template.schedule = json.dumps(data["schedule"])
            if "metrics" in data:
                template.metrics = json.dumps(data["metrics"])
            if "is_active" in data:
                template.is_active = data["is_active"]

            # Reemplazar filas en la tabla pivote si se proporcionan user_ids
            if "user_ids" in data:
                db.query(ReportTemplateUser).filter(
                    ReportTemplateUser.template_id == template_id
                ).delete()
                for uid in data["user_ids"]:
                    rtu = ReportTemplateUser(
                        template_id=template_id, user_id=uid
                    )
                    db.add(rtu)

            db.commit()
            db.refresh(template)
            return template
        finally:
            db.close()

    def delete(self, template_id: int) -> None:
        """Elimina una plantilla.

        Raises:
            TemplateNotFoundError: si la plantilla no existe.
        """
        db = self._get_db()
        try:
            template = db.query(ReportTemplate).filter(
                ReportTemplate.id == template_id
            ).first()
            if template is None:
                raise TemplateNotFoundError(f"Plantilla {template_id} no encontrada")
            db.delete(template)
            db.commit()
        finally:
            db.close()

    def get_all(self) -> list[dict]:
        """Lista todas las plantillas con destinatarios resueltos via JOIN."""
        db = self._get_db()
        try:
            templates = db.query(ReportTemplate).all()
            return [self._template_to_dict(db, t) for t in templates]
        finally:
            db.close()

    def get_one(self, template_id: int) -> dict:
        """Obtiene una plantilla por ID con destinatarios resueltos.

        Raises:
            TemplateNotFoundError: si la plantilla no existe.
        """
        db = self._get_db()
        try:
            template = db.query(ReportTemplate).filter(
                ReportTemplate.id == template_id
            ).first()
            if template is None:
                raise TemplateNotFoundError(f"Plantilla {template_id} no encontrada")
            return self._template_to_dict(db, template)
        finally:
            db.close()

    def _resolve_recipients(self, db: Session, template_id: int) -> tuple[list[str], list[int]]:
        """Resuelve telefonos y user_ids desde la tabla pivote + users.

        Returns:
            (phones, user_ids) donde phones son los telefonos actuales
            de los usuarios vinculados a la plantilla.
        """
        rows = (
            db.query(User.phone, User.id)
            .join(ReportTemplateUser, ReportTemplateUser.user_id == User.id)
            .filter(ReportTemplateUser.template_id == template_id)
            .all()
        )
        phones = [r.phone for r in rows if r.phone]
        user_ids = [r.id for r in rows]
        return phones, user_ids

    def _template_to_dict(self, db: Session, template: ReportTemplate) -> dict:
        """Convierte un ReportTemplate a dict con destinatarios resueltos."""
        phones, uids = self._resolve_recipients(db, template.id)
        return {
            "id": template.id,
            "name": template.name,
            "schedule": json.loads(template.schedule) if template.schedule else [],
            "recipients": phones,
            "recipient_ids": uids,
            "metrics": json.loads(template.metrics) if template.metrics else [],
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        }

    def get_recipient_phones(self, template_id: int) -> list[str]:
        """Obtiene los telefonos actuales de los destinatarios de una plantilla.

        Usado por el scheduler SMS para resolver destinatarios al enviar reportes.
        Los telefonos se obtienen via JOIN desde la tabla pivote + users,
        garantizando que esten siempre actualizados.
        """
        db = self._get_db()
        try:
            rows = (
                db.query(User.phone)
                .join(ReportTemplateUser, ReportTemplateUser.user_id == User.id)
                .filter(ReportTemplateUser.template_id == template_id)
                .all()
            )
            return [r.phone for r in rows if r.phone]
        finally:
            db.close()

    def get_active_by_schedule(self, time_str: str) -> list[ReportTemplate]:
        """Retorna plantillas activas cuyo schedule incluye la hora dada.

        Args:
            time_str: hora en formato "HH:MM"
        """
        db = self._get_db()
        try:
            all_active = (
                db.query(ReportTemplate)
                .filter(ReportTemplate.is_active == True)
                .all()
            )
            matching: list[ReportTemplate] = []
            for template in all_active:
                try:
                    schedule = json.loads(template.schedule)
                except (json.JSONDecodeError, TypeError):
                    continue
                if time_str in schedule:
                    matching.append(template)
            return matching
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Generacion de reportes (T17)
    # ------------------------------------------------------------------

    def generate_report(self, template: ReportTemplate, db: Session) -> str:
        """Genera el texto del reporte con SOLO las metricas seleccionadas.

        Ejecuta consultas SQL directas (sin LLM). Formatea para SMS
        (160 caracteres por segmento, concatenado si es necesario).
        """
        try:
            metrics = json.loads(template.metrics)
        except (json.JSONDecodeError, TypeError):
            metrics = []

        now = datetime.now(timezone.utc)
        today = now.date()
        today_str = today.isoformat()

        lines: list[str] = [f"Reporte {template.name} [{today_str}]"]
        lines.append("=" * 20)

        for metric in metrics:
            handler = METRIC_HANDLERS.get(metric)
            if handler is None:
                logger.warning("Metrica desconocida en plantilla %s: %s", template.id, metric)
                continue
            try:
                result = handler(db, today)
                if result:
                    lines.append(result)
            except Exception:
                logger.exception("Error generando metrica %s para plantilla %s", metric, template.id)

        return "\n".join(lines)


# ------------------------------------------------------------------
# Handlers de metricas
# ------------------------------------------------------------------

@_register_metric("count")
def _metric_count(db: Session, today: date) -> str:
    count = (
        db.query(func.count(Weighing.id))
        .filter(Weighing.fecha == today)
        .scalar()
    ) or 0
    return f"Total pesajes: {count}"


@_register_metric("avg")
def _metric_avg(db: Session, today: date) -> str:
    row = (
        db.query(
            func.coalesce(func.avg(
                Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
            ), 0)
        )
        .filter(Weighing.fecha == today)
        .first()
    )
    avg = round(float(row[0]), 2)
    return f"Peso promedio: {avg} kg"


@_register_metric("min_max")
def _metric_min_max(db: Session, today: date) -> str:
    total_w = Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
    row = (
        db.query(
            func.coalesce(func.min(total_w), 0).label("min"),
            func.coalesce(func.max(total_w), 0).label("max"),
        )
        .filter(Weighing.fecha == today)
        .first()
    )
    return f"Min: {round(float(row.min), 1)} kg | Max: {round(float(row.max), 1)} kg"


@_register_metric("breakdown_by_hacienda")
def _metric_breakdown_hacienda(db: Session, today: date) -> str:
    rows = (
        db.query(
            Hacienda.codigo,
            func.count(Weighing.id),
            func.coalesce(func.sum(
                Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
            ), 0),
        )
        .join(Hacienda, Weighing.hacienda_id == Hacienda.id)
        .filter(Weighing.fecha == today)
        .group_by(Hacienda.id)
        .all()
    )
    if not rows:
        return "Por hacienda: sin datos"
    parts = [f"{r.codigo}: {int(r[1])}p/{round(float(r[2]), 1)}kg" for r in rows]
    return "Por hacienda: " + " | ".join(parts)


@_register_metric("breakdown_by_operator")
def _metric_breakdown_operator(db: Session, today: date) -> str:
    rows = (
        db.query(
            User.username,
            func.count(Weighing.id),
            func.coalesce(func.sum(
                Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
            ), 0),
        )
        .join(User, Weighing.usuario_id == User.id)
        .filter(Weighing.fecha == today)
        .group_by(User.id)
        .all()
    )
    if not rows:
        return "Por operador: sin datos"
    parts = [f"{r.username}: {int(r[1])}p/{round(float(r[2]), 1)}kg" for r in rows]
    return "Por operador: " + " | ".join(parts)


@_register_metric("composition")
def _metric_composition(db: Session, today: date) -> str:
    row = (
        db.query(
            func.coalesce(func.sum(Weighing.peso_muestra), 0),
            func.coalesce(func.sum(Weighing.peso_mineral), 0),
            func.coalesce(func.sum(Weighing.peso_vegetal_extrano), 0),
        )
        .filter(Weighing.fecha == today)
        .first()
    )
    m, mi, v = float(row[0]), float(row[1]), float(row[2])
    total = m + mi + v
    if total == 0:
        return "Composicion: sin datos"
    return (
        f"Composicion: M={m/total*100:.0f}% "
        f"Min={mi/total*100:.0f}% "
        f"Veg={v/total*100:.0f}%"
    )


@_register_metric("anomaly_count")
def _metric_anomaly_count(db: Session, today: date) -> str:
    count = (
        db.query(func.count(AnomalyLog.id))
        .filter(func.date(AnomalyLog.created_at) == today)
        .scalar()
    ) or 0
    return f"Anomalias hoy: {count}"


@_register_metric("trend")
def _metric_trend(db: Session, today: date) -> str:
    """Tendencia: compara el peso total de hoy vs ayer."""
    yesterday = today - timedelta(days=1)
    total_w = Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano

    today_total = (
        db.query(func.coalesce(func.sum(total_w), 0))
        .filter(Weighing.fecha == today)
        .scalar()
    ) or 0
    yesterday_total = (
        db.query(func.coalesce(func.sum(total_w), 0))
        .filter(Weighing.fecha == yesterday)
        .scalar()
    ) or 0

    if float(yesterday_total) == 0:
        return "Tendencia: primer dia de datos"

    change_pct = (float(today_total) - float(yesterday_total)) / float(yesterday_total) * 100
    direction = "sube" if change_pct > 0 else ("baja" if change_pct < 0 else "estable")
    return f"Tendencia: {direction} {abs(change_pct):.1f}% vs ayer"


@_register_metric("std")
def _metric_std(db: Session, today: date) -> str:
    """Desviacion estandar del peso total del dia actual."""
    total_w = Weighing.peso_muestra + Weighing.peso_mineral + Weighing.peso_vegetal_extrano
    rows = (
        db.query(total_w)
        .filter(Weighing.fecha == today)
        .all()
    )
    values = [float(r[0]) for r in rows]
    n = len(values)
    if n < 2:
        return "Desviacion estandar: sin datos (menos de 2 pesajes)"
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    std = variance ** 0.5
    return f"Desviacion estandar: {std:.2f} kg"
