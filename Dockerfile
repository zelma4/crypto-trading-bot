# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копіюємо лише список залежностей для кешування
COPY requirements.txt ./

# Інсталюємо лише Python-пакети
RUN pip install --no-cache-dir -r requirements.txt

# Тепер копіюємо весь код (без venv, згідно з .dockerignore)
COPY . .

# Компонуємо контейнер для FastAPI
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]