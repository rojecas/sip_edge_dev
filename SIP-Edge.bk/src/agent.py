import json
import re
from openai import OpenAI  # Usamos el cliente estándar de OpenAI

class SIPEdgeAgent:
    def __init__(self, model_path, tools_logic):
        # Conectamos al servidor local (que levantaremos en el siguiente paso)
        self.client = OpenAI(base_url="http://localhost:8000/v1", api_key="local-dev")
        self.tools = tools_logic
        self.grammar_file = "sip_edge.gbnf" 

    def run(self, user_input):
        # 1. Preparar el Prompt (Ingrediente 7)
        prompt = f"Usuario: {user_input}"
        
        # 2. Inferencia (Aquí es donde ocurre la magia local)
        # Pasamos la gramática para que la respuesta sea perfecta
        response = self.client.completions.create(
            model="qwen-2.5-3b",
            prompt=prompt,
            extra_body={"grammar": open(self.grammar_file).read()} # Gramática GBNF
        )
        
        raw_output = response.choices[0].text
        
        # 3. Parsing (Extracción de Action y Args)
        try:
            action = re.search(r"Action: (\w+)", raw_output).group(1)
            args_str = re.search(r"Args: (\{.*\})", raw_output).group(1)
            args = json.loads(args_str)
            
            # 4. Ejecución de la Herramienta (Ingrediente 5)
            if action == "query_weighing_data":
                return self.tools.query_weighing_data(**args)
            elif action == "detect_anomalies":
                return self.tools.detect_anomalies(**args)
            elif action == "send_sms_alert":
                return self.tools.send_sms_alert(**args)
            else:
                return "No se requiere acción adicional."
                
        except Exception as e:
            return f"Error en procesamiento: {str(e)}"