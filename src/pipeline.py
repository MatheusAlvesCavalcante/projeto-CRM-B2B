import pandas as pd

COLUNAS_PADRAO = [
    "customer_id", "order_id", "data_pedido", "categoria_produto",
    "quantidade", "preco_unitario", "desconto_valor", "valor_total",
    "localizacao", "forma_pagamento", "dispositivo", "tempo_entrega_dias",
    "avaliacao_cliente", "cliente_recorrente", "idade_cliente",
    "genero_cliente", "marca",
]

def padronizar_marca_a(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["customer_id"] = df["Customer_ID"].astype(str)
    df["order_id"] = df["Order_ID"]
    df["data_pedido"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    df["categoria_produto"] = df["Product_Category"]
    df["quantidade"] = df["Quantity"]
    df["preco_unitario"] = df["Unit_Price"]
    df["desconto_valor"] = df["Discount_Amount"]
    df["valor_total"] = df["Total_Amount"]
    df["localizacao"] = df["City"]
    df["forma_pagamento"] = df["Payment_Method"]
    df["dispositivo"] = df["Device_Type"]
    df["tempo_entrega_dias"] = df["Delivery_Time_Days"]
    df["avaliacao_cliente"] = df["Customer_Rating"].astype(float)
    df["cliente_recorrente"] = df["Is_Returning_Customer"]
    df["idade_cliente"] = df["Age"]
    df["genero_cliente"] = df["Gender"]
    df["marca"] = "marca_a"
    return df[COLUNAS_PADRAO] 



def padronizar_marca_b(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["customer_id"] = df["customer_id"].astype(str)
    df["order_id"] = df["order_id"]
    df["data_pedido"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y")
    df["categoria_produto"] = df["product_category"]
    df["quantidade"] = df["quantity"]
    df["preco_unitario"] = df["unit_price"]
    df["desconto_valor"] = df["discount"] * df["unit_price"] * df["quantity"]
    df["valor_total"] = df["revenue"]
    df["localizacao"] = df["region"]
    df["forma_pagamento"] = df["payment_method"]
    df["dispositivo"] = None
    df["tempo_entrega_dias"] = df["delivery_days"]
    df["avaliacao_cliente"] = df["customer_rating"].astype(float)
    df["cliente_recorrente"] = df["customer_id"].duplicated(keep=False)
    df["idade_cliente"] = None
    df["genero_cliente"] = None
    df["marca"] = "marca_b"
    return df[COLUNAS_PADRAO]


def rodar_pipeline(caminho_csv: str, marca: str) -> pd.DataFrame:
    df_bruto = pd.read_csv(caminho_csv)

    if marca == "marca_a":
        df_padrao = padronizar_marca_a(df_bruto)
    elif marca == "marca_b":
        df_padrao = padronizar_marca_b(df_bruto)
    else:
        raise ValueError(f"Marca desconhecida: {marca}")

    antes = len(df_padrao)
    df_padrao = df_padrao.drop_duplicates()
    depois = len(df_padrao)

    if antes != depois:
        print(f"Removidas {antes - depois} linhas duplicadas")

    return df_padrao

def agregar_por_cliente(dados: pd.DataFrame) -> pd.DataFrame:
    """Agrega o dataframe padronizado (nivel pedido) para nivel cliente."""
    por_cliente = dados.groupby(["marca", "customer_id"]).agg(
        ultima_compra=("data_pedido", "max"),
        primeira_compra=("data_pedido", "min"),
        total_pedidos=("order_id", "count"),
        total_gasto=("valor_total", "sum"),
        ticket_medio=("valor_total", "mean"),
        categorias_distintas=("categoria_produto", "nunique"),
    ).reset_index()
    return por_cliente


def definir_churn(por_cliente: pd.DataFrame, percentil: float = 0.75) -> pd.DataFrame:
    """Define o alvo de churn usando um limite adaptativo por marca (percentil
    da distribuicao de dias desde a ultima compra, calculado separadamente
    para cada marca). Ver docs/definicao_churn.md para o racional completo.
    """
    por_cliente = por_cliente.copy()
    data_ref = por_cliente.groupby("marca")["ultima_compra"].transform("max")
    por_cliente["dias_desde_ultima_compra"] = (data_ref - por_cliente["ultima_compra"]).dt.days

    limite = por_cliente.groupby("marca")["dias_desde_ultima_compra"].transform(
        lambda x: x.quantile(percentil)
    )
    por_cliente["limite_churn_dias"] = limite
    por_cliente["churn"] = (por_cliente["dias_desde_ultima_compra"] > limite).astype(int)

    # frequencia de compra do proprio cliente (usado como feature no modelo)
    intervalo_total = (por_cliente["ultima_compra"] - por_cliente["primeira_compra"]).dt.days
    por_cliente["intervalo_medio_compra"] = (
        intervalo_total / por_cliente["total_pedidos"].clip(lower=1)
    ).fillna(0)

    return por_cliente