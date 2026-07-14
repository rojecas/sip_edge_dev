"""Tests de integracion para flujo completo de conversacion multiturno AI.

Feature 28 — ai_multi_turn.
"""

import unittest
from datetime import date, time
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import Base, Hacienda, SmsAiToolLog, SmsConversation, Suerte, User, Weighing
from src.sms_persistence import SmsPersistenceService
from src.ai_multi_turn import AiMultiTurnService


def _build_test_db_engine():
    """Crea un engine SQLite en memoria para tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


class TestFullConversationFlow(unittest.TestCase):
    """T10: Tests de integracion del flujo AI multiturno completo."""

    def setUp(self):
        """Configura engine, persistence, servicio y mocks."""
        self.engine = _build_test_db_engine()
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.persistence = SmsPersistenceService(db_session_factory=self.Session)

        # Datos de prueba
        db = self.Session()
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
        finally:
            db.close()

        self.ai_multi_turn = AiMultiTurnService(
            db_session_factory=self.Session,
            persistence=self.persistence,
        )

        # Mocks para el orquestador
        self.mock_llm = mock.MagicMock()
        self.mock_sql_tools = mock.MagicMock()
        self.mock_sms = mock.MagicMock()
        self.mock_sms.send_sms.return_value = True

        from src.agent_orchestrator import AgentOrchestrator
        self.orchestrator = AgentOrchestrator(
            llm_client=self.mock_llm,
            sql_tools=self.mock_sql_tools,
            sms_service=self.mock_sms,
            db_session_factory=self.Session,
            ai_multi_turn_service=self.ai_multi_turn,
        )

    # ==================================================================
    # test_full_conversation_flow
    # ==================================================================

    def test_full_conversation_flow(self):
        """R1, R2, R4, R6: 3 rounds de preguntas, historial crece, tools se loggean."""
        peer = "+573001234567"

        # --- Round 1 ---
        msg1 = self.persistence.create_message(
            conversation_id=1,  # se ignora, se crea nueva conversacion
            direction="received",
            peer_number=peer,
            body="cuantos pesajes en junio?",
            status="received",
        )
        # LLM responde con tool_call
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
                                "arguments": '{"fecha_inicio":"2026-06-01","fecha_fin":"2026-06-30"}',
                            },
                        }],
                    },
                }],
            },
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "En junio hubo 42 pesajes.",
                    },
                }],
            },
        ]
        self.mock_sql_tools.execute_tool.return_value = {"count": 42, "avg": 107.0}

        self.orchestrator.handle_sms_query(
            peer, "cuantos pesajes en junio?",
            message_id=msg1.id,
        )

        # Verificar que se creo conversacion y tool log
        conv = self.persistence.get_active_conversation_by_peer(peer, "ai_query")
        self.assertIsNotNone(conv, "Debe existir conversacion ai_query activa")

        # Reload para ver metadata actualizada
        conv = self.persistence.get_conversation(conv.id)
        history = self.ai_multi_turn.get_message_history(conv)
        self.assertEqual(len(history), 1, "Debe tener 1 exchange despues del round 1")
        self.assertEqual(history[0]["user"], "cuantos pesajes en junio?")

        # Verificar tool log
        db = self.Session()
        try:
            logs = db.query(SmsAiToolLog).filter(
                SmsAiToolLog.conversation_id == conv.id,
            ).all()
            self.assertEqual(len(logs), 1, "Debe haber 1 tool log")
            self.assertEqual(logs[0].tool_name, "get_basic_stats")
        finally:
            db.close()

        # --- Round 2 ---
        # Reload conversation to get updated metadata
        conv = self.persistence.get_active_conversation_by_peer(peer, "ai_query")

        self.mock_llm.chat_completion.side_effect = [
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "El promedio fue 107 kg.",
                    },
                }],
            },
        ]

        self.orchestrator.handle_sms_query(
            peer, "cual fue el promedio?",
            conversation_id=conv.id,
        )

        # Reload to get updated metadata
        conv_reloaded = self.persistence.get_conversation(conv.id)
        history = self.ai_multi_turn.get_message_history(conv_reloaded)
        self.assertEqual(len(history), 2, "Debe tener 2 exchanges despues del round 2")
        self.assertEqual(history[1]["user"], "cual fue el promedio?")

        # --- Round 3 ---
        # Reload conversation to get updated metadata
        conv = self.persistence.get_active_conversation_by_peer(peer, "ai_query")

        self.mock_llm.chat_completion.side_effect = [
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "El total fue 4494 kg.",
                    },
                }],
            },
        ]

        self.orchestrator.handle_sms_query(
            peer, "y el total?",
            conversation_id=conv.id,
        )

        # Reload to get updated metadata
        conv_reloaded = self.persistence.get_conversation(conv.id)
        history = self.ai_multi_turn.get_message_history(conv_reloaded)
        self.assertEqual(len(history), 3, "Debe tener 3 exchanges despues del round 3")
        self.assertEqual(history[2]["user"], "y el total?")

        # Verificar que los 3 exchanges existen secuencialmente
        self.assertEqual(history[0]["user"], "cuantos pesajes en junio?")
        self.assertEqual(history[1]["user"], "cual fue el promedio?")
        self.assertEqual(history[2]["user"], "y el total?")

    # ==================================================================
    # test_farewell_ends_conversation
    # ==================================================================

    def test_farewell_ends_conversation(self):
        """R8: Enviar 'gracias' completa la conversacion."""
        peer = "+573001234567"

        conv = self.persistence.create_conversation(
            peer_number=peer,
            workflow_type="ai_query",
            status="active",
            metadata={
                "message_history": [
                    {"user": "cuantos pesajes?", "assistant": "42 pesajes."},
                ],
            },
        )

        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "De nada, hasta luego!",
                },
            }],
        }

        self.orchestrator.handle_sms_query(
            peer, "gracias!",
            conversation_id=conv.id,
        )

        updated = self.persistence.get_conversation(conv.id)
        self.assertEqual(updated.status, "completed",
                         "Conversacion debe estar completed tras despedida")

    # ==================================================================
    # test_fifo_rotation_integration
    # ==================================================================

    def test_fifo_rotation_integration(self):
        """R3, R10: 11 mensajes, solo 10 exchanges en historial."""
        peer = "+573001234567"

        # Crear conversacion con 9 exchanges pre-existentes
        pre_history = [
            {"user": f"msg{i}", "assistant": f"resp{i}"}
            for i in range(9)
        ]
        conv = self.persistence.create_conversation(
            peer_number=peer,
            workflow_type="ai_query",
            status="active",
            metadata={"message_history": pre_history},
        )

        # Enviar 2 mensajes mas — debe quedar en 10 exchanges por FIFO
        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Respuesta",
                },
            }],
        }

        self.orchestrator.handle_sms_query(
            peer, "msg9", conversation_id=conv.id,
        )

        updated = self.persistence.get_conversation(conv.id)
        history = self.ai_multi_turn.get_message_history(updated)
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]["user"], "msg0")

        # Mensaje 10: FIFO elimina msg0
        self.orchestrator.handle_sms_query(
            peer, "msg10", conversation_id=conv.id,
        )

        updated = self.persistence.get_conversation(conv.id)
        history = self.ai_multi_turn.get_message_history(updated)
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0]["user"], "msg1",
                         "msg0 debio ser eliminado por FIFO")
        self.assertEqual(history[-1]["user"], "msg10")

    # ==================================================================
    # test_new_conversation_after_completed
    # ==================================================================

    def test_new_conversation_after_completed(self):
        """R7: Despues de despedida, nuevo mensaje crea nueva conversacion."""
        peer = "+573001234567"

        # Conversacion completada
        old_conv = self.persistence.create_conversation(
            peer_number=peer,
            workflow_type="ai_query",
            status="completed",
        )

        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hola de nuevo!",
                },
            }],
        }

        # Si se pasa el conversation_id de la conversacion completada,
        # debe crear una nueva porque status != 'active'
        self.orchestrator.handle_sms_query(
            peer, "hola de nuevo",
            conversation_id=old_conv.id,
        )

        # Debe haber una nueva conversacion activa
        new_conv = self.persistence.get_active_conversation_by_peer(peer, "ai_query")
        self.assertIsNotNone(new_conv, "Debe existir nueva conversacion activa")
        self.assertNotEqual(new_conv.id, old_conv.id,
                           "Debe ser una conversacion diferente a la completada")

    # ==================================================================
    # test_dispatcher_unknown_conversation_upgrade
    # ==================================================================

    def test_dispatcher_unknown_conversation_upgrade(self):
        """R1, R7: Conversacion 'unknown' del dispatcher se actualiza a 'ai_query'."""
        peer = "+573001234567"

        # Simular conversacion creada por el dispatcher como 'unknown'
        dispatcher_conv = self.persistence.create_conversation(
            peer_number=peer,
            workflow_type="unknown",
            status="active",
        )
        msg = self.persistence.create_message(
            conversation_id=dispatcher_conv.id,
            direction="received",
            peer_number=peer,
            body="cuantos pesajes hoy?",
            status="received",
        )

        self.mock_llm.chat_completion.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hoy hubo 15 pesajes.",
                },
            }],
        }

        self.orchestrator.handle_sms_query(
            peer, "cuantos pesajes hoy?",
            message_id=msg.id,
            conversation_id=dispatcher_conv.id,
        )

        # La misma conversacion debe haberse actualizado a ai_query
        updated = self.persistence.get_conversation(dispatcher_conv.id)
        self.assertEqual(updated.workflow_type, "ai_query",
                         "Workflow type debe ser 'ai_query'")
        self.assertEqual(updated.status, "active")

        # No debe haber conversaciones duplicadas
        db = self.Session()
        try:
            count = db.query(SmsConversation).filter(
                SmsConversation.peer_number == peer,
            ).count()
            self.assertEqual(count, 1,
                             "No debe haber conversaciones duplicadas")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
