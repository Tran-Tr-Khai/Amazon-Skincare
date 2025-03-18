FROM apache/airflow:2.9.2

USER root

# Cài đặt các gói hệ thống cần thiết (nếu cần thêm cho Selenium hoặc các thư viện khác)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Quay lại user airflow (mặc định của Airflow image)
USER airflow

# Sao chép file requirements.txt vào container
COPY requirements.txt .

# Cài đặt các thư viện từ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# (Tùy chọn) Đặt biến môi trường PYTHONPATH nếu cần
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow"
