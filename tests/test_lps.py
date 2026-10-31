"""Testes das correções técnicas. Rodar na raiz do projeto:
    python -m unittest discover -s tests -t . -v
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from common.lps import ServiceError
from common.model import FEATURES, MANDATORY, VARIATION_POINTS, cardinality, validate
import generate_product as gp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cfg(**over):
    """Configuração completa válida; over = {feature: dict} substitui a feature."""
    base = {
        "auth": {"enabled": True, "variant": ["email", "social"]},
        "catalog": {"enabled": True, "variant": "search"},
        "cart": {"enabled": True}, "order": {"enabled": True},
        "payment": {"enabled": True, "variant": ["pix", "card", "boleto"]},
        "recommendation": {"enabled": True, "variant": "history"},
        "shipping": {"enabled": True, "variant": "cep"},
        "notification": {"enabled": True, "variant": ["email", "sms"]},
    }
    base.update(over)
    return {"product_name": "Teste", "features": base}


class ValidacaoOrXor(unittest.TestCase):
    def test_config_completa_e_minima_sao_validas(self):
        self.assertEqual(validate(cfg()), [])
        minima = cfg(recommendation={"enabled": False}, shipping={"enabled": False},
                     notification={"enabled": False}, auth={"variant": ["email"]},
                     payment={"variant": "pix"}, catalog={"variant": ["simple"]})
        self.assertEqual(validate(minima), [])

    def test_features_json_do_repositorio_e_valido(self):
        with open(os.path.join(ROOT, "features.json"), encoding="utf-8") as f:
            self.assertEqual(validate(json.load(f)), [])

    def test_xor_exige_exatamente_uma_variante(self):
        for cat in (["simple", "search"], [], "inexistente", None):
            with self.subTest(catalogo=cat):
                self.assertTrue(validate(cfg(catalog={"enabled": True, "variant": cat})))
        for key in ("recommendation", "shipping"):
            with self.subTest(feature=key):
                v = VARIATION_POINTS[key]["variants"]
                self.assertTrue(validate(cfg(**{key: {"enabled": True, "variant": v}})))

    def test_or_exige_de_uma_a_n_e_sem_repeticao(self):
        for key in ("auth", "payment", "notification"):
            with self.subTest(feature=key):
                self.assertTrue(validate(cfg(**{key: {"enabled": True, "variant": []}})), "vazio deve falhar")
                self.assertTrue(validate(cfg(**{key: {"enabled": True, "variant": ["x"]}})), "inexistente deve falhar")
                v = VARIATION_POINTS[key]["variants"][0]
                self.assertTrue(validate(cfg(**{key: {"enabled": True, "variant": [v, v]}})), "repetida deve falhar")

    def test_variante_ignorada_quando_feature_opcional_desligada(self):
        self.assertEqual(validate(cfg(notification={"enabled": False, "variant": []})), [])

    def test_obrigatorias_nao_podem_ser_desligadas(self):
        for f in MANDATORY:
            with self.subTest(feature=f):
                c = cfg(); c["features"][f]["enabled"] = False
                self.assertTrue(any("obrigatória" in e for e in validate(c)))

    def test_feature_desconhecida_e_variante_em_feature_sem_variacao(self):
        self.assertTrue(any("desconhecida" in e for e in validate(cfg(cupons={"enabled": True}))))
        self.assertTrue(any("não tem pontos de variação" in e for e in validate(cfg(cart={"enabled": True, "variant": "x"}))))

    def test_estrutura_invalida(self):
        for bad in (None, [], {}, {"features": []}):
            self.assertTrue(validate(bad))

    def test_resolve_aborta_com_todos_os_erros(self):
        c = cfg(catalog={"enabled": True, "variant": ["simple", "search"]}, payment={"enabled": True, "variant": []})
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(c, f)
        try:
            with self.assertRaises(SystemExit) as ctx:
                gp.resolve(f.name)
            msg = str(ctx.exception)
            self.assertIn("'catalog'", msg); self.assertIn("'payment'", msg)
        finally:
            os.unlink(f.name)


class ModeloCodigoDiagramas(unittest.TestCase):
    def test_registros_de_componentes_batem_com_o_modelo(self):
        from services.auth.service import PROVIDERS
        from services.catalog.service import CATALOGS
        from services.payment.service import METHODS
        from services.recommendation.service import STRATEGIES as REC
        from services.shipping.service import STRATEGIES as SHIP
        from services.notification.service import CHANNELS
        reg = {"auth": PROVIDERS, "catalog": CATALOGS, "payment": METHODS,
               "recommendation": REC, "shipping": SHIP, "notification": CHANNELS}
        self.assertEqual(set(reg), set(VARIATION_POINTS))
        for f, registry in reg.items():
            with self.subTest(feature=f):
                self.assertEqual(set(registry), set(VARIATION_POINTS[f]["variants"]))

    def test_diagrama_de_variabilidade_bate_com_o_modelo(self):
        spec = importlib.util.spec_from_file_location("gd", os.path.join(ROOT, "docs", "diagramas", "gerar_diagramas.py"))
        gd = importlib.util.module_from_spec(spec); spec.loader.exec_module(gd)
        ids = {"auth": "auth", "catalog": "catalog", "payment": "payment",
               "rec": "recommendation", "ship": "shipping", "notif": "notification"}
        self.assertEqual({v[0] for v in gd.VPS}, set(ids))
        for vid, _nome, card, variantes in gd.VPS:
            with self.subTest(vp=vid):
                feat = ids[vid]
                self.assertEqual(card, cardinality(feat))
                self.assertEqual(len(variantes), len(VARIATION_POINTS[feat]["variants"]))

    def test_cardinalidades(self):
        esperado = {"auth": "[1,2]", "catalog": "[1,1]", "payment": "[1,3]",
                    "recommendation": "[1,1]", "shipping": "[1,1]", "notification": "[1,2]"}
        self.assertEqual({f: cardinality(f) for f in VARIATION_POINTS}, esperado)


class ComposeGerado(unittest.TestCase):
    def gerar(self, c):
        with tempfile.TemporaryDirectory(dir=ROOT) as out:
            f = os.path.join(out, "f.json")
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(c, fh)
            name, active, env = gp.resolve(f)
            text = gp.build_compose(name, active, env, out)
            return text, out, active

    def test_contexto_de_build_aponta_para_a_raiz_do_projeto(self):
        text, out, _ = self.gerar(cfg())
        ctx = [l.split(":", 1)[1].strip() for l in text.splitlines() if l.strip().startswith("context:")]
        self.assertTrue(ctx)
        for c in ctx:
            raiz = os.path.normpath(os.path.join(out, c))
            self.assertEqual(raiz, ROOT)
            self.assertTrue(os.path.isfile(os.path.join(raiz, "Dockerfile.service")))
            self.assertTrue(os.path.isdir(os.path.join(raiz, "services")))
        self.assertTrue(os.path.isfile(os.path.join(ROOT, ".dockerignore")))

    def test_yaml_valido_e_so_com_servicos_ativos(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML não instalado (pip install pyyaml)")
        minima = cfg(recommendation={"enabled": False}, shipping={"enabled": False},
                     notification={"enabled": False}, auth={"variant": ["email"]}, payment={"variant": ["pix"]})
        text, _, active = self.gerar(minima)
        doc = yaml.safe_load(text)
        self.assertEqual(set(doc["services"]), {"gateway"} | {f"{s}-service" for s in active})
        self.assertNotIn("recommendation-service", doc["services"])
        pay = doc["services"]["payment-service"]
        self.assertEqual(pay["environment"]["PAYMENT_METHODS"], "pix")
        self.assertEqual(pay["command"][-1], "8005")
        self.assertEqual(doc["services"]["gateway"]["environment"]["ENABLED_SERVICES"], ",".join(active))
        self.assertNotIn("RECOMMENDATION_URL", doc["services"]["gateway"]["environment"])
        for svc in doc["services"].values():
            self.assertEqual(svc["build"]["dockerfile"], "Dockerfile.service")

    def test_nome_do_projeto_sem_acentos(self):
        self.assertEqual(gp.slug("Loja Básica"), "loja-basica")
        self.assertEqual(gp.slug("Loja Completa #2"), "loja-completa-2")


class CanaisDeNotificacao(unittest.TestCase):
    class Repo:
        def __init__(self): self.rows = []
        def add(self, u, ch, msg): self.rows.append((u, ch, msg))
        def all(self): return self.rows

    def servico(self, canais):
        from services.notification.service import NotificationService
        with mock.patch.dict(os.environ, {"NOTIFICATION_CHANNELS": canais}):
            return NotificationService(self.Repo())

    def notificar(self, svc, canal=None):
        from services.notification.dto import Notice
        with contextlib.redirect_stdout(io.StringIO()):
            return svc.notify(Notice(user_id=1, message="oi", channel=canal))

    def test_sem_canal_usa_somente_os_habilitados(self):
        for habilitados in ("sms", "email", "email,sms"):
            with self.subTest(canais=habilitados):
                svc = self.servico(habilitados)
                r = self.notificar(svc)
                self.assertEqual(r["channels"], habilitados.split(","))
                self.assertEqual([row[1] for row in svc.repo.rows], habilitados.split(","))

    def test_canal_desabilitado_e_recusado(self):
        svc = self.servico("sms")
        with self.assertRaises(ServiceError) as ctx:
            self.notificar(svc, "email")
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(svc.repo.rows, [])

    def test_canal_explicito_habilitado_funciona(self):
        svc = self.servico("email,sms")
        self.assertEqual(self.notificar(svc, "sms")["channels"], ["sms"])

    def test_pedido_nao_fixa_canal(self):
        with open(os.path.join(ROOT, "services", "order", "service.py"), encoding="utf-8") as f:
            self.assertNotIn('"channel"', f.read())


if __name__ == "__main__":
    unittest.main()
