#!/usr/bin/env python3
"""Sobe o produto sem Docker (processos uvicorn locais) e mostra a tabela de portas (item 6.4)."""
import os
import signal
import subprocess
import sys
import time
from common.lps import PORTS, GATEWAY_PORT
from generate_product import resolve

name, active, env = resolve(sys.argv[1] if len(sys.argv) > 1 else "features.json")
base = {**os.environ, "ENABLED_SERVICES": ",".join(active), "PYTHONPATH": os.getcwd()}
procs = []


def start(label, module, port, extra):
    procs.append(subprocess.Popen(
        [sys.executable, "-m", "uvicorn", module, "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        env={**base, **extra}))
    print(f"  {label:<26} http://127.0.0.1:{port}")


def _stop(*_):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, _stop)  # kill/terminate também encerra os serviços filhos
print(f"Produto: {name}\nMicroserviços em execução:")
for s in active:
    start(f"{s}-service", f"services.{s}.main:app", PORTS[s], env.get(s, {}))
start("api-gateway", "gateway.main:app", GATEWAY_PORT, {})
print("\nDocs do gateway: http://127.0.0.1:8000/ui/ (loja) e http://127.0.0.1:8000/docs   |   Ctrl+C para encerrar")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for p in procs:
        p.terminate()
    for p in procs:
        p.wait()  # só encerra quando todas as portas foram liberadas
