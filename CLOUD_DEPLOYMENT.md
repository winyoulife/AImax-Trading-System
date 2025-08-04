# 🌐 智能交易系統 - 雲端部署指南

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
