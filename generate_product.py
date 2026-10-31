#!/usr/bin/env python3
"""Seletor de features -> produto. Lê um features.json, valida e gera o docker-compose do produto.

Uso:
  python generate_product.py                         # features.json -> generated/docker-compose.yml
  python generate_product.py loja.json --out build   # outro arquivo e outra pasta de saída
  python generate_product.py loja.json --check       # só valida (não gera nada)

A validação confere features obrigatórias, dependências (requer) e as cardinalidades dos pontos
de variação (XOR [1,1] e OR [1,n]) definidas em common/model.py. Ela roda antes de gerar/subir.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

from common.lps import PORTS, GATEWAY_PORT
from common.model import FEATURES, MANDATORY, VARIATION_POINTS, validate, variants_of

ROOT = os.path.dirname(os.path.abspath(__file__))


def resolve(path="features.json"):
    """Valida e devolve (nome do produto, serviços ativos, variáveis de ambiente por serviço)."""
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"Arquivo não encontrado: {path}")
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON inválido em {path}: {e}")
    errors = validate(cfg)
    if errors:
        raise SystemExit(f"Configuração inválida em {path}:\n" + "\n".join(f"  - {e}" for e in errors))
    feats = cfg["features"]
    active = [s for s in FEATURES if feats.get(s, {}).get("enabled", s in MANDATORY)]
    env = {s: {VARIATION_POINTS[s]["env"]: ",".join(variants_of(feats[s]))} for s in active if s in VARIATION_POINTS}
    return cfg.get("product_name", "produto"), active, env


def slug(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9_-]+", "-", ascii_name.lower()).strip("-") or "lps"


def common_env(active):
    e = {"ENABLED_SERVICES": ",".join(active)}
    for s in active:
        e[f"{s.upper()}_URL"] = f"http://{s}-service:{PORTS[s]}"
    return e


def build_compose(name, active, env, out_dir):
    """Texto do docker-compose.yml. O contexto de build é a raiz do projeto, relativa ao arquivo gerado."""
    context = os.path.relpath(ROOT, out_dir).replace(os.sep, "/")
    shared = common_env(active)
    q = json.dumps  # JSON é YAML válido para textos e listas
    lines = ["# Gerado por generate_product.py — não edite à mão", f"name: {slug(name)}", "services:"]

    def add(svc_name, module, port, extra):
        probe = f"import urllib.request; urllib.request.urlopen('http://127.0.0.1:{port}/health')"
        lines.extend([
            f"  {svc_name}:",
            "    build:",
            f"      context: {context}",
            "      dockerfile: Dockerfile.service",
            f"    command: {q(['uvicorn', module, '--host', '0.0.0.0', '--port', str(port)])}",
            f"    ports: [{q(f'{port}:{port}')}]",
            f"    volumes: [{q('lps-data:/data')}]",
            f"    healthcheck: {{test: {q(['CMD', 'python', '-c', probe])}, interval: 10s, timeout: 3s, retries: 5}}",
            "    environment:",
        ])
        for k, v in {**shared, **extra}.items():
            lines.append(f"      {k}: {q(v)}")

    add("gateway", "gateway.main:app", GATEWAY_PORT, {})
    for s in active:
        add(f"{s}-service", f"services.{s}.main:app", PORTS[s], env.get(s, {}))
    lines += ["volumes:", "  lps-data: {}"]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Valida e gera um produto da LPS a partir de um features.json")
    ap.add_argument("features", nargs="?", default="features.json")
    ap.add_argument("--out", default="generated", help="pasta de saída do docker-compose.yml")
    ap.add_argument("--check", action="store_true", help="apenas valida a configuração")
    args = ap.parse_args(argv)

    name, active, env = resolve(args.features)
    print(f"Configuração válida. Produto '{name}': {', '.join(active)}")
    for s, e in env.items():
        print(f"  {s}: " + ", ".join(f"{k}={v}" for k, v in e.items()))
    if args.check:
        return
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "docker-compose.yml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_compose(name, active, env, out_dir))
    print(f"Gerado: {os.path.relpath(path)}")
    print(f"Suba com:  docker compose -f {os.path.relpath(path)} up --build")


if __name__ == "__main__":
    main()
