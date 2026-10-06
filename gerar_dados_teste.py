"""
Gera um relatorio.xlsx de exemplo (dados fictícios) só para você testar
o assistente hoje, sem depender do relatório real da empresa ainda.
"""
import pandas as pd
import numpy as np

np.random.seed(42)  # sempre gera os mesmos números "aleatórios" (facilita testar)

produtos = ["Notebook", "Mouse", "Teclado", "Monitor", "Headset"]
regioes = ["Sul", "Sudeste", "Nordeste", "Norte", "Centro-Oeste"]
meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto"]

linhas = []
for mes in meses:
    for _ in range(15):  # 15 vendas por mês
        linhas.append({
            "Mes": mes,
            "Produto": np.random.choice(produtos),
            "Regiao": np.random.choice(regioes),
            "Quantidade": np.random.randint(1, 20),
            "Valor_Unitario": round(np.random.uniform(50, 3000), 2),
        })

df = pd.DataFrame(linhas)
df["Faturamento"] = df["Quantidade"] * df["Valor_Unitario"]

df.to_excel("relatorio.xlsx", index=False, sheet_name="Vendas")
print(f"Criado relatorio.xlsx com {len(df)} linhas.")
print(df.head())
