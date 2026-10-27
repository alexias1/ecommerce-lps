#!/usr/bin/env python3
"""Teste de fumaça do produto em execução. Uso: python smoke_test.py [http://127.0.0.1:8000]

Percorre o fluxo principal pelo gateway, confere os resultados e mostra o tempo de cada etapa.
Os testes se adaptam às features ativas (lê /health). Código de saída 1 se algum teste falhar.
"""
import sys
import time
import uuid
import httpx

G = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
c = httpx.Client(base_url=G, timeout=60)
S, R = {}, {"ok": 0, "fail": 0, "skip": 0}


def step(name, fn):
    t = time.perf_counter()
    try:
        out = fn()
        status = "SKIP" if out == "skip" else "PASS"
    except Exception as e:  # noqa
        status, msg = "FAIL", f"  <- {type(e).__name__}: {e}"
    ms = int((time.perf_counter() - t) * 1000)
    R[{"PASS": "ok", "FAIL": "fail", "SKIP": "skip"}[status]] += 1
    print(f"[{status}] {name:<52}{ms:>6} ms" + (msg if status == "FAIL" else ""))


def info(svc):
    return S["services"].get(svc, {}).get("info", {})


def on(svc):
    return svc in S["services"]


def t_health():
    d = c.get("/health").json()
    S["services"] = d["services"]
    down = [k for k, v in d["services"].items() if v["status"] != "up"]
    assert not down, f"serviços fora do ar: {down}"


def t_auth():
    S["email"] = f"t{uuid.uuid4().hex[:6]}@teste.com"
    if "email" in info("auth").get("variants", []):
        r = c.post("/auth/register", json={"email": S["email"], "password": "123"}); assert r.status_code == 200, r.text
        r = c.post("/auth/login", json={"email": S["email"], "password": "123"}); assert r.status_code == 200, r.text
        assert c.post("/auth/login", json={"email": S["email"], "password": "errada"}).status_code == 401
    else:
        r = c.post("/auth/login/social", json={"provider": "google", "email": S["email"]}); assert r.status_code == 200, r.text
    S["uid"] = r.json()["user_id"]


def t_catalog():
    items = c.get("/catalog/products").json()
    assert len(items) > 0
    S["products"] = items


def t_filter():
    if info("catalog").get("variant") != "search":
        return "skip"
    items = c.get("/catalog/products", params={"category": "livros"}).json()
    assert items and all(i["category"] == "livros" for i in items)


def t_view():
    r = c.get(f"/catalog/products/{S['products'][0]['id']}", headers={"x-user-id": str(S["uid"])})
    assert r.status_code == 200
    assert c.get("/catalog/products/9999").status_code == 404


def t_cart():
    a, b = S["products"][0], S["products"][1]
    c.post(f"/cart/cart/{S['uid']}/items", json={"product_id": a["id"], "qty": 2})
    cart = c.post(f"/cart/cart/{S['uid']}/items", json={"product_id": b["id"], "qty": 1}).json()
    esperado = round(a["price"] * 2 + b["price"], 2)
    assert cart["total"] == esperado, f"total {cart['total']} != {esperado}"
    S["subtotal"] = esperado


def t_checkout():
    method = info("payment")["methods"][0]
    r = c.post("/orders/orders", json={"user_id": S["uid"], "payment_method": method, "cep": "57000000"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["subtotal"] == S["subtotal"]
    assert d["total"] == round(d["subtotal"] + d["shipping"], 2)
    if on("shipping"):
        assert d["shipping"] > 0
    assert d["payment"]["status"] == ("pending" if method == "boleto" else "approved")
    S["order_id"] = d["order_id"]
    assert c.get(f"/cart/cart/{S['uid']}").json()["items"] == [], "carrinho não foi esvaziado"


def t_orders():
    ids = [o["id"] for o in c.get(f"/orders/orders/{S['uid']}").json()]
    assert S["order_id"] in ids


def t_recommend():
    if not on("recommendation"):
        assert c.get(f"/recommendations/recommend/{S['uid']}").status_code == 404
        return
    d = c.get(f"/recommendations/recommend/{S['uid']}").json()
    assert d["items"], "sem recomendações"
    bought = {S["products"][0]["id"], S["products"][1]["id"]}
    if info("recommendation").get("strategy") == "history":
        assert d["strategy"] == "history"
        assert not bought & {i["id"] for i in d["items"]}, "recomendou item já comprado"
    new = c.get("/recommendations/recommend/999999").json()
    assert new["strategy"] == "popularity", "usuário sem histórico deveria cair em popularidade"


def t_bad_payment():
    c.post(f"/cart/cart/{S['uid']}/items", json={"product_id": S["products"][2]["id"], "qty": 1})
    r = c.post("/orders/orders", json={"user_id": S["uid"], "payment_method": "cripto"})
    assert r.status_code >= 400, "método inexistente deveria ser recusado"
    c.delete(f"/cart/cart/{S['uid']}")
    r = c.post("/orders/orders", json={"user_id": S["uid"], "payment_method": "pix"})
    assert r.status_code == 400, "carrinho vazio deveria dar erro 400"


print(f"Testando {G}\n")
for name, fn in [
    ("Todos os serviços respondem (/health)", t_health),
    ("Autenticação (cadastro, login, senha errada)", t_auth),
    ("Catálogo lista produtos", t_catalog),
    ("Catálogo filtra por categoria (variante search)", t_filter),
    ("Ver detalhes / produto inexistente = 404", t_view),
    ("Carrinho soma corretamente", t_cart),
    ("Checkout: frete + pagamento + carrinho esvaziado", t_checkout),
    ("Pedido aparece em 'Meus pedidos'", t_orders),
    ("Recomendação (histórico e fallback)", t_recommend),
    ("Erros: método inválido e carrinho vazio", t_bad_payment),
]:
    if name.startswith("Todos") or "uid" in S or name.startswith("Autent"):
        step(name, fn)
    else:
        print(f"[SKIP] {name}")
print(f"\n{R['ok']} passaram, {R['fail']} falharam, {R['skip']} ignorados")
sys.exit(1 if R["fail"] else 0)
