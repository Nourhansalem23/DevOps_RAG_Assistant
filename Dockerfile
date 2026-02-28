FROM python:3.11
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://ollama.com/install.sh | sh
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
# Start Ollama and pull the model in the background, then run your app
CMD ollama serve & sleep 10 && ollama pull qwen2.5:1.5b && python app.py
