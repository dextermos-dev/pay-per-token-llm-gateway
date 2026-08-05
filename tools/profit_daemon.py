"""
Módulo de Automatización de Profit: Daemon de Rastreo Rápido (tools/profit_daemon.py)
Ejecuta el escaneo de la API REST de GitHub cada 10 minutos (0 tokens consumidos durante el escaneo).
Prioriza respuestas ultra-rápidas para asegurar la recompensa.
"""

import time
import os
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_profit_daemon(interval_minutes: int = 10):
    print(f"[*] Profit Daemon iniciado. Escaneando nuevas oportunidades cada {interval_minutes} minutos (0 tokens)...")
    while True:
        try:
            print("[+] Ejecutando ciclo de descubrimiento de alta velocidad...")
            cmd = ["/usr/local/bin/python3", os.path.join(PROJECT_ROOT, "main.py")]
            subprocess.run(cmd, cwd=PROJECT_ROOT)
        except Exception as e:
            print(f"[!] Error en Profit Daemon: {e}")
        
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    run_profit_daemon(interval_minutes=10)
