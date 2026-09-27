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

from chat_sql import obter_schema, gerar_sql, sql_e_seguro, BANCO

st.set_page_config(page_title="Assistente de Relatórios", page_icon="📊")
st.title("📊 Assistente de Relatórios")
st.caption("Pergunte algo sobre os relatórios da empresa (100% local, sem dados saindo da máquina).")


@st.cache_resource
def conectar_banco():
    """@st.cache_resource: abre a conexão UMA vez só e reaproveita entre perguntas,
    em vez de abrir uma conexão nova a cada pergunta do usuário."""
    return sqlite3.connect(BANCO, check_same_thread=False)


conexao = conectar_banco()
schema = obter_schema(conexao)

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
            sql = gerar_sql(pergunta, schema)

            if not sql_e_seguro(sql):
                resposta = "Essa pergunta gerou um comando não permitido. Tente reformular."
            else:
                try:
                    linhas = conexao.execute(sql).fetchall()
                    resposta = f"**Resultado:** {linhas}"
                except Exception as e:
                    resposta = f"O SQL gerado deu erro ({e}). Tente reformular a pergunta."

            # Mostra o SQL gerado num painel que dá pra abrir/fechar,
            # pra você (ou seu gestor) auditar como a resposta foi calculada
            with st.expander("Ver SQL gerado"):
                st.code(sql, language="sql")

            st.write(resposta)
            st.session_state.historico.append({"papel": "assistant", "conteudo": resposta})
