# Schema Padrão — Meta 2

Este documento define o formato único de colunas que qualquer base (marca) precisa seguir depois de passar pelo pipeline de padronização (`src/pipeline.py`). É o rascunho direto das funções `padronizar_marca_a()` e `padronizar_marca_b()`.

## Tabela de correspondência

| Coluna padrão | Marca A (`ecommerce_customer_behavior_v2`) | Marca B (`ecommerce_sales_analytics_5000`) | Observação / transformação necessária |
|---|---|---|---|
| `customer_id` | `Customer_ID` (texto `CUST_...`) | `customer_id` (número) | Converter ambos pra texto, para não misturar tipo |
| `order_id` | `Order_ID` | `order_id` | Sem transformação |
| `data_pedido` | `Date` (`AAAA-MM-DD`) | `order_date` (`M/D/AAAA`) | `pd.to_datetime()` nos dois, com o `format` certo pra cada um |
| `categoria_produto` | `Product_Category` | `product_category` | Nomes de categoria diferem entre marcas — não precisa igualar, só renomear a coluna |
| `quantidade` | `Quantity` | `quantity` | Sem transformação |
| `preco_unitario` | `Unit_Price` | `unit_price` | Sem transformação (moedas diferentes — ver observações gerais) |
| `desconto_valor` | `Discount_Amount` (já em valor) | `discount` × `unit_price` × `quantity` (B está em fração) | **Precisa de cálculo**, não é renomear |
| `valor_total` | `Total_Amount` | `revenue` | Conferir se o cálculo bate: `quantidade × preço − desconto` |
| `localizacao` | `City` (cidade) | `region` (região) | Renomear os dois, mas documentar que o nível de detalhe é diferente |
| `forma_pagamento` | `Payment_Method` | `payment_method` | Valores possíveis diferem entre as marcas, não precisa igualar |
| `dispositivo` | `Device_Type` | *(não existe)* | Nulo/"não informado" na Marca B |
| `tempo_entrega_dias` | `Delivery_Time_Days` | `delivery_days` | Sem transformação |
| `avaliacao_cliente` | `Customer_Rating` (inteiro) | `customer_rating` (decimal) | Manter como decimal (`float`) nos dois |
| `cliente_recorrente` | `Is_Returning_Customer` (já existe) | *(não existe — derivar)* | Para B: `True` se `customer_id` aparece mais de uma vez na base |
| `idade_cliente` | `Age` | *(não existe)* | Nulo na Marca B |
| `genero_cliente` | `Gender` | *(não existe)* | Nulo na Marca B |
| `marca` | fixo: `"marca_a"` | fixo: `"marca_b"` | Coluna nova, criada na padronização, não vem do CSV original |

## Decisões registradas (não são erro, são escolha consciente)

1. **Moeda:** Marca A está em TRY (lira turca); Marca B não informa moeda. Não trava a demo, mas vale uma nota no roteiro de apresentação para não dar a entender que os valores são comparáveis 1:1 como se fosse a mesma moeda real.
2. **Colunas que só existem em uma marca** (`dispositivo`, `idade_cliente`, `genero_cliente`) permanecem no schema padrão mesmo assim, preenchidas como nulas para quem não tem o dado. Isso garante que uma "Marca C" real, no futuro, já encaixe no mesmo schema sem precisar redesenhar a tabela.

## Próximo passo

Escrever `padronizar_marca_a(df)` e `padronizar_marca_b(df)` em `src/pipeline.py`, cada uma devolvendo um DataFrame com exatamente as colunas da tabela acima, na mesma ordem.
