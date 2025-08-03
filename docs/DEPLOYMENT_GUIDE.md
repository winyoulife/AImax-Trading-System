# 🚀 AImax 多交易對交易系統部署指南

## 📋 **文檔概述**
**文檔版本**: 1.0  
**更新時間**: 2025年7月27日  
**適用版本**: AImax v1.0+  

## 🎯 **部署概述**

本指南詳細說明了AImax多交易對交易系統的部署流程，包括環境準備、依賴安裝、配置設置、系統啟動和監控等步驟。

## 📋 **系統要求**

### **硬件要求**
- **CPU**: 4核心以上 (推薦8核心)
- **內存**: 8GB以上 (推薦16GB)
- **存儲**: 50GB可用空間 (推薦SSD)
- **網絡**: 穩定的互聯網連接

### **軟件要求**
- **操作系統**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8+ (推薦3.9+)
- **Git**: 最新版本
- **Ollama**: 用於AI模型運行

## 🔧 **環境準備**

### **1. Python環境設置**
```bash
# 檢查Python版本
python --version

# 創建虛擬環境
python -m venv aimax_env

# 激活虛擬環境 (Windows)
aimax_env\Scripts\activate

# 激活虛擬環境 (macOS/Linux)
source aimax_env/bin/activate

# 升級pip
pip install --upgrade pip
```

### **2. Ollama安裝和配置**
```bash
# 安裝Ollama (Windows)
# 下載並運行: https://ollama.ai/download

# 安裝Ollama (macOS)
brew install ollama

# 安裝Ollama (Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# 啟動Ollama服務
ollama serve

# 下載AI模型
ollama pull qwen2.5:7b
```

### **3. 獲取源代碼**
```bash
# 克隆倉庫
git clone https://github.com/your-repo/aimax.git
cd aimax

# 檢查分支
git branch -a
git checkout main
```

## 📦 **依賴安裝**

### **1. 安裝Python依賴**
```bash
# 安裝核心依賴
pip install -r requirements.txt

# 安裝開發依賴 (可選)
pip install -r requirements-dev.txt

# 驗證安裝
python -c "import pandas, numpy, requests, sqlite3; print('依賴安裝成功')"
```

### **2. 安裝額外組件**
```bash
# 安裝GUI依賴
pip install tkinter matplotlib plotly

# 安裝測試依賴
pip install pytest pytest-cov

# 安裝性能監控依賴
pip install psutil memory-profiler
```

## ⚙️ **配置設置**

### **1. 基本配置**
```bash
# 複製配置模板
cp config/trading_system.json.template config/trading_system.json
cp config/ai_models.json.template config/ai_models.json

# 編輯配置文件
nano config/trading_system.json
```

### **2. API配置**
```json
{
  "api": {
    "max_api_key": "YOUR_MAX_API_KEY",
    "max_api_secret": "YOUR_MAX_API_SECRET",
    "base_url": "https://max-api.maicoin.com"
  }
}
```

### **3. 數據庫初始化**
```bash
# 創建數據庫目錄
mkdir -p data

# 初始化數據庫
python scripts/initialize_database.py

# 驗證數據庫
python scripts/validate_database.py
```

## 🚀 **系統部署**

### **1. 開發環境部署**
```bash
# 設置環境變量
export AIMAX_ENV=development
export AIMAX_DEBUG=true

# 啟動系統
python -m aimax.main --env development

# 或使用腳本啟動
python scripts/run_development.py
```

### **2. 生產環境部署**
```bash
# 設置環境變量
export AIMAX_ENV=production
export AIMAX_DEBUG=false

# 創建系統服務 (Linux)
sudo cp scripts/aimax.service /etc/systemd/system/
sudo systemctl enable aimax
sudo systemctl start aimax

# 檢查服務狀態
sudo systemctl status aimax
```

### **3. Docker部署 (可選)**
```bash
# 構建Docker鏡像
docker build -t aimax:latest .

# 運行容器
docker run -d \
  --name aimax \
  -p 8080:8080 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  aimax:latest

# 檢查容器狀態
docker ps
docker logs aimax
```

## 🔍 **部署驗證**

### **1. 系統健康檢查**
```bash
# 檢查系統狀態
python scripts/health_check.py

# 檢查API連接
python scripts/test_api_connection.py

# 檢查AI模型
python scripts/test_ai_models.py
```

### **2. 功能測試**
```bash
# 運行基本測試
python -m pytest tests/basic/

# 運行集成測試
python -m pytest tests/integration/

# 運行性能測試
python scripts/performance_test.py
```

### **3. 監控設置**
```bash
# 啟動監控服務
python scripts/start_monitoring.py

# 檢查監控指標
curl http://localhost:8080/api/v1/system/status

# 設置告警
python scripts/setup_alerts.py
```

## 📊 **監控和維護**

### **1. 系統監控**
```bash
# 實時監控
python scripts/system_monitor.py

# 性能分析
python scripts/performance_analyzer.py

# 日誌分析
tail -f logs/aimax.log
```

### **2. 數據備份**
```bash
# 手動備份
python scripts/backup_data.py

# 設置自動備份
crontab -e
# 添加: 0 2 * * * /path/to/aimax/scripts/backup_data.py
```

### **3. 系統更新**
```bash
# 停止系統
sudo systemctl stop aimax

# 更新代碼
git pull origin main

# 更新依賴
pip install -r requirements.txt --upgrade

# 重啟系統
sudo systemctl start aimax
```

## 🔧 **配置優化**

### **1. 性能調優**
```json
{
  "performance": {
    "max_threads": 50,
    "memory_limit_mb": 4096,
    "api_rate_limit": 200,
    "cache_size_mb": 1024
  }
}
```

### **2. 安全加固**
```bash
# 設置文件權限
chmod 600 config/*.json
chmod 700 scripts/*.py

# 配置防火牆
sudo ufw allow 8080/tcp
sudo ufw enable
```

### **3. 日誌配置**
```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/aimax.log",
    "max_size_mb": 100,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

## 🚨 **故障排除**

### **1. 常見問題**

#### **依賴問題**
```bash
# 重新安裝依賴
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# 清理緩存
pip cache purge
```

#### **權限問題**
```bash
# 修復權限
sudo chown -R $USER:$USER /path/to/aimax
chmod -R 755 /path/to/aimax
```

#### **端口衝突**
```bash
# 檢查端口使用
netstat -tulpn | grep 8080

# 終止進程
sudo kill -9 $(lsof -t -i:8080)
```

### **2. 日誌分析**
```bash
# 查看錯誤日誌
grep ERROR logs/aimax.log

# 查看警告日誌
grep WARNING logs/aimax.log

# 實時監控日誌
tail -f logs/aimax.log | grep -E "(ERROR|WARNING)"
```

### **3. 性能問題**
```bash
# 檢查系統資源
htop
df -h
free -h

# 分析性能瓶頸
python scripts/performance_profiler.py
```

## 🔄 **升級流程**

### **1. 準備升級**
```bash
# 備份當前版本
cp -r /path/to/aimax /path/to/aimax_backup_$(date +%Y%m%d)

# 備份數據庫
python scripts/backup_database.py
```

### **2. 執行升級**
```bash
# 停止服務
sudo systemctl stop aimax

# 更新代碼
git fetch origin
git checkout v1.1.0

# 更新依賴
pip install -r requirements.txt --upgrade

# 運行遷移腳本
python scripts/migrate_database.py
```

### **3. 驗證升級**
```bash
# 啟動服務
sudo systemctl start aimax

# 檢查狀態
python scripts/health_check.py

# 運行測試
python -m pytest tests/smoke/
```

## 📚 **部署腳本**

### **1. 一鍵部署腳本**
```bash
#!/bin/bash
# deploy.sh

set -e

echo "開始部署AImax系統..."

# 檢查環境
python --version
ollama --version

# 安裝依賴
pip install -r requirements.txt

# 初始化數據庫
python scripts/initialize_database.py

# 啟動系統
python -m aimax.main

echo "部署完成！"
```

### **2. 健康檢查腳本**
```bash
#!/bin/bash
# health_check.sh

# 檢查進程
if pgrep -f "aimax.main" > /dev/null; then
    echo "✅ AImax進程運行正常"
else
    echo "❌ AImax進程未運行"
    exit 1
fi

# 檢查API
if curl -s http://localhost:8080/api/v1/system/status > /dev/null; then
    echo "✅ API服務正常"
else
    echo "❌ API服務異常"
    exit 1
fi

echo "✅ 系統健康檢查通過"
```

---

**📚 本部署指南提供了AImax系統的完整部署流程，確保系統正確安裝和運行。**

*文檔版本: 1.0*  
*更新時間: 2025年7月27日*  
*維護者: AImax開發團隊*