"""Recommendation Service (porta 8006) — camada Controller."""
from fastapi import FastAPI
from common.lps import install_error_handlers
from services.recommendation.dto import Event
from services.recommendation.repository import EventRepository
from services.recommendation.service import RecommendationService

app = FastAPI(title="Recommendation Service")
install_error_handlers(app)
service = RecommendationService(EventRepository())


@app.get("/health")
def health():
    return {"service": "recommendation", "strategy": service.strategy_name}


@app.post("/events")
def add_event(e: Event):
    return service.add_event(e)


@app.get("/recommend/{user_id}")
def recommend(user_id: int, limit: int = 5):
    return service.recommend(user_id, limit)
