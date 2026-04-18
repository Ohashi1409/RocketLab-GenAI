import os
import sqlite3
from google import genai
from google.genai import types 
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = FastAPI(title="Agente Analítico E-commerce (Text-to-SQL)", version="1.0")

class QueryRequest(BaseModel):
    pergunta: str

def obter_esquema():
    """Lê o banco.db e retorna as tabelas e colunas para o Gemini entender a estrutura."""
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()
    
    esquema = ""
    for (nome_tabela,) in tabelas: 
        # PRAGMA inspeciona a estrutura do banco (colunas, tipos, chaves)
        cursor.execute(f"PRAGMA table_info({nome_tabela});")
        colunas = [col[1] for col in cursor.fetchall()]
        esquema += f"Tabela: {nome_tabela} | Colunas: {', '.join(colunas)}\n"
        
    conn.close()
    return esquema

@app.post("/consultar")
async def consultar_agente(request: QueryRequest):
    try:
        esquema = obter_esquema()
        
        # =====================================================================
        # ETAPA 1: TRADUÇÃO TEXT-TO-SQL (O Cérebro Analítico)
        # =====================================================================
        prompt_sql = f"""
        Você é um Analista de Dados Sênior especialista no banco de dados SQLite de um grande E-commerce.
        Sua missão é traduzir perguntas de negócio feitas por usuários não técnicos em consultas SQL precisas.
        
        REGRAS DE NEGÓCIO E CONTEXTO:
        1. "Pedidos" e "Vendas" são tratados como sinônimos.
        2. Tabelas 'dim_' são dimensões (cadastros) e 'fat_' são fatos (transações e eventos).
        3. Realize os JOINs necessários entre as tabelas usando as chaves correspondentes.
        4. SEGURANÇA: Gere EXCLUSIVAMENTE consultas de leitura (SELECT). Nunca use INSERT, UPDATE, DELETE ou DROP.
        5. AMBIGUIDADE DE VENDAS: Quando o usuário perguntar quem "mais vendeu", "top vendedores" ou "menos vendeu" sem especificar a métrica, calcule SEMPRE pela Receita Total (soma do valor financeiro das vendas). Só use contagem (COUNT) se o usuário pedir explicitamente por "quantidade" ou "volume" de pedidos.
        
        ESQUEMA DO BANCO DE DADOS:
        {esquema}
        
        PERGUNTA DO USUÁRIO: "{request.pergunta}"
        
        INSTRUÇÃO CRÍTICA DE SAÍDA:
        Retorne ABSOLUTAMENTE SOMENTE o código SQL. 
        - SEM formatação markdown (```).
        - SEM a palavra 'sql'.
        - SEM explicações ou textos adicionais.
        """
        
        # Chamada com Temperatura 0.0 para garantir lógica determinística
        resposta_sql = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt_sql,
            config=types.GenerateContentConfig(temperature=0.0) 
        )
        
        # Tratamento do bloqueio de segurança
        if not resposta_sql.text:
            raise HTTPException(
                status_code=403, 
                detail="Ação bloqueada pelas políticas de segurança. O agente só tem permissão para realizar consultas de leitura (SELECT) na base de dados."
            )
            
        query_sql = resposta_sql.text.strip().replace("```sql", "").replace("```", "")
        
        # =====================================================================
        # ETAPA 2: EXECUÇÃO DA QUERY E RETORNO DIRETO (Otimização)
        # =====================================================================
        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute(query_sql)
            resultados = cursor.fetchall()
            nomes_colunas = [desc[0] for desc in cursor.description] if cursor.description else []
        except sqlite3.OperationalError as erro_sql:
            conn.close()
            raise HTTPException(status_code=400, detail=f"O Agente gerou um SQL inválido: {erro_sql}\nQuery: {query_sql}")
            
        conn.close()
        
        # Retornamos os dados estruturados para o Frontend lidar com a exibição
        return {
            "pergunta": request.pergunta,
            "sql_gerado": query_sql,
            "colunas": nomes_colunas,
            "dados": resultados
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))