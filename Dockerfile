FROM python:3.11-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema necessárias para compilar algumas libs (como fpdf2/weasyprint caso necessário no futuro)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas os requirements primeiro (para aproveitar o cache do Docker)
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código do projeto
COPY . .

# Expor a porta padrão do Streamlit
EXPOSE 8501

# Comando para rodar a aplicação quando o container iniciar
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
