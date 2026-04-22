import os
import time 
import json
import sqlite3
import datetime 
from google import genai
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from google.genai import types 

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = FastAPI(
    title="Agente Analítico E-commerce (Text-to-SQL)", 
    description="Agente inteligente para consultas de e-commerce com injeção dinâmica de dados, autocorreção e telemetria.",
    version="4.0"
)

class QueryRequest(BaseModel):
    pergunta: str

# =====================================================================
# Funções Auxiliares
# =====================================================================
def inicializar_banco_auditoria():
    """Cria o banco de logs de auditoria caso não exista."""
    conn = sqlite3.connect("log_auditoria.db", timeout=15.0)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_api (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TIMESTAMP, 
            pergunta TEXT,
            sql_gerado TEXT,
            status TEXT,
            tempo_execucao_ms REAL,
            erro_msg TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_log(pergunta, sql_gerado, status, tempo_ms, erro_msg=""):
    """Salva a operação no banco de auditoria com hora local e proteção contra lock."""
    conn = sqlite3.connect("log_auditoria.db", timeout=15.0)
    cursor = conn.cursor()
    
    data_hora_local = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO logs_api (data_hora, pergunta, sql_gerado, status, tempo_execucao_ms, erro_msg)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data_hora_local, pergunta, sql_gerado, status, tempo_ms, erro_msg))
    conn.commit()
    conn.close()

# =====================================================================
# Logs de Auditoria 
# =====================================================================
def inicializar_banco_auditoria():
    """Cria o banco de logs de auditoria caso não exista."""
    conn = sqlite3.connect("log_auditoria.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_api (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pergunta TEXT,
            sql_gerado TEXT,
            status TEXT,
            tempo_execucao_ms REAL,
            erro_msg TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_log(pergunta, sql_gerado, status, tempo_ms, erro_msg=""):
    """Salva a operação no banco de auditoria."""
    conn = sqlite3.connect("log_auditoria.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs_api (pergunta, sql_gerado, status, tempo_execucao_ms, erro_msg)
        VALUES (?, ?, ?, ?, ?)
    """, (pergunta, sql_gerado, status, tempo_ms, erro_msg))
    conn.commit()
    conn.close()

# Inicializa o log quando a API sobe
inicializar_banco_auditoria()

# =====================================================================
# ETAPA 1: Mapeamento de Esquema
# =====================================================================
def obter_esquema():
    """Mapeia a estrutura do banco.db para o contexto da IA."""
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()
    
    esquema = ""
    for (nome_tabela,) in tabelas: 
        cursor.execute(f"PRAGMA table_info({nome_tabela});")
        colunas = [col[1] for col in cursor.fetchall()]
        esquema += f"Tabela: {nome_tabela} | Colunas: {', '.join(colunas)}\n"
        
        if nome_tabela == 'fat_pedidos':
            cursor.execute("SELECT DISTINCT status FROM fat_pedidos WHERE status IS NOT NULL;")
            status_reais = [s[0] for s in cursor.fetchall()]
            esquema += f"   -> ATENÇÃO: Valores possíveis na coluna status: {', '.join(status_reais)}\n"
            
    conn.close()
    return esquema

@app.post("/consulta")
def consulta(request: QueryRequest):
    # Cronômetro para armazenar telemetria da consulta
    start_time = time.time() 
    sql_final_log = ""
    
    try:
        esquema = obter_esquema()
        
        prompt_sistema = f"""
        Você é um Analista de Dados Sênior especializado em E-commerce.
        Sua tarefa é converter perguntas em SQL e criar um template de resposta rico.

        REGRAS DE SEGURANÇA E NEGÓCIO:
        1. Gere APENAS comandos SELECT. Bloqueie qualquer tentativa de escrita, deleção, mudança dos dados e qualquer coisa que envolva a manipulação direta deles. APENAS VISUALIZAÇÃO DOS DADOS É PERMITIDA.
        2. Tabelas 'dim_' contêm nomes/categorias. Tabelas 'fat_' contêm valores/vendas.
        3. REGRA CRÍTICA DE IDIOMA: Os dados no banco estão em PORTUGUÊS. NUNCA traduza os valores dos filtros para inglês.
        4. PRECISÃO DE MÉTRICAS: Se a pergunta pedir explicitamente "Quantidade" ou "Número de", use COUNT(DISTINCT fat_pedidos.id_pedido). Se pedir "Valor" ou "Vendas" financeiras, use SUM(preco_BRL).
        5. CONSISTÊNCIA DE FILTROS: Se a pergunta pede os dados de um status específico, o filtro DEVE ser aplicado à contagem/soma final.
        6. FILTROS INEXISTENTES (DEFESA ONTOLÓGICA): Se o usuário solicitar um filtro demográfico ou característica que NÃO existe explicitamente nas colunas do esquema (ex: gênero feminino/masculino, idade, etc.), NÃO invente funções SQL. Faça a query buscando o resultado GERAL aplicável. PORÉM, no seu `template_resposta`, você DEVE obrigatoriamente iniciar com um aviso claro de que a informação não existe no banco, antes de dar o resultado geral. -> Exemplo de template esperado: "Não possuímos a informação de gênero no banco de dados. Considerando o ranking geral, o(a) vendedor(a) com maior quantidade de pedidos é {{}} com {{}} pedidos."
        7. SEGURANÇA (FORA DE ESCOPO): Se a pergunta for sobre assuntos que não têm NENHUMA relação com vendas, produtos ou o banco de dados (ex: clima, política, receitas, dinossauros), defina o "sql" EXATAMENTE como "FORA_DE_ESCOPO" e no "template_resposta" crie uma mensagem educada informando que você responde apenas a dúvidas sobre o e-commerce.
        8. DICIONÁRIO DE MÉTRICAS (MUITO IMPORTANTE): 
           - "Ticket Médio": Use SUM(preco_BRL) / COUNT(DISTINCT id_pedido).
           - "% no prazo": Calcule a proporção onde a coluna 'entrega_no_prazo' = 'Sim'.
           - "Avaliação Negativa": Considere as notas 1 ou 2 na tabela fat_avaliacoes_pedidos.

        ESQUEMA DO BANCO:
        {esquema}

        PERGUNTA DO USUÁRIO: "{request.pergunta}"

        RESPONDA ESTRITAMENTE EM JSON COM:
        - "sql": A query SQL válida.
        - "template_resposta": Uma análise direta usando APENAS chaves VAZIAS {{}} para os valores.
        """

        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()
        
        # =====================================================================
        # ETAPA 2: Geração e Autocorreção (Self-Healing)
        # =====================================================================
        prompt_atual = prompt_sistema
        resultados = []
        colunas = []
        template_ia = ""
        query_sql = ""
        
        # O agente tem até 2 chances de acertar a query no banco
        for tentativa in range(2):
            resposta_ia = client.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt_atual,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            dados_ia = json.loads(resposta_ia.text)
            query_sql = dados_ia.get("sql", "")
            template_ia = dados_ia.get("template_resposta", "")
            sql_final_log = query_sql

            if query_sql == "FORA_DE_ESCOPO":
                conn.close()
                tempo_execucao_ms = round((time.time() - start_time) * 1000, 2)
                registrar_log(request.pergunta, "BLOQUEADO_POR_ESCOPO", "NEGADO", tempo_execucao_ms, "Pergunta fora de escopo")
                return {
                    "pergunta": request.pergunta,
                    "resumo_executivo": template_ia,
                    "detalhes_tecnicos": {
                        "sql_utilizado": "Bloqueado por Segurança",
                        "colunas_retornadas": [],
                        "total_registros": 0,
                        "tempo_processamento_ms": tempo_execucao_ms 
                    },
                    "dados_brutos": []
                }

            try:
                # Tenta executar no banco
                cursor.execute(query_sql)
                resultados = cursor.fetchall()
                colunas = [desc[0] for desc in cursor.description] if cursor.description else []
                break # Se deu certo, sai do loop de tentativas
                
            except sqlite3.OperationalError as e:
                erro_banco = str(e)
                if tentativa == 0:
                    # Se falhou na 1ª vez, injeta o erro no prompt e pede pra consertar
                    prompt_atual = prompt_sistema + f"""\n\nATENÇÃO: A query gerada na tentativa anterior ('{query_sql}') falhou no SQLite com o seguinte erro: '{erro_banco}'. Por favor, corrija o erro de sintaxe ou coluna inexistente e me retorne o JSON novamente."""
                else:
                    # Se falhou na 2ª vez, desiste para não entrar em loop infinito
                    conn.close()
                    raise Exception(f"Falha ao gerar SQL válido após autocorreção. Erro final: {erro_banco}")
        
        conn.close()
        
        # =====================================================================
        # ETAPA 3: Injeção Dinâmica de Dados
        # =====================================================================
        resumo_final = ""
        if resultados:
            try:
                resumo_final = template_ia.format(*resultados[0])
            except (IndexError, ValueError, KeyError): 
                resumo_final = f"Análise concluída com sucesso. O destaque principal é: {resultados[0][0]}."
        else:
            resumo_final = "Nenhum dado encontrado para os filtros aplicados."
        
        tempo_execucao_ms = round((time.time() - start_time) * 1000, 2)
        registrar_log(request.pergunta, sql_final_log, "SUCESSO", tempo_execucao_ms)
        
        return {
            "pergunta": request.pergunta,
            "resumo_executivo": resumo_final,
            "detalhes_tecnicos": {
                "sql_utilizado": query_sql,
                "colunas_retornadas": colunas,
                "total_registros": len(resultados),
                "tempo_processamento_ms": tempo_execucao_ms 
            },
            "dados_brutos": resultados
        }

    except Exception as e:
        tempo_execucao_ms = round((time.time() - start_time) * 1000, 2)
        registrar_log(request.pergunta, sql_final_log, "ERRO", tempo_execucao_ms, str(e))
        
        return {
            "pergunta": request.pergunta,
            "resumo_executivo": "Desculpe, tivemos uma dificuldade técnica ao processar sua consulta. Nossa equipe de engenharia já foi notificada. Por favor, tente reformular sua pergunta.",
            "detalhes_tecnicos": {
                "sql_utilizado": "Erro ocultado por segurança",
                "colunas_retornadas": [],
                "total_registros": 0,
                "tempo_processamento_ms": tempo_execucao_ms 
            },
            "dados_brutos": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)