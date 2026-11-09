# Resultados de testes e demonstração — LPS de E-commerce

## Suíte automatizada
- Comando: `python -m unittest discover -s tests -t . -v`
- Resultado: 19 testes aprovados, sem falhas nem itens ignorados.
- Cobertura: validação OR/XOR, consistência entre componentes e diagramas, geração do Compose e canais de notificação.

## Loja Básica — execução local
- Configuração: `configs/loja-basica.json`
- Serviços: gateway e auth, catalog, cart, order e payment.
- Smoke test: 10 aprovados, 0 falhas, 1 ignorado. O filtro não se aplica ao catálogo `simple`.
- Health: `loja-basica-health.json`.

## Loja Completa — execução local
- Configuração: `configs/loja-completa.json`
- Serviços: gateway e os oito microsserviços.
- Smoke test: 11 aprovados, 0 falhas, 0 ignorados.
- Health: `loja-completa-health.json`.

## Loja Completa — Docker Compose
- Imagens construídas e nove contêineres iniciados; todos passaram os healthchecks.
- `/health`: os oito microsserviços responderam `up` nas portas 8001–8008; gateway na 8000.
- Smoke test: 11 aprovados, 0 falhas, 0 ignorados.
- A recomendação por histórico e o fallback por popularidade passaram.
- Evidências: `docker-compose-ps.log`, `loja-completa-docker-health.json` e `loja-completa-docker-smoke.log`.
- O stack permanece rodando em `http://127.0.0.1:8000/ui/` para demonstração.

## Encerrar os contêineres
Na raiz do projeto:

```powershell
docker compose -f evidence\compose-loja-completa\docker-compose.yml down
```
