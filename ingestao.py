"""
Sprint 3 - Ingestão (100% local, sem API externa)
Lê o relatório, transforma cada linha em uma frase e guarda os vetores
num banco de dados local (ChromaDB, salvo em disco, nada sai da máquina).
"""
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb

# Modelo de embedding: baixa uma vez da internet (só os "pesos" do modelo,
# nenhum dado seu), depois roda 100% offline.
MODELO_EMBEDDING = "paraphrase-multilingual-MiniLM-L12-v2"
ARQUIVO = "relatorio.xlsx"
PASTA_BANCO = "./banco_vetorial"


def linha_para_texto(linha, colunas):
    """Transforma uma linha da planilha numa frase, para poder buscar por significado."""
    partes = [f"{col}: {linha[col]}" for col in colunas]
    return "Registro -> " + "; ".join(partes)


def montar_chunks(arquivo):
    abas = pd.read_excel(arquivo, sheet_name=None)
    chunks = []
    for tabela in abas.values():
        colunas = tabela.columns.tolist()
        for _, linha in tabela.iterrows():
            chunks.append(linha_para_texto(linha, colunas))
    return chunks


def main():
    chunks = montar_chunks(ARQUIVO)
    print(f"{len(chunks)} registros convertidos em texto.")

    modelo = SentenceTransformer(MODELO_EMBEDDING)
    vetores = modelo.encode(chunks).tolist()

    cliente = chromadb.PersistentClient(path=PASTA_BANCO)
    colecao = cliente.get_or_create_collection("relatorios")

    # Limpa execuções anteriores para não duplicar ao rodar de novo
    ids_existentes = colecao.get()["ids"]
    if ids_existentes:
        colecao.delete(ids=ids_existentes)

    colecao.add(
        ids=[str(i) for i in range(len(chunks))],
        documents=chunks,
        embeddings=vetores,
    )
    print(f"Banco vetorial criado em {PASTA_BANCO}")


if __name__ == "__main__":
    main()
