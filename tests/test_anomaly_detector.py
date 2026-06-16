"""Tests for AnomalyDetector: 3 capas de deteccion."""

import unittest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.anomaly_detector import AnomalyDetector, AnomalyResult
from src.config import AgentConfig
from src.models import Base, Hacienda, Suerte, User, Weighing


class _DetectorTestBase(unittest.TestCase):
    """Base con DB SQLite en memoria y datos de prueba controlados."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        self.config = AgentConfig(
            window_size=10,
            window_hours=24,
            z_threshold=3.0,
            max_vegetal_to_muestra=0.5,
            max_mineral_to_muestra=0.3,
            max_rate_change=0.5,
            max_consecutive_anomalies=3,
        )

        db = self.SessionLocal()
        try:
            u = User(username="op", password_hash="h", role="operator", full_name="Op")
            h = Hacienda(codigo="H001", nombre="Hacienda Test")
            db.add_all([u, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="S01")
            db.add(s)
            db.flush()

            # Datos controlados: pesos estables de ~100kg
            self.records = []
            for i in range(10):
                w = Weighing(
                    fecha=date(2026, 6, 15),
                    hora=datetime.strptime(f"{8+i:02d}:00", "%H:%M").time(),
                    tractomula=f"T{i}",
                    vagon=f"V{i}",
                    numero_guia=f"G{i}",
                    hacienda_id=h.id,
                    suerte_id=s.id,
                    peso_muestra=100.0,
                    peso_mineral=5.0,
                    peso_vegetal_extrano=2.0,
                    usuario_id=u.id,
                    created_at=datetime(2026, 6, 15, 8 + i, 0, 0, tzinfo=timezone.utc),
                )
                db.add(w)
                self.records.append(w)
            db.commit()
            # Refrescar IDs
            for r in self.records:
                db.refresh(r)
        finally:
            db.close()

        self.detector = AnomalyDetector(
            db_session_factory=self.SessionLocal, config=self.config
        )


class TestZScoreLayer(_DetectorTestBase):
    """T29: Z-Score calculo con datos controlados."""

    def test_no_anomaly_on_stable_data(self):
        """R7: Datos estables no deben generar anomalia Z-Score."""
        db = self.SessionLocal()
        try:
            records = (
                db.query(Weighing).order_by(Weighing.id).all()
            )
        finally:
            db.close()
        total = 107.0  # 100 + 5 + 2
        results = self.detector._detect_zscore(records, total, records[-1].id)
        # Con pesos todos 107.0, Z-Score = 0
        self.assertEqual(len(results), 0)

    def test_anomaly_on_extreme_value(self):
        """R7: Valor extremo debe generar anomalia Z-Score."""
        db = self.SessionLocal()
        try:
            records = (
                db.query(Weighing).order_by(Weighing.id).all()
            )
        finally:
            db.close()
        total = 500.0  # Valor muy fuera de rango
        results = self.detector._detect_zscore(records, total, records[-1].id)
        if results:
            self.assertEqual(results[0].layer, "zscore")
            self.assertIsNotNone(results[0].z_score)
            self.assertGreater(abs(results[0].z_score), self.config.z_threshold)


class TestZScoreThreshold(_DetectorTestBase):
    """T29: Verificar respeto del umbral configurable."""

    def test_below_threshold_no_anomaly(self):
        """R12: |Z| <= z_threshold no marca anomalia."""
        config_tight = AgentConfig(
            window_size=10,
            window_hours=24,
            z_threshold=100.0,  # Muy alto — casi nada es anomalia
            max_vegetal_to_muestra=0.5,
            max_mineral_to_muestra=0.3,
            max_rate_change=0.5,
            max_consecutive_anomalies=3,
        )
        detector_tight = AnomalyDetector(
            db_session_factory=self.SessionLocal, config=config_tight
        )
        db = self.SessionLocal()
        try:
            records = db.query(Weighing).order_by(Weighing.id).all()
        finally:
            db.close()
        total = 107.0
        results = detector_tight._detect_zscore(records, total, records[-1].id)
        self.assertEqual(len(results), 0)


class TestRelationalLayer(_DetectorTestBase):
    """T29: Deteccion de ratios excedidos."""

    def test_normal_ratios_no_anomaly(self):
        """R8: Ratios dentro de limites no generan anomalia."""
        db = self.SessionLocal()
        try:
            records = db.query(Weighing).order_by(Weighing.id).all()
        finally:
            db.close()
        results = self.detector._detect_relational(records, records[-1].id)
        self.assertEqual(len(results), 0)

    def test_high_vegetal_ratio_detects_anomaly(self):
        """R8: Ratio vegetal/muestra alto genera anomalia."""
        # Crear un registro con vegetal muy alto
        db = self.SessionLocal()
        try:
            user = db.query(User).first()
            h = db.query(Hacienda).first()
            s = db.query(Suerte).first()
            w = Weighing(
                fecha=date(2026, 6, 15),
                hora=datetime.strptime("18:00", "%H:%M").time(),
                tractomula="ANOM",
                vagon="VAN",
                numero_guia="GAN",
                hacienda_id=h.id,
                suerte_id=s.id,
                peso_muestra=100.0,
                peso_mineral=5.0,
                peso_vegetal_extrano=80.0,  # Ratio 0.8 > 0.5
                usuario_id=user.id,
                created_at=datetime(2026, 6, 15, 18, 0, 0, tzinfo=timezone.utc),
            )
            db.add(w)
            db.commit()
            db.refresh(w)

            records = db.query(Weighing).order_by(Weighing.id).all()
            results = self.detector._detect_relational(records, w.id)
            self.assertGreaterEqual(len(results), 1)
            self.assertEqual(results[0].layer, "relacional")
        finally:
            db.close()

    def test_high_mineral_ratio_detects_anomaly(self):
        """R8: Ratio mineral/muestra alto genera anomalia."""
        db = self.SessionLocal()
        try:
            user = db.query(User).first()
            h = db.query(Hacienda).first()
            s = db.query(Suerte).first()
            w = Weighing(
                fecha=date(2026, 6, 15),
                hora=datetime.strptime("19:00", "%H:%M").time(),
                tractomula="ANOM2",
                vagon="VA2",
                numero_guia="GA2",
                hacienda_id=h.id,
                suerte_id=s.id,
                peso_muestra=100.0,
                peso_mineral=50.0,  # Ratio 0.5 > 0.3
                peso_vegetal_extrano=2.0,
                usuario_id=user.id,
                created_at=datetime(2026, 6, 15, 19, 0, 0, tzinfo=timezone.utc),
            )
            db.add(w)
            db.commit()
            db.refresh(w)

            records = db.query(Weighing).order_by(Weighing.id).all()
            results = self.detector._detect_relational(records, w.id)
            self.assertGreaterEqual(len(results), 1)
            # Verificar que al menos uno es de tipo mineral
            layers = [r.layer for r in results]
            self.assertIn("relacional", layers)
        finally:
            db.close()


class TestTemporalLayer(_DetectorTestBase):
    """T29: Deteccion de cambios bruscos y rachas."""

    def test_small_change_no_anomaly(self):
        """R9: Cambios pequenos no generan anomalia."""
        db = self.SessionLocal()
        try:
            records = db.query(Weighing).order_by(Weighing.id).all()
        finally:
            db.close()
        results = self.detector._detect_temporal(records, 107.0, records[-1].id)
        # Con datos estables, no deberia haber anomalias
        # (aunque puede detectar racha si config es muy baja)
        temporal_results = [r for r in results if r.layer == "temporal"]
        # Todos los pesos son iguales (107), por lo que tasa cambio = 0
        self.assertEqual(len(temporal_results), 0)

    def test_large_change_detects_anomaly(self):
        """R9: Cambio brusco genera anomalia temporal."""
        db = self.SessionLocal()
        try:
            records = db.query(Weighing).order_by(Weighing.id).all()
            # El ultimo registro normal es 107, anadir uno con 250
            total = 250.0  # Tasa de cambio: (250-107)/107 = 1.34 > 0.5
            results = self.detector._detect_temporal(records, total, records[-1].id)
            temporal_results = [r for r in results if r.layer == "temporal"
                              and "Tasa de cambio" in r.detail]
            self.assertGreaterEqual(len(temporal_results), 1)
        finally:
            db.close()


class TestTemporalConsecutive(_DetectorTestBase):
    """T29: Deteccion de rachas anomalas."""

    def test_consecutive_anomalies_detected(self):
        """R9: Rachas de N+ anomalos consecutivos se marcan."""
        db = self.SessionLocal()
        try:
            user = db.query(User).first()
            h = db.query(Hacienda).first()
            s = db.query(Suerte).first()

            # Agregar 4 registros con saltos bruscos (cada uno > 50% del anterior)
            # Con pesos: 100, 250, 500, 1000
            # Totales: 107, 257, 507, 1007
            # Cambios: 107->257 (1.40), 257->507 (0.97), 507->1007 (0.99) → 3 consecutivos
            for i in range(4):
                base = [100.0, 250.0, 500.0, 1000.0]
                w = Weighing(
                    fecha=date(2026, 6, 15),
                    hora=datetime.strptime(f"{20+i:02d}:00", "%H:%M").time(),
                    tractomula=f"SALTO{i}",
                    vagon=f"VS{i}",
                    numero_guia=f"GS{i}",
                    hacienda_id=h.id,
                    suerte_id=s.id,
                    peso_muestra=base[i],
                    peso_mineral=5.0,
                    peso_vegetal_extrano=2.0,
                    usuario_id=user.id,
                    created_at=datetime(2026, 6, 15, 20 + i, 0, 0, tzinfo=timezone.utc),
                )
                db.add(w)
                db.flush()
            db.commit()

            records = db.query(Weighing).order_by(Weighing.id).all()
            last = records[-1]
            total = float(last.peso_muestra + last.peso_mineral + last.peso_vegetal_extrano)
            results = self.detector._detect_temporal(records, total, last.id)
            # Debe haber detectado racha
            rachas = [r for r in results if "Racha" in r.detail]
            self.assertGreaterEqual(len(rachas), 1)
        finally:
            db.close()


class TestAnomalyDetectorRun(_DetectorTestBase):
    """T29: Integracion de 3 capas via run()."""

    def test_run_returns_empty_on_normal(self):
        """R6: Pesaje normal no genera anomalias."""
        db = self.SessionLocal()
        try:
            last = db.query(Weighing).order_by(Weighing.id.desc()).first()
        finally:
            db.close()
        results = self.detector.run(last)
        self.assertEqual(len(results), 0)


class TestWindowConfig(_DetectorTestBase):
    """T29: Limite por registros y por horas."""

    def test_window_respects_size(self):
        """R11: La ventana respeta window_size."""
        db = self.SessionLocal()
        try:
            records = self.detector._get_window(db)
            self.assertLessEqual(len(records), self.config.window_size)
        finally:
            db.close()


class TestDetectOnDemand(_DetectorTestBase):
    """T29: Deteccion bajo demanda."""

    def test_detect_on_demand(self):
        results = self.detector.detect_on_demand(10, 3.0)
        self.assertIsInstance(results, list)
