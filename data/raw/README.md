# data/raw — Dados brutos

Esta pasta guarda os CSVs originais, **do jeito que foram baixados**. Nunca edite esses arquivos: qualquer tratamento é feito pelo pipeline e salvo em `data/processed/`.

Os CSVs não são versionados no Git (estão no `.gitignore`). Este README é o que fica no repositório, para qualquer pessoa saber onde baixar cada base.

| Arquivo esperado | Origem | Link | Marca simulada |
|---|---|---|---|
| `ecommerce_customer_behavior_dataset_v2.csv` | Kaggle | _(preencher)_ | Marca A |
| `ecommerce_sales_analytics_5000.csv` | Kaggle | _(preencher)_ | Marca B |
| `customer_conversion_traing_dataset_.csv` | Kaggle | _(preencher)_ | Leads (treino) |
| `customer_conversion_testing_dataset.csv` | Kaggle | _(preencher)_ | Leads (teste) |

## Como montar em uma máquina nova

1. Baixe os 4 arquivos dos links acima.
2. Coloque-os nesta pasta (`data/raw/`).
3. Confira os nomes exatamente como na tabela.

Detalhes de cada coluna: veja `docs/data_dictionary.md`.
