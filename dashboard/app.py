"""
Dashboard do sistema de inteligencia de CRM B2B da Gobeaute.

Roda com: streamlit run dashboard/app.py
(rodar a partir da RAIZ do projeto, nao de dentro da pasta dashboard/,
para os caminhos relativos de data/processed/ funcionarem)
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gobeaute — CRM B2B", layout="wide")
st.title("Gobeaute — Inteligencia de CRM B2B")
st.caption(
    "Demonstracao com dados publicos (Kaggle) simulando duas marcas diferentes "
    "no mesmo pipeline. Troque a marca no seletor abaixo."
)

# -- carregar dados pre-processados (gerados por src/pipeline.py, src/churn_model.py etc.) --
por_cliente = pd.read_csv("data/processed/por_cliente_com_risco.csv")
recomendacoes = pd.read_csv("data/processed/recomendacoes_mix.csv")
leads = pd.read_csv("data/processed/leads_priorizados.csv")

marca = st.selectbox("Marca simulada", sorted(por_cliente["marca"].unique()))

col1, col2, col3 = st.columns(3)
clientes_marca = por_cliente[por_cliente["marca"] == marca]
col1.metric("Clientes", len(clientes_marca))
col2.metric("Em risco de churn", int((clientes_marca["churn"] == 1).sum()))
col3.metric("Risco medio", f"{clientes_marca['risco_churn'].mean():.0%}")

st.divider()

tab_churn, tab_mix, tab_leads = st.tabs(["Risco de Churn", "Sugestoes de Mix", "Leads Priorizados"])

with tab_churn:
    st.subheader(f"Clientes em maior risco de churn — {marca}")
    ranking_churn = clientes_marca.sort_values("risco_churn", ascending=False)
    st.dataframe(
        ranking_churn[["customer_id", "total_pedidos", "total_gasto", "intervalo_medio_compra", "risco_churn"]]
        .head(20)
        .style.format({"risco_churn": "{:.0%}", "total_gasto": "{:.2f}"}),
        use_container_width=True,
    )
    st.bar_chart(ranking_churn.head(15).set_index("customer_id")["risco_churn"])

with tab_mix:
    st.subheader(f"Sugestoes de produtos por cliente — {marca}")
    mix_marca = recomendacoes[recomendacoes["marca"] == marca]
    st.dataframe(mix_marca[["customer_id", "categorias_sugeridas"]].head(20), use_container_width=True)

with tab_leads:
    st.subheader("Ranking de leads priorizados")
    st.caption(
        "Este modelo roda sobre uma base separada de leads (nao e dividido por marca simulada). "
        "Score de 0 a 100 = probabilidade estimada de conversao."
    )
    top_leads = leads.sort_values("score_conversao", ascending=False).head(20)
    st.dataframe(top_leads[["LeadID", "LeadSource", "LeadStatus", "score_conversao"]], use_container_width=True)
    st.bar_chart(top_leads.set_index("LeadID")["score_conversao"])
