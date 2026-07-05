"""Orquestador que conecta LLM + SQL Tools + SMS para consultas y anomalias."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.anomaly_detector import AnomalyResult
from src.database import SessionLocal
from src.llm_client import LlamaClient, LlamaConnectionError
from src.models import AnomalyLog, Weighing
from src.sql_tools import SqlTools, TOOL_DEFINITIONS

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Eres un asistente de analisis de datos de pesaje agricola (SIP-Edge). "
    "Tu funcion es responder consultas sobre pesajes de cana de azucar usando "
    "exclusivamente las herramientas SQL disponibles. "
    "NUNCA inventes numeros, totales, promedios ni ninguna metrica cuantitativa. "
    "Solo reporta valores que provengan de la ejecucion de herramientas SQL. "
    "Cuando uses herramientas, espera los resultados antes de responder. "
    "Si no hay datos disponibles para el periodo consultado, informa claramente. "
    "Responde siempre en espanol, en formato conciso para SMS (max 160 caracteres)."
    "\n\n"
    "COMANDOS RECONOCIDOS POR EL SISTEMA (NO son consultas de datos):\n"
    "- manual on [N{h|m}]: activar modo manual de emergencia\n"
    "- manual on ext N{h|m}: extender tiempo de modo manual\n"
    "- manual off: desactivar modo manual\n"
    "- reset password <usuario>: restablecer contrasena de usuario\n\n"
    "Si el usuario envia uno de estos comandos (incluso con errores de ortografia), "
    "NO intentes procesarlo como consulta de datos. Responde unicamente indicando "
    "que es un comando del sistema y cual es la sintaxis correcta."
)

ANOMALY_SYSTEM_PROMPT = (
    "Eres un asistente de deteccion de anomalias para SIP-Edge. "
    "Se te proporcionara el contexto estadistico de una ventana de pesajes "
    "y una lista de anomalias detectadas por tres capas de analisis: "
    "Z-Score, ratios entre materiales (vegetal/muestra, mineral/muestra), "
    "y tasa de cambio temporal. "
    "Genera un reporte narrativo en espanol describiendo las anomalias "
    "encontradas, su posible significado operativo, y recomendaciones. "
    "Se conciso: maximo 500 caracteres. No uses herramientas SQL aqui."
)


class AgentOrchestrator:
    """Orquestador central del sistema inteligente.

    Conecta el LLM local (Qwen 2.5 1.5B) con las herramientas SQL
    parametrizadas y el servicio SMS para:
    - Generar reportes narrativos ante anomalias detectadas.
    - Procesar consultas ad-hoc via SMS con Function Calling.
    """

    def __init__(
        self,
        llm_client: LlamaClient,
        sql_tools: SqlTools,
        sms_service,
        db_session_factory,
    ) -> None:
        self._llm = llm_client
        self._sql_tools = sql_tools
        self._sms = sms_service
        self._db_session_factory = db_session_factory

    # ------------------------------------------------------------------
    # Manejo de anomalias (T18)
    # ------------------------------------------------------------------

    def handle_anomaly(
        self, anomalies: list[AnomalyResult], context: dict
    ) -> list[AnomalyLog]:
        """Invoca LLM con contexto de anomalias, genera narrativa, envia SMS.

        Retorna la lista de registros AnomalyLog creados.

        Si el LLM falla, registra el error y continua sin interrumpir
        el servicio de pesaje.
        """
        if not anomalies:
            logger.debug("handle_anomaly llamado sin anomalias, omitiendo")
            return []

        db = self._db_session_factory()
        try:
            # Construir prompt para el LLM
            context_text = json.dumps(context, ensure_ascii=False, indent=2)
            anomaly_list = [
                {
                    "capa": a.layer,
                    "metrica": a.metric_value,
                    "umbral": a.threshold,
                    "detalle": a.detail,
                }
                for a in anomalies
            ]
            anomaly_text = json.dumps(anomaly_list, ensure_ascii=False, indent=2)

            messages = [
                {"role": "system", "content": ANOMALY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Contexto de la ventana de pesajes:\n{context_text}\n\n"
                        f"Anomalias detectadas:\n{anomaly_text}\n\n"
                        "Genera un reporte narrativo describiendo estas anomalias."
                    ),
                },
            ]

            llm_report: str | None = None
            try:
                response = self._llm.chat_completion(messages, tools=None)
                choices = response.get("choices", [])
                if choices:
                    llm_report = choices[0].get("message", {}).get("content", "")
            except LlamaConnectionError:
                logger.error(
                    "Fallo LLM al generar reporte de anomalias, "
                    "continuando sin narrativa"
                )
                llm_report = None

            # Insertar registros en anomaly_log
            logs: list[AnomalyLog] = []
            for anomaly in anomalies:
                log_entry = AnomalyLog(
                    record_id=anomaly.record_id,
                    layer=anomaly.layer,
                    z_score=anomaly.z_score,
                    metric_value=anomaly.metric_value,
                    threshold=anomaly.threshold,
                    llm_report=llm_report if anomaly == anomalies[0] else None,
                    sent_sms=False,
                    anomaly_context=json.dumps(context, ensure_ascii=False),
                )
                db.add(log_entry)
                logs.append(log_entry)

            db.commit()

            # Enviar SMS con el reporte narrativo si el LLM respondio
            if llm_report:
                sms_text = self._truncate_for_sms(llm_report)
                self._send_to_corresponsales(sms_text)
                # Marcar como enviado
                for log_entry in logs:
                    log_entry.sent_sms = True
                db.commit()

            return logs
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Manejo de consultas SMS (T19)
    # ------------------------------------------------------------------

    def handle_sms_query(self, sender_phone: str, text: str) -> bool:
        """Procesa consulta SMS: LLM → tool_calls → ejecucion → respuesta SMS.

        Flujo:
        1. Construye mensajes del sistema + consulta + definiciones de tools.
        2. Invoca LLM con tools.
        3. Si hay tool_calls, ejecuta cada tool con datos reales.
        4. Pasa resultados al LLM para segunda vuelta (parafraseo).
        5. Envia respuesta por SMS al remitente.
        """
        # Look up user role for context-aware responses
        role = "unknown"
        _db = None
        try:
            _db = self._db_session_factory()
            from src.models import User
            _user = _db.query(User).filter(
                User.phone == sender_phone, User.is_active == True
            ).first()
            if _user:
                role = _user.role
        except Exception:
            pass
        finally:
            if _db:
                _db.close()

        role_note = ""
        if role == "corresponsal":
            role_note = (
                "\n\nIMPORTANTE: El usuario es CORRESPONSAL. "
                "SOLO puede hacer consultas de datos de pesaje. "
                "Si el mensaje NO es una consulta de datos, responde UNICAMENTE: "
                "'Solo puedo responder consultas sobre datos de pesaje.' "
                "NO menciones comandos del sistema."
            )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + role_note},
            {"role": "user", "content": text},
        ]

        try:
            # Primera vuelta: LLM decide que tools llamar
            response = self._llm.chat_completion(messages, tools=TOOL_DEFINITIONS)
        except LlamaConnectionError:
            self._sms.send_sms(
                sender_phone,
                "Lo siento, el sistema de analisis no esta disponible en este momento.",
            )
            return False

        choices = response.get("choices", [])
        if not choices:
            self._sms.send_sms(sender_phone, "No se pudo procesar la consulta.")
            return True

        msg = choices[0].get("message", {})
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            # LLM respondio directamente sin tools
            direct_response = msg.get("content", "")
            if direct_response:
                self._sms.send_sms(sender_phone, self._truncate_for_sms(direct_response))
            else:
                self._sms.send_sms(sender_phone, "No se pudo procesar la consulta.")
            return True

        # Anadir respuesta del asistente con tool_calls al historial
        messages.append({
            "role": "assistant",
            "content": msg.get("content"),
            "tool_calls": tool_calls,
        })

        # Ejecutar cada tool_call
        for tc in tool_calls:
            func_info = tc.get("function", {})
            tool_name = func_info.get("name", "")
            try:
                arguments = json.loads(func_info.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}

            try:
                result = self._sql_tools.execute_tool(tool_name, arguments)
            except Exception as e:
                logger.error("Error ejecutando tool %s: %s", tool_name, e)
                result = {"error": str(e)}

            # Anadir resultado de la tool al historial
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        # Segunda vuelta: LLM parafrasea los resultados
        try:
            final_response = self._llm.chat_completion(messages, tools=TOOL_DEFINITIONS)
        except LlamaConnectionError:
            # Sin LLM, enviar resumen crudo
            self._sms.send_sms(
                sender_phone,
                self._format_crude_results(messages),
            )
            return True

        final_choices = final_response.get("choices", [])
        if final_choices:
            final_text = final_choices[0].get("message", {}).get("content", "")
            if final_text:
                self._sms.send_sms(sender_phone, self._truncate_for_sms(final_text))
                return True

        self._sms.send_sms(sender_phone, "No se pudo generar una respuesta.")
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _send_to_corresponsales(self, message: str) -> None:
        """Envia un SMS a todos los corresponsales configurados."""
        db = self._db_session_factory()
        try:
            from src.models import User as _U
            corresponsales = (
                db.query(_U)
                .filter(_U.role == "corresponsal", _U.is_active == True)
                .all()
            )
            phones = [c.phone for c in corresponsales if c.phone]
            if not phones:
                # Fallback: usar admin_phones del SMS config
                self._sms.send_alert_to_admins(message)
                return
            for phone in phones:
                self._sms.send_sms(phone, message)
        finally:
            db.close()

    def _truncate_for_sms(self, text: str, max_chars: int = 480) -> str:
        """Trunca texto para SMS (3 segmentos de 160 chars)."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."

    @staticmethod
    def _has_data(result: dict) -> bool:
        """Verifica si un resultado de tool tiene datos no vacios."""
        if isinstance(result, dict):
            if result.get("count", 0) > 0:
                return True
            if len(result.get("violations", [])) > 0:
                return True
            total = result.get("total") or result.get("peso_total") or result.get("total_weight")
            if total is not None and float(total) > 0:
                return True
        if isinstance(result, list) and len(result) > 0:
            return True
        return False

    @staticmethod
    def _format_crude_results(messages: list[dict]) -> str:
        """Formatea resultados crudos cuando el LLM no esta disponible."""
        results = []
        for msg in messages:
            if msg.get("role") == "tool":
                content = msg.get("content", "")
                try:
                    data = json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    continue
                if isinstance(data, dict):
                    # Extraer campos clave
                    count = data.get("count", "?")
                    avg = data.get("avg") or data.get("peso_promedio") or ""
                    total = data.get("total") or data.get("peso_total") or ""
                    if avg:
                        results.append(f"Prom={avg}")
                    if total:
                        results.append(f"Tot={total}")
                    results.append(f"N={count}")
        return "Resumen: " + " ".join(results)
