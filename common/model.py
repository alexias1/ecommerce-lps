"""Modelo de features da LPS: fonte única da verdade sobre features, variantes e restrições.

Usado pelo generate_product.py (validação), pelos testes e conferido contra os registros de
componentes de cada serviço e contra os diagramas.

Cardinalidades (notação do relatório):
  xor -> [1,1]  exatamente uma variante
  or  -> [1,n]  de uma a n variantes
"""
FEATURES = ["auth", "catalog", "cart", "order", "payment", "recommendation", "shipping", "notification"]
MANDATORY = ["auth", "catalog", "cart", "order", "payment"]
REQUIRES = {"cart": ["catalog"], "order": ["cart", "payment"]}

VARIATION_POINTS = {
    "auth":           {"env": "AUTH_VARIANT",          "kind": "or",  "variants": ["email", "social"]},
    "catalog":        {"env": "CATALOG_VARIANT",       "kind": "xor", "variants": ["simple", "search"]},
    "payment":        {"env": "PAYMENT_METHODS",       "kind": "or",  "variants": ["pix", "card", "boleto"]},
    "recommendation": {"env": "REC_STRATEGY",          "kind": "xor", "variants": ["history", "popularity"]},
    "shipping":       {"env": "SHIPPING_VARIANT",      "kind": "xor", "variants": ["fixed", "cep"]},
    "notification":   {"env": "NOTIFICATION_CHANNELS", "kind": "or",  "variants": ["email", "sms"]},
}


def cardinality(feature: str) -> str:
    vp = VARIATION_POINTS[feature]
    return "[1,1]" if vp["kind"] == "xor" else f"[1,{len(vp['variants'])}]"


def variants_of(spec: dict) -> list:
    """Normaliza 'variant' (texto ou lista) para lista; [] se ausente ou em formato inválido."""
    v = spec.get("variant")
    if isinstance(v, str):
        return [v]
    return list(v) if isinstance(v, list) else []


def _check_variants(feature: str, spec: dict) -> list:
    vp = VARIATION_POINTS[feature]
    allowed, xor = vp["variants"], vp["kind"] == "xor"
    rule = "exatamente 1 variante" if xor else "de 1 a %d variantes" % len(allowed)
    where = f"'{feature}' {cardinality(feature)}: escolha {rule} entre {allowed}"
    chosen = variants_of(spec)
    if not chosen:
        return [f"{where} (nenhuma variante informada)."]
    errors = []
    bad = [v for v in chosen if not isinstance(v, str) or v not in allowed]
    if bad:
        errors.append(f"{where}; valor(es) inválido(s): {bad}.")
    if len(set(map(str, chosen))) != len(chosen):
        errors.append(f"{where}; há variantes repetidas: {chosen}.")
    if xor and len(chosen) != 1:
        errors.append(f"{where}; foram informadas {len(chosen)}: {chosen}.")
    return errors


def validate(cfg) -> list:
    """Devolve a lista de erros (vazia = configuração válida)."""
    if not isinstance(cfg, dict) or not isinstance(cfg.get("features"), dict):
        return ["O arquivo precisa ter o objeto 'features'."]
    feats, errors, enabled = cfg["features"], [], {}
    for name in feats:
        if name not in FEATURES:
            errors.append(f"Feature desconhecida: '{name}'. Válidas: {FEATURES}.")
    for f in FEATURES:
        spec = feats.get(f, {})
        if not isinstance(spec, dict):
            errors.append(f"A configuração de '{f}' deve ser um objeto.")
            spec = {}
        on = spec.get("enabled", f in MANDATORY)
        if not isinstance(on, bool):
            errors.append(f"'{f}.enabled' deve ser true ou false.")
            on = f in MANDATORY
        if f in MANDATORY and not on:
            errors.append(f"A feature obrigatória '{f}' não pode ser desabilitada.")
        enabled[f] = on
    for f in FEATURES:
        if not enabled[f]:
            continue
        spec = feats.get(f) if isinstance(feats.get(f), dict) else {}
        for dep in REQUIRES.get(f, []):
            if not enabled[dep]:
                errors.append(f"'{f}' requer '{dep}', que está desabilitada.")
        if f in VARIATION_POINTS:
            errors += _check_variants(f, spec)
        elif "variant" in spec:
            errors.append(f"'{f}' não tem pontos de variação; remova 'variant'.")
    return errors
