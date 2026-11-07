"""
Roda o projeto inteiro, do zero, na ordem certa.

Uso (da raiz do projeto):  python src/rodar_tudo.py
Depois:                    streamlit run dashboard/app.py
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASSOS = [
    ("Padronizando as bases e gerando dados unificados", "src/gerar_dados_processados.py"),
    ("Treinando e pontuando o churn", "src/churn_model.py"),
    ("Pontuando os leads", "src/lead_model.py"),
    ("Gerando sugestões de mix", "src/mix_model.py"),
]

if __name__ == "__main__":
    for i, (titulo, script) in enumerate(PASSOS, start=1):
        print(f"\n[{i}/{len(PASSOS)}] {titulo}...")
        resultado = subprocess.run([sys.executable, script], cwd=RAIZ)
        if resultado.returncode != 0:
            print(f"\nFalhou em {script}. Confira se os CSVs brutos estão em data/raw/ (veja data/raw/README.md).")
            sys.exit(resultado.returncode)
    print("\nTudo pronto. Abra o dashboard com:  streamlit run dashboard/app.py")
