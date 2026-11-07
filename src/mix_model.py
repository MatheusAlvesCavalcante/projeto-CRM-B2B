"""
Recomendacao de mix de produtos.

Abordagem: nao e um modelo de Machine Learning treinado, e sim uma regra
de "popularidade condicional" (uma forma simples de collaborative filtering):
para cada cliente, olha quais categorias ele ainda NAO comprou, e recomenda
as mais populares entre isso -- calculado separadamente por marca, para nao
misturar catalogos diferentes.

Por que essa abordagem em vez de um modelo de ML: e mais facil de explicar
na apresentacao ("recomendamos o que mais vende, entre o que o cliente ainda
nao tem"), nao depende de historico longo por cliente para funcionar (bom
para a Marca B, que tem poucos pedidos por cliente), e evita a armadilha de
um modelo de recomendacao "caixa-preta" dificil de justificar com pouco dado.
"""
import pandas as pd


def calcular_popularidade_categorias(dados: pd.DataFrame) -> pd.DataFrame:
    """Ranking de categorias mais vendidas, por marca."""
    pop = (
        dados.groupby(["marca", "categoria_produto"])
        .size()
        .reset_index(name="total_vendas")
        .sort_values(["marca", "total_vendas"], ascending=[True, False])
    )
    return pop


def recomendar_mix(dados: pd.DataFrame, top_n: int = 2) -> pd.DataFrame:
    """Para cada cliente, recomenda as top_n categorias mais populares da
    marca dele que ele ainda nao comprou."""
    popularidade = calcular_popularidade_categorias(dados)
    ticket_cat = dados.groupby(["marca", "categoria_produto"])["valor_total"].mean().to_dict()
    comprados = dados.groupby(["marca", "customer_id"])["categoria_produto"].apply(set).reset_index()
    comprados = comprados.rename(columns={"categoria_produto": "categorias_compradas"})

    recomendacoes = []
    for marca in dados["marca"].unique():
        ranking_marca = popularidade[popularidade["marca"] == marca]["categoria_produto"].tolist()
        clientes_marca = comprados[comprados["marca"] == marca]

        for _, linha in clientes_marca.iterrows():
            ja_comprou = linha["categorias_compradas"]
            sugestoes = [cat for cat in ranking_marca if cat not in ja_comprou][:top_n]
            recomendacoes.append({
                "marca": marca,
                "customer_id": linha["customer_id"],
                "categorias_sugeridas": ", ".join(sugestoes) if sugestoes else "ja comprou de tudo",
                 "potencial_estimado": round(sum(ticket_cat[(marca, c)] for c in sugestoes), 2),
            })

    return pd.DataFrame(recomendacoes)


if __name__ == "__main__":
    dados = pd.read_csv("data/processed/dados_unificados.csv")
    popularidade = calcular_popularidade_categorias(dados)
    print(popularidade)

    recomendacoes = recomendar_mix(dados)
    recomendacoes.to_csv("data/processed/recomendacoes_mix.csv", index=False)
    print(recomendacoes.head(10))
    print("Recomendacoes salvas em data/processed/recomendacoes_mix.csv")
