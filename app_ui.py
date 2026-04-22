# =================================================================================
# O Arquivo abaixo é dedicado a ideia de poder ter uma forma de interface
# gráfica onde é possível realizar a chamada a nossa IA através dessa tela

# A ideia é que funcione como um facilitador e evite o uso cru do backend, 
# que é justamente nossa IA e a rota desenvolvida pra fazer a mágica acontecer
# =================================================================================

import streamlit as st
import requests
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Assistente de Dados - Visagio", page_icon="📊", layout="centered")

# URL da sua API FastAPI (certifique-se de que o main.py está rodando)
API_URL = "http://localhost:8000/consulta"

st.title("📊 Agente Analítico de E-commerce")
st.markdown("Faça perguntas em linguagem natural sobre as vendas, produtos e clientes.")

# Caixa de texto para o usuário digitar a pergunta
pergunta_usuario = st.text_area("O que você deseja saber sobre os dados?", placeholder="Ex: Qual foi o produto mais vendido em quantidade?")

if st.button("Gerar Análise 🚀"):
    if pergunta_usuario.strip() == "":
        st.warning("Por favor, digite uma pergunta antes de analisar.")
    else:
        with st.spinner("Analisando o banco de dados e gerando insights..."):
            try:
                # Faz a requisição POST para o seu backend (main.py)
                response = requests.post(API_URL, json={"pergunta": pergunta_usuario})
                
                if response.status_code == 200:
                    dados = response.json()
                    
                    # 1. Mostra o Resumo Executivo (A resposta principal da IA)
                    st.success("Análise Concluída!")
                    st.markdown(f"### 💡 Resposta\n{dados['resumo_executivo']}")
                    
                    st.divider()
                    
                    # 2. Mostra os Dados Brutos em formato de Tabela e Gráfico
                    st.markdown("### 📋 Visualização de Dados")
                    if dados["dados_brutos"]:
                        df = pd.DataFrame(dados["dados_brutos"], columns=dados["detalhes_tecnicos"]["colunas_retornadas"])
                        
                        # Cria abas para o usuário escolher entre Tabela e Gráfico
                        aba_tabela, aba_grafico = st.tabs(["🧮 Tabela", "📊 Gráfico"])
                        
                        with aba_tabela:
                            st.dataframe(df, use_container_width=True)
                            
                        with aba_grafico:
                            # Se a tabela tiver pelo menos 2 colunas e a segunda for numérica, desenha um gráfico!
                            if len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
                                st.bar_chart(df.set_index(df.columns[0]))
                            else:
                                st.info("Os dados retornados não são adequados para um gráfico de barras (necessário 1 coluna de texto e 1 de números).")
                    else:
                        st.info("Nenhum dado tabular para exibir.")
                    
                    # 3. Detalhes Técnicos Escondidos (Para os Chefes/Avaliadores verem que você manja)
                    with st.expander("🛠️ Detalhes Técnicos (Para Engenheiros)"):
                        st.markdown("**SQL Gerado pela IA:**")
                        st.code(dados["detalhes_tecnicos"]["sql_utilizado"], language="sql")
                        st.markdown(f"**Tempo de Processamento:** `{dados['detalhes_tecnicos']['tempo_processamento_ms']} ms`")
                        st.markdown(f"**Total de Registros Encontrados:** `{dados['detalhes_tecnicos']['total_registros']}`")
                        
                else:
                    st.error(f"Erro na API: {response.json().get('detail', 'Erro desconhecido')}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Erro de conexão! Verifique se a sua API (main.py) está rodando na porta 8000.")