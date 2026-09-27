"""
Sprint 4 - Chat texto-para-SQL, 100% local (Ollama), sem API externa.
O gestor pergunta em português, o modelo local escreve um SELECT,
e o SQLite executa. A LLM nunca modifica dados: só SELECT é permitido.

Antes de rodar:
  1) Instalar o Ollama: https://ollama.com
  2) ollama pull qwen2.5-coder:3b   (bom em SQL e leve o suficiente pra CPU)
  3) Colocar os arquivos .xlsx/.csv em ./relatorios/
  4) python carregar_para_sqlite.py
  5) python chat_sql.py
"""
import sqlite3
import requests

BANCO = "relatorios.db"
MODELO_OLLAMA = "qwen2.5-coder:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Palavras que NUNCA podem aparecer no SQL gerado (trava de segurança)
PALAVRAS_PROIBIDAS = ["drop", "delete", "update", "insert", "alter", "attach", "pragma"]


def obter_schema(conexao) -> str:
    """Monta a descrição das tabelas para a LLM saber o que existe."""
    cursor = conexao.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = [linha[0] for linha in cursor.fetchall()]

    descricao = []
    for tabela in tabelas:
        colunas = conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
        nomes_colunas = ", ".join(c[1] for c in colunas)
        descricao.append(f"Tabela {tabela}: colunas ({nomes_colunas})")
    return "\n".join(descricao)


def gerar_sql(pergunta: str, schema: str) -> str:
    prompt = f"""Você escreve consultas SQLite. Aqui estão as tabelas disponíveis:

{schema}

Escreva APENAS um comando SELECT (nada de explicação, nada de markdown,
nada de ```) que responda à pergunta abaixo, usando só as tabelas e colunas
listadas acima.

Pergunta: {pergunta}
SQL:"""
    resposta = requests.post(
        OLLAMA_URL,
        json={"model": MODELO_OLLAMA, "prompt": prompt, "stream": False},
        timeout=120,
    )
    resposta.raise_for_status()
    sql = resposta.json()["response"].strip()
    return sql.replace("```sql", "").replace("```", "").strip()


def sql_e_seguro(sql: str) -> bool:
    sql_minusculo = sql.lower()
    if not sql_minusculo.strip().startswith("select"):
        return False
    return not any(palavra in sql_minusculo for palavra in PALAVRAS_PROIBIDAS)


def main():
    conexao = sqlite3.connect(BANCO)
    schema = obter_schema(conexao)

    print("Chat SQL local pronto (100% offline). Digite 'sair' para encerrar.\n")
    while True:
        pergunta = input("Pergunta: ").strip()
        if pergunta.lower() == "sair":
            break

        sql = gerar_sql(pergunta, schema)
        print(f"  [SQL gerado: {sql}]")

        if not sql_e_seguro(sql):
            print("Esse comando não é permitido (só consultas de leitura). Reformule a pergunta.\n")
            continue

        try:
            resultado = conexao.execute(sql).fetchall()
            print(f"Resposta: {resultado}\n")
        except Exception as e:
            print(f"O SQL gerado deu erro ({e}). Tente reformular a pergunta.\n")

    conexao.close()


if __name__ == "__main__":
    main()
