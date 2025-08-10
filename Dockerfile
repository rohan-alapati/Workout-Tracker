FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/src/instance

EXPOSE 8000
ENV FLASK_APP="src.app:create_app"
CMD sh -c "flask db upgrade && gunicorn -w 3 -b 0.0.0.0:8000 wsgi:app"
