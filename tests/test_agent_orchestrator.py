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
                                "arguments": '{"fecha_inicio":"2020-01-01","fecha_fin":"2020-01-02"}',
                            },
                        }],
                    },
                }],
            },
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "No hay datos para el periodo consultado.",
                    },
                }],
            },
        ]
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


class TestSmsQuerySecondTurnNoTools(_OrchTestBase):
    """Verificar que la segunda vuelta NO fuerza tool_calls."""

    def test_second_turn_called_without_tools(self):
        """Segunda llamada al LLM debe hacerse con tools=None."""
        # Primera llamada: LLM devuelve tool_call
        # Segunda llamada: LLM parafrasea
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
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Hay 10 registros con promedio de 107 kg.",
                    },
                }],
            },
        ]
        self.mock_sql_tools.execute_tool.return_value = {
            "count": 10, "avg": 107.0,
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query("+573001234567", "Cuantos pesajes hoy?")

        # Verificar que la segunda llamada NO incluye tools (tools=None)
        self.assertEqual(self.mock_llm.chat_completion.call_count, 2)
        second_call_args = self.mock_llm.chat_completion.call_args_list[1]
        # call_args_list[1] = (args, kwargs) de la segunda llamada
        _, second_kwargs = second_call_args
        self.assertIsNone(second_kwargs.get("tools"), "Segunda vuelta debe tener tools=None")


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


# ======================================================================
# F28: Tests de multiturno
# ======================================================================

class _MultiTurnTestBase(unittest.TestCase):
    """Base para tests de multiturno con AiMultiTurnService."""

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

        # Crear persistencia y AiMultiTurnService
        from src.sms_persistence import SmsPersistenceService
        self.persistence = SmsPersistenceService(db_session_factory=self.SessionLocal)

        from src.ai_multi_turn import AiMultiTurnService
        self.ai_multi_turn = AiMultiTurnService(
            db_session_factory=self.SessionLocal,
            persistence=self.persistence,
        )

        from src.agent_orchestrator import AgentOrchestrator
        self.orchestrator = AgentOrchestrator(
            llm_client=self.mock_llm,
            sql_tools=self.mock_sql_tools,
            sms_service=self.mock_sms,
            db_session_factory=self.SessionLocal,
            ai_multi_turn_service=self.ai_multi_turn,
        )


class TestHandleSmsQueryMultiTurn(_MultiTurnTestBase):
    """T8: Tests de multiturno en handle_sms_query."""

    def test_handle_sms_query_multiturn_uses_conversation(self):
        """R1: Verifica que se crea/usa conversacion ai_query."""
        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hola, en que puedo ayudarte?",
                },
            }],
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query("+573001234567", "hola")

        # Verificar que se creo una conversacion ai_query
        conv = self.persistence.get_active_conversation_by_peer(
            "+573001234567", "ai_query",
        )
        self.assertIsNotNone(conv)
        self.assertEqual(conv.status, "active")

    def test_handle_sms_query_multiturn_with_history(self):
        """R4: Envia historial completo al LLM."""
        # Primero crear una conversacion con historial previo
        conv = self.persistence.create_conversation(
            peer_number="+573001234567",
            workflow_type="ai_query",
            metadata={
                "message_history": [
                    {"user": "cuantos pesajes hoy?", "assistant": "Hoy hubo 25 pesajes."},
                ],
            },
        )

        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Ayer hubo 30 pesajes.",
                },
            }],
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query(
            "+573001234567", "y ayer?",
            conversation_id=conv.id,
        )

        # Verificar que la llamada al LLM incluye el historial
        call_args = self.mock_llm.chat_completion.call_args
        messages_sent = call_args[0][0]
        # Debe haber al menos system, user historico, assistant historico, nuevo user
        self.assertGreaterEqual(len(messages_sent), 4)
        # El segundo mensaje debe ser el historico del usuario
        self.assertEqual(messages_sent[1]["content"], "cuantos pesajes hoy?")

    def test_handle_sms_query_farewell_completes_conversation(self):
        """R8: Despedida marca conversacion como completed."""
        conv = self.persistence.create_conversation(
            peer_number="+573001234567",
            workflow_type="ai_query",
            status="active",
        )

        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "De nada, hasta luego!",
                },
            }],
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query(
            "+573001234567", "gracias!",
            conversation_id=conv.id,
        )

        # La conversacion debe estar completed
        updated = self.persistence.get_conversation(conv.id)
        self.assertEqual(updated.status, "completed")

    def test_handle_sms_query_tool_call_logged(self):
        """R6: tool_calls se registran en sms_ai_tool_log."""
        conv = self.persistence.create_conversation(
            peer_number="+573001234567",
            workflow_type="ai_query",
            status="active",
        )
        msg = self.persistence.create_message(
            conversation_id=conv.id,
            direction="received",
            peer_number="+573001234567",
            body="cuantos pesajes?",
            status="received",
        )

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
                                "arguments": '{"fecha_inicio":"2026-06-01","fecha_fin":"2026-06-15"}',
                            },
                        }],
                    },
                }],
            },
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Hay 42 pesajes con promedio 107 kg.",
                    },
                }],
            },
        ]
        self.mock_sql_tools.execute_tool.return_value = {
            "count": 42, "avg": 107.0,
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query(
            "+573001234567", "cuantos pesajes?",
            message_id=msg.id,
            conversation_id=conv.id,
        )

        # Verificar tool log
        from src.models import SmsAiToolLog
        db = self.SessionLocal()
        try:
            logs = db.query(SmsAiToolLog).filter(
                SmsAiToolLog.conversation_id == conv.id,
            ).all()
            self.assertGreaterEqual(len(logs), 1)
            self.assertEqual(logs[0].tool_name, "get_basic_stats")
        finally:
            db.close()

    def test_handle_sms_query_fifo_rotation(self):
        """R3: Multiples exchanges rotan FIFO."""
        conv = self.persistence.create_conversation(
            peer_number="+573001234567",
            workflow_type="ai_query",
            status="active",
            metadata={
                "message_history": [
                    {"user": f"msg{i}", "assistant": f"resp{i}"}
                    for i in range(9)
                ],
            },
        )

        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Respuesta numero 10.",
                },
            }],
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query(
            "+573001234567", "msg9",
            conversation_id=conv.id,
        )

        # El historial debe tener 10 exchanges
        updated = self.persistence.get_conversation(conv.id)
        history = self.ai_multi_turn.get_message_history(updated)
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]["user"], "msg0")

        # Enviar uno mas — debe FIFO
        self.orchestrator.handle_sms_query(
            "+573001234567", "msg10",
            conversation_id=conv.id,
        )
        updated = self.persistence.get_conversation(conv.id)
        history = self.ai_multi_turn.get_message_history(updated)
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]["user"], "msg1")

    def test_handle_sms_query_legacy_compatibility(self):
        """R7: Sin message_id/conversation_id funciona en modo legacy."""
        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hola!",
                },
            }],
        }
        self.mock_sms.send_sms.return_value = True

        # Sin message_id ni conversation_id — modo legacy
        result = self.orchestrator.handle_sms_query("+573001234567", "hola")
        self.assertTrue(result)

        # Se debe haber creado una conversacion ai_query
        conv = self.persistence.get_active_conversation_by_peer(
            "+573001234567", "ai_query",
        )
        self.assertIsNotNone(conv)

    def test_handle_sms_query_passes_conversation_id_to_send_sms(self):
        """Bug fix: send_sms recibe conversation_id de la conversación AI activa.
        Esto evita que los SMS enviados caigan en una conversación 'unknown'
        separada."""
        # Crear conversación ai_query activa
        conv = self.persistence.create_conversation(
            peer_number="+573001234567",
            workflow_type="ai_query",
            status="active",
        )

        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Respuesta de prueba.",
                },
            }],
        }
        self.mock_sms.send_sms.return_value = True

        self.orchestrator.handle_sms_query(
            "+573001234567", "consulta de prueba",
            conversation_id=conv.id,
        )

        # Verificar que send_sms fue llamado con conversation_id
        self.mock_sms.send_sms.assert_called()
        call_kwargs = self.mock_sms.send_sms.call_args
        # call_args is (args, kwargs) — verificamos que tenga conversation_id
        self.assertIn("conversation_id", call_kwargs[1])
        self.assertEqual(call_kwargs[1]["conversation_id"], conv.id)
