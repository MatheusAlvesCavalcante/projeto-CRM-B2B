# Decisões e Racional — Meta 3 e Meta 4

Este documento explica **por que** cada escolha técnica foi feita, não só o que foi feito. Todo o código foi testado de verdade contra as suas 4 bases (não é pseudocódigo) — os números abaixo são resultados reais.

---

## 1. Modelo de Churn

### 1.1 Definição do alvo (retomando de onde paramos)
Já tínhamos fechado: churn é definido por um limite de inatividade calculado **separadamente por marca**, usando o percentil 75 da distribuição de `dias_desde_ultima_compra` de cada marca (ver `docs/definicao_churn.md`). Isso deu um balanceamento saudável nas duas marcas (~75%/25%).

### 1.2 Comparação de modelos
Testei três algoritmos, todos com validação estratificada (mesma proporção de churn em treino e teste):

| modelo | roc_auc | precisão (churn) | recall (churn) | f1 (churn) |
|---|---|---|---|---|
| Regressão Logística | 0.811 | 0.478 | **0.738** | 0.580 |
| Random Forest | 0.811 | 0.521 | 0.463 | 0.490 |
| Gradient Boosting | **0.833** | 0.504 | 0.480 | 0.491 |

**Escolha: Regressão Logística**, apesar de ter o ROC AUC levemente menor que o Gradient Boosting (0.811 vs 0.833).

**Por quê:** o objetivo de negócio de um modelo de churn é *agir antes do cliente sumir* — ou seja, o custo de não identificar um cliente que vai dar churn (falso negativo) é muito maior que o custo de mandar uma ação de retenção para alguém que não precisava (falso positivo). Isso significa priorizar **recall** da classe churn=1, não acurácia geral. A Regressão Logística captura 74% dos clientes que realmente vão dar churn; os modelos de árvore capturam menos da metade (46-48%). Na prática, isso seria a diferença entre a equipe comercial agir sobre a maioria dos clientes em risco ou perder mais da metade deles.

### 1.3 Vazamento de dados evitado (data leakage)
`dias_desde_ultima_compra` e `limite_churn_dias` foram usadas para **criar** o alvo `churn` — por isso foram **excluídas** das features de treino. Se entrassem no modelo, ele aprenderia a fórmula do rótulo (quase 100% de acerto, mas inútil, porque em produção você não teria essas colunas ainda calculadas do jeito que precisa pra prever o futuro).

### 1.4 O que mais pesa na decisão (importância das variáveis)
Rodei a importância de variáveis do Random Forest como diagnóstico:

1. `intervalo_medio_compra` (36%) — o fator mais importante, de longe
2. `total_gasto` (22%)
3. `ticket_medio` (22%)
4. `total_pedidos` (11%)
5. `categorias_distintas` (8%)

Isso é bom argumento pra reunião: "o modelo aprendeu, sozinho, que o principal sinal de risco é o cliente estar comprando com intervalos maiores que o normal dele — exatamente a intuição que qualquer time comercial já tem, só que agora quantificada."

---

## 2. Modelo de Priorização de Leads

### 2.1 Comparação de modelos

| modelo | roc_auc | pr_auc | precisão | recall | f1 |
|---|---|---|---|---|---|
| Regressão Logística | 0.982 | 0.361 | 0.195 | 0.985 | 0.326 |
| Random Forest | 1.000 | 1.000 | 1.000 | 0.910 | 0.953 |
| Gradient Boosting | **1.000** | **1.000** | **1.000** | **1.000** | **1.000** |

### 2.2 Achado importante: por que os números de árvore são "perfeitos demais"
Antes de comemorar 100%, investiguei — número perfeito quase sempre é sinal de problema, não de sucesso. Testei uma árvore de decisão simples em profundidades crescentes:

| profundidade da árvore | acurácia no treino |
|---|---|
| 3 | 98.3% (= só chutar a classe majoritária) |
| 6 | 99.1% |
| 10 | **100%** |

Com só 10 níveis de decisão (61 "folhas"), uma árvore simples já memoriza os 100 mil registros perfeitamente. Isso é a assinatura de um **dataset sintético gerado por uma regra fixa** combinando algumas variáveis — não existe isso em dado real de comportamento humano, que sempre tem ruído.

**O que isso significa para a apresentação:** o 100% de acerto prova que o *pipeline* funciona (o modelo consegue aprender qualquer padrão presente nos dados), mas **não** deve ser vendido como "é assim que vai performar com os dados reais da Gobeaute". Isso deve ser dito com todas as letras na reunião — é sinal de rigor técnico saber explicar isso, não esconder.

**Escolha: Gradient Boosting**, para usar na demonstração (melhor desempenho entre os três), com essa ressalva documentada.

### 2.3 Como o ranking funciona
O modelo gera uma probabilidade (0 a 1) por lead via `predict_proba()`, convertida em um score de 0 a 100 (`score_conversao`). É esse score que ordena o ranking priorizado no dashboard — não é 0/1, é uma escala contínua, então dá pra decidir "atender os 50 primeiros" ou "atender todo mundo acima de 80 pontos", dependendo da capacidade do time comercial.

---

## 3. Modelo de Recomendação de Mix

### 3.1 Por que não é um modelo de Machine Learning treinado
Decisão deliberada: em vez de um modelo de recomendação complexo (ex: filtragem colaborativa com fatoração de matriz), usei uma regra de **popularidade condicional** — para cada cliente, sugerir as categorias mais vendidas da marca dele que ele ainda não comprou.

**Motivos:**
1. **Explicabilidade:** dá pra explicar em uma frase na reunião ("sugerimos o que mais vende, entre o que o cliente ainda não tem"), sem precisar defender a caixa-preta de um modelo complexo.
2. **Funciona com pouco histórico:** a Marca B tem poucos pedidos por cliente (1 a 14). Um modelo de recomendação tradicional (ex: baseado em similaridade entre clientes) precisaria de muito mais dado por cliente pra funcionar bem; a regra de popularidade não tem esse problema.
3. **Já prova o conceito:** o objetivo da entrega é mostrar que o sistema multi-marca funciona, não entregar o recomendador mais sofisticado do mercado.

### 3.2 Exemplo de saída real (Marca A)
| cliente | categorias sugeridas |
|---|---|
| CUST_00001 | Beauty, Food |
| CUST_00002 | Sports, Books |
| CUST_00003 | Sports, Beauty |

---

## 4. Dashboard

Construído em Streamlit (`dashboard/app.py`), com 3 abas (Churn, Mix, Leads) e um seletor de marca no topo — é esse seletor que resolve o requisito de "trocar entre bases ao vivo" da entrega final. Todos os dados vêm de `data/processed/` (nunca lê os CSVs brutos direto), reforçando que o dashboard é a camada de consumo, não de processamento.

Testei a lógica de carregamento e filtro de dados sem abrir o navegador (simulando as mesmas operações que o Streamlit faz) — sem erros. Para ver visualmente, é rodar `streamlit run dashboard/app.py` na sua máquina.

---

## 5. Ordem de execução dos scripts

Para reproduzir tudo do zero, nessa ordem:

```bash
python src/pipeline.py         # (ainda a extrair como script — hoje roda via notebook)
python src/churn_model.py      # gera data/processed/por_cliente_com_risco.csv
python src/lead_model.py       # gera data/processed/leads_priorizados.csv
python src/mix_model.py        # gera data/processed/recomendacoes_mix.csv
streamlit run dashboard/app.py # abre o dashboard
```

Note que `churn_model.py` depende de `data/processed/por_cliente.csv` já existir (gerado a partir de `pipeline.py` + `agregar_por_cliente()` + `definir_churn()`, que você já rodou manualmente no notebook). Um próximo passo de limpeza (não urgente) é extrair isso do notebook para um script `gerar_dados_processados.py`, para não depender de rodar célula por célula toda vez.
