# Guia de Estudo — Assistente de Relatórios

Objetivo deste guia: você conseguir ler, ajustar e evoluir este projeto
sozinha, usando o GitHub Copilot como ferramenta — não como muleta. A
diferença entre os dois: você pede o quê fazer e revisa o resultado, em vez
de aceitar sugestões sem entender.

## Trilha de estudo, na ordem

### 1. Python que aparece no projeto (base para tudo o resto)
- **f-strings**: `f"Tabela: {nome}"` — como montar texto com variáveis dentro
- **list comprehension**: `[x for x in lista if condicao]` — usado em
  `nome_tabela_valido` e `montar_chunks`
- **dicionários**: `{"chave": valor}` — usado o tempo todo (ex.: `abas` no
  `carregar_para_sqlite.py`, que é um dicionário de nome_da_aba → tabela)
- **`with` e gerenciamento de recursos**: por que fechamos conexões de banco
- Onde estudar: tutorial oficial em docs.python.org, seção "The Python Tutorial"

### 2. pandas (você já viu um pouco, mas vale aprofundar)
- `read_excel(sheet_name=None)` → devolve um dicionário de DataFrames
- `to_sql()` → como um DataFrame vira uma tabela SQL
- `DataFrame.dtypes`, `.head()`, `.shape` → como inspecionar dados rapidamente
- Onde estudar: pandas.pydata.org tem um "10 minutes to pandas" muito direto

### 3. SQL (o coração do projeto agora)
- `SELECT`, `WHERE`, `GROUP BY`, `ORDER BY`
- Funções de agregação: `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`
- `JOIN` (você ainda não precisa, mas vai precisar quando tiver mais de uma
  tabela relacionada — está no roadmap)
- Onde estudar: sqlite.org/lang.html (referência oficial, curta e direta)
- **Exercício prático**: abra `relatorios.db` com uma ferramenta como o
  [DB Browser for SQLite](https://sqlitebrowser.org/) e escreva consultas
  manualmente, comparando com o que a LLM gera

### 4. Módulo `sqlite3` do Python
- `conexao.execute(sql)`, `.fetchall()` — é conceitualmente parecido com
  `Statement`/`ResultSet` do JDBC em Java, se você já viu isso
- `PRAGMA table_info(tabela)` — comando específico do SQLite para listar
  colunas (equivalente a `DESCRIBE` no MySQL)

### 5. Como funciona uma chamada de API HTTP (para entender o Ollama)
- O que é um `POST`, corpo em JSON, resposta em JSON
- `requests.post(url, json=...)` no Python é o mesmo princípio de um
  `HttpClient` em Java fazendo uma chamada REST
- Documentação do Ollama: https://github.com/ollama/ollama/blob/main/docs/api.md

### 6. Streamlit (a interface)
- `st.session_state` — por que existe (Streamlit reroda o script inteiro a
  cada clique, então precisa de um jeito de "lembrar" o histórico)
- `st.cache_resource` — evita reabrir a conexão do banco toda hora
- Onde estudar: docs.streamlit.io tem um tutorial de "Build a basic chatbot"

## Como montar seus próprios testes (antes de confiar no modelo)

Antes de apresentar ao gestor, monte uma lista de 15-20 perguntas reais que
ele faria, com a resposta certa calculada manualmente (ou por SQL que você
escreveu à mão). Rode cada pergunta pelo `chat_sql.py` e compare. Isso vira
sua "taxa de acerto" — é o dado mais importante para decidir se o modelo
pequeno serve ou se precisa trocar por um maior.

```python
# esqueleto simples pra automatizar esse teste (pode pedir ajuda ao Copilot
# pra expandir isso, já que você já entende o objetivo)
casos_de_teste = [
    ("Qual o faturamento total de Janeiro?", 208983.9),
    # adicione seus próprios casos aqui
]
for pergunta, esperado in casos_de_teste:
    sql = gerar_sql(pergunta, schema)
    resultado = conexao.execute(sql).fetchall()
    print(pergunta, "->", resultado, "(esperado:", esperado, ")")
```

## Como usar o Copilot com critério (não como dependência)

A diferença entre "usar Copilot" e "depender do Copilot" é **quem entende a
decisão**. Algumas práticas:

1. **Peça explicação, não só código.** Em vez de "escreva uma função que
   faça X", peça "explique como você faria X e por quê" primeiro. Você já
   faz isso comigo — mantenha o hábito.
2. **Nunca aceite uma sugestão que mexa em `sql_e_seguro` ou em qualquer
   trava de segurança sem entender exatamente o que mudou.** Essa função é
   a que impede um `DROP TABLE` acidental — é a parte mais sensível do
   projeto.
3. **Peça para o Copilot explicar o código já existente antes de pedir para
   ele mudar algo.** Selecione a função, peça "explique o que essa função
   faz e por quê", e só depois peça a alteração.
4. **Desconfie de sugestões que adicionem dependências novas sem necessidade**
   — isso vai contra a preferência de manter a solução simples para o MVP.
5. **Trate cada sugestão do Copilot como um code review**: leia, entenda o
   trade-off, só então aceite — exatamente como você já pede que eu faça
   com você.

## Checklist antes de subir pro GitHub

- [ ] `.gitignore` está commitado e `relatorios.db` / `relatorios/*.xlsx`
      **não aparecem** no `git status`
- [ ] Nenhum dado real da empresa está em nenhum arquivo versionado
      (confira `relatorio.xlsx` — é só o de teste, com dados fictícios)
- [ ] README revisado e atualizado com o que você mudou
- [ ] Testou rodar o projeto do zero num clone limpo (`git clone` numa pasta
      nova) para garantir que o README realmente basta para outra pessoa rodar
