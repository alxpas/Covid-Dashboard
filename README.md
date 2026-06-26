# Aplicações em Data Science - Turma 3
## Trabalho 1  -  COVID Dashboard

Atividade Pratica - Dashboard COVID-19

Streamlit + Snowflake + GitHub + Deploy

Objetivo
Reproduzir o pipeline completo da aula usando um dataset diferente: dados publicos de COVID-19 da Our World in Data (OWID). Ao final, o
aluno tera um dashboard publicado na internet conectado ao Snowflake.Dataset
CSV público via GitHub : https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv
Colunas principais: location, date, new cases, t otal deaths, people_vaccinated, population
Filtrar por paises e periodo antes de enviar ao Snowflake (arquivo tem 400 mil linhas)
8 Etapas
Criar conta Snowflake > 2. Preparar ambiente local > 3. Configurar secrets.toml > 4. Criar covid_dashboard.py > 5. Implementar as 4
visualizacoes -> 6. Testar localmente > 7. Publicar no GitHub > 8. Deploy no Streamlit Community Cloud
4 Visualizações Obrigatórias
Linha - Evolucao de casos novos por pais
Barras - Total de obitos por pais
Pizza - Proporção de vacinados (1 dose)
Dispersao - População x Total de casos

Também obrigatório: 3 KPIs (st.metric), 1 filtro interativo, aba de Dados Brutos com exportação CSV

Entrega: Link do app + repositório GitHub + print do dashboard + texto descritivo (5-10 linhas)