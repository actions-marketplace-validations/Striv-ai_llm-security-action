FROM python:3.12-slim

# Copy action source
WORKDIR /llm-policy-action
COPY . .

RUN pip install --no-cache-dir pyyaml rich

# ► Absolute path so GitHub’s work-dir override doesn’t matter
ENTRYPOINT ["python", "/llm-policy-action/entrypoint.py"]
