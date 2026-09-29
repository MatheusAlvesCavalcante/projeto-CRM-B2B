# Definição de Churn — Meta 3

## Problema encontrado

Ao calcular churn com um limite fixo de dias (90, depois 365) aplicado igual pras duas marcas, o resultado saiu muito desbalanceado:

| Marca | Churn = 1 | Churn = 0 |
|---|---|---|
| Marca A | ~51% | ~49% |
| Marca B | ~92% | ~8% |

## Causa

As datas da Marca B (`ecommerce_sales_analytics_5000.csv`) são sintéticas e sequenciais — uma por dia, de 01/01/2022 a 09/09/2035 (já registrado em `docs/data_dictionary.md`). Com poucos pedidos por cliente (1 a 14) espalhados num intervalo de 13 anos, o tempo médio entre duas compras do mesmo cliente é de anos, não meses. Um limite fixo de dias comparável ao padrão da Marca A (dados reais, compras mais próximas no tempo) classifica quase todo mundo da Marca B como churn — não é um problema no código, é a estrutura dos dados sendo diferente entre as marcas.

## Decisão

Em vez de um número fixo de dias igual para todas as marcas, o limite de inatividade é calculado **por marca**, usando o percentil 75 da distribuição de `dias_desde_ultima_compra` daquela marca:

```python
LIMITE_PERCENTIL = 0.75

por_cliente["limite_churn_dias"] = por_cliente.groupby("marca")["dias_desde_ultima_compra"].transform(
    lambda x: x.quantile(LIMITE_PERCENTIL)
)
por_cliente["churn"] = (por_cliente["dias_desde_ultima_compra"] > por_cliente["limite_churn_dias"]).astype(int)
```

Isso faz cada marca ser comparada contra a própria régua de comportamento, em vez de um número absoluto que só faz sentido pra uma delas.

## Por que isso não é "trapacear" o resultado

O objetivo do projeto é provar que o **pipeline generaliza** entre marcas com padrões de dados diferentes — não que as marcas têm o mesmo comportamento. Adaptar a definição de inatividade à cadência de compra de cada marca é o comportamento esperado de um sistema real: uma marca de compra frequente (ex: cosméticos) e uma de compra esporádica (ex: eletrônicos) não deveriam usar o mesmo limite de dias para "risco de churn". Isso é um ponto bom para mencionar na apresentação.

## Pendência

Confirmar a distribuição de `dias_desde_ultima_compra` por marca (`por_cliente.groupby("marca")["dias_desde_ultima_compra"].describe()`) antes de seguir para o treino do modelo, para validar que o novo balanceamento ficou saudável (esperado: perto de 25%/75% nas duas marcas, por construção do percentil).
