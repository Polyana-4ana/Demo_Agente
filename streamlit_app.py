"""
Sprint 5 - Interface Streamlit para o chatbot de relatórios.
Reaproveita o back-end do chat_sql.py (mesma lógica, mesma segurança).

Antes de rodar:
  1) pip install streamlit  (além do que já estava no requirements.txt)
  2) python carregar_para_sqlite.py   (se ainda não rodou)
  3) streamlit run streamlit_app.py
"""

import sqlite3
import streamlit as st

from chat_sql import (
    obter_schema,
    gerar_sql,
    sql_e_seguro,
    tabelas_sao_validas,
    listar_tabelas,
    BANCO,
)

st.set_page_config(page_title="Assistente de Relatórios", page_icon="📊")
st.title("📊 Assistente de Relatórios")
st.caption(
    "Pergunte algo sobre os relatórios da empresa (100% local, sem dados saindo da máquina)."
)


@st.cache_resource
def conectar_banco():
    """@st.cache_resource: abre a conexão UMA vez só e reaproveita entre perguntas,
    em vez de abrir uma conexão nova a cada pergunta do usuário."""
    return sqlite3.connect(BANCO, check_same_thread=False)


conexao = conectar_banco()
schema = obter_schema(conexao)
tabelas_reais = listar_tabelas(conexao)
print(f"\n[INICIO] Tabelas reais disponíveis no banco: {tabelas_reais}")

# Guarda o histórico de mensagens na sessão (senão some a cada pergunta nova)
if "historico" not in st.session_state:
    st.session_state.historico = []

# Reexibe as mensagens já trocadas
for mensagem in st.session_state.historico:
    with st.chat_message(mensagem["papel"]):
        st.write(mensagem["conteudo"])

pergunta = st.chat_input("Ex: Qual foi o faturamento total de Janeiro?")

if pergunta:
    st.session_state.historico.append({"papel": "user", "conteudo": pergunta})
    with st.chat_message("user"):
        st.write(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando o relatório..."):
            print(f"\n[PERGUNTA] {pergunta}")
            sql = gerar_sql(pergunta, schema)
            print(f"[SQL GERADO PELA IA] {sql}")

            if not sql_e_seguro(sql):
                print("[BLOQUEADO] Comando não é uma consulta de leitura permitida.")
                resposta = (
                    "Essa pergunta gerou um comando não permitido. Tente reformular."
                )
            else:
                valido, tabela_invalida = tabelas_sao_validas(sql, tabelas_reais)
                if not valido:
                    print(
                        f"[BLOQUEADO - ANTI-ALUCINAÇÃO] A IA tentou usar a tabela "
                        f"'{tabela_invalida}', que NÃO existe no banco real "
                        f"{tabelas_reais}. Consulta recusada antes de rodar."
                    )
                    resposta = (
                        f"⚠️ A resposta foi **recusada**: a IA tentou consultar uma "
                        f"tabela chamada `{tabela_invalida}`, que não existe nos seus "
                        f"dados reais. Isso evita uma resposta inventada — reformule "
                        f"a pergunta ou confira se os dados foram carregados."
                    )
                else:
                    try:
                        linhas = conexao.execute(sql).fetchall()
                        print(f"[EXECUTADO COM SUCESSO] Resultado: {linhas}")
                        resposta = f"**Resultado:** {linhas}"
                    except Exception as e:
                        print(f"[ERRO AO EXECUTAR] {e}")
                        resposta = (
                            f"O SQL gerado deu erro ({e}). Tente reformular a pergunta."
                        )

            # Mostra o SQL gerado num painel que dá pra abrir/fechar,
            # pra você (ou seu gestor) auditar como a resposta foi calculada
            with st.expander("Ver SQL gerado"):
                st.code(sql, language="sql")

            st.write(resposta)
            st.session_state.historico.append(
                {"papel": "assistant", "conteudo": resposta}
            )
