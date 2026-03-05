FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY wick-play-5d.py .
EXPOSE 5000
CMD ["python", "wick-play-5d.py"]

