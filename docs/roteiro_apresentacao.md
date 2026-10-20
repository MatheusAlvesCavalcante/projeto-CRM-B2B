# Roteiro de Apresentação — Meta 5

## 1. Abertura (1-2 min)
Qual problema real do grupo isso resolve:
- Churn não identificado a tempo → clientes somem antes de qualquer ação de retenção.
- Mix de produtos abaixo do potencial → cliente compra sempre a mesma categoria, mesmo tendo perfil de comprar outras.
- Time comercial sem priorização de leads → esforço distribuído igual entre leads quentes e frios.

## 2. Demonstração ao vivo
1. Abrir o dashboard já com a Marca A selecionada.
2. Mostrar a aba de Churn: destacar os clientes no topo do ranking e explicar que o risco vem de `intervalo_medio_compra` — o cliente está comprando com um intervalo maior que o normal dele.
3. Trocar para Marca B no seletor **sem tocar em nenhum código** — mesmas abas, mesma lógica, dados diferentes. Esse é o momento chave da demo: prova que o sistema generaliza.
4. Mostrar a aba de Mix: pegar um cliente específico e explicar a lógica ("essa é a categoria mais vendida da marca que esse cliente ainda não comprou").
5. Mostrar a aba de Leads: destacar que o score é uma probabilidade contínua (0-100), não um sim/não — dá pra decidir o corte conforme a capacidade do time.

## 3. Como foi construído
Pipeline único → schema padrão → 3 modelos → dashboard.
- Mencionar que os dados são públicos (Kaggle), usados **de propósito** para provar a arquitetura antes de plugar dados reais.
- Ser transparente sobre o achado do modelo de leads: os 100% de acerto vêm da base ser sintética/determinística, não é uma promessa de desempenho com dados reais. Isso mostra rigor, não fraqueza.
- Mencionar a decisão de usar Regressão Logística para churn (não o modelo de "maior número", mas o de maior recall) — mostra que a escolha do modelo seguiu o objetivo de negócio, não só a métrica mais bonita.

## 4. Resposta pronta para "e com nossos dados reais, como fica?"
O pipeline foi desenhado para receber qualquer base nova escrevendo só uma função de padronização (`padronizar_marca_x()` em `src/pipeline.py`) — o resto do sistema (definição de churn, modelos, dashboard) não muda uma linha. Mostrar rapidamente o arquivo `src/pipeline.py` como prova.

Pontos a admitir com transparência:
- Dados reais provavelmente terão mais ruído — os modelos precisarão ser re-treinados e re-validados nesses dados, os números vão mudar (principalmente o modelo de leads, que hoje reflete um padrão sintético).
- O limite de churn (percentil 75) e o número de sugestões de mix (top 2) são parâmetros ajustáveis, não hardcoded para sempre — o time de negócio pode calibrar.

## 5. Proposta final
_(decidir antes da reunião — está em aberto no plano original)_
- [ ] Parceria
- [ ] Venda do projeto
- [ ] CLT com entregas trimestrais
