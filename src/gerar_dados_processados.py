"""
Roda o pipeline completo do zero: le os CSVs brutos, padroniza, agrega por
cliente e define churn. Salva tudo em data/processed/.

Rodar a partir da raiz do projeto: python src/gerar_dados_processados.py
"""
import pandas as pd
from pipeline import rodar_pipeline, agregar_por_cliente, definir_churn

if __name__ == "__main__":
    marca_a = rodar_pipeline("data/raw/ecommerce_customer_behavior_dataset_v2.csv", "marca_a")
    marca_b = rodar_pipeline("data/raw/ecommerce_sales_analytics_5000.csv", "marca_b")
    dados = pd.concat([marca_a, marca_b], ignore_index=True)

    por_cliente = agregar_por_cliente(dados)
    por_cliente = definir_churn(por_cliente, percentil=0.75)

    marca_a.to_csv("data/processed/marca_a.csv", index=False)
    marca_b.to_csv("data/processed/marca_b.csv", index=False)
    dados.to_csv("data/processed/dados_unificados.csv", index=False)
    por_cliente.to_csv("data/processed/por_cliente.csv", index=False)

    print("Balanceamento de churn por marca:")
    print(por_cliente.groupby("marca")["churn"].value_counts(normalize=True))
    print("\nArquivos salvos em data/processed/")
