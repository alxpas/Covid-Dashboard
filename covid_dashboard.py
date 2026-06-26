import streamlit as st
import pandas as pd
import plotly.express as px
from snowflake.snowpark import Session
import datetime

# Constantes
URL_CSV = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
TABLE_NAME = "COVID_DATA"

def init_connection():
    """Inicializa a conexão com o Snowflake usando Snowpark."""
    connection_parameters = {
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "account": st.secrets["snowflake"]["account"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": "TEST_DB",
        "schema": "PUBLIC",
        "role": st.secrets["snowflake"]["role"]
    }
    return Session.builder.configs(connection_parameters).create()

def carregar_dados_no_snowflake():
    """Baixa o CSV, filtra os dados e escreve a tabela no Snowflake."""
    with st.spinner("Baixando e filtrando dados da OWID..."):
        df = pd.read_csv(URL_CSV)
        
        # Filtragem conforme instruções
        paises = ['Brazil', 'United States', 'India', 'Germany', 'South Africa', 'Japan']
        df = df[df['location'].isin(paises)]
        df = df[df['date'] >= '2021-01-01']
        
        # Snowflake tem preferência por colunas em maiúsculo
        df.columns = [c.upper() for c in df.columns]

    with st.spinner("Enviando dados para o Snowflake..."):
        try:
            session = init_connection()
            # Escreve os dados (cria a tabela ou sobrescreve se já existir)
            session.write_pandas(df, TABLE_NAME, auto_create_table=True, overwrite=True)
            st.sidebar.success("✅ Dados carregados com sucesso no Snowflake!")
        except Exception as e:
            st.sidebar.error(f"Erro ao carregar no Snowflake: {e}")

def carregar_dashboard_do_snowflake():
    """Lê a tabela do Snowflake e salva no session_state."""
    with st.spinner("Lendo dados do Snowflake..."):
        try:
            session = init_connection()
            # Lê a tabela direto para um DataFrame Pandas
            df = session.table(TABLE_NAME).to_pandas()
            st.session_state['covid_data'] = df
            st.sidebar.success("✅ Dashboard carregado!")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler do Snowflake: {e}")

def render_dashboard():
    """Função principal que desenha a interface do Dashboard."""
    
    # Configuração da página (DEVE SER O PRIMEIRO COMANDO STREAMLIT)
    st.set_page_config(page_title="Dashboard COVID-19", page_icon="🦠", layout="wide")
    st.title("🦠 Dashboard COVID-19 - Análise OWID")

    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Ações e Conexão")
    
    if st.sidebar.button("■ Carregar Dados no Snowflake"):
        carregar_dados_no_snowflake()
        
    if st.sidebar.button("■ Carregar Dashboard"):
        carregar_dashboard_do_snowflake()

    # Verifica se os dados já foram carregados na sessão
    if 'covid_data' not in st.session_state:
        st.info("👈 Utilize os botões na barra lateral para carregar os dados no banco e no dashboard.")
        return

    # Recupera os dados e formata a data
    df = st.session_state['covid_data']
    df['DATE'] = pd.to_datetime(df['DATE'])

    # --- FILTRO INTERATIVO ---
    st.sidebar.divider()
    st.sidebar.header("🔍 Filtros")
    paises_disponiveis = df['LOCATION'].unique().tolist()
    paises_selecionados = st.sidebar.multiselect("Selecione os Países", options=paises_disponiveis, default=paises_disponiveis)

    if not paises_selecionados:
        st.warning("Por favor, selecione pelo menos um país na barra lateral para exibir as visualizações.")
        return

    # Aplica o filtro
    df_filtrado = df[df['LOCATION'].isin(paises_selecionados)]

    # --- KPIs ---
    col1, col2, col3 = st.columns(3)
    total_casos_novos = df_filtrado['NEW_CASES'].sum()
    total_obitos_acumulados = df_filtrado.groupby('LOCATION')['TOTAL_DEATHS'].max().sum()
    qtd_paises = len(paises_selecionados)

    col1.metric("🦠 Total de Casos Novos", f"{total_casos_novos:,.0f}")
    col2.metric("💀 Total de Óbitos (Acumulado)", f"{total_obitos_acumulados:,.0f}")
    col3.metric("🌎 Países Analisados", qtd_paises)
    st.divider()

    # --- ABAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Visualizações", "🗄️ Dados Brutos", "💻 Query SQL"])

    with tab1:
        c1, c2 = st.columns(2)

        with c1:
            # 1. Evolução de casos novos ao longo do tempo (Linha)
            fig_linha = px.line(df_filtrado, x='DATE', y='NEW_CASES', color='LOCATION', title="1. Evolução de Casos Novos no Tempo")
            st.plotly_chart(fig_linha, use_container_width=True)

            # 3. Proporção de pessoas vacinadas na data mais recente (Pizza)
            # Como é um valor acumulado, pegamos o valor máximo relatado por cada país
            df_pizza = df_filtrado.groupby('LOCATION')['PEOPLE_VACCINATED'].max().reset_index()
            
            # Remove qualquer país que por acaso não tenha dados de vacina para não quebrar o gráfico
            df_pizza = df_pizza.dropna(subset=['PEOPLE_VACCINATED'])
            
            fig_pizza = px.pie(df_pizza, values='PEOPLE_VACCINATED', names='LOCATION', title="3. Proporção de Vacinados (Total Acumulado)")
            st.plotly_chart(fig_pizza, use_container_width=True)

        with c2:
            # 2. Comparação do total de óbitos entre os países (Barras)
            df_obitos = df_filtrado.groupby('LOCATION')['TOTAL_DEATHS'].max().reset_index()
            fig_barras = px.bar(df_obitos, x='LOCATION', y='TOTAL_DEATHS', color='LOCATION', title="2. Comparativo de Óbitos Acumulados")
            st.plotly_chart(fig_barras, use_container_width=True)

            # 4. Relação entre população e total de casos (Dispersão)
            df_dispersao = df_filtrado.groupby('LOCATION').agg({'POPULATION': 'max', 'TOTAL_CASES': 'max'}).reset_index()
            fig_dispersao = px.scatter(df_dispersao, x='POPULATION', y='TOTAL_CASES', color='LOCATION', size='TOTAL_CASES', hover_name='LOCATION', title="4. População vs Total de Casos")
            st.plotly_chart(fig_dispersao, use_container_width=True)

    with tab2:
        st.subheader("Explorador de Dados Brutos")
        st.dataframe(df_filtrado)
        
        # Botão de exportação
        csv_data = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Exportar para CSV", data=csv_data, file_name="covid_dashboard_export.csv", mime="text/csv")

    with tab3:
        st.subheader("Console SQL Interativo")
        st.markdown(f"**Tabela disponível:** `{TABLE_NAME}`")
        query = st.text_area("Digite sua Query:", f"SELECT * FROM {TABLE_NAME} LIMIT 50;")
        
        if st.button("▶ Executar Consulta"):
            with st.spinner("Executando consulta no Snowflake..."):
                try:
                    session = init_connection()
                    df_sql = session.sql(query).to_pandas()
                    st.dataframe(df_sql)
                except Exception as e:
                    st.error(f"Erro na SQL: {e}")

# (Opcional) Permite rodar este arquivo diretamente para testes, mas o ideal é chamar pelo main.py
if __name__ == "__main__":
    render_dashboard()