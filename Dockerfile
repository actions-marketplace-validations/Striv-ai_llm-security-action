FROM python:3.12-slim

# Copy code
COPY . /app
WORKDIR /app

# Lightweight deps
RUN pip install --no-cache-dir pyyaml rich

ENTRYPOINT ["python", "entrypoint.py"]
