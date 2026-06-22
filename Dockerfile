# syntax=docker/dockerfile:1
FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema necesarias para psycopg2 y utilidades
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /code/
# Script de entrada para esperar a DB y migrar
CMD ["sh", "-c", "python wait_for_db.py && python manage.py migrate && python setup_groups.py && python manage.py runserver 0.0.0.0:8000"]
