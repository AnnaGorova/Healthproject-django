FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Тимчасово: settings.py використовує стару назву Europe/Kiev.
# Можна прибрати, коли TIME_ZONE зміниться на Europe/Kyiv.
RUN apt-get update && apt-get install -y --no-install-recommends tzdata-legacy && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN SECRET_KEY=build-only EMAIL_HOST_USER=build@example.com EMAIL_HOST_PASSWORD=build \
    python manage.py collectstatic --no-input

USER appuser
EXPOSE 8000

CMD ["gunicorn", "healthproject.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]