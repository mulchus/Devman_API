FROM python:3.10-slim as base
LABEL maintainer="Make by @mulchus"

# Сборка зависимостей
ARG BUILD_DEPS="curl"
RUN apt-get update && apt-get install -y $BUILD_DEPS

# Инициализация проекта
WORKDIR /opt/devman-api
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Установка зависимостей
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копирование в контейнер папок и файлов.
COPY . .

# запуск бота
CMD ["python", "./main.py"]