# Stage 1 - Build

FROM python:3.11-slim AS build

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wick-play.py .


# Stage 2 - Runtime

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=build /app /app
EXPOSE 5000
CMD ["python", "wick-play.py"]
