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
import re

BANCO = "relatorios.db"
MODELO_OLLAMA = "qwen2.5-coder:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Palavras que NUNCA podem aparecer no SQL gerado (trava de segurança)
PALAVRAS_PROIBIDAS = ["drop", "delete", "update", "insert", "alter", "attach", "pragma"]


def listar_tabelas(conexao) -> list:
    """Lista só os NOMES das tabelas reais do banco (usado para validar o SQL gerado)."""
    cursor = conexao.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return [linha[0] for linha in cursor.fetchall()]


def obter_schema(conexao) -> str:
    """Monta a descrição das tabelas para a LLM saber o que existe."""
    descricao = []
    for tabela in listar_tabelas(conexao):
        colunas = conexao.execute(f"PRAGMA table_info({tabela})").fetchall()
        nomes_colunas = ", ".join(c[1] for c in colunas)
        descricao.append(f"Tabela {tabela}: colunas ({nomes_colunas})")
    return "\n".join(descricao)


def gerar_sql(pergunta: str, schema: str) -> str:
    prompt = f"""Você escreve consultas SQLite. Aqui estão as ÚNICAS tabelas e colunas
que existem de verdade no banco:

{schema}

REGRAS OBRIGATÓRIAS:
- Use SOMENTE as tabelas e colunas listadas acima, exatamente com esses nomes.
- NUNCA invente, adivinhe ou use nomes de tabela/coluna que não estejam na lista,
  mesmo que pareçam nomes comuns (ex.: não existe tabela "vendas" se ela não
  aparecer acima — o nome real pode ser diferente).
- Se a pergunta não puder ser respondida com as tabelas acima, responda apenas:
  SELECT 'PERGUNTA_FORA_DOS_DADOS_DISPONIVEIS' AS aviso

Escreva APENAS um comando SELECT (nada de explicação, nada de markdown,
nada de ```).

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

def extrair_tabelas_usadas(sql: str) -> list:
    """Acha todo nome de tabela que aparece depois de FROM ou JOIN no SQL gerado."""
    padrao = r'(?:FROM|JOIN)\s+["\']?(\w+)["\']?'
    return re.findall(padrao, sql, re.IGNORECASE)


def tabelas_sao_validas(sql: str, tabelas_reais: list):
    """
    Confere se a IA usou só tabelas que existem de verdade no banco.
    Pega a 'alucinação' (tabela inventada) ANTES de tentar rodar o SQL.
    """
    usadas = extrair_tabelas_usadas(sql)
    tabelas_reais_lower = [t.lower() for t in tabelas_reais]
    for tabela in usadas:
        if tabela.lower() not in tabelas_reais_lower:
            return False, tabela
    return True, None

def main():
    conexao = sqlite3.connect(BANCO)
    schema = obter_schema(conexao)

    tabelas_reais = listar_tabelas(conexao)
    print(f"Tabelas reais no banco: {tabelas_reais}\n")

    print("Chat SQL local pronto (100% offline). Digite 'sair' para encerrar.\n")
    while True:
        pergunta = input("Pergunta: ").strip()
        if pergunta.lower() == "sair":
            break

        sql = gerar_sql(pergunta, schema)
        print(f"  [SQL gerado: {sql}]")

        if not sql_e_seguro(sql):
            print("  [BLOQUEADO] Comando não é uma consulta de leitura permitida.\n")
            continue

        valido, tabela_invalida = tabelas_sao_validas(sql, tabelas_reais)
        if not valido:
            print(f"  [BLOQUEADO] A IA tentou usar a tabela '{tabela_invalida}', "
                  f"que NÃO existe no banco. Isso evita uma resposta inventada.\n")
            continue

        try:
            resultado = conexao.execute(sql).fetchall()
            print(f"  [EXECUTADO COM SUCESSO] Resposta: {resultado}\n")
        except Exception as e:
            print(f"  [ERRO AO EXECUTAR] {e}. Tente reformular a pergunta.\n")

    conexao.close()


if __name__ == "__main__":
    main()
