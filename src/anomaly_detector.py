"""Detector de anomalias en 3 capas: Z-Score, relacional y temporal."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from src.config import AgentConfig
from src.models import Weighing

logger = logging.getLogger(__name__)


class AnomalyDetectionError(Exception):
    """Se lanza cuando ocurre un error inesperado durante la deteccion."""


@dataclass(frozen=True)
class AnomalyResult:
    record_id: int
    layer: str  # "zscore" | "relacional" | "temporal"
    z_score: float | None
    metric_value: float
    threshold: float
    detail: str


class AnomalyDetector:
    """Detector de anomalias en 3 capas secuenciales.

    Tras cada pesaje confirmado, ejecuta las 3 capas contra la ventana
    movil configurada. Si alguna capa detecta anomalia, se notifica
    al LLM para generar reporte narrativo.
    """

    def __init__(self, db_session_factory, config: AgentConfig) -> None:
        self._db_session_factory = db_session_factory
        self._config = config

    def run(self, weighing: Weighing) -> list[AnomalyResult]:
        """Ejecuta las 3 capas contra la ventana actual.

        Retorna lista de anomalias detectadas (vacia si no hay).
        """
        db = self._db_session_factory()
        try:
            records = self._get_window(db)
            if not records:
                return []

            total_weight = _total(weighing)
            results: list[AnomalyResult] = []

            # Capa 1: Z-Score
            results.extend(self._detect_zscore(records, total_weight, weighing.id))

            # Capa 2: Relacional
            results.extend(self._detect_relational(records, weighing.id))

            # Capa 3: Temporal
            results.extend(self._detect_temporal(records, total_weight, weighing.id))

            return results
        finally:
            db.close()

    def detect_on_demand(self, window_size: int, z_threshold: float) -> list[AnomalyResult]:
        """Ejecuta deteccion bajo demanda con parametros personalizados."""
        db = self._db_session_factory()
        try:
            records = (
                db.query(Weighing)
                .order_by(Weighing.id.desc())
                .limit(window_size)
                .all()
            )
            if not records:
                return []
            results: list[AnomalyResult] = []
            for r in records:
                tw = _total(r)
                results.extend(self._detect_zscore(records, tw, r.id, z_threshold=z_threshold))
                results.extend(self._detect_relational(records, r.id))
                results.extend(self._detect_temporal(records, tw, r.id))
            return results
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Ventana movil (T10)
    # ------------------------------------------------------------------

    def _get_window(self, db: Session) -> list[Weighing]:
        """Obtiene los registros de la ventana movil configurada.

        Aplica el limite que se alcance primero entre window_size registros
        y window_hours horas hacia atras.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=self._config.window_hours)

        # Obtener registros ordenados por id descendente
        query = (
            db.query(Weighing)
            .order_by(Weighing.id.desc())
            .limit(self._config.window_size)
        )
        records = query.all()

        # Filtrar por ventana de horas
        filtered: list[Weighing] = []
        for r in records:
            if r.created_at is not None:
                if r.created_at.replace(tzinfo=timezone.utc) >= cutoff:
                    filtered.append(r)
            else:
                # Si no tiene created_at, incluir (fallback)
                filtered.append(r)

        # Invertir para orden cronologico ascendente
        filtered.reverse()
        return filtered

    # ------------------------------------------------------------------
    # Capa 1: Z-Score (T11)
    # ------------------------------------------------------------------

    def _detect_zscore(
        self,
        records: list[Weighing],
        new_total: float,
        record_id: int,
        z_threshold: float | None = None,
    ) -> list[AnomalyResult]:
        """Capa 1: Z-Score con ventana movil.

        Calcula la media y desviacion estandar del peso total de la ventana.
        Si |Z| > threshold, es anomalia.
        """
        if z_threshold is None:
            z_threshold = self._config.z_threshold

        weights = [_total(r) for r in records]
        if not weights:
            return []

        n = len(weights)
        mean = sum(weights) / n
        if n > 1:
            variance = sum((w - mean) ** 2 for w in weights) / (n - 1)
            std = variance ** 0.5
        else:
            std = 1e-6  # Evitar division por cero

        if std < 1e-6:
            return []

        z = (new_total - mean) / std
        if abs(z) > z_threshold:
            return [
                AnomalyResult(
                    record_id=record_id,
                    layer="zscore",
                    z_score=round(z, 4),
                    metric_value=round(new_total, 3),
                    threshold=z_threshold,
                    detail=f"Z-Score {z:+.3f} excede umbral {z_threshold} "
                           f"(media={mean:.2f}, std={std:.2f})",
                )
            ]
        return []

    # ------------------------------------------------------------------
    # Capa 2: Relacional (T12)
    # ------------------------------------------------------------------

    def _detect_relational(
        self, records: list[Weighing], record_id: int
    ) -> list[AnomalyResult]:
        """Capa 2: Ratios entre materiales.

        Calcula ratios vegetal/muestra y mineral/muestra.
        Marca si algun ratio excede los umbrales configurables.
        """
        # Evaluar solo el registro nuevo (ultimo)
        target = None
        for r in records:
            if r.id == record_id:
                target = r
                break
        if target is None:
            return []

        muestra = float(target.peso_muestra)
        if muestra <= 0:
            return []

        vegetal = float(target.peso_vegetal_extrano)
        mineral = float(target.peso_mineral)

        ratio_veg = vegetal / muestra
        ratio_min = mineral / muestra

        results: list[AnomalyResult] = []

        if ratio_veg > self._config.max_vegetal_to_muestra:
            results.append(AnomalyResult(
                record_id=record_id,
                layer="relacional",
                z_score=None,
                metric_value=round(ratio_veg, 4),
                threshold=self._config.max_vegetal_to_muestra,
                detail=f"Ratio vegetal/muestra {ratio_veg:.4f} > "
                       f"{self._config.max_vegetal_to_muestra}",
            ))

        if ratio_min > self._config.max_mineral_to_muestra:
            results.append(AnomalyResult(
                record_id=record_id,
                layer="relacional",
                z_score=None,
                metric_value=round(ratio_min, 4),
                threshold=self._config.max_mineral_to_muestra,
                detail=f"Ratio mineral/muestra {ratio_min:.4f} > "
                       f"{self._config.max_mineral_to_muestra}",
            ))

        return results

    # ------------------------------------------------------------------
    # Capa 3: Temporal (T13)
    # ------------------------------------------------------------------

    def _detect_temporal(
        self, records: list[Weighing], new_total: float, record_id: int
    ) -> list[AnomalyResult]:
        """Capa 3: Tasa de cambio y rachas anomalas.

        - Calcula tasa de cambio porcentual entre pesajes consecutivos.
        - Marca cambios que superen max_rate_change.
        - Detecta rachas de N+ anomalos consecutivos como anomalia sistemica.
        """
        results: list[AnomalyResult] = []

        if len(records) < 2:
            return results

        # Encontrar el registro previo (el penultimo en orden cronologico)
        weights = [_total(r) for r in records]

        # El ultimo en la lista deberia ser el recien insertado
        prev_weight = weights[-2] if len(weights) >= 2 else weights[-1]

        if prev_weight > 0:
            rate = abs(new_total - prev_weight) / prev_weight
            if rate > self._config.max_rate_change:
                results.append(AnomalyResult(
                    record_id=record_id,
                    layer="temporal",
                    z_score=None,
                    metric_value=round(rate, 4),
                    threshold=self._config.max_rate_change,
                    detail=f"Tasa de cambio {rate:.4f} ({rate*100:.1f}%) > "
                           f"{self._config.max_rate_change} ({self._config.max_rate_change*100:.0f}%)",
                ))

        # Detectar rachas de anomalias consecutivas
        consecutive = 0
        for i in range(1, len(weights)):
            prev = weights[i - 1]
            curr = weights[i]
            if prev > 0:
                rate = abs(curr - prev) / prev
                if rate > self._config.max_rate_change:
                    consecutive += 1
                else:
                    consecutive = 0
            if consecutive >= self._config.max_consecutive_anomalies:
                results.append(AnomalyResult(
                    record_id=record_id,
                    layer="temporal",
                    z_score=None,
                    metric_value=float(consecutive),
                    threshold=float(self._config.max_consecutive_anomalies),
                    detail=f"Racha de {consecutive} anomalias consecutivas "
                           f"(umbral: {self._config.max_consecutive_anomalies}) — posible anomalia sistemica",
                ))
                break

        return results


def _total(w: Weighing) -> float:
    """Calcula el peso total de un registro de pesaje."""
    return float(w.peso_muestra + w.peso_mineral + w.peso_vegetal_extrano)
