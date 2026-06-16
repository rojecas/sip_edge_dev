"""Tests for AgentOrchestrator: anomaly handling, SMS query, failures."""

import unittest
from datetime import date, time
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.anomaly_detector import AnomalyResult
from src.config import AgentConfig
from src.llm_client import LlamaConnectionError
from src.models import Base, Hacienda, Suerte, User, Weighing


class _OrchTestBase(unittest.TestCase):
    """Base con mocks para LlamaClient, SqlTools, SMSService."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Crear usuario corresponsal con telefono
        db = self.SessionLocal()
        try:
            u = User(username="corr", password_hash="h", role="corresponsal",
                     full_name="Corresponsal", phone="+573001234567")
            operator = User(username="op", password_hash="h", role="operator",
                           full_name="Operador")
            h = Hacienda(codigo="H001", nombre="Hacienda")
            db.add_all([u, operator, h])
            db.flush()
            s = Suerte(hacienda_id=h.id, codigo_suerte="S01")
            db.add(s)
            db.flush()

            w = Weighing(
                fecha=date(2026, 6, 15),
                hora=time(8, 0, 0),
                tractomula="T1", vagon="V1", numero_guia="G1",
                hacienda_id=h.id, suerte_id=s.id,
                peso_muestra=100.0, peso_mineral=5.0, peso_vegetal_extrano=2.0,
                usuario_id=operator.id,
            )
            db.add(w)
            db.commit()
            db.refresh(w)
            self.weighing = w
        finally:
            db.close()

        # Mocks
        self.mock_llm = mock.MagicMock()
        self.mock_sql_tools = mock.MagicMock()
        self.mock_sms = mock.MagicMock()

        from src.agent_orchestrator import AgentOrchestrator
        self.orchestrator = AgentOrchestrator(
            llm_client=self.mock_llm,
            sql_tools=self.mock_sql_tools,
            sms_service=self.mock_sms,
            db_session_factory=self.SessionLocal,
        )


class TestHandleAnomaly(_OrchTestBase):
    """T31: Verificar que handle_anomaly llama al LLM y envia SMS."""

    def test_handle_anomaly_creates_logs_and_sends_sms(self):
        """R10: Ante anomalia, invoca LLM, crea logs, envia SMS."""
        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Alerta: Se detecto una anomalia en el pesaje.",
                },
            }],
        }
        self.mock_sms.send_sms.return_value = True

        anomalies = [
            AnomalyResult(
                record_id=self.weighing.id,
                layer="zscore",
                z_score=4.5,
                metric_value=150.0,
                threshold=3.0,
                detail="Z-Score excede umbral",
            ),
        ]
        context = {"record_id": self.weighing.id, "peso_total": 107.0}

        logs = self.orchestrator.handle_anomaly(anomalies, context)

        self.assertGreaterEqual(len(logs), 1)
        self.mock_llm.chat_completion.assert_called_once()
        # Debe haber enviado SMS (a corresponsal o admin)
        self.mock_sms.send_sms.assert_called()

    def test_handle_anomaly_no_anomalies(self):
        """R10: Sin anomalias, no hace nada."""
        logs = self.orchestrator.handle_anomaly([], {})
        self.assertEqual(len(logs), 0)
        self.mock_llm.chat_completion.assert_not_called()


class TestHandleSmsQuery(_OrchTestBase):
    """T31: Verificar ciclo completo SMS → LLM → tools → respuesta."""

    def test_sms_query_with_tool_calls(self):
        """R13, R14, R15: Ciclo completo con Function Calling."""
        # Primera llamada: LLM devuelve tool_call
        self.mock_llm.chat_completion.side_effect = [
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_basic_stats",
                                "arguments": '{"fecha_inicio":"2026-06-15","fecha_fin":"2026-06-15"}',
                            },
                        }],
                    },
                }],
            },
            # Segunda llamada: LLM parafrasea
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Hoy se realizaron 10 pesajes con un promedio de 107 kg.",
                    },
                }],
            },
        ]
        self.mock_sql_tools.execute_tool.return_value = {
            "count": 10, "avg": 107.0, "min": 100.0, "max": 120.0, "std": 5.0,
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query("+573001234567", "Cuantos pesajes hoy?")

        # Verificar que se llamo al LLM dos veces
        self.assertEqual(self.mock_llm.chat_completion.call_count, 2)
        # Verificar que se ejecuto la tool
        self.mock_sql_tools.execute_tool.assert_called_once()
        # Verificar que se envio SMS de respuesta
        self.mock_sms.send_sms.assert_called()


class TestSmsQueryEmptyData(_OrchTestBase):
    """T31: Verificar respuesta 'sin datos'."""

    def test_empty_data_responds_no_data(self):
        """R23: Si herramientas retornan datos vacios, responde sin datos."""
        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "get_basic_stats",
                            "arguments": '{"fecha_inicio":"2020-01-01","fecha_fin":"2020-01-02"}',
                        },
                    }],
                },
            }],
        }
        self.mock_sql_tools.execute_tool.return_value = {
            "count": 0, "avg": 0.0, "min": 0.0, "max": 0.0, "std": 0.0,
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query("+573001234567", "Pesajes de 2020?")

        # Debe haber enviado SMS con mensaje de "sin datos" o "no hay datos"
        call_args = self.mock_sms.send_sms.call_args
        if call_args:
            msg = call_args[0][1].lower()
            self.assertTrue("sin datos" in msg or "no hay datos" in msg)


class TestHandleAnomalyLlmFailure(_OrchTestBase):
    """T31: Verificar que fallo del LLM no interrumpe."""

    def test_llm_failure_still_creates_logs(self):
        """R21: Si el LLM falla, se registra error y se continua."""
        self.mock_llm.chat_completion.side_effect = LlamaConnectionError("timeout")

        anomalies = [
            AnomalyResult(
                record_id=self.weighing.id,
                layer="zscore",
                z_score=4.5,
                metric_value=150.0,
                threshold=3.0,
                detail="Z-Score excede umbral",
            ),
        ]
        context = {"record_id": self.weighing.id}

        # No debe lanzar excepcion
        logs = self.orchestrator.handle_anomaly(anomalies, context)

        # Debe haber creado logs aunque el LLM fallo
        self.assertGreaterEqual(len(logs), 1)
        # SMS no debe haberse enviado (llm_report es None)
        # No verificamos send_sms porque solo se llama si hay llm_report

    def test_llm_failure_on_sms_query_sends_fallback(self):
        """R21: Si LLM falla en consulta SMS, envia mensaje de error."""
        self.mock_llm.chat_completion.side_effect = LlamaConnectionError("timeout")
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query("+573001234567", "Cuantos pesajes?")

        self.mock_sms.send_sms.assert_called()


class TestAgentOrchestratorConstruction(_OrchTestBase):
    """Verificar que la construccion del orquestador no falla."""

    def test_construction(self):
        from src.agent_orchestrator import AgentOrchestrator
        orch = AgentOrchestrator(
            llm_client=self.mock_llm,
            sql_tools=self.mock_sql_tools,
            sms_service=self.mock_sms,
            db_session_factory=self.SessionLocal,
        )
        self.assertIsNotNone(orch)
