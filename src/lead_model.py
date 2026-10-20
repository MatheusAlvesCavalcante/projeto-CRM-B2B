"""
Modelo de priorizacao de leads.

ACHADO IMPORTANTE (documentado em detalhe em docs/definicao_leads.md):
os modelos baseados em arvore (Random Forest, Gradient Boosting) atingem
~100% de acerto nesta base. Isso NAO significa que o problema e "facil" --
significa que o dataset e sintetico, gerado por uma combinacao fixa e
deterministica de poucas variaveis (confirmado: uma arvore de decisao com
so 10 niveis de profundidade ja memoriza 100% dos 100 mil registros).
Isso nao acontece em dados reais, que sempre tem ruido.

Decisao: usar Gradient Boosting para a demonstracao (melhor desempenho),
mas deixar claro na apresentacao que o numero de 100% reflete a natureza
sintetica do dataset publico, nao uma promessa de desempenho em producao
com dados reais da Gobeaute.
"""
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
import joblib

CATEGORICAS = ["Gender", "Location", "LeadSource", "LeadStatus", "DeviceType", "ReferralSource", "PaymentHistory"]
ALVO = "Conversion (Target)"


def preparar_dados(df_train: pd.DataFrame, df_test: pd.DataFrame):
    X_train = pd.get_dummies(df_train.drop(columns=["LeadID", ALVO]), columns=CATEGORICAS)
    X_test = pd.get_dummies(df_test.drop(columns=["LeadID", ALVO]), columns=CATEGORICAS)
    X_train, X_test = X_train.align(X_test, join="left", axis=1, fill_value=0)
    return X_train, df_train[ALVO], X_test, df_test[ALVO]


def treinar_modelo_leads(df_train: pd.DataFrame, df_test: pd.DataFrame):
    X_train, y_train, X_test, y_test = preparar_dados(df_train, df_test)
    modelo = GradientBoostingClassifier(n_estimators=200, random_state=42)
    modelo.fit(X_train, y_train)
    return modelo, list(X_train.columns)


def pontuar_leads(df: pd.DataFrame, modelo, colunas_treino) -> pd.DataFrame:
    """Adiciona a coluna score_conversao (0-100) para cada lead."""
    X = pd.get_dummies(df.drop(columns=["LeadID", ALVO]) if ALVO in df.columns else df.drop(columns=["LeadID"]),
                        columns=CATEGORICAS)
    X = X.reindex(columns=colunas_treino, fill_value=0)
    df = df.copy()
    df["score_conversao"] = (modelo.predict_proba(X)[:, 1] * 100).round(1)
    return df


if __name__ == "__main__":
    df_train = pd.read_csv("data/raw/customer_conversion_traing_dataset_.csv")
    df_test = pd.read_csv("data/raw/customer_conversion_testing_dataset.csv")

    modelo, colunas = treinar_modelo_leads(df_train, df_test)
    leads_pontuados = pontuar_leads(df_test, modelo, colunas)
    ranking = leads_pontuados.sort_values("score_conversao", ascending=False)

    ranking.to_csv("data/processed/leads_priorizados.csv", index=False)
    joblib.dump({"modelo": modelo, "colunas": colunas}, "data/processed/modelo_leads.joblib")
    print(ranking[["LeadID", "score_conversao", "Conversion (Target)"]].head(10))
    print("Modelo salvo em data/processed/modelo_leads.joblib")
