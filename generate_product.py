#!/usr/bin/env python3
"""Seletor de features -> produto. Lê features.json e gera generated/docker-compose.yml.

Uso:  python generate_product.py [features.json]
É aqui que a Linha de Produto "constrói" um novo produto: só os serviços (features)
escolhidos entram no compose, e as variantes viram variáveis de ambiente.
"""
import json
import os
import sys
from common.lps import PORTS, GATEWAY_PORT

MANDATORY = ["auth", "catalog", "cart", "order", "payment"]
REQUIRES = {"cart": ["catalog"], "order": ["cart", "payment"]}
ENV_VAR = {"auth": "AUTH_VARIANT", "catalog": "CATALOG_VARIANT", "payment": "PAYMENT_METHODS",
           "recommendation": "REC_STRATEGY", "shipping": "SHIPPING_VARIANT",
           "notification": "NOTIFICATION_CHANNELS"}


def resolve(path="features.json"):
    cfg = json.load(open(path, encoding="utf-8"))
    feats = cfg["features"]
    active = [s for s in PORTS if feats.get(s, {}).get("enabled", s in MANDATORY)]
    for m in MANDATORY:
        if m not in active:
            raise SystemExit(f"Feature obrigatória '{m}' não pode ser desabilitada")
    for svc in active:
        for dep in REQUIRES.get(svc, []):
            if dep not in active:
                raise SystemExit(f"'{svc}' requer '{dep}'")
    env = {}
    for svc in active:
        v = feats.get(svc, {}).get("variant")
        if v is not None and svc in ENV_VAR:
            env[svc] = {ENV_VAR[svc]: ",".join(v) if isinstance(v, list) else v}
    return cfg.get("product_name", "produto"), active, env


def common_env(active):
    e = {"ENABLED_SERVICES": ",".join(active)}
    for s in active:
        e[f"{s.upper()}_URL"] = f"http://{s}-service:{PORTS[s]}"
    return e


def build_compose(active, env):
    shared = common_env(active)
    lines = ["# Gerado por generate_product.py — não edite à mão", "services:"]

    def add(name, module, port, extra):
        lines.append(f"  {name}:")
        lines.append("    build: {context: ., dockerfile: Dockerfile.service}")
        lines.append(f"    command: uvicorn {module} --host 0.0.0.0 --port {port}")
        lines.append(f"    ports: ['{port}:{port}']")
        lines.append("    volumes: ['lps-data:/data']")
        lines.append("    environment:")
        for k, v in {**shared, **extra}.items():
            lines.append(f"      {k}: \"{v}\"")

    add("gateway", "gateway.main:app", GATEWAY_PORT, {})
    for s in active:
        add(f"{s}-service", f"services.{s}.main:app", PORTS[s], env.get(s, {}))
    lines += ["volumes:", "  lps-data: {}"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    name, active, env = resolve(sys.argv[1] if len(sys.argv) > 1 else "features.json")
    os.makedirs("generated", exist_ok=True)
    with open("generated/docker-compose.yml", "w", encoding="utf-8") as f:
        f.write(build_compose(active, env))
    print(f"Produto '{name}' gerado com os serviços: {', '.join(active)}")
    print("Suba com:  docker compose -f generated/docker-compose.yml up --build")
