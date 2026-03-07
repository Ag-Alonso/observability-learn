FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY distribution_tracker.py .
COPY db.py .
COPY indicators.py .

CMD ["python", "distribution_tracker.py"]


