FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir . pytest httpx
COPY app app
COPY migrations migrations
COPY data data
COPY scripts scripts
COPY README.md DESIGN.md BUILDLOG.md EVIDENCE.md capstone.yaml ./

