"""
Engenharia de features para churn e segmentacao de carteira.

Ideia central (mesma regra para qualquer marca):
- A "janela" de cada marca e uma fracao do periodo coberto pelos dados dela
  (padrao: 20%). Isso adapta o criterio ao ritmo de cada marca sem hardcode.
- Para TREINAR: escolhe-se uma data de corte = ultima data - janela. As features
  usam so pedidos ATE o corte; o rotulo (churn) e "nao comprou na janela seguinte".
  Assim o modelo realmente preve o futuro, em vez de descrever o presente.
- Para PONTUAR (dashboard): as mesmas features sao calculadas na ultima data
  disponivel, e o modelo estima a chance de o cliente nao comprar na proxima janela.
"""
import numpy as np
import pandas as pd

FRACAO_JANELA = 0.20

# thresholds da regra de atraso de recompra (dias sem comprar / intervalo habitual)
LIMITE_RISCO_MEDIO = 1.0
LIMITE_RISCO_ALTO = 2.0

FEATURES = [
    "frequencia", "valor_total_log", "ticket_medio_log", "categorias_distintas",
    "nota_media", "nota_ultima", "entrega_media", "desconto_medio",
    "recencia_j", "tenure_j", "intervalo_j", "sem_intervalo", "atraso_recompra",
]

# (texto se o valor esta ALTO, texto se o valor esta BAIXO) -- usado nos "motivos" do risco
TEXTO_FATORES = {
    "frequencia": ("Muitos pedidos", "Poucos pedidos"),
    "valor_total_log": ("Alto valor acumulado", "Baixo valor acumulado"),
    "ticket_medio_log": ("Ticket médio alto", "Ticket médio baixo"),
    "categorias_distintas": ("Muita variedade de categorias", "Pouca variedade de categorias"),
    "nota_media": ("Nota média alta", "Nota média baixa"),
    "nota_ultima": ("Última nota alta", "Última nota baixa"),
    "entrega_media": ("Entregas demoradas", "Entregas rápidas"),
    "desconto_medio": ("Descontos altos", "Descontos baixos"),
    "recencia_j": ("Muito tempo sem comprar", "Compra recente"),
    "tenure_j": ("Cliente antigo", "Cliente recente"),
    "intervalo_j": ("Intervalo longo entre compras", "Intervalo curto entre compras"),
    "sem_intervalo": ("Histórico curto (1 pedido)", "Histórico com recompra"),
    "atraso_recompra": ("Fora do ciclo de recompra", "Dentro do ciclo de recompra"),
}


def janela_da_marca(dm: pd.DataFrame, fracao: float = FRACAO_JANELA) -> int:
    """Tamanho da janela futura (em dias) para uma marca."""
    span = (dm["data_pedido"].max() - dm["data_pedido"].min()).days
    return max(int(round(span * fracao)), 1)


def _com_desconto_pct(dm: pd.DataFrame) -> pd.DataFrame:
    dm = dm.copy()
    base = (dm["preco_unitario"] * dm["quantidade"]).replace(0, np.nan)
    dm["desconto_pct"] = (dm["desconto_valor"] / base).fillna(0).clip(0, 1)
    return dm


def construir_features(dm: pd.DataFrame, data_ref: pd.Timestamp, janela: int) -> pd.DataFrame:
    """Uma linha por cliente, usando apenas pedidos ate data_ref (inclusive)."""
    h = _com_desconto_pct(dm[dm["data_pedido"] <= data_ref]).sort_values("data_pedido")
    g = h.groupby("customer_id")

    f = pd.DataFrame({
        "frequencia": g.size(),
        "valor_total": g["valor_total"].sum(),
        "ticket_medio": g["valor_total"].mean(),
        "primeira_compra": g["data_pedido"].min(),
        "ultima_compra": g["data_pedido"].max(),
        "categorias_distintas": g["categoria_produto"].nunique(),
        "nota_media": g["avaliacao_cliente"].mean(),
        "nota_ultima": g["avaliacao_cliente"].last(),
        "entrega_media": g["tempo_entrega_dias"].mean(),
        "desconto_medio": g["desconto_pct"].mean(),
        "localizacao": g["localizacao"].last(),
        "categoria_favorita": g["categoria_produto"].agg(lambda s: s.value_counts().index[0]),
    })

    f["dias_sem_comprar"] = (data_ref - f["ultima_compra"]).dt.days
    f["tenure_dias"] = (data_ref - f["primeira_compra"]).dt.days

    intervalo_dias = (f["ultima_compra"] - f["primeira_compra"]).dt.days / (f["frequencia"] - 1).replace(0, np.nan)
    f["sem_intervalo"] = intervalo_dias.isna().astype(int)
    # cliente com 1 pedido: usa o intervalo mediano da marca como referencia
    intervalo_dias = intervalo_dias.fillna(intervalo_dias.median())
    intervalo_dias = intervalo_dias.clip(lower=1)
    f["intervalo_dias"] = intervalo_dias

    f["recencia_j"] = f["dias_sem_comprar"] / janela
    f["tenure_j"] = f["tenure_dias"] / janela
    f["intervalo_j"] = f["intervalo_dias"] / janela
    f["atraso_recompra"] = f["dias_sem_comprar"] / f["intervalo_dias"]

    f["valor_total_log"] = np.log1p(f["valor_total"])
    f["ticket_medio_log"] = np.log1p(f["ticket_medio"])
    f["desconto_medio"] = f["desconto_medio"].fillna(0)
    f["nota_media"] = f["nota_media"].fillna(f["nota_media"].median())
    f["nota_ultima"] = f["nota_ultima"].fillna(f["nota_media"])
    f["entrega_media"] = f["entrega_media"].fillna(f["entrega_media"].median())
    return f


def rotular_churn(dm: pd.DataFrame, clientes_corte: pd.Index, data_corte: pd.Timestamp) -> pd.Series:
    """1 = o cliente NAO comprou depois da data de corte."""
    compraram_depois = set(dm.loc[dm["data_pedido"] > data_corte, "customer_id"])
    return pd.Series(
        [0 if c in compraram_depois else 1 for c in clientes_corte],
        index=clientes_corte, name="churn",
    )


def montar_base_treino(dados: pd.DataFrame, fracao: float = FRACAO_JANELA):
    """Constroi features no corte + rotulo para todas as marcas, com a MESMA regra."""
    partes, info = [], {}
    for marca, dm in dados.groupby("marca"):
        janela = janela_da_marca(dm, fracao)
        corte = dm["data_pedido"].max() - pd.Timedelta(days=janela)
        f = construir_features(dm, corte, janela)
        f["churn"] = rotular_churn(dm, f.index, corte)
        f["marca"] = marca
        partes.append(f.reset_index())
        info[marca] = {
            "janela_dias": int(janela),
            "data_corte": str(corte.date()),
            "clientes": int(len(f)),
            "taxa_churn": float(f["churn"].mean()),
        }
    return pd.concat(partes, ignore_index=True), info


def faixa_de_risco(atraso: pd.Series) -> pd.Series:
    """Regra explicavel: quantas vezes o cliente passou do intervalo habitual dele."""
    return pd.Series(
        np.select(
            [atraso >= LIMITE_RISCO_ALTO, atraso >= LIMITE_RISCO_MEDIO],
            ["Alto", "Médio"], default="Baixo",
        ),
        index=atraso.index,
    )


def segmentar_rfm(df: pd.DataFrame) -> pd.Series:
    """Segmentacao simples por recencia x frequencia, calculada DENTRO de cada marca."""
    r = df.groupby("marca")["dias_sem_comprar"].rank(pct=True, ascending=False, method="average")
    f = df.groupby("marca")["frequencia"].rank(pct=True, ascending=True, method="average")
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    rs = pd.cut(r, bins=bins, labels=[1, 2, 3, 4, 5], include_lowest=True).astype(int)
    fs = pd.cut(f, bins=bins, labels=[1, 2, 3, 4, 5], include_lowest=True).astype(int)

    seg = np.select(
        [
            (rs >= 4) & (fs >= 4),
            (rs >= 3) & (fs >= 3),
            (rs >= 4) & (fs <= 2),
            (rs <= 2) & (fs >= 3),
            (rs <= 2) & (fs <= 2),
        ],
        ["Campeões", "Leais", "Novos / promissores", "Em risco", "Hibernando"],
        default="Precisam de atenção",
    )
    return pd.Series(seg, index=df.index, name="segmento")
