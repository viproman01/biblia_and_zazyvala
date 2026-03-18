FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Создаем пользователя для безопасности (Hugging Face это требует)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user . $HOME/app

# Порт для сервера проверки здоровья (по умолчанию 7860 на HF)
ENV PORT=7860
ENV RENDER=true

# Команда запуска
CMD ["python", "merged_bot/main.py"]
