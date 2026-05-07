FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết cho mysqlclient và google-cloud-vision
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pymysql cryptography uvicorn fastapi sqlalchemy python-multipart jinja2 google-cloud-vision requests

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
