FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY distribution_tracker.py .
COPY db.py .
COPY indicators.py .
COPY web_app.py .

CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8000"]


