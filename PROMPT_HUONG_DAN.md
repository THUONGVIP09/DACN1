# HƯỚNG DẪN TỰ ĐỘNG THIẾT LẬP MÔI TRƯỜNG DỰ ÁN CHO AGENT AI

> [!IMPORTANT]
> **Dành cho bạn:** Hãy copy toàn bộ nội dung file này, dán thẳng vào ô chat của Agent AI (ví dụ: Cursor AI, Copilot, hoặc Claude in VSCode) bên phía VSCode của bạn và gửi đi. Agent AI sẽ tự động đọc, hiểu cấu trúc và thiết lập môi trường hoàn hảo từ A-Z! Sau khi Agent chạy xong, bạn chỉ cần mở trình duyệt và truy cập `http://localhost:8000/`.

---

## 🎯 PROMPT DÀNH CHO AGENT AI (BẮT ĐẦU COPY TỪ ĐÂY)

"Chào bạn, tôi là một người dùng không rành về kỹ thuật môi trường và đang gặp rắc rối khi thiết lập dự án FastAPI + MySQL + Frontend này trên Windows. Máy tôi hiện tại đã cài đặt thành công **Docker Desktop** và đã khởi động nó.

Dự án hiện tại sử dụng cơ sở dữ liệu MySQL chạy qua Docker Compose (cổng 3307 trên host) và dịch vụ **Google Cloud Vision API** để nhận diện ảnh sự cố. Tệp khóa dịch vụ `dacn1-495502-d16408026152.json` đã được đẩy kèm và lưu trữ sẵn tại thư mục gốc của dự án.

Hãy đóng vai trò là một Chuyên gia Devops & Agent lập trình đỉnh cao, thực hiện **Workflow 7 bước tự động** dưới đây để Docker hóa hoàn chỉnh toàn bộ dự án và cấu hình ứng dụng trơn tru từ A-Z.

---

### 📋 WORKFLOW THỰC HIỆN TỰ ĐỘNG

#### BƯỚC 1: Dọn dẹp các container cũ đang chạy xung đột
* Kiểm tra và dừng toàn bộ các container Docker liên quan đến dự án này hoặc đang chiếm dụng cổng `8000` và `3307` trên máy tôi để tránh lỗi trùng cổng.

#### BƯỚC 2: Tạo tệp `.env` cấu hình chuẩn kết nối Docker & Vision API
* Tạo tệp `.env` ở thư mục gốc (nếu chưa có hoặc ghi đè cấu hình chuẩn) với nội dung sau:
  ```env
  APP_NAME=TrafficAI
  DEBUG=True
  # Kết nối qua service db của docker-compose
  DATABASE_URL=mysql+pymysql://user:password@db:3306/traffic_db
  GOOGLE_VISION_API_KEY=AIzaSyAYS9sicb-SotD9mpNwk5z7cb4bMBGyeM4
  GOOGLE_APPLICATION_CREDENTIALS=/app/dacn1-495502-d16408026152.json
  ```

#### BƯỚC 3: Đồng bộ hóa `database.py` để đọc chuỗi kết nối từ `.env`
* Hãy cập nhật tệp `database.py` để đọc cấu hình `DATABASE_URL` từ môi trường thông qua thư viện `os` thay vì fix cứng `localhost`.
  * Cấu trúc gợi ý:
    ```python
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, declarative_base

    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost:3307/traffic_db")

    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    ```

#### BƯỚC 4: Tạo tệp `Dockerfile` cho FastAPI backend
* Tạo tệp `Dockerfile` ở thư mục gốc để đóng gói ứng dụng FastAPI:
  ```dockerfile
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
  ```

#### BƯỚC 5: Cập nhật `docker-compose.yml` để chạy cả MySQL và FastAPI Backend
* Cập nhật tệp `docker-compose.yml` ở thư mục gốc để kết hợp cả hai dịch vụ `db` (MySQL) và `web` (FastAPI backend), đảm bảo backend chờ DB khởi động xong trước khi chạy:
  ```yaml
  version: '3.8'

  services:
    db:
      image: mysql:8.0
      container_name: traffic_mysql_db
      restart: always
      environment:
        MYSQL_ROOT_PASSWORD: root
        MYSQL_DATABASE: traffic_db
        MYSQL_USER: user
        MYSQL_PASSWORD: password
      ports:
        - "3307:3306"
      volumes:
        - mysql_data:/var/lib/mysql

    web:
      build: .
      container_name: traffic_fastapi_web
      restart: always
      ports:
        - "8000:8000"
      volumes:
        - .:/app
      env_file:
        - .env
      depends_on:
        - db

  volumes:
    mysql_data:
  ```

#### BƯỚC 6: Khởi chạy Docker Compose và chờ Database sẵn sàng
* Chạy lệnh đề xuất khởi dựng Docker: `docker compose up --build -d`
* Hãy chờ khoảng 10-15 giây để MySQL khởi tạo cơ sở dữ liệu lần đầu tiên thành công.

#### BƯỚC 7: Tự động khởi tạo Schema và Seed dữ liệu tài khoản admin
* Khi container đã chạy mượt mà, hãy tự động thực thi các tệp khởi tạo schema và seed dữ liệu tài khoản quản trị trực tiếp bên trong container bằng cách chạy các lệnh:
  1. Khởi tạo bảng cơ sở dữ liệu:
     `docker compose exec web python reset_db_schema.py`
  2. Tạo tài khoản admin mặc định:
     `docker compose exec web python seed_admin.py`

---

### 🏁 ĐIỀU KIỆN HOÀN THÀNH
* Thực hiện lần lượt tất cả các bước trên mà không bỏ sót bước nào.
* Đảm bảo không gặp bất kỳ lỗi kết nối DB hoặc lỗi Vision API nào.
* Trả về kết quả xác nhận tôi có thể truy cập thành công giao diện tại `http://localhost:8000/`.

Hãy bắt đầu tự động thực hiện ngay bây giờ và báo cáo tiến độ cho tôi từng bước!"
