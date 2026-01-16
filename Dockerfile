FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ✅ AgentBeats / A2A 标准入口
ENTRYPOINT ["python", "-m", "src.server"]
