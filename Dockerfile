FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製requirements文件
COPY requirements.txt .

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY . .

# 暴露端口
EXPOSE 5000

# 設置環境變量
ENV FLASK_APP=src/web/trading_api.py
ENV FLASK_ENV=production

# 啟動命令
CMD ["python", "src/web/trading_api.py"]
