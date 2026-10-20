"""
Modelo de churn.

Decisao de modelo: Regressao Logistica, apesar de ter ROC AUC um pouco menor
que Gradient Boosting (0.811 vs 0.833), foi escolhida porque tem o melhor
RECALL para a classe churn=1 (0.738 vs ~0.48). Ver docs/comparativo_modelos_churn.md
para a tabela completa e o racional de negocio por tras dessa escolha.

Features usadas: total_pedidos, total_gasto, ticket_medio, categorias_distintas,
intervalo_medio_compra, marca (one-hot).

IMPORTANTE: dias_desde_ultima_compra e limite_churn_dias NAO entram como
features -- foram usadas para CRIAR o alvo (churn), entao usa-las de novo
seria vazamento de dados (data leakage): o modelo aprenderia a formula do
rotulo em vez de padroes reais de comportamento.
"""
import sys
sys.path.append("..")
sys.path.append("src")
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score
import joblib

FEATURES = ["total_pedidos", "total_gasto", "ticket_medio", "categorias_distintas", "intervalo_medio_compra"]


def preparar_dados(por_cliente: pd.DataFrame):
    X = pd.get_dummies(por_cliente[FEATURES + ["marca"]], columns=["marca"], drop_first=True)
    y = por_cliente["churn"]
    return X, y


def treinar_modelo_churn(por_cliente: pd.DataFrame):
    X, y = preparar_dados(por_cliente)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    modelo = LogisticRegression(max_iter=1000, class_weight="balanced")
    modelo.fit(X_train_s, y_train)

    pred = modelo.predict(X_test_s)
    proba = modelo.predict_proba(X_test_s)[:, 1]

    print("ROC AUC:", round(roc_auc_score(y_test, proba), 3))
    print(classification_report(y_test, pred))

    return modelo, scaler, list(X.columns)


def prever_risco_churn(por_cliente: pd.DataFrame, modelo, scaler, colunas_treino) -> pd.DataFrame:
    """Adiciona a coluna risco_churn (probabilidade 0-1) para cada cliente."""
    X, _ = preparar_dados(por_cliente)
    X = X.reindex(columns=colunas_treino, fill_value=0)
    X_s = scaler.transform(X)
    por_cliente = por_cliente.copy()
    por_cliente["risco_churn"] = modelo.predict_proba(X_s)[:, 1]
    return por_cliente


if __name__ == "__main__":
    por_cliente = pd.read_csv("data/processed/por_cliente.csv")
    modelo, scaler, colunas = treinar_modelo_churn(por_cliente)
    resultado = prever_risco_churn(por_cliente, modelo, scaler, colunas)
    resultado.to_csv("data/processed/por_cliente_com_risco.csv", index=False)
    joblib.dump({"modelo": modelo, "scaler": scaler, "colunas": colunas}, "data/processed/modelo_churn.joblib")
    print("Modelo salvo em data/processed/modelo_churn.joblib")
