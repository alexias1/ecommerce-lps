# LPS de E-commerce com Microsserviços e Componentes

Linha de Produto de Software (LPS) para sistemas de e-commerce. Cada **feature** é um microsserviço;
o arquivo `features.json` (seletor de features) define quais serviços e variantes entram no produto.

## Estrutura
```
common/lps.py          utilitários compartilhados (portas, enabled(), call(), db())
gateway/               API Gateway (porta 8000) + gateway/static/index.html (interface web)
services/<nome>/       microsserviços FastAPI (um SQLite por serviço), em camadas:
                         main.py (Controller) · service.py (Service + componentes) ·
                         repository.py (Repository) · dto.py (DTO)
features.json          seleção de features/variantes do produto
generate_product.py    gera generated/docker-compose.yml a partir do features.json
run_local.py           sobe o produto sem Docker e imprime a tabela de portas
```

## Features, variantes e portas
| Serviço | Porta | Tipo | Variantes (variável de ambiente) |
|---|---|---|---|
| gateway | 8000 | obrigatório | – |
| auth | 8001 | obrigatório | `email`, `social` (AUTH_VARIANT) |
| catalog | 8002 | obrigatório | `simple`, `search` (CATALOG_VARIANT) |
| cart | 8003 | obrigatório | – |
| order | 8004 | obrigatório | – |
| payment | 8005 | obrigatório | `pix`, `card`, `boleto` (PAYMENT_METHODS) |
| recommendation | 8006 | opcional | `history`, `popularity` (REC_STRATEGY) |
| shipping | 8007 | opcional | `fixed`, `cep` (SHIPPING_VARIANT) |
| notification | 8008 | opcional | `email`, `sms` (NOTIFICATION_CHANNELS) |

## Arquitetura interna e componentes
Cada microsserviço segue as camadas **Controller → Service → Repository (→ banco SQLite)**, com **DTOs** nas bordas.
Na camada Service, cada ponto de variação é um **componente**: uma interface abstrata (ABC) com uma
implementação por variante. A variante é escolhida em tempo de montagem do produto (`features.json`),
e `common/lps.py: build()` instancia só as implementações selecionadas.

| Ponto de variação | Interface (componente) | Variantes (implementações) | Cardinalidade |
|---|---|---|---|
| Autenticação | `AuthProvider` | `EmailPasswordProvider`, `SocialProvider` | [1,2] (OR) |
| Catálogo | `CatalogInterface` | `SimpleCatalog`, `SearchCatalog` | [1,1] (XOR) |
| Pagamento | `PaymentMethod` | `PixPayment`, `CardPayment`, `BoletoPayment` | [1,3] (OR) |
| Recomendação | `RecommendationStrategy` | `HistoryStrategy`, `PopularityStrategy` | [1,1] (XOR) |
| Frete | `ShippingStrategy` | `FixedShipping`, `CepShipping` | [1,1] (XOR) |
| Notificações | `NotificationChannel` | `EmailChannel`, `SmsChannel` | [1,2] (OR) |
| Carrinho | `CartInterface` | `Cart` | sem variação |
| Pedidos | `OrderInterface` | `OrderService` | sem variação |

Features opcionais (recomendação, frete, notificações) são microsserviços inteiros que podem ficar fora do produto.
Os serviços obrigatórios os chamam via `common.lps.call()`, que devolve `None` quando a feature está desligada.
O `shipping-service` não tem Repository porque não guarda estado.

## Como executar
Sem Docker:
```bash
pip install -r requirements.txt
python run_local.py            # lê features.json, sobe os serviços e mostra as portas
```
Com Docker:
```bash
python generate_product.py     # gera generated/docker-compose.yml
docker compose -f generated/docker-compose.yml up --build
```
**Interface web (loja + seletor de features): http://localhost:8000/ui/**

Documentação interativa (Swagger): http://localhost:8000/docs e `http://localhost:<porta>/docs` de cada serviço.

## Testar
Com o produto rodando, em outro terminal:
```bash
python smoke_test.py          # fluxo principal pelo gateway, com o tempo de cada etapa
```
Os testes se adaptam às features ativas (lidas de `/health`). Termina com código 1 se algo falhar.

Nota (Windows): use `127.0.0.1` em vez de `localhost`. O `localhost` tenta IPv6 primeiro e cada chamada entre serviços
pode demorar alguns segundos; o projeto já usa `127.0.0.1` internamente.

## Construir um novo produto
1. Edite `features.json`: `enabled` liga/desliga features opcionais e `variant` escolhe as variantes.
2. Rode `python run_local.py` (ou `generate_product.py` + docker compose).
3. Só os serviços escolhidos sobem; o gateway responde 404 para features desabilitadas.

## Rotas pelo gateway (prefixo + rota do serviço)
```bash
G=http://localhost:8000
curl -X POST $G/auth/register -H 'content-type: application/json' -d '{"email":"a@a.com","password":"123"}'
curl "$G/catalog/products?category=livros"
curl $G/catalog/products/5 -H 'x-user-id: 1'                      # registra visualização
curl -X POST $G/cart/cart/1/items -H 'content-type: application/json' -d '{"product_id":1,"qty":2}'
curl -X POST $G/orders/orders -H 'content-type: application/json' -d '{"user_id":1,"payment_method":"pix","cep":"57000000"}'
curl $G/recommendations/recommend/1                               # recomendação por histórico
curl $G/health                                                    # status e portas dos serviços
```

## Interface web
- **Loja:** login, catálogo, carrinho, pedido e recomendações. A faixa no topo mostra cada microsserviço com sua porta; os serviços acionados por cada ação acendem e aparecem em "Serviços acionados".
- **Montar produto:** seletor de features/variantes que gera o `features.json` do novo produto.

## Próximos passos
Diagramas, testes e relatório.
