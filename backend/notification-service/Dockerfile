FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose cổng 8006
EXPOSE 8006

# Sử dụng socket_app thay vì app và cổng 8007 thay vì 8000
CMD ["uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"] 