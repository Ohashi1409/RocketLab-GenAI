# 🚀 Agente Analítico E-commerce (Text-to-SQL)

Projeto desenvolvido para o Rocket Lab 2026. Este é um agente de Inteligência Artificial capaz de traduzir perguntas de negócio em linguagem natural para consultas SQL, executá-las em um banco de dados SQLite e retornar análises em tempo real para usuários não técnicos através de uma interface web interativa.

**Diferenciais da Arquitetura:**
* **Self-Healing (Autocorreção):** Se a IA gerar um SQL com erro de sintaxe, o sistema intercepta o erro e pede para o modelo corrigir antes de falhar.
* **Fail-Safe e Blindagem de Escopo:** Perguntas fora de escopo (ex: clima, política) são bloqueadas pela IA. Erros técnicos são mascarados para o usuário final, evitando vazamento de dados da infraestrutura.
* **Telemetria / Auditoria:** Todo o fluxo (sucessos, bloqueios e erros) é registrado automaticamente em um banco de dados local de log (`log_auditoria.db`).

## 🛠️ Stack Tecnológica
* **Linguagem:** Python 3.10+
* **Backend / API:** FastAPI
* **Frontend / UI:** Streamlit
* **Modelo de IA:** Google Gemini 2.5 Flash
* **Banco de Dados:** SQLite3 (Embutido)

## ⚙️ Pré-requisitos
Antes de começar, você precisará ter o [Python](https://www.python.org/downloads/) instalado na sua máquina e uma chave de API do [Google AI Studio](https://aistudio.google.com/).

## 🚀 Passo a Passo para Execução

**1. Clone o repositório**
```bash
git clone [https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git](https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git)
cd NOME_DO_REPOSITORIO
```

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
Certifique-se de que o seu arquivo `requirements.txt` possua os seguintes pacotes: `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, `google-genai`, `streamlit`, `pandas` e `requests`.
```bash
pip install -r requirements.txt
```

**4. Configure as Variáveis de Ambiente**
Crie um arquivo chamado `.env` na raiz do projeto e adicione a sua chave de API do Gemini:
```env
GEMINI_API_KEY=sua_chave_api_aqui
```

**5. Execute a Aplicação (Arquitetura de Microsserviços)**
Este projeto roda com o Backend e o Frontend operando simultaneamente. Você precisará abrir **dois terminais** no seu VS Code ou prompt de comando (certifique-se de que o `venv` está ativado em ambos):

* **Terminal 1: Ligando o Backend (API)**
  ```bash
  uvicorn main:app --reload
  ```
  *(O servidor FastAPI ficará rodando em http://localhost:8000)*

* **Terminal 2: Ligando o Frontend (Interface Visual)**
  ```bash
  streamlit run app_ui.py
  ```
  *(A interface será aberta automaticamente no seu navegador padrão em http://localhost:8501)*

**6. Acesse e Teste a Aplicação**
Vá até a aba do navegador que o Streamlit abriu (`http://localhost:8501`) e faça suas perguntas em linguagem natural!

**Sugestões de teste:**
* *Caminho Feliz:* "Quais são os top 10 produtos mais vendidos em quantidade?"
* *Injeção Dinâmica:* "Qual o ticket médio de vendas do estado de SP?"
* *Teste de Segurança (Fora de escopo):* "Me dê uma receita de bolo de chocolate."