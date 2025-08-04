#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雲端部署腳本
幫助將智能交易系統部署到雲端服務器
"""

import os
import json
import subprocess
import sys

def create_requirements():
    """創建requirements.txt文件"""
    requirements = [
        "flask==2.3.3",
        "flask-cors==4.0.0",
        "pandas==2.0.3",
        "numpy==1.24.3",
        "requests==2.31.0",
        "python-dotenv==1.0.0"
    ]
    
    with open("requirements.txt", "w", encoding='utf-8') as f:
        f.write("\n".join(requirements))
    
    print("✅ requirements.txt 已創建")

def create_dockerfile():
    """創建Dockerfile"""
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \\
    gcc \\
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
"""
    
    with open("Dockerfile", "w", encoding='utf-8') as f:
        f.write(dockerfile_content)
    
    print("✅ Dockerfile 已創建")

def create_docker_compose():
    """創建docker-compose.yml"""
    compose_content = """version: '3.8'

services:
  trading-system:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
"""
    
    with open("docker-compose.yml", "w", encoding='utf-8') as f:
        f.write(compose_content)
    
    print("✅ docker-compose.yml 已創建")

def create_nginx_config():
    """創建Nginx配置"""
    nginx_config = """server {
    listen 80;
    server_name your-domain.com;  # 替換為你的域名

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    
    with open("nginx.conf", "w", encoding='utf-8') as f:
        f.write(nginx_config)
    
    print("✅ nginx.conf 已創建")

def create_systemd_service():
    """創建systemd服務文件"""
    service_content = """[Unit]
Description=Smart Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/AImax
Environment=PATH=/home/ubuntu/AImax/.venv/bin
ExecStart=/home/ubuntu/AImax/.venv/bin/python src/web/trading_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open("trading-system.service", "w", encoding='utf-8') as f:
        f.write(service_content)
    
    print("✅ trading-system.service 已創建")

def create_deployment_script():
    """創建部署腳本"""
    deploy_script = """#!/bin/bash

# 雲端部署腳本
echo "🚀 開始部署智能交易系統到雲端..."

# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝必要軟件
sudo apt install -y python3 python3-pip python3-venv nginx docker.io docker-compose

# 創建虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝Python依賴
pip install -r requirements.txt

# 設置Nginx
sudo cp nginx.conf /etc/nginx/sites-available/trading-system
sudo ln -sf /etc/nginx/sites-available/trading-system /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 設置systemd服務
sudo cp trading-system.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trading-system
sudo systemctl start trading-system

# 設置防火牆
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

echo "✅ 部署完成！"
echo "🌐 你的交易系統現在可以通過以下地址訪問:"
echo "   http://你的服務器IP地址"
echo ""
echo "📱 手機App訪問地址:"
echo "   http://你的服務器IP地址"
echo ""
echo "🔧 管理命令:"
echo "   sudo systemctl status trading-system  # 查看狀態"
echo "   sudo systemctl restart trading-system # 重啟服務"
echo "   sudo systemctl logs trading-system    # 查看日誌"
"""
    
    with open("deploy.sh", "w", encoding='utf-8') as f:
        f.write(deploy_script)
    
    # 設置執行權限
    os.chmod("deploy.sh", 0o755)
    
    print("✅ deploy.sh 已創建")

def create_cloud_readme():
    """創建雲端部署說明"""
    readme_content = """# 🌐 智能交易系統 - 雲端部署指南

## 📱 功能特色

- **手機友好**: 響應式設計，完美支持手機操作
- **實時監控**: 24/7 雲端運行，實時狀態更新
- **遠程控制**: 隨時隨地啟動/停止交易系統
- **安全保障**: 多重停止機制，緊急停止功能
- **數據統計**: 實時獲利統計，交易記錄查看

## 🚀 快速部署

### 方法1: 使用部署腳本 (推薦)

1. 將整個AImax文件夾上傳到雲端服務器
2. 運行部署腳本:
   ```bash
   cd AImax
   chmod +x deploy.sh
   ./deploy.sh
   ```

### 方法2: 使用Docker

1. 構建並運行:
   ```bash
   docker-compose up -d
   ```

### 方法3: 手動部署

1. 安裝依賴:
   ```bash
   pip install -r requirements.txt
   ```

2. 啟動服務:
   ```bash
   python src/web/trading_api.py
   ```

## 📱 手機App使用

1. 在手機瀏覽器中打開: `http://你的服務器IP:5000`
2. 添加到主屏幕，就像原生App一樣使用
3. 支持所有功能：
   - 🚀 啟動/停止交易系統
   - 📊 實時查看交易統計
   - ⚙️ 修改交易配置
   - 🚨 緊急停止功能
   - 📈 查看交易記錄

## 🛡️ 安全功能

- **多重停止機制**: GUI按鈕、緊急停止、文件控制
- **風險控制**: 每日虧損限制、交易次數限制
- **實時監控**: 24小時狀態監控
- **模擬模式**: 先測試再實際交易

## 🌍 雲端服務商推薦

### AWS EC2
- t2.micro (免費層)
- Ubuntu 20.04 LTS
- 開放端口: 22, 80, 443

### Google Cloud Platform
- e2-micro (免費層)
- Ubuntu 20.04 LTS

### DigitalOcean
- $5/月 Droplet
- Ubuntu 20.04 LTS

### 阿里雲 ECS
- 1核2GB (輕量應用服務器)
- Ubuntu 20.04 LTS

## 📞 API 接口

系統提供完整的RESTful API:

- `GET /api/status` - 獲取系統狀態
- `POST /api/start` - 啟動交易系統
- `POST /api/stop` - 停止交易系統
- `POST /api/emergency-stop` - 緊急停止
- `GET/POST /api/config` - 配置管理
- `GET /api/trades` - 交易記錄
- `GET /api/performance` - 績效統計
- `GET /api/market-data` - 市場數據

## 🔧 維護命令

```bash
# 查看服務狀態
sudo systemctl status trading-system

# 重啟服務
sudo systemctl restart trading-system

# 查看日誌
sudo journalctl -u trading-system -f

# 緊急停止
python scripts/emergency_stop.py
```

## 📊 監控建議

1. 設置服務器監控 (CPU、內存、磁盤)
2. 配置日誌輪轉
3. 定期備份交易數據
4. 設置異常告警

## 🆘 故障排除

### 服務無法啟動
```bash
# 檢查日誌
sudo journalctl -u trading-system -n 50

# 檢查端口占用
sudo netstat -tlnp | grep :5000
```

### 無法訪問Web界面
```bash
# 檢查防火牆
sudo ufw status

# 檢查Nginx狀態
sudo systemctl status nginx
```

## 📞 技術支持

如有問題，請檢查:
1. 服務器日誌
2. 網絡連接
3. 防火牆設置
4. 服務運行狀態
"""
    
    with open("CLOUD_DEPLOYMENT.md", "w", encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ CLOUD_DEPLOYMENT.md 已創建")

def main():
    """主函數"""
    print("🌐 智能交易系統 - 雲端部署準備")
    print("=" * 50)
    
    # 創建所有必要文件
    create_requirements()
    create_dockerfile()
    create_docker_compose()
    create_nginx_config()
    create_systemd_service()
    create_deployment_script()
    create_cloud_readme()
    
    print("\n🎉 雲端部署文件準備完成！")
    print("\n📋 接下來的步驟:")
    print("1. 將整個AImax文件夾上傳到雲端服務器")
    print("2. 在服務器上運行: chmod +x deploy.sh && ./deploy.sh")
    print("3. 在手機瀏覽器中訪問: http://你的服務器IP:5000")
    print("4. 添加到主屏幕，就像原生App一樣使用！")
    print("\n📖 詳細說明請查看: CLOUD_DEPLOYMENT.md")

if __name__ == "__main__":
    main()