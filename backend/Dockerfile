# Contexto de build = raiz del proyecto (ver docker-compose.yml),
# porque este contenedor tambien necesita db/ para correr las
# migraciones antes de levantar la API.
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/entrypoint.sh ./entrypoint.sh
COPY db ./db

RUN chmod +x ./entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
