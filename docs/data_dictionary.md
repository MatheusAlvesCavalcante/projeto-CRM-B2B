# Dicionário de Dados — Projeto CRM B2B

Este documento descreve cada base usada no projeto: de onde veio, o que cada coluna significa e qual "marca simulada" ela representa. As colunas abaixo foram conferidas contra os arquivos reais (não só contra a descrição do Kaggle).

## Visão geral

| Base | Arquivo | Linhas | Colunas | Marca simulada | Uso nos modelos |
|---|---|---|---|---|---|
| E-commerce Customer Behavior v2 | `ecommerce_customer_behavior_dataset_v2.csv` | 17.049 | 18 | Marca A | Churn + Mix |
| E-Commerce Sales Analytics 5000 | `ecommerce_sales_analytics_5000.csv` | 5.000 | 12 | Marca B | Churn + Mix |
| Customer Conversion (treino) | `customer_conversion_traing_dataset_.csv` | 100.000 | 19 | Frente de leads | Priorização de leads |
| Customer Conversion (teste) | `customer_conversion_testing_dataset.csv` | 26.145 | 19 | Frente de leads | Priorização de leads |

Todas as bases: sem valores nulos e sem linhas duplicadas (verificado).

---

## Marca A — `ecommerce_customer_behavior_dataset_v2.csv`

- **Origem:** Kaggle, "E-Commerce Customer Behavior and Sales Dataset" (versão v2). Link: _(preencher)_
- **Contexto:** plataforma de varejo online turca. Valores em **TRY (lira turca)**.
- **Licença:** CC0 (domínio público).
- **Diferença da v1:** cada cliente tem de 1 a 10 pedidos ao longo do tempo, então serve para análise de recorrência (churn, RFM, CLV).

| Coluna | Tipo | Significado |
|---|---|---|
| `Order_ID` | texto | Identificador único do pedido (ex: `ORD_000001-1`, o sufixo é a ordem do pedido do cliente) |
| `Customer_ID` | texto | Identificador do cliente (ex: `CUST_00001`) |
| `Date` | data | Data da compra |
| `Age` | inteiro | Idade do cliente (18–75) |
| `Gender` | texto | Gênero (Male, Female, Other) |
| `City` | texto | Cidade do cliente (10 cidades turcas) |
| `Product_Category` | texto | Categoria: Electronics, Fashion, Home & Garden, Sports, Books, Beauty, Toys, Food |
| `Unit_Price` | decimal | Preço por unidade (TRY) |
| `Quantity` | inteiro | Unidades compradas (1–5) |
| `Discount_Amount` | decimal | Desconto em **valor absoluto** (TRY), não porcentagem |
| `Total_Amount` | decimal | Valor final pago (`Unit_Price × Quantity − Discount_Amount`) |
| `Payment_Method` | texto | Forma de pagamento (5 tipos) |
| `Device_Type` | texto | Dispositivo: Mobile, Desktop, Tablet |
| `Session_Duration_Minutes` | inteiro | Tempo na sessão do site (1–120 min) |
| `Pages_Viewed` | inteiro | Páginas vistas na sessão (1–50) |
| `Is_Returning_Customer` | booleano | Cliente que já comprou antes |
| `Delivery_Time_Days` | inteiro | Dias de entrega (1–30) |
| `Customer_Rating` | inteiro | Nota de satisfação (1–5) |

---

## Marca B — `ecommerce_sales_analytics_5000.csv`

- **Origem:** Kaggle, "E-Commerce Sales Analytics (5,000 Records)". Link: _(preencher)_
- **Contexto:** dados **sintéticos** que imitam um marketplace online. Moeda não informada.
- **Atenção:** a descrição do Kaggle fala em 15 colunas, com idade, gênero, localização e data de envio. **O arquivo real tem só 12 colunas e não tem nenhuma dessas.** Documentamos o que existe de fato.
- **Datas:** vão de 01/01/2022 a 09/09/2035, uma por dia em sequência. Ou seja, não refletem sazonalidade real (a descrição menciona pico no Q4, o que não aparece nos dados).

| Coluna | Tipo | Significado |
|---|---|---|
| `order_id` | inteiro | Identificador do pedido (10001 a 15000) |
| `order_date` | data | Data do pedido (formato M/D/AAAA) |
| `customer_id` | inteiro | Identificador do cliente (989 clientes únicos) |
| `product_category` | texto | Categoria do produto (ex: Beauty, Clothing, Electronics) |
| `region` | texto | Região (ex: North, South, East, West) |
| `quantity` | inteiro | Unidades compradas |
| `unit_price` | decimal | Preço por unidade |
| `discount` | decimal | Desconto em **fração** (0.28 = 28%), diferente da Marca A |
| `payment_method` | texto | Forma de pagamento (ex: Card, Wallet, COD) |
| `delivery_days` | inteiro | Dias de entrega |
| `customer_rating` | decimal | Nota do cliente (1.0–5.0) |
| `revenue` | decimal | Receita líquida (`quantity × unit_price × (1 − discount)`) |

---

## Frente de leads — `customer_conversion_traing_dataset_.csv` e `customer_conversion_testing_dataset.csv`

- **Origem:** Kaggle. Link: _(preencher — ainda a localizar)_
- **Estrutura:** duas partes da mesma base, com colunas idênticas. Treino (100 mil) e teste (26 mil) já vêm separados.
- **Alvo do modelo:** `Conversion (Target)` (1 = converteu, 0 = não converteu).
- **Localização:** as cidades são paquistanesas (Lahore, Faisalabad, Islamabad...).
- **Nota:** as descrições abaixo foram inferidas pelos nomes das colunas. Confirmar na página do Kaggle quando o link for encontrado.

| Coluna | Tipo | Significado (inferido) |
|---|---|---|
| `LeadID` | inteiro | Identificador do lead |
| `Age` | inteiro | Idade |
| `Gender` | texto | Gênero |
| `Location` | texto | Cidade |
| `LeadSource` | texto | Canal de origem do lead (ex: Organic, Email, Referral) |
| `TimeSpent (minutes)` | inteiro | Tempo no site |
| `PagesViewed` | inteiro | Páginas vistas |
| `LeadStatus` | texto | Temperatura do lead (ex: Hot, Warm) |
| `EmailSent` | inteiro | E-mails enviados ao lead |
| `DeviceType` | texto | Dispositivo (Mobile, Desktop, Tablet) |
| `ReferralSource` | texto | De onde veio a indicação (ex: Facebook, Google, Direct) |
| `FormSubmissions` | inteiro | Formulários preenchidos |
| `Downloads` | inteiro | Downloads feitos |
| `CTR_ProductPage` | decimal | Taxa de clique na página de produto |
| `ResponseTime (hours)` | inteiro | Tempo de resposta ao lead, em horas |
| `FollowUpEmails` | inteiro | E-mails de acompanhamento |
| `SocialMediaEngagement` | inteiro | Engajamento em redes sociais |
| `PaymentHistory` | texto | Histórico de pagamento (ex: Good, No Payment) |
| `Conversion (Target)` | inteiro | **Alvo:** converteu (1) ou não (0) |

---

## Diferenças que o pipeline (Meta 2) precisa resolver

| Tema | Marca A | Marca B |
|---|---|---|
| Nome do cliente | `Customer_ID` (texto `CUST_...`) | `customer_id` (número) |
| Data | `Date` (AAAA-MM-DD) | `order_date` (M/D/AAAA) |
| Desconto | valor absoluto | fração (0 a 1) |
| Valor final | `Total_Amount` | `revenue` |
| Região | `City` | `region` (bem mais genérica) |
| Recorrência | `Is_Returning_Customer` existe | não existe, precisa ser derivada |
| Idade/Gênero | existem | não existem |
| Moeda | TRY | não informada |
