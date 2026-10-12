FROM python:3.14.3-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

# Библиотеки ставим под root (это нормально, так как они нужны системе)
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# 1. Создаем системного пользователя без прав администратора
RUN useradd -u 1000 appuser && chown -R appuser:appuser /app

# 2. МЕНЯЕМ пользователя на безопасного
USER appuser

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
