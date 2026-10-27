"""API Gateway: ponto único de entrada. Encaminha /<prefixo>/... para o microserviço certo."""
import os
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from common.lps import PORTS, enabled, url

app = FastAPI(title="API Gateway - LPS E-commerce")

# Interface web (loja + seletor de features) em http://localhost:8000/ui/
# Montada antes da rota proxy para ter prioridade.
app.mount("/ui", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), name="ui")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/")

# prefixo público -> nome do serviço
ROUTES = {
    "auth": "auth", "catalog": "catalog", "cart": "cart", "orders": "order",
    "payments": "payment", "recommendations": "recommendation",
    "shipping": "shipping", "notifications": "notification",
}


@app.get("/health", tags=["gateway"])
def health():
    """Lista os serviços ativos neste produto e se estão respondendo."""
    status = {}
    for svc in PORTS:
        if not enabled(svc):
            continue
        try:
            r = httpx.get(url(svc) + "/health", timeout=2)
            r.raise_for_status()
            status[svc] = {"port": PORTS[svc], "status": "up", "info": r.json()}
        except httpx.HTTPError:
            status[svc] = {"port": PORTS[svc], "status": "down"}
    return {"gateway_port": 8000, "services": status}


@app.get("/features", tags=["gateway"])
def features():
    """Features ativas no produto (usado pela interface do front-end)."""
    return {"enabled_services": [s for s in PORTS if enabled(s)]}


@app.api_route("/{prefix}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], tags=["proxy"])
async def proxy(prefix: str, path: str, request: Request):
    svc = ROUTES.get(prefix)
    if svc is None:
        raise HTTPException(404, f"Rota '{prefix}' desconhecida")
    if not enabled(svc):
        raise HTTPException(404, f"Feature '{svc}' não está habilitada neste produto")
    target = f"{url(svc)}/{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.request(
                request.method, target, params=request.query_params,
                content=await request.body(),
                headers={k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")},
            )
        except httpx.HTTPError:
            raise HTTPException(503, f"Serviço '{svc}' indisponível")
    return Response(r.content, r.status_code, media_type=r.headers.get("content-type"))
