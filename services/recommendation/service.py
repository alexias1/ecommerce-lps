"""Componente de recomendação.

RecommendationStrategy é o contrato. Variantes do ponto de variação "Recomendação":
HistoryStrategy (perfil/histórico do usuário) e PopularityStrategy.
"""
from abc import ABC, abstractmethod
from collections import Counter
from common.lps import build, call, variants


class RecommendationStrategy(ABC):
    name = ""

    def __init__(self, repo):
        self.repo = repo

    @abstractmethod
    def recommend(self, user_id, products, limit):
        ...


class HistoryStrategy(RecommendationStrategy):
    """Pontua categorias pelo histórico (compra=3, visualização=1); exclui itens já comprados."""
    name = "history"

    def recommend(self, user_id, products, limit):
        history = self.repo.by_user(user_id)
        if not history:
            return []
        weight = Counter()
        for h in history:
            weight[h["category"]] += 3 if h["type"] == "purchase" else 1
        bought = {h["product_id"] for h in history if h["type"] == "purchase"}
        ranked = sorted((p for p in products if p["id"] not in bought and weight[p["category"]] > 0),
                        key=lambda p: -weight[p["category"]])
        return ranked[:limit]


class PopularityStrategy(RecommendationStrategy):
    name = "popularity"

    def recommend(self, user_id, products, limit):
        pop = self.repo.popularity()
        return sorted(products, key=lambda p: (-pop[p["id"]], p["id"]))[:limit]


STRATEGIES = {"history": HistoryStrategy, "popularity": PopularityStrategy}


class RecommendationService:
    def __init__(self, repo):
        self.repo = repo
        self.strategy_name = variants("REC_STRATEGY", "history")[0]
        self.strategy = build(STRATEGIES, [self.strategy_name], repo)[self.strategy_name]
        self.fallback = PopularityStrategy(repo)

    def add_event(self, e):
        self.repo.add(e)
        return {"stored": True}

    def recommend(self, user_id, limit=5):
        products = call("GET", "catalog", "/products") or []
        items, used = self.strategy.recommend(user_id, products, limit), self.strategy.name
        if not items:  # sem histórico: cai para popularidade
            items, used = self.fallback.recommend(user_id, products, limit), "popularity"
        return {"user_id": user_id, "strategy": used, "items": items}
