# Usa uma imagem oficial e leve de Python
FROM python:3.11-slim

# Define o diretório de trabalho no contentor
WORKDIR /app

# Instala as dependências necessárias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte para o contentor
COPY main.py .

# Arranca a API REST com o Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]