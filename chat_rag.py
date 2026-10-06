"""
Sprint 3 - Chat RAG 100% local
Nenhuma pergunta ou dado sai da máquina: embeddings locais (sentence-transformers)
+ LLM local via Ollama (http://localhost:11434), sem nenhuma API externa.

Antes de rodar:
  1) Instalar o Ollama: https://ollama.com
  2) No terminal: ollama pull llama3.2   (ou outro modelo que a empresa aprove)
  3) python ingestao.py   (cria o banco vetorial a partir do relatorio.xlsx)
  4) python chat_rag.py
"""
import requests
from sentence_transformers import SentenceTransformer
import chromadb

MODELO_EMBEDDING = "paraphrase-multilingual-MiniLM-L12-v2"
MODELO_OLLAMA = "llama3.2"          # troque pelo nome do modelo que você baixou
OLLAMA_URL = "http://localhost:11434/api/generate"
PASTA_BANCO = "./banco_vetorial"

modelo_embedding = SentenceTransformer(MODELO_EMBEDDING)
cliente = chromadb.PersistentClient(path=PASTA_BANCO)
colecao = cliente.get_collection("relatorios")


def buscar_contexto(pergunta: str, n: int = 5):
    """Acha os N registros mais parecidos com a pergunta (busca por significado)."""
    vetor_pergunta = modelo_embedding.encode([pergunta]).tolist()
    resultado = colecao.query(query_embeddings=vetor_pergunta, n_results=n)
    return resultado["documents"][0]


def perguntar_ao_modelo_local(pergunta: str, contexto: list[str]) -> str:
    texto_contexto = "\n".join(contexto)
    prompt = f"""Use APENAS as informações abaixo para responder.
Se a resposta não estiver nas informações, diga que não encontrou no relatório.
Não invente números.

Informações:
{texto_contexto}

Pergunta: {pergunta}
Resposta:"""
    resposta = requests.post(
        OLLAMA_URL,
        json={"model": MODELO_OLLAMA, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resposta.raise_for_status()
    return resposta.json()["response"].strip()


if __name__ == "__main__":
    print("Chat RAG local pronto (100% offline). Digite 'sair' para encerrar.\n")
    while True:
        pergunta = input("Pergunta: ").strip()
        if pergunta.lower() == "sair":
            break
        contexto = buscar_contexto(pergunta)
        print("  [registros usados como base]:")
        for c in contexto[:2]:
            print(f"    - {c[:100]}...")
        resposta = perguntar_ao_modelo_local(pergunta, contexto)
        print(f"Resposta: {resposta}\n")
