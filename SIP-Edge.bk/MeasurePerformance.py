import time
import psutil
import os

def measure_performance(agent, test_prompt):
    process = psutil.Process(os.getpid())
    
    # --- Medición de Inicio ---
    start_mem = process.memory_info().rss / (1024 * 1024)  # MB
    start_time = time.perf_counter()
    
    # --- Ejecución ---
    result = agent.run(test_prompt)
    
    # --- Medición de Fin ---
    end_time = time.perf_counter()
    end_mem = process.memory_info().rss / (1024 * 1024)  # MB
    
    latency = end_time - start_time
    mem_peak = end_mem - start_mem  # Consumo incremental
    
    return {
        "prompt": test_prompt,
        "latency_sec": round(latency, 3),
        "ram_usage_mb": round(end_mem, 2),
        "cpu_percent": psutil.cpu_percent(),
        "result_preview": str(result)[:50] # Solo para verificar
    }

# Ejemplo de uso en el piloto:
# metrics = measure_performance(mi_agente, "¿Hay anomalías hoy?")
# print(metrics)