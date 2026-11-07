"""
Modelo de churn (versao 2: com data de corte) + pontuacao da carteira.

O que mudou em relacao a versao 1 (ver docs/revisao_churn_v2.md):
- A v1 calculava features e rotulo na MESMA janela de tempo. O AUC de 0.81 era um
  artefato mecanico (quem tem poucos pedidos tem ultima compra mais antiga), nao previsao.
- A v2 usa uma data de corte: features so com o passado, rotulo = "nao comprou depois".
- A avaliacao e feita por marca, com baseline simples, e o resultado e salvo em JSON
  para o dashboard mostrar com transparencia.

Saidas em data/processed/:
- clientes_scoring.csv   (uma linha por cliente: segmento, risco, prioridade, motivos)
- metricas_churn.json    (metricas e leitura honesta do resultado)
- modelo_churn.joblib    (modelo treinado)

Rodar da raiz do projeto: python src/churn_model.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from features import (
    FEATURES, FRACAO_JANELA, TEXTO_FATORES, construir_features, faixa_de_risco,
    janela_da_marca, montar_base_treino, segmentar_rfm,
)

RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = RAIZ / "data" / "processed"


def carregar_dados() -> pd.DataFrame:
    return pd.read_csv(
        PROCESSED / "dados_unificados.csv",
        dtype={"customer_id": str},
        parse_dates=["data_pedido"],
    )


def _auc_seguro(y, p) -> float:
    return float(roc_auc_score(y, p)) if len(set(y)) > 1 else float("nan")


def avaliar(base: pd.DataFrame) -> dict:
    """Treina em 75% dos clientes e mede em 25%, geral e por marca."""
    y = base["churn"]
    estrato = base["marca"] + "_" + y.astype(str)
    idx_tr, idx_te = train_test_split(base.index, test_size=0.25, random_state=42, stratify=estrato)

    X_tr, X_te = base.loc[idx_tr, FEATURES], base.loc[idx_te, FEATURES]
    y_tr, y_te = y.loc[idx_tr], y.loc[idx_te]
    marcas_te = base.loc[idx_te, "marca"]

    scaler = StandardScaler().fit(X_tr)
    lr = LogisticRegression(max_iter=2000, class_weight="balanced").fit(scaler.transform(X_tr), y_tr)
    p_lr = lr.predict_proba(scaler.transform(X_te))[:, 1]

    gb = GradientBoostingClassifier(random_state=42).fit(X_tr, y_tr)
    p_gb = gb.predict_proba(X_te)[:, 1]

    # baseline ingenuo: so a frequencia de compra
    bl = LogisticRegression(max_iter=1000).fit(X_tr[["frequencia"]], y_tr)
    p_bl = bl.predict_proba(X_te[["frequencia"]])[:, 1]

    def por_marca(p):
        out = {"geral": _auc_seguro(y_te, p)}
        for m in sorted(marcas_te.unique()):
            mask = (marcas_te == m).values
            out[m] = _auc_seguro(y_te[mask], p[mask])
        return out

    pred = (p_lr >= 0.5).astype(int)
    return {
        "n_treino": int(len(idx_tr)),
        "n_teste": int(len(idx_te)),
        "auc": {
            "regressao_logistica": por_marca(p_lr),
            "gradient_boosting": por_marca(p_gb),
            "baseline_so_frequencia": por_marca(p_bl),
        },
        "precisao_churn_lr": float(precision_score(y_te, pred, zero_division=0)),
        "recall_churn_lr": float(recall_score(y_te, pred, zero_division=0)),
    }


def treinar_final(base: pd.DataFrame):
    scaler = StandardScaler().fit(base[FEATURES])
    modelo = LogisticRegression(max_iter=2000, class_weight="balanced")
    modelo.fit(scaler.transform(base[FEATURES]), base["churn"])
    return modelo, scaler


def leitura_do_resultado(auc_por_marca: dict) -> str:
    melhor = max(v for k, v in auc_por_marca.items() if k != "geral" and not np.isnan(v))
    if melhor < 0.60:
        return "sem_sinal"
    if melhor < 0.70:
        return "sinal_fraco"
    return "sinal_moderado"


def pontuar_carteira(dados: pd.DataFrame, modelo, scaler, fracao: float = FRACAO_JANELA) -> pd.DataFrame:
    """Calcula as mesmas features na ultima data de cada marca e pontua cada cliente."""
    partes = []
    for marca, dm in dados.groupby("marca"):
        janela = janela_da_marca(dm, fracao)
        f = construir_features(dm, dm["data_pedido"].max(), janela)
        f["marca"] = marca
        partes.append(f.reset_index())
    cli = pd.concat(partes, ignore_index=True)

    Xs = scaler.transform(cli[FEATURES])
    cli["prob_churn_modelo"] = modelo.predict_proba(Xs)[:, 1]

    # motivos: os 2 fatores que mais empurram o risco para cima neste cliente
    contrib = Xs * modelo.coef_[0]
    ordem = np.argsort(-contrib, axis=1)[:, :2]
    motivos = []
    for i in range(len(cli)):
        textos = []
        for j in ordem[i]:
            if contrib[i, j] > 0.05:
                alto, baixo = TEXTO_FATORES[FEATURES[j]]
                textos.append(alto if Xs[i, j] > 0 else baixo)
        motivos.append(" · ".join(textos) if textos else "Sem fatores de risco relevantes")
    cli["motivos"] = motivos

    cli["faixa_risco"] = faixa_de_risco(cli["atraso_recompra"])
    cli["segmento"] = segmentar_rfm(cli)
    # prioridade de contato: valor do cliente x quanto ele passou do ciclo (limitado a 3x)
    cli["valor_em_risco"] = cli["valor_total"] * (cli["atraso_recompra"].clip(upper=3) / 3)

    colunas = [
        "marca", "customer_id", "localizacao", "categoria_favorita", "frequencia",
        "valor_total", "ticket_medio", "primeira_compra", "ultima_compra",
        "dias_sem_comprar", "intervalo_dias", "atraso_recompra", "nota_media",
        "entrega_media", "categorias_distintas", "segmento", "faixa_risco",
        "prob_churn_modelo", "valor_em_risco", "motivos", "sem_intervalo",
    ]
    return cli[colunas]


def main():
    dados = carregar_dados()
    base, info_janela = montar_base_treino(dados)

    metricas = avaliar(base)
    metricas["janela"] = info_janela
    metricas["leitura"] = leitura_do_resultado(metricas["auc"]["regressao_logistica"])

    modelo, scaler = treinar_final(base)
    metricas["coeficientes"] = {f: float(c) for f, c in zip(FEATURES, modelo.coef_[0])}

    clientes = pontuar_carteira(dados, modelo, scaler)
    clientes.to_csv(PROCESSED / "clientes_scoring.csv", index=False)
    joblib.dump({"modelo": modelo, "scaler": scaler, "features": FEATURES}, PROCESSED / "modelo_churn.joblib")
    with open(PROCESSED / "metricas_churn.json", "w", encoding="utf-8") as fh:
        json.dump(metricas, fh, ensure_ascii=False, indent=2)

    print("Janela por marca:", json.dumps(info_janela, ensure_ascii=False))
    print("AUC (teste):", json.dumps(metricas["auc"], indent=2))
    print("Leitura:", metricas["leitura"])
    print("\nFaixas de risco por marca:")
    print(pd.crosstab(clientes["marca"], clientes["faixa_risco"], normalize="index").round(3))
    print("\nSegmentos por marca:")
    print(pd.crosstab(clientes["marca"], clientes["segmento"]))
    print("\nSalvo em data/processed/: clientes_scoring.csv, metricas_churn.json, modelo_churn.joblib")


if __name__ == "__main__":
    main()
