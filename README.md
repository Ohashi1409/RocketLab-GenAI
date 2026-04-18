# 🚀 Agente Analítico E-commerce (Text-to-SQL)

Projeto desenvolvido para o Rocket Lab 2026. Este é um agente de Inteligência Artificial capaz de traduzir perguntas de negócio em linguagem natural para consultas SQL, executá-las em um banco de dados SQLite e retornar análises em tempo real para usuários não técnicos.

## 🛠️ Stack Tecnológica
* **Linguagem:** Python 3.10+
* **Framework:** FastAPI (Backend / API REST)
* **Modelo de IA:** Google Gemini 2.5 Flash
* **Banco de Dados:** SQLite3 (Embutido)

## ⚙️ Pré-requisitos
Antes de começar, você precisará ter o [Python](https://www.python.org/downloads/) instalado na sua máquina e uma chave de API do [Google AI Studio](https://aistudio.google.com/).

## 🚀 Passo a Passo para Execução

**1. Clone o repositório**
```bash
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git](https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git)
cd NOME_DO_REPOSITORIO
````

**2. Crie e ative o Ambiente Virtual (venv)**

  * **No Mac/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
  * **No Windows:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

**3. Instale as dependências**

```bash
pip install -r requirements.txt
```

*(Nota: Certifique-se de que os pacotes `fastapi`, `uvicorn`, `pydantic`, `python-dotenv` e `google-genai` estão listados no seu requirements.txt)*

**4. Configure as Variáveis de Ambiente**
Crie um arquivo chamado `.env` na raiz do projeto e adicione a sua chave de API do Gemini:

```env
GEMINI_API_KEY=sua_chave_api_aqui
```

**5. Execute o Servidor**

```bash
uvicorn main:app --reload
```

**6. Acesse e Teste a Aplicação**
Abra o seu navegador e acesse a documentação interativa (Swagger UI) gerada automaticamente pelo FastAPI:
👉 **[http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)**

Vá no endpoint `/consultar`, clique em "Try it out" e faça perguntas de negócio como:

  * *"Quais são os top 10 produtos mais vendidos?"*
  * *"Qual o ticket médio de vendas por estado?"*

<!-- end list -->