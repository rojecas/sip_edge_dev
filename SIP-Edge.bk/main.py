import json
import time
import psutil
import os
import csv
from src.agent import SIPEdgeAgent
from src.tools import SIPEdgeTools

# --- CONFIGURACIÓN ---
PROMPTS_FILE = "data/test_prompts.json"
RESULTS_FILE = "results/metricas_piloto.csv"
MODEL_NAME = "qwen2.5-1.5b-q4_k_m"

def run_pilot():
    # 1. Inicializar componentes
    tools = SIPEdgeTools(db_path="data/materia_prima.db")
    agent = SIPEdgeAgent(model_path=MODEL_NAME, tools_logic=tools)
    
    # 2. Cargar Prompts
    with open(PROMPTS_FILE, 'r') as f:
        test_cases = json.load(f)

    # 3. Preparar CSV de resultados
    os.makedirs("results", exist_ok=True)
    csv_headers = ["id", "category", "prompt", "latency_sec", "ram_peak_mb", "cpu_percent", "success_format"]
    
    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

        print(f"🚀 Iniciando piloto de rendimiento con {len(test_cases)} prompts...")

        # 4. Loop de Ejecución y Medición
        for case in test_cases:
            print(f"Testing ID {case['id']}: {case['category']}...", end="\r")
            
            # Medición de Recursos Inicial
            process = psutil.Process(os.getpid())
            start_mem = process.memory_info().rss / (1024 * 1024)
            start_time = time.perf_counter()
            
            # --- INFERENCIA ---
            try:
                # Ejecutamos el agente
                response = agent.run(case['prompt'])
                success_format = 1
            except Exception as e:
                print(f"\n❌ Error en ID {case['id']}: {e}")
                response = None
                success_format = 0
            
            # Medición de Recursos Final
            end_time = time.perf_counter()
            end_mem = process.memory_info().rss / (1024 * 1024)
            
            # Cálculo de Métricas
            latency = end_time - start_time
            ram_peak = end_mem # RAM total ocupada en el pico
            cpu_usage = psutil.cpu_percent(interval=None)

            # 5. Guardar en CSV
            writer.writerow([
                case['id'], 
                case['category'], 
                case['prompt'], 
                round(latency, 3), 
                round(ram_peak, 2), 
                cpu_usage,
                success_format
            ])
            
            # Pequeña pausa para estabilizar CPU entre pruebas
            time.sleep(0.5)

    print(f"\n✅ Piloto finalizado. Resultados guardados en: {RESULTS_FILE}")

if __name__ == "__main__":
    run_pilot()