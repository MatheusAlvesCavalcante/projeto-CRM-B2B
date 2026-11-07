"""
Dashboard — CRM B2B Intelligence.

Rodar da raiz do projeto:  streamlit run dashboard/app.py
Pre-requisito: ter rodado, nesta ordem,
    python src/gerar_dados_processados.py
    python src/churn_model.py
    python src/lead_model.py
    python src/mix_model.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = RAIZ / "data" / "processed"

st.set_page_config(page_title="CRM B2B Intelligence", page_icon="📊", layout="wide")

# ----------------------------------------------------------------------------
# Estilo
# ----------------------------------------------------------------------------
PALETA = ["#8B5CF6", "#22D3EE", "#F472B6", "#FBBF24", "#34D399", "#60A5FA", "#FB7185", "#A3E635"]
COR_RISCO = {"Alto": "#F43F5E", "Médio": "#FBBF24", "Baixo": "#34D399"}
COR_SEGMENTO = {
    "Campeões": "#34D399", "Leais": "#22D3EE", "Novos / promissores": "#60A5FA",
    "Precisam de atenção": "#FBBF24", "Em risco": "#F97316", "Hibernando": "#F43F5E",
}
ORDEM_SEGMENTOS = list(COR_SEGMENTO)
NOMES_MARCA = {"marca_a": "Marca A", "marca_b": "Marca B"}

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px;}
    h1 {font-weight: 800; letter-spacing: -0.02em; margin-bottom: 0.2rem;}
    [data-testid="stMetric"] {
        background: #161B26; border: 1px solid #232B3B; border-radius: 14px; padding: 14px 18px;
    }
    [data-testid="stMetricLabel"] p {
        opacity: .72; font-size: .74rem; text-transform: uppercase; letter-spacing: .05em;
    }
    [data-testid="stMetricValue"] {font-weight: 700;}
    button[data-baseweb="tab"] {padding: 8px 16px; border-radius: 8px 8px 0 0;}
    .tag {
        display: inline-block; padding: 3px 12px; border-radius: 999px; background: #1E2433;
        border: 1px solid #2B3550; font-size: .74rem; margin: 0 6px 6px 0; color: #C9D1E3;
    }
    .nota {color: #98A2B8; font-size: .85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------
ARQUIVOS = [
    "clientes_scoring.csv", "dados_unificados.csv", "recomendacoes_mix.csv",
    "leads_priorizados.csv", "metricas_churn.json",
]
faltando = [a for a in ARQUIVOS if not (PROCESSED / a).exists()]
if faltando:
    st.error(f"Arquivos não encontrados em data/processed/: {', '.join(faltando)}")
    st.write("Gere os dados rodando, na raiz do projeto e nesta ordem:")
    st.code(
        "python src/gerar_dados_processados.py\npython src/churn_model.py\n"
        "python src/lead_model.py\npython src/mix_model.py",
        language="bash",
    )
    st.stop()


@st.cache_data(show_spinner=False)
def carregar():
    clientes = pd.read_csv(
        PROCESSED / "clientes_scoring.csv", dtype={"customer_id": str},
        parse_dates=["primeira_compra", "ultima_compra"],
    )
    pedidos = pd.read_csv(
        PROCESSED / "dados_unificados.csv", dtype={"customer_id": str}, parse_dates=["data_pedido"],
    )
    mix = pd.read_csv(PROCESSED / "recomendacoes_mix.csv", dtype={"customer_id": str})
    leads = pd.read_csv(PROCESSED / "leads_priorizados.csv")
    metricas = json.loads((PROCESSED / "metricas_churn.json").read_text(encoding="utf-8"))
    return clientes, pedidos, mix, leads, metricas


clientes, pedidos, mix, leads, metricas = carregar()


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def fmt(v, casas=0) -> str:
    """Formata numero no padrao brasileiro (1.234,5)."""
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def compacto(v) -> str:
    """Numero curto para cards: 21,7 mi / 8,5 mi / 12,3 mil."""
    a = abs(v)
    if a >= 1e9:
        return f"{fmt(v / 1e9, 1)} bi"
    if a >= 1e6:
        return f"{fmt(v / 1e6, 1)} mi"
    if a >= 1e4:
        return f"{fmt(v / 1e3, 1)} mil"
    return fmt(v)


NOMES_VARIAVEIS = {
    "frequencia": "Frequência de compra", "valor_total_log": "Valor acumulado",
    "ticket_medio_log": "Ticket médio", "categorias_distintas": "Variedade de categorias",
    "nota_media": "Nota média", "nota_ultima": "Última nota", "entrega_media": "Tempo de entrega",
    "desconto_medio": "Desconto médio", "recencia_j": "Tempo sem comprar", "tenure_j": "Tempo de casa",
    "intervalo_j": "Intervalo entre compras", "sem_intervalo": "Só 1 pedido (sem histórico)",
    "atraso_recompra": "Atraso de recompra",
}


def estilizar(fig, altura=330, legenda=True):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=altura,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        font=dict(size=12),
    )
    fig.update_xaxes(gridcolor="#1E2433", zeroline=False)
    fig.update_yaxes(gridcolor="#1E2433", zeroline=False)
    return fig


def grafico(fig, chave):
    st.plotly_chart(fig, key=chave, config={"displayModeBar": False})


def tabela(df, **kw):
    """st.dataframe compativel com versoes novas e antigas do Streamlit."""
    try:
        st.dataframe(df, width="stretch", hide_index=True, **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True, **kw)


def kpis(itens):
    colunas = st.columns(len(itens))
    for col, (rotulo, valor, ajuda) in zip(colunas, itens):
        col.metric(rotulo, valor, help=ajuda)


def baixar(df, nome, rotulo="Baixar lista (CSV)"):
    st.download_button(
        rotulo, df.to_csv(index=False).encode("utf-8-sig"), file_name=nome, mime="text/csv",
    )


def curva_ganho(df, score, alvo):
    d = df.sort_values(score, ascending=False)
    total = d[alvo].sum()
    if total == 0 or len(d) < 2:
        return None
    cum = d[alvo].cumsum().to_numpy() / total
    idx = np.unique(np.linspace(0, len(d) - 1, 400).astype(int))
    return (idx + 1) / len(d), cum[idx]


# ----------------------------------------------------------------------------
# Cabecalho e barra lateral
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📊 CRM B2B Intelligence")
    marca = st.selectbox("Marca simulada", list(NOMES_MARCA), format_func=NOMES_MARCA.get)
    st.caption("Troque a marca: o mesmo pipeline processa as duas bases, sem alterar código.")

cli_marca = clientes[clientes["marca"] == marca].copy()
ped_marca = pedidos[pedidos["marca"] == marca].copy()

with st.sidebar:
    st.markdown("#### Filtros da carteira")
    seg_sel = st.multiselect("Segmento", ORDEM_SEGMENTOS, placeholder="Todos")
    risco_sel = st.multiselect("Faixa de risco", ["Alto", "Médio", "Baixo"], placeholder="Todas")
    local_sel = st.multiselect(
        "Localização", sorted(cli_marca["localizacao"].dropna().unique()), placeholder="Todas",
    )
    st.divider()
    st.caption("Dados públicos (Kaggle) usados para demonstração. Valores na moeda original de cada base.")

cf = cli_marca
if seg_sel:
    cf = cf[cf["segmento"].isin(seg_sel)]
if risco_sel:
    cf = cf[cf["faixa_risco"].isin(risco_sel)]
if local_sel:
    cf = cf[cf["localizacao"].isin(local_sel)]

st.title("Inteligência de CRM B2B")
st.markdown(
    f"""<span class="tag">{NOMES_MARCA[marca]}</span>
    <span class="tag">{fmt(len(cli_marca))} clientes</span>
    <span class="tag">{ped_marca['data_pedido'].min():%b/%Y} → {ped_marca['data_pedido'].max():%b/%Y}</span>
    <span class="tag">Demonstração com dados públicos</span>""",
    unsafe_allow_html=True,
)
if len(cf) != len(cli_marca):
    st.caption(f"Filtros ativos: {fmt(len(cf))} de {fmt(len(cli_marca))} clientes na seleção (abas Carteira, Mix e Ficha).")

abas = st.tabs([
    "Visão geral", "Carteira e churn", "Mix de produtos", "Leads", "Ficha do cliente", "Sobre o modelo",
])


# ----------------------------------------------------------------------------
# Aba 1 — Visao geral
# ----------------------------------------------------------------------------
def comparativo_marcas() -> pd.DataFrame:
    linhas = {}
    for m, nome in NOMES_MARCA.items():
        p = pedidos[pedidos["marca"] == m]
        c = clientes[clientes["marca"] == m]
        linhas[nome] = {
            "Clientes": fmt(len(c)),
            "Pedidos": fmt(len(p)),
            "Receita total": fmt(p["valor_total"].sum()),
            "Ticket médio por pedido": fmt(p["valor_total"].mean()),
            "Pedidos por cliente": fmt(len(p) / max(len(c), 1), 1),
            "Nota média": fmt(p["avaliacao_cliente"].mean(), 2),
            "Entrega média (dias)": fmt(p["tempo_entrega_dias"].mean(), 1),
            "Clientes em risco alto": f"{(c['faixa_risco'] == 'Alto').mean():.0%}",
            "Período": f"{p['data_pedido'].min():%m/%Y} a {p['data_pedido'].max():%m/%Y}",
        }
    return pd.DataFrame(linhas).reset_index().rename(columns={"index": "Indicador"})


with abas[0]:
    kpis([
        ("Clientes", fmt(len(cli_marca)), "Clientes únicos com pelo menos um pedido."),
        ("Pedidos", fmt(len(ped_marca)), None),
        ("Receita total", compacto(ped_marca["valor_total"].sum()), "Soma do valor final dos pedidos."),
        ("Ticket médio", fmt(ped_marca["valor_total"].mean()), "Valor médio por pedido."),
        ("Nota média", fmt(ped_marca["avaliacao_cliente"].mean(), 2), "Avaliação média dos clientes."),
        ("Entrega média", f"{fmt(ped_marca['tempo_entrega_dias'].mean(), 1)} dias", None),
    ])
    st.write("")

    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("##### Receita mensal")
        mensal = (
            ped_marca.assign(mes=ped_marca["data_pedido"].dt.to_period("M").dt.to_timestamp())
            .groupby("mes", as_index=False)["valor_total"].sum()
        )
        fig = px.area(mensal, x="mes", y="valor_total", color_discrete_sequence=[PALETA[0]])
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        grafico(estilizar(fig, legenda=False), "receita_mensal")
    with c2:
        st.markdown("##### Receita por categoria")
        cat = ped_marca.groupby("categoria_produto", as_index=False)["valor_total"].sum().sort_values("valor_total")
        fig = px.bar(cat, x="valor_total", y="categoria_produto", orientation="h", color_discrete_sequence=[PALETA[1]])
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        grafico(estilizar(fig, legenda=False), "receita_categoria")

    c3, c4 = st.columns([3, 2])
    with c3:
        st.markdown("##### Receita por localização")
        loc = (
            ped_marca.groupby("localizacao", as_index=False)["valor_total"].sum()
            .sort_values("valor_total", ascending=False).head(10)
        )
        fig = px.bar(loc, x="localizacao", y="valor_total", color_discrete_sequence=[PALETA[2]])
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        grafico(estilizar(fig, legenda=False), "receita_local")
    with c4:
        st.markdown("##### Forma de pagamento")
        pag = ped_marca["forma_pagamento"].value_counts().reset_index()
        pag.columns = ["forma", "pedidos"]
        fig = px.pie(pag, names="forma", values="pedidos", hole=0.55, color_discrete_sequence=PALETA)
        grafico(estilizar(fig), "pagamento")

    st.markdown("##### Comparativo entre marcas")
    st.caption("O mesmo pipeline gera os mesmos indicadores para cada marca, o que torna a comparação direta.")
    tabela(comparativo_marcas())


# ----------------------------------------------------------------------------
# Aba 2 — Carteira e churn
# ----------------------------------------------------------------------------
with abas[1]:
    if cf.empty:
        st.warning("Nenhum cliente com esses filtros.")
    else:
        alto = cf[cf["faixa_risco"] == "Alto"]
        kpis([
            ("Clientes na seleção", fmt(len(cf)), None),
            (f"Risco alto ({len(alto) / len(cf):.0%})", fmt(len(alto)),
             "Clientes que já passaram de 2x o intervalo habitual de recompra."),
            ("Valor em risco", compacto(cf["valor_em_risco"].sum()),
             "Soma de (valor histórico × quanto o cliente passou do ciclo de recompra, limitado a 3x)."),
            ("Atraso mediano", f"{cf['atraso_recompra'].median():.1f}x",
             "Dias sem comprar ÷ intervalo habitual do próprio cliente. Acima de 1x = fora do ciclo."),
            ("Receita da seleção", compacto(cf["valor_total"].sum()), None),
        ])
        st.write("")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Clientes por segmento")
            seg = (
                cf.groupby("segmento", as_index=False)
                .agg(clientes=("customer_id", "count"), receita=("valor_total", "sum"))
            )
            seg["segmento"] = pd.Categorical(seg["segmento"], ORDEM_SEGMENTOS, ordered=True)
            seg = seg.sort_values("segmento")
            fig = px.bar(
                seg, x="clientes", y="segmento", orientation="h", color="segmento",
                color_discrete_map=COR_SEGMENTO, text="clientes",
            )
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            fig.update_yaxes(categoryorder="array", categoryarray=ORDEM_SEGMENTOS[::-1])
            grafico(estilizar(fig, legenda=False), "segmentos")
        with c2:
            st.markdown("##### Receita por segmento")
            fig = px.pie(
                seg, names="segmento", values="receita", hole=0.55,
                color="segmento", color_discrete_map=COR_SEGMENTO,
            )
            grafico(estilizar(fig), "receita_segmento")

        c3, c4 = st.columns([2, 3])
        with c3:
            st.markdown("##### Faixas de risco")
            fr = cf["faixa_risco"].value_counts().reindex(["Alto", "Médio", "Baixo"]).fillna(0).reset_index()
            fr.columns = ["faixa", "clientes"]
            fig = px.bar(fr, x="faixa", y="clientes", color="faixa", color_discrete_map=COR_RISCO, text="clientes")
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            grafico(estilizar(fig, legenda=False), "faixas")
        with c4:
            st.markdown("##### Mapa da carteira: tempo sem comprar × frequência")
            amostra = cf if len(cf) <= 3000 else cf.sample(3000, random_state=1)
            fig = px.scatter(
                amostra, x="dias_sem_comprar", y="frequencia", color="faixa_risco",
                size="valor_total", size_max=18, opacity=0.65, color_discrete_map=COR_RISCO,
                hover_data={"customer_id": True, "segmento": True, "valor_total": ":.0f"},
                category_orders={"faixa_risco": ["Alto", "Médio", "Baixo"]},
                labels={"dias_sem_comprar": "Dias sem comprar", "frequencia": "Pedidos", "faixa_risco": "Risco"},
            )
            grafico(estilizar(fig), "mapa_carteira")

        st.markdown("##### Quem contatar primeiro")
        st.caption(
            "Ordenado por valor em risco: clientes de maior valor que mais passaram do próprio ciclo de recompra. "
            "A faixa de risco é uma regra explicável; a probabilidade do modelo aparece à parte "
            "(veja a aba Sobre o modelo antes de usá-la)."
        )
        n_top = st.slider("Quantos clientes listar", 10, 100, 20, step=5)
        lista = cf.sort_values("valor_em_risco", ascending=False)
        topo = lista.head(n_top)[[
            "customer_id", "segmento", "faixa_risco", "dias_sem_comprar", "atraso_recompra",
            "valor_total", "valor_em_risco", "prob_churn_modelo", "motivos",
        ]].copy()
        topo["prob_churn_modelo"] = (topo["prob_churn_modelo"] * 100).round(0)
        topo.columns = [
            "Cliente", "Segmento", "Risco", "Dias sem comprar", "Atraso (x ciclo)",
            "Valor total", "Valor em risco", "Prob. modelo (%)", "Fatores (modelo)",
        ]
        tabela(topo, column_config={
            "Atraso (x ciclo)": st.column_config.NumberColumn(format="%.1f"),
            "Valor total": st.column_config.NumberColumn(format="%.0f"),
            "Valor em risco": st.column_config.ProgressColumn(
                format="%.0f", min_value=0, max_value=float(max(topo["Valor em risco"].max(), 1)),
            ),
            "Prob. modelo (%)": st.column_config.NumberColumn(format="%.0f"),
        })
        baixar(lista, f"carteira_{marca}.csv", "Baixar carteira filtrada completa (CSV)")


# ----------------------------------------------------------------------------
# Aba 3 — Mix de produtos
# ----------------------------------------------------------------------------
with abas[2]:
    if cf.empty:
        st.warning("Nenhum cliente com esses filtros.")
    else:
        taxa = st.slider(
            "Conversão esperada das sugestões (%)", 1, 30, 5,
            help="Quantos % dos clientes sem a categoria devem comprá-la após uma ação comercial. Ajuste para simular cenários.",
        ) / 100

        ped_sel = ped_marca[ped_marca["customer_id"].isin(cf["customer_id"])]
        ticket_cat = ped_marca.groupby("categoria_produto")["valor_total"].mean()
        compradores = ped_sel.groupby("categoria_produto")["customer_id"].nunique()
        base_cat = pd.DataFrame({"ticket_medio": ticket_cat}).join(compradores.rename("compradores")).fillna(0)
        base_cat["penetracao"] = base_cat["compradores"] / len(cf)
        base_cat["sem_comprar"] = len(cf) - base_cat["compradores"]
        base_cat["potencial"] = base_cat["sem_comprar"] * base_cat["ticket_medio"] * taxa
        base_cat = base_cat.reset_index().rename(columns={"index": "categoria", "categoria_produto": "categoria"})

        mix_f = mix[mix["marca"] == marca].merge(
            cf[["customer_id", "segmento", "faixa_risco", "valor_total"]], on="customer_id",
        )
        mix_f["potencial_ajustado"] = mix_f["potencial_estimado"] * taxa

        kpis([
            ("Clientes com sugestão", fmt((mix_f["categorias_sugeridas"] != "já comprou de tudo").sum()), None),
            ("Potencial estimado", compacto(base_cat["potencial"].sum()),
             "Clientes sem a categoria × ticket médio da categoria × conversão esperada."),
            ("Categoria com maior potencial", base_cat.sort_values("potencial").iloc[-1]["categoria"], None),
            ("Penetração média", f"{base_cat['penetracao'].mean():.0%}", "% médio de clientes que já compraram cada categoria."),
        ])
        st.write("")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Penetração por categoria")
            d = base_cat.sort_values("penetracao")
            fig = px.bar(d, x="penetracao", y="categoria", orientation="h", color_discrete_sequence=[PALETA[0]])
            fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis_tickformat=".0%")
            grafico(estilizar(fig, legenda=False), "penetracao")
        with c2:
            st.markdown("##### Potencial por categoria")
            d = base_cat.sort_values("potencial")
            fig = px.bar(d, x="potencial", y="categoria", orientation="h", color_discrete_sequence=[PALETA[4]])
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            grafico(estilizar(fig, legenda=False), "potencial")

        st.markdown("##### Sugestões por cliente")
        st.caption("Regra: categorias mais vendidas da marca que o cliente ainda não comprou.")
        n_mix = st.slider("Quantos clientes listar", 10, 100, 20, step=5, key="n_mix")
        tabela_mix = mix_f.sort_values("potencial_ajustado", ascending=False).head(n_mix)[[
            "customer_id", "segmento", "valor_total", "categorias_sugeridas", "potencial_ajustado",
        ]].copy()
        tabela_mix.columns = ["Cliente", "Segmento", "Valor total", "Categorias sugeridas", "Potencial (ajustado)"]
        tabela(tabela_mix, column_config={
            "Valor total": st.column_config.NumberColumn(format="%.0f"),
            "Potencial (ajustado)": st.column_config.NumberColumn(format="%.0f"),
        })
        baixar(mix_f, f"mix_{marca}.csv", "Baixar sugestões completas (CSV)")


# ----------------------------------------------------------------------------
# Aba 4 — Leads
# ----------------------------------------------------------------------------
with abas[3]:
    st.info(
        "Esta base de leads é separada das marcas (não depende do seletor). O score vem de um modelo treinado em dados "
        "públicos sintéticos: o desempenho quase perfeito mostrado aqui reflete a natureza do dataset, "
        "não uma promessa para dados reais."
    )
    alvo = "Conversion (Target)"
    f1, f2, f3, f4 = st.columns(4)
    origem_sel = f1.multiselect("Origem do lead", sorted(leads["LeadSource"].unique()), placeholder="Todas")
    status_sel = f2.multiselect("Status", sorted(leads["LeadStatus"].unique()), placeholder="Todos")
    loc_lead_sel = f3.multiselect("Localização", sorted(leads["Location"].unique()), placeholder="Todas")
    score_min = f4.slider("Score mínimo", 0, 100, 0)

    lf = leads
    if origem_sel:
        lf = lf[lf["LeadSource"].isin(origem_sel)]
    if status_sel:
        lf = lf[lf["LeadStatus"].isin(status_sel)]
    if loc_lead_sel:
        lf = lf[lf["Location"].isin(loc_lead_sel)]
    lf = lf[lf["score_conversao"] >= score_min]

    if lf.empty:
        st.warning("Nenhum lead com esses filtros.")
    else:
        kpis([
            ("Leads", fmt(len(lf)), None),
            ("Conversão real", f"{lf[alvo].mean():.1%}", "% de leads que de fato converteram na base."),
            ("Score médio", fmt(lf["score_conversao"].mean(), 1), None),
            ("Leads com score ≥ 50", fmt((lf["score_conversao"] >= 50).sum()), None),
        ])
        st.write("")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Conversão por origem do lead")
            por_origem = lf.groupby("LeadSource", as_index=False)[alvo].mean().sort_values(alvo)
            fig = px.bar(por_origem, x=alvo, y="LeadSource", orientation="h", color_discrete_sequence=[PALETA[2]])
            fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis_tickformat=".1%")
            grafico(estilizar(fig, legenda=False), "conv_origem")
        with c2:
            st.markdown("##### Quanto a priorização captura")
            ganho = curva_ganho(lf, "score_conversao", alvo)
            if ganho is None:
                st.caption("Sem conversões na seleção para calcular a curva.")
            else:
                x, y = ganho
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name="Priorizando pelo score",
                                         line=dict(color=PALETA[4], width=3)))
                fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Contato aleatório",
                                         line=dict(color="#6B7280", dash="dash")))
                fig.update_layout(
                    xaxis_title="% de leads contatados (maior score primeiro)",
                    yaxis_title="% das conversões capturadas",
                    xaxis_tickformat=".0%", yaxis_tickformat=".0%",
                )
                grafico(estilizar(fig), "ganho")

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("##### Distribuição dos scores")
            fig = px.histogram(lf, x="score_conversao", nbins=25, color_discrete_sequence=[PALETA[0]])
            fig.update_yaxes(type="log")
            fig.update_layout(xaxis_title="Score", yaxis_title="Leads (escala log)")
            grafico(estilizar(fig, legenda=False), "hist_score")
        with c4:
            st.markdown("##### Conversão por status")
            por_status = lf.groupby("LeadStatus", as_index=False)[alvo].mean()
            fig = px.bar(por_status, x="LeadStatus", y=alvo, color_discrete_sequence=[PALETA[1]])
            fig.update_layout(xaxis_title=None, yaxis_title=None, yaxis_tickformat=".1%")
            grafico(estilizar(fig, legenda=False), "conv_status")

        st.markdown("##### Leads priorizados")
        n_leads = st.slider("Quantos leads listar", 10, 100, 20, step=5, key="n_leads")
        top = lf.sort_values("score_conversao", ascending=False).head(n_leads)[[
            "LeadID", "LeadSource", "LeadStatus", "Location", "DeviceType", "PagesViewed", "EmailSent", "score_conversao",
        ]].copy()
        top.columns = ["Lead", "Origem", "Status", "Cidade", "Dispositivo", "Páginas vistas", "E-mails enviados", "Score"]
        tabela(top, column_config={"Score": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=100)})
        baixar(lf.sort_values("score_conversao", ascending=False), "leads_priorizados.csv", "Baixar leads filtrados (CSV)")


# ----------------------------------------------------------------------------
# Aba 5 — Ficha do cliente
# ----------------------------------------------------------------------------
with abas[4]:
    if cf.empty:
        st.warning("Nenhum cliente com esses filtros.")
    else:
        ordenados = cf.sort_values("valor_em_risco", ascending=False)
        rotulos = dict(zip(ordenados["customer_id"], ordenados["customer_id"] + "  ·  " + ordenados["segmento"]))
        escolhido = st.selectbox(
            "Cliente (ordenado por valor em risco)", list(rotulos), format_func=rotulos.get,
        )
        c = cli_marca[cli_marca["customer_id"] == escolhido].iloc[0]
        historico = ped_marca[ped_marca["customer_id"] == escolhido].sort_values("data_pedido")

        kpis([
            ("Segmento", c["segmento"], None),
            ("Faixa de risco", c["faixa_risco"], "Regra: dias sem comprar ÷ intervalo habitual."),
            ("Atraso de recompra", f"{c['atraso_recompra']:.1f}x", None),
            ("Prob. do modelo", f"{c['prob_churn_modelo']:.0%}", "Veja a aba Sobre o modelo antes de confiar neste número."),
        ])
        st.write("")
        kpis([
            ("Valor total", fmt(c["valor_total"]), None),
            ("Pedidos", fmt(c["frequencia"]), None),
            ("Última compra", f"{c['ultima_compra']:%d/%m/%Y}", None),
            ("Dias sem comprar", fmt(c["dias_sem_comprar"]), None),
        ])
        st.write("")

        e1, e2 = st.columns([3, 2])
        with e1:
            st.markdown("##### Histórico de pedidos")
            fig = px.scatter(
                historico, x="data_pedido", y="valor_total", color="categoria_produto",
                size="valor_total", size_max=22, color_discrete_sequence=PALETA,
                labels={"data_pedido": "", "valor_total": "Valor do pedido", "categoria_produto": "Categoria"},
            )
            grafico(estilizar(fig), "historico_cliente")
        with e2:
            st.markdown("##### Leitura do cliente")
            if c["sem_intervalo"] == 1:
                st.markdown(
                    f"**Ciclo de recompra:** só 1 pedido; usando o ciclo mediano da marca (~{fmt(c['intervalo_dias'])} dias). "
                    f"Está há **{fmt(c['dias_sem_comprar'])} dias** sem comprar ({c['atraso_recompra']:.1f}x o ciclo)."
                )
            else:
                st.markdown(
                    f"**Ciclo de recompra:** costuma comprar a cada **{fmt(c['intervalo_dias'])} dias** e está há "
                    f"**{fmt(c['dias_sem_comprar'])} dias** sem comprar ({c['atraso_recompra']:.1f}x o ciclo)."
                )
            sug = mix[(mix["marca"] == marca) & (mix["customer_id"] == escolhido)]
            if not sug.empty:
                st.markdown(f"**Sugestão de mix:** {sug.iloc[0]['categorias_sugeridas']}")
            st.markdown(f"**Categorias compradas:** {', '.join(sorted(historico['categoria_produto'].unique()))}")
            st.markdown(f"**Localização:** {c['localizacao']}")
            st.markdown(f"**Nota média:** {c['nota_media']:.1f}  ·  **Entrega média:** {c['entrega_media']:.1f} dias")
            st.caption(f"Fatores segundo o modelo (baixa confiabilidade nestas bases): {c['motivos']}")

        hist = historico[[
            "data_pedido", "order_id", "categoria_produto", "quantidade", "preco_unitario", "desconto_valor", "valor_total",
        ]].copy()
        hist["data_pedido"] = hist["data_pedido"].dt.strftime("%d/%m/%Y")
        hist.columns = ["Data", "Pedido", "Categoria", "Qtd", "Preço unit.", "Desconto", "Valor total"]
        tabela(hist, column_config={
            "Preço unit.": st.column_config.NumberColumn(format="%.2f"),
            "Desconto": st.column_config.NumberColumn(format="%.2f"),
            "Valor total": st.column_config.NumberColumn(format="%.2f"),
        })


# ----------------------------------------------------------------------------
# Aba 6 — Sobre o modelo
# ----------------------------------------------------------------------------
with abas[5]:
    auc = metricas["auc"]
    leitura = metricas["leitura"]
    melhor = max(v for k, v in auc["regressao_logistica"].items() if k != "geral")

    mensagens = {
        "sem_sinal": (
            st.warning,
            f"Nestas bases o modelo não encontra sinal relevante de churn: o melhor AUC por marca é {melhor:.2f}, "
            "no nível de um baseline ingênuo. É esperado, porque são dados públicos sintéticos. O mecanismo está pronto; "
            "o resultado só passa a ter valor com dados reais.",
        ),
        "sinal_fraco": (st.info, f"O modelo encontra sinal fraco (melhor AUC por marca: {melhor:.2f})."),
        "sinal_moderado": (st.success, f"O modelo encontra sinal moderado (melhor AUC por marca: {melhor:.2f})."),
    }
    caixa, texto = mensagens[leitura]
    caixa(texto)

    m1, m2 = st.columns([3, 2])
    with m1:
        st.markdown("##### Como o churn é previsto")
        janela_a = metricas["janela"]["marca_a"]
        janela_b = metricas["janela"]["marca_b"]
        st.markdown(
            f"""
1. **Janela por marca:** 20% do período coberto pelos dados da própria marca
   (Marca A: {janela_a['janela_dias']} dias, Marca B: {janela_b['janela_dias']} dias). A mesma regra se adapta a cada ritmo de compra.
2. **Data de corte:** última data menos a janela. As variáveis usam **só pedidos até o corte**: frequência, valor, ticket,
   recência, intervalo entre compras, nota, entrega, desconto e variedade de categorias.
3. **Rótulo:** churn = o cliente **não comprou** na janela seguinte ao corte.
4. **Avaliação:** treino em 75% dos clientes, teste em 25%, medindo o AUC **por marca** e comparando com um baseline que usa só frequência.
5. **Pontuação:** as mesmas variáveis são calculadas na última data disponível para estimar o risco atual.
            """
        )
        st.caption(
            "Uma versão anterior calculava variáveis e rótulo na mesma janela e mostrava AUC de 0,81. Era um artefato: "
            "quem compra pouco tem última compra mais antiga por simples mecânica. Foi descartada."
        )
    with m2:
        st.markdown("##### AUC no conjunto de teste")
        linhas = []
        for nome, chave in [
            ("Regressão logística", "regressao_logistica"),
            ("Gradient boosting", "gradient_boosting"),
            ("Baseline (só frequência)", "baseline_so_frequencia"),
        ]:
            linhas.append({
                "Modelo": nome, "Geral": f"{auc[chave]['geral']:.2f}",
                "Marca A": f"{auc[chave]['marca_a']:.2f}", "Marca B": f"{auc[chave]['marca_b']:.2f}",
            })
        tabela(pd.DataFrame(linhas))
        st.caption("AUC 0,50 equivale a acertar no acaso. Clientes de teste: " + fmt(metricas["n_teste"]) + ".")

    st.markdown("##### Peso de cada variável no modelo")
    coef = pd.DataFrame({"variavel": list(metricas["coeficientes"]), "peso": list(metricas["coeficientes"].values())})
    coef["variavel"] = coef["variavel"].map(NOMES_VARIAVEIS).fillna(coef["variavel"])
    coef["abs"] = coef["peso"].abs()
    coef = coef.sort_values("abs").tail(13)
    coef["efeito"] = np.where(coef["peso"] > 0, "Aumenta o risco", "Reduz o risco")
    fig = px.bar(
        coef, x="peso", y="variavel", orientation="h", color="efeito",
        color_discrete_map={"Aumenta o risco": "#F43F5E", "Reduz o risco": "#34D399"},
    )
    fig.update_layout(xaxis_title="Coeficiente (variáveis padronizadas)", yaxis_title=None)
    grafico(estilizar(fig, altura=380), "coeficientes")

    st.markdown("##### O que seria diferente com dados reais")
    st.markdown(
        """
- Basta escrever uma função de padronização para a nova base; segmentos, risco, mix, leads e este painel funcionam sem alteração.
- O modelo é treinado de novo e reavaliado, e o AUC por marca decide se ele entra em uso ou se a regra de atraso de recompra basta.
- A janela (20% do período), os limites de risco (1x e 2x o ciclo) e a conversão esperada do mix são parâmetros ajustáveis pela área comercial.
        """
    )
