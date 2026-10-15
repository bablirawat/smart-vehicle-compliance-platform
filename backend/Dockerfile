FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "if [ ! -f smart_vehicle.db ]; then python seed_data.py; fi && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
