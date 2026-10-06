"""
Assistente de relatórios: o gestor pergunta em português,
a LLM escreve o código pandas para responder, e o PYTHON executa
esse código — a LLM nunca "inventa" o número, ela só escreve a conta.

Antes de rodar:
  1) pip install pandas openpyxl anthropic
  2) export ANTHROPIC_API_KEY="sua_chave_aqui"
  3) python gerar_dados_teste.py   (cria o relatorio.xlsx de teste)
  4) python assistente.py
"""
import pandas as pd
from anthropic import Anthropic

ARQUIVO = "relatorio.xlsx"

# ---------------------------------------------------------------
# 1) Carregar a planilha (todas as abas viram um dicionário)
# ---------------------------------------------------------------
abas = pd.read_excel(ARQUIVO, sheet_name=None)

# ---------------------------------------------------------------
# 2) Montar um "resumo" da planilha para a LLM entender a estrutura
#    sem que a gente precise mandar os dados todos (mais barato e mais seguro)
# ---------------------------------------------------------------
def resumir_aba(nome, tabela):
    colunas = ", ".join(f"{c} ({t})" for c, t in tabela.dtypes.items())
    exemplo = tabela.head(3).to_string(index=False)
    return f"Aba '{nome}': colunas -> {colunas}\nExemplo de linhas:\n{exemplo}"

resumo = "\n\n".join(resumir_aba(n, t) for n, t in abas.items())

# ---------------------------------------------------------------
# 3) Pedir para a LLM escrever o código pandas que responde à pergunta
# ---------------------------------------------------------------
cliente = Anthropic()

def gerar_codigo(pergunta: str) -> str:
    prompt = f"""Você recebe a estrutura de planilhas pandas (dicionário `abas`,
onde cada chave é o nome da aba e o valor é um DataFrame).

{resumo}

Escreva APENAS uma linha de código Python (sem explicação, sem markdown,
sem ```) que calcule a resposta para a pergunta abaixo e guarde o resultado
na variável `resultado`. Use exclusivamente as colunas que existem acima.

Pergunta: {pergunta}
"""
    resposta = cliente.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    codigo = resposta.content[0].text.strip()
    # remove cercas de código, caso a LLM ignore a instrução
    codigo = codigo.replace("```python", "").replace("```", "").strip()
    return codigo

# ---------------------------------------------------------------
# 4) Executar o código gerado NUM ESPAÇO CONTROLADO
#    (só enxerga `abas` e `pd` — não tem acesso a arquivos, rede, etc.)
# ---------------------------------------------------------------
def executar_com_seguranca(codigo: str):
    espaco = {"abas": abas, "pd": pd}
    exec(codigo, {"__builtins__": {}}, espaco)  # __builtins__ vazio = sem open(), import, etc.
    return espaco.get("resultado")

# ---------------------------------------------------------------
# 5) Loop de chat simples no terminal
# ---------------------------------------------------------------
if __name__ == "__main__":
    print("Assistente de relatórios pronto. Digite 'sair' para encerrar.\n")
    while True:
        pergunta = input("Pergunta: ").strip()
        if pergunta.lower() == "sair":
            break
        try:
            codigo = gerar_codigo(pergunta)
            print(f"  [código gerado: {codigo}]")
            resultado = executar_com_seguranca(codigo)
            print(f"Resposta: {resultado}\n")
        except Exception as e:
            print(f"Não consegui responder essa (erro: {e}). Tente reformular.\n")
