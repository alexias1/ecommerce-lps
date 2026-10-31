#!/usr/bin/env python3
"""Gera os diagramas da LPS de e-commerce (Graphviz). Uso: python gerar_diagramas.py
Requer o programa `dot` (https://graphviz.org). Saídas: ./saida/*.png, *.svg e fontes *.dot."""
import os
import subprocess

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
os.makedirs(OUT, exist_ok=True)

FONT = "DejaVu Sans"
HEAD = f'''graph [fontname="{FONT}", fontsize=13, pad=0.3, bgcolor=white];
node [fontname="{FONT}", fontsize=11];
edge [fontname="{FONT}", fontsize=9];
'''
INK, MAND, OPT, VAR, SVC = "#14213d", "#dcecee", "#ffffff", "#f3efe0", "#e6ecf7"


def render(name, dot, dpi=170):
    path = os.path.join(OUT, name + ".dot")
    open(path, "w", encoding="utf-8").write(dot)
    for fmt, extra in (("png", [f"-Gdpi={dpi}"]), ("svg", [])):
        subprocess.run(["dot", f"-T{fmt}", *extra, path, "-o", os.path.join(OUT, f"{name}.{fmt}")], check=True)
    print("ok", name)


def vtag(letter, text, fill="#ffffff"):
    return (f'<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4" BGCOLOR="{fill}">'
            f'<TR><TD BGCOLOR="black"><FONT COLOR="white"><B>{letter}</B></FONT></TD><TD>{text}</TD></TR></TABLE>>')


# ---------------------------------------------------------------- 1. FEATURES
FEATURES = [  # (id, nome, obrigatória, tipo do grupo (or/xor/None), variantes)
    ("auth", "Autenticação", True, "or", ["Email e senha", "Login social"]),
    ("catalog", "Catálogo de\nprodutos", True, "xor", ["Lista simples", "Busca e filtros"]),
    ("cart", "Carrinho", True, None, []),
    ("order", "Pedidos", True, None, []),
    ("payment", "Pagamento", True, "or", ["Pix", "Cartão", "Boleto"]),
    ("rec", "Recomendação", False, "xor", ["Por histórico\ndo usuário", "Por\npopularidade"]),
    ("ship", "Frete", False, "xor", ["Frete fixo", "Frete por CEP"]),
    ("notif", "Notificações", False, "or", ["Email", "SMS"]),
]


def features():
    d = f'graph features {{\nrankdir=TB; ranksep=0.55; nodesep=0.25; splines=line;\n{HEAD}'
    d += f'root [label="Loja E-commerce\\n(Linha de Produto)", shape=box, style="filled", fillcolor="{INK}", fontcolor=white, fontsize=14];\n'
    for fid, name, must, grp, vs in FEATURES:
        d += f'{fid} [label="{name}", shape=box, style="rounded,filled", fillcolor="{MAND if must else OPT}"];\n'
        d += f'root -- {fid} [arrowhead={"dot" if must else "odot"}, dir=forward, arrowsize=0.9];\n'
        if grp:
            fill = "black" if grp == "or" else "white"
            d += f'g_{fid} [label="", shape=triangle, style=filled, fillcolor={fill}, width=0.32, height=0.28, fixedsize=true];\n'
            d += f'{fid} -- g_{fid};\n'
            for i, v in enumerate(vs):
                d += f'v_{fid}{i} [label="{v}", shape=box, style=filled, fillcolor=white];\ng_{fid} -- v_{fid}{i};\n'
    # restrições entre features (requer)
    for a, b in (("order", "cart"), ("order", "payment"), ("cart", "catalog")):
        d += f'{a} -- {b} [style=dashed, color="#c8553d", dir=forward, arrowhead=vee, constraint=false, label=" requer", fontcolor="#c8553d"];\n'
    d += '''legend [shape=plain, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="2" CELLPADDING="3" BGCOLOR="#fafafa">
<TR><TD ALIGN="LEFT"><B>Legenda</B></TD></TR>
<TR><TD ALIGN="LEFT">● feature obrigatória</TD></TR>
<TR><TD ALIGN="LEFT">○ feature opcional</TD></TR>
<TR><TD ALIGN="LEFT">▲ (preenchido) grupo OR: uma ou mais variantes</TD></TR>
<TR><TD ALIGN="LEFT">△ (vazio) grupo XOR: exatamente uma variante</TD></TR>
<TR><TD ALIGN="LEFT"><FONT COLOR="#c8553d">⇢ requer (dependência entre features)</FONT></TD></TR></TABLE>>];
{rank=sink; legend}
v_cart0 [style=invis,label="",width=0,height=0]; 
}
'''
    return d.replace('v_cart0 [style=invis,label="",width=0,height=0]; \n', '')


# ---------------------------------------------------------------- 2. VARIABILIDADE
VPS = [  # id, nome, cardinalidade, variantes
    ("auth", "Autenticação", "[1,2]", ["Email e senha", "Login social"]),
    ("catalog", "Catálogo", "[1,1]", ["Lista simples", "Busca e filtros"]),
    ("payment", "Pagamento", "[1,3]", ["Pix", "Cartão", "Boleto"]),
    ("rec", "Recomendação", "[1,1]", ["Por histórico", "Por popularidade"]),
    ("ship", "Frete", "[1,1]", ["Frete fixo", "Frete por CEP"]),
    ("notif", "Notificações", "[1,2]", ["Email", "SMS"]),
]


def vp_node(vid, nome, card, extra=""):
    return (f'vp_{vid} [shape=triangle, style=filled, fillcolor=white, width=1.5, height=1.3, margin=0, '
            f'label=<<FONT POINT-SIZE="10"><B>{nome}</B></FONT><BR/><FONT POINT-SIZE="9">{card}</FONT>> {extra}];\n')


def variabilidade():
    d = f'graph variab {{\nrankdir=TB; ranksep=0.5; nodesep=0.35; newrank=true;\n{HEAD}'
    for vid, nome, card, vs in VPS:
        d += vp_node(vid, nome, card)
        for i, v in enumerate(vs):
            d += f'v_{vid}{i} [shape=plain, label={vtag("V", v)}];\n'
            d += f'vp_{vid} -- v_{vid}{i} [style=dashed];\n'
    for row in (("auth", "catalog", "payment"), ("rec", "ship", "notif")):
        d += "{rank=same; " + "; ".join(f"vp_{x}" for x in row) + "}\n"
    # força a grade 3x2 com arestas invisíveis
    for a, b in (("auth", "rec"), ("catalog", "ship"), ("payment", "notif")):
        d += f'v_{a}0 -- vp_{b} [style=invis];\n'
    d += '''legend [shape=plain, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="2" CELLPADDING="3" BGCOLOR="#fafafa">
<TR><TD ALIGN="LEFT"><B>Legenda</B></TD></TR>
<TR><TD ALIGN="LEFT">△ VP: ponto de variação, com a cardinalidade das variantes</TD></TR>
<TR><TD ALIGN="LEFT">[1,1]: escolhe-se exatamente 1 variante (XOR)</TD></TR>
<TR><TD ALIGN="LEFT">[1,n]: escolhe-se de 1 a n variantes (OR)</TD></TR>
<TR><TD ALIGN="LEFT"><B>V</B>: variante</TD></TR></TABLE>>];
v_notif0 -- legend [style=invis];
}
'''
    return d


# ---------------------------------------------------------------- 3. CAMADAS
SERVICES = [  # id, nome, porta, db, vp (nome, card) ou None, opcional
    ("auth", "auth-service", 8001, "auth.db", ("Autenticação", "[1,2]"), False),
    ("catalog", "catalog-service", 8002, "catalog.db", ("Catálogo", "[1,1]"), False),
    ("cart", "cart-service", 8003, "cart.db", None, False),
    ("order", "order-service", 8004, "order.db", None, False),
    ("payment", "payment-service", 8005, "payment.db", ("Pagamento", "[1,3]"), False),
    ("rec", "recommendation-service", 8006, "recommendation.db", ("Recomendação", "[1,1]"), True),
    ("ship", "shipping-service", 8007, None, ("Frete", "[1,1]"), True),
    ("notif", "notification-service", 8008, "notification.db", ("Notificações", "[1,2]"), True),
]


def camadas():
    order = ["auth", "catalog", "payment", "rec", "ship", "notif", "cart", "order"]
    S = {x[0]: x for x in SERVICES}
    d = f'digraph camadas {{\nrankdir=TB; compound=true; ranksep=0.6; nodesep=0.3; newrank=true;\n{HEAD}'
    d += f'subgraph cluster_ui {{ label="Camada de Apresentação"; style="filled"; fillcolor="{VAR}"; color="#a89f7a";\n'
    d += 'ui1 [label="Loja\\n(login, catálogo, carrinho, pedidos, recomendações)", shape=box, style="filled", fillcolor=white];\n'
    d += 'ui2 [label="Montar produto\\n(seletor de features)", shape=box, style="filled", fillcolor=white];\n}\n'
    d += f'subgraph cluster_gw {{ label="Camada de Acesso"; style="filled"; fillcolor="#e9e4f3"; color="#8a7fb0";\n'
    d += 'gw [label="API Gateway  :8000\\nroteamento: /auth  /catalog  /cart  /orders  /payments  /recommendations  /shipping  /notifications\\n/health  /features  /ui", shape=box, style="filled", fillcolor=white];\n}\n'
    d += f'subgraph cluster_svc {{ label="Camada de Serviços: microsserviços (Controller → Service → Repository)"; style="filled"; fillcolor="{SVC}"; color="#6f86b8";\n'
    for sid in order:
        _, name, port, dbn, vp, opt = S[sid]
        style = "filled,dashed" if opt else "filled"
        extra = '<BR/><FONT POINT-SIZE="9">(feature opcional)</FONT>' if opt else ""
        d += (f'{sid} [shape=box, style="{style}", fillcolor=white, label=<<B>{name}</B><BR/>:{port}<BR/>'
              f'<FONT POINT-SIZE="9">Controller · Service<BR/>Repository</FONT>{extra}>];\n')
        if vp:
            d += vp_node(sid, *vp).replace("width=1.5, height=1.3", "width=1.3, height=1.05")
            d += f'vp_{sid} -> {sid} [style=dashed, arrowhead=vee];\ngw -> vp_{sid} [style=invis];\n'
        else:
            d += f'gw -> {sid} [style=invis, minlen=2];\n'
    d += "{rank=same; " + "; ".join(order) + "}\n"
    d += " -> ".join(order) + " [style=invis];\n" + "{rank=same; " + "; ".join(f"vp_{x}" for x in order[:6]) + "}\n" + " -> ".join(f"vp_{x}" for x in order[:6]) + " [style=invis];\n}\n"
    d += f'subgraph cluster_db {{ label="Camada de Persistência: um banco por serviço"; style="filled"; fillcolor="#e3f0e4"; color="#6aa06e";\n'
    for sid in order:
        dbn = S[sid][3]
        d += (f'db_{sid} [label="SQLite\\n{dbn}", shape=cylinder, style=filled, fillcolor=white];\n' if dbn
              else f'db_{sid} [label="sem estado\\n(sem banco)", shape=note, style=filled, fillcolor="#f4f4f4"];\n')
        d += f'{sid} -> db_{sid} [style={"solid" if dbn else "dotted"}, arrowhead={"normal" if dbn else "none"}];\n'
    d += "{rank=same; " + "; ".join(f"db_{x}" for x in order) + "}\n" + " -> ".join(f"db_{x}" for x in order) + " [style=invis];\n}\n"
    d += 'ui1 -> gw [label=" HTTP/JSON"]; ui2 -> gw [label=" HTTP/JSON"];\n'
    d += 'gw -> rec [lhead=cluster_svc, penwidth=1.6];\n'
    d += '''legend [shape=plain, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="2" CELLPADDING="3" BGCOLOR="#fafafa">
<TR><TD ALIGN="LEFT"><B>Legenda</B></TD></TR>
<TR><TD ALIGN="LEFT">△ ponto de variação (VP) com cardinalidade → serviço afetado</TD></TR>
<TR><TD ALIGN="LEFT">borda tracejada: serviço opcional (pode ficar fora do produto)</TD></TR></TABLE>>];
db_order -> legend [style=invis];
}
'''
    return d


# ---------------------------------------------------------------- 4. COMPONENTES
COMPS = [  # id, serviço, porta, Controller, Service, interface, [variantes], Repository, db, VP
    ("auth", "auth-service", 8001, "AuthController", "AuthService", "AuthProvider",
     ["EmailPasswordProvider", "SocialProvider"], "UserRepository", "auth.db", ("Autenticação", "[1,2]")),
    ("catalog", "catalog-service", 8002, "CatalogController", "CatalogService", "CatalogInterface",
     ["SimpleCatalog", "SearchCatalog"], "ProductRepository", "catalog.db", ("Catálogo", "[1,1]")),
    ("payment", "payment-service", 8005, "PaymentController", "PaymentService", "PaymentMethod",
     ["PixPayment", "CardPayment", "BoletoPayment"], "PaymentRepository", "payment.db", ("Pagamento", "[1,3]")),
    ("rec", "recommendation-service", 8006, "RecommendationController", "RecommendationService", "RecommendationStrategy",
     ["HistoryStrategy", "PopularityStrategy"], "EventRepository", "recommendation.db", ("Recomendação", "[1,1]")),
    ("ship", "shipping-service", 8007, "ShippingController", "ShippingService", "ShippingStrategy",
     ["FixedShipping", "CepShipping"], None, None, ("Frete", "[1,1]")),
    ("notif", "notification-service", 8008, "NotificationController", "NotificationService", "NotificationChannel",
     ["EmailChannel", "SmsChannel"], "NotificationRepository", "notification.db", ("Notificações", "[1,2]")),
    ("cart", "cart-service", 8003, "CartController", "Cart", "CartInterface", [], "CartRepository", "cart.db", None),
    ("order", "order-service", 8004, "OrderController", "OrderService", "OrderInterface", [], "OrderRepository", "order.db", None),
]


def comp(cid, text, fill=MAND):
    return f'{cid} [shape=component, style=filled, fillcolor="{fill}", label="«component»\\n{text}"];\n'


def componentes():
    d = f'digraph comps {{\nrankdir=LR; ranksep=0.45; nodesep=0.2; newrank=true; compound=true;\n{HEAD}'
    d += f'gw [shape=component, style=filled, fillcolor="#e9e4f3", label="«component»\\nAPI Gateway\\n:8000"];\n'
    for cid, svc, port, ctrl, srv, iface, vs, repo, dbn, vp in COMPS:
        d += f'subgraph cluster_{cid} {{ label="{svc}  :{port}"; style="filled"; fillcolor="{SVC}"; color="#6f86b8"; fontsize=12;\n'
        d += comp(f"{cid}_c", ctrl + "\\n(main.py)") + comp(f"{cid}_s", srv + "\\n(service.py)")
        d += f'{cid}_i [shape=box, style="filled", fillcolor="#fff7d6", label="«interface»\\n{iface}"];\n'
        if vs:
            for i, v in enumerate(vs):
                d += f'{cid}_v{i} [shape=plain, label={vtag("V", "«component»<BR/>" + v)}];\n'
        if repo:
            d += comp(f"{cid}_r", repo + "\\n(repository.py)", "#e3f0e4")
            d += f'{cid}_db [label="SQLite\\n{dbn}", shape=cylinder, style=filled, fillcolor=white];\n'
        if vp:
            d += vp_node(cid, *vp).replace("width=1.5, height=1.3", "width=1.2, height=1.0")
        d += '}\n'
        d += f'gw -> {cid}_c [color="#8a7fb0"];\n{cid}_c -> {cid}_s;\n'
        if vs:
            d += f'{cid}_s -> {cid}_i [style=dashed, arrowhead=vee, label=" usa"];\n'
        else:  # sem variação: o próprio componente de serviço implementa a interface
            d += f'{cid}_s -> {cid}_i [style=dashed, arrowhead=onormal, label=" implementa"];\n'
        for i in range(len(vs)):
            d += f'{cid}_i -> {cid}_v{i} [dir=back, arrowtail=onormal, style=dashed];\n'
            if vp:
                d += f'{cid}_v{i} -> vp_{cid} [dir=none, style=dashed];\n'
        if repo:
            d += f'{cid}_s -> {cid}_r;\n{cid}_r -> {cid}_db;\n'
    d += '''legend [shape=plain, label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="2" CELLPADDING="3" BGCOLOR="#fafafa">
<TR><TD ALIGN="LEFT"><B>Legenda</B></TD></TR>
<TR><TD ALIGN="LEFT">seta tracejada com ponta vazada: implementa a interface</TD></TR>
<TR><TD ALIGN="LEFT"><B>V</B>: variante (componente alternativo)</TD></TR>
<TR><TD ALIGN="LEFT">△ VP: ponto de variação com cardinalidade</TD></TR>
<TR><TD ALIGN="LEFT">cart e order: sem variação (uma só implementação)</TD></TR></TABLE>>];
gw -> legend [style=invis];
}
'''
    return d


# ---------------------------------------------------------------- 5. MICROSSERVIÇOS
def microsservicos():
    d = f'digraph ms {{\nrankdir=TB; ranksep=0.9; nodesep=0.45; newrank=true;\n{HEAD}'
    d += f'client [label="Navegador\\n(interface web /ui)", shape=box, style="rounded,filled", fillcolor="{VAR}"];\n'
    d += 'gw [label=<<B>API Gateway</B> :8000<BR/><FONT POINT-SIZE="9">roteia /auth /catalog /cart /orders /payments<BR/>/recommendations /shipping /notifications</FONT>>, shape=box, style="filled", fillcolor="#e9e4f3", penwidth=2];\n'
    d += 'client -> gw [label=" HTTP/JSON"];\n'
    top = ["auth", "catalog", "cart", "order", "payment"]
    bottom = ["rec", "ship", "notif"]
    S = {x[0]: x for x in SERVICES}
    for sid in top + bottom:
        _, name, port, dbn, vp, opt = S[sid]
        fill = "#fde9b8" if sid == "rec" else SVC
        extra = ""
        if sid == "rec":
            extra = '<BR/><FONT POINT-SIZE="9">perfil do usuário: histórico de<BR/>visualizações e compras</FONT>'
        elif opt:
            extra = '<BR/><FONT POINT-SIZE="9">(feature opcional)</FONT>'
        dbrow = (f'<TR><TD BGCOLOR="#e3f0e4"><FONT POINT-SIZE="9">SQLite · {dbn}</FONT></TD></TR>' if dbn
                 else '<TR><TD BGCOLOR="#eeeeee"><FONT POINT-SIZE="9">sem estado (sem banco)</FONT></TD></TR>')
        border = "3" if sid == "rec" else "1"
        style = ' STYLE="dashed"' if opt else ""
        d += (f'{sid} [shape=plain, label=<<TABLE BORDER="{border}"{style} CELLBORDER="0" CELLSPACING="0" CELLPADDING="6" BGCOLOR="{fill}">'
              f'<TR><TD><B>{name}</B><BR/>:{port}{extra}</TD></TR>{dbrow}</TABLE>>];\n')
        d += f'gw -> {sid} [color="#8a7fb0"{", constraint=false" if sid in bottom else ""}];\n'
    d += "{rank=same; " + "; ".join(top) + "}\n{rank=same; " + "; ".join(bottom) + "}\n"
    d += " -> ".join(top) + " [style=invis];\n" + " -> ".join(bottom) + " [style=invis];\n"
    calls = [  # nº, origem, destino, chamada, opcional, cor, estilo, constraint
        (1, "cart", "catalog", "GET /products/{id}", False, "#0f8b8d", "solid", "false"),
        (2, "order", "cart", "GET /cart/{user} e DELETE /cart/{user}", False, "#0f8b8d", "solid", "false"),
        (3, "order", "payment", "POST /payments", False, "#0f8b8d", "solid", "false"),
        (4, "order", "ship", "POST /quote", True, "#0f8b8d", "dashed", "true"),
        (5, "order", "rec", "POST /events (compra)", True, "#c8553d", "dashed", "true"),
        (6, "catalog", "rec", "POST /events (visualização)", True, "#c8553d", "dashed", "true"),
        (7, "rec", "catalog", "GET /products (candidatos à recomendação)", True, "#c8553d", "dashed", "false"),
        (8, "order", "notif", "POST /notify (assíncrono; canais habilitados)", True, "#8a7fb0", "dotted", "true"),
    ]
    names = {x[0]: x[1] for x in SERVICES}
    for n, a, b, _txt, _opt, color, style, cons in calls:
        d += (f'{a} -> {b} [label=<<B>{n}</B>>, fontsize=12, constraint={cons}, color="{color}", '
              f'fontcolor="{color}", style="{style}", penwidth=1.4];\n')
    rows = "".join(
        f'<TR><TD ALIGN="CENTER"><B>{n}</B></TD><TD ALIGN="LEFT">{names[a]} → {names[b]}</TD>'
        f'<TD ALIGN="LEFT">{txt}</TD><TD>{"opcional" if opt else "obrigatória"}</TD></TR>'
        for n, a, b, txt, opt, _c, _s, _k in calls)
    d += ('legend [shape=plain, label=<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4" BGCOLOR="#fafafa">'
          '<TR><TD COLSPAN="4" ALIGN="LEFT"><B>Chamadas entre microsserviços (HTTP/JSON)</B></TD></TR>'
          f'{rows}'
          '<TR><TD COLSPAN="4" ALIGN="LEFT"><FONT POINT-SIZE="9">Borda tracejada = serviço opcional. Cada microsserviço tem o seu próprio banco (database per service). '
          'Vermelho: perfil/histórico do usuário (recomendação).</FONT></TD></TR></TABLE>>];\n'
          'ship -> legend [style=invis];\n}\n')
    return d


if __name__ == "__main__":
    render("01_diagrama_de_features", features())
    render("02_diagrama_de_variabilidade", variabilidade())
    render("03_arquitetura_em_camadas", camadas())
    render("04_diagrama_de_componentes", componentes())
    render("05_arquitetura_de_microsservicos", microsservicos())
