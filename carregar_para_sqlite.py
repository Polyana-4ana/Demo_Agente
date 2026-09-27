"""
Sprint 4 - Carregar planilhas (Excel e/ou exports do Power BI em CSV)
para um banco SQLite local. Um banco de tabelas é o formato mais fácil
para a LLM escrever consultas SQL confiáveis.
"""
import pandas as pd
import sqlite3
from pathlib import Path

PASTA_RELATORIOS = "./relatorios"   # coloque aqui seus .xlsx e .csv
BANCO = "relatorios.db"


def nome_tabela_valido(nome: str) -> str:
    """SQL não gosta de espaços/acentos em nome de tabela; troca por _"""
    return "".join(c if c.isalnum() else "_" for c in nome)


def carregar_arquivo(caminho: Path, conexao):
    if caminho.suffix.lower() in (".xlsx", ".xls"):
        abas = pd.read_excel(caminho, sheet_name=None)
        for nome_aba, tabela in abas.items():
            nome_tabela = nome_tabela_valido(f"{caminho.stem}_{nome_aba}")
            tabela.to_sql(nome_tabela, conexao, if_exists="replace", index=False)
            print(f"  Tabela criada: {nome_tabela} ({len(tabela)} linhas)")
    elif caminho.suffix.lower() == ".csv":
        tabela = pd.read_csv(caminho)
        nome_tabela = nome_tabela_valido(caminho.stem)
        tabela.to_sql(nome_tabela, conexao, if_exists="replace", index=False)
        print(f"  Tabela criada: {nome_tabela} ({len(tabela)} linhas)")


def main():
    conexao = sqlite3.connect(BANCO)
    arquivos = list(Path(PASTA_RELATORIOS).glob("*.xlsx")) + \
               list(Path(PASTA_RELATORIOS).glob("*.csv"))

    if not arquivos:
        print(f"Nenhum arquivo encontrado em {PASTA_RELATORIOS}/. "
              f"Coloque seus .xlsx ou .csv (exportados do Power BI) lá.")
        return

    for arquivo in arquivos:
        print(f"Lendo {arquivo.name}...")
        carregar_arquivo(arquivo, conexao)

    conexao.close()
    print(f"\nBanco pronto: {BANCO}")


if __name__ == "__main__":
    main()
