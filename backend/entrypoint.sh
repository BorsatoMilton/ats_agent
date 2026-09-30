#!/bin/sh
set -e

echo "Esperando a Postgres..."
until python -c "
import os, psycopg2
psycopg2.connect(
    host=os.environ.get('POSTGRES_HOST'),
    port=os.environ.get('POSTGRES_PORT'),
    dbname=os.environ.get('POSTGRES_DB'),
    user=os.environ.get('POSTGRES_USER'),
    password=os.environ.get('POSTGRES_PASSWORD'),
).close()
" 2>/dev/null; do
  sleep 1
done

echo "Corriendo migraciones..."
python db/migrate.py

echo "Arrancando la API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
