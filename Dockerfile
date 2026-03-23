FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Порт будет предоставлен Render автоматически в переменной PORT
ENV RENDER=true

# Команда запуска
CMD ["python", "merged_bot/main.py"]
