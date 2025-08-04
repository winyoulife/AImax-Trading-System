# 🤖 AImax - 智能交易系統

一個功能完整的智能加密貨幣交易系統，具備85.7%勝率的智能平衡策略，支援雲端部署和手機App控制。

## ✨ 核心特色

- 🎯 **高勝率策略**: 智能平衡版本達到85.7%勝率
- 📱 **手機App控制**: 響應式Web界面，隨時隨地控制交易
- ☁️ **雲端部署**: 支援Docker、AWS、GCP等雲端平台
- 🔄 **實時數據**: 直接從MAX交易所獲取實時BTC價格
- 🛡️ **安全保障**: 多重停止機制、風險控制、緊急停止
- 📊 **智能分析**: 多重技術指標結合，動態閾值調整
- 🔔 **Telegram通知**: 即時交易通知和狀態更新

## 📊 策略表現

### 🏆 智能平衡版本 (推薦)
- **勝率**: 85.7% (6勝1敗)
- **總獲利**: 198,232 TWD
- **平均獲利**: 28,319 TWD/筆
- **信號強度**: 87.5/100

### 📈 其他版本比較
| 策略版本 | 勝率 | 交易次數 | 總獲利 | 平均獲利 |
|---------|------|----------|--------|----------|
| 進階版本 | 75.0% | 8筆 | 158,092 TWD | 19,761 TWD |
| 超級版本 | 77.8% | 9筆 | 53,321 TWD | 5,925 TWD |
| 智能平衡版本 | 85.7% | 7筆 | 198,232 TWD | 28,319 TWD |

## 🚀 快速開始

### 方法1: 本地運行
```bash
# 克隆項目
git clone https://github.com/你的用戶名/AImax.git
cd AImax

# 安裝依賴
pip install -r requirements.txt

# 啟動Web控制台
python src/web/trading_api.py

# 在瀏覽器中打開
http://localhost:5000
```

### 方法2: 雲端部署
```bash
# 準備部署文件
python deploy_cloud.py

# 上傳到雲端服務器後運行
chmod +x deploy.sh
./deploy.sh

# 在手機瀏覽器中訪問
http://你的服務器IP:5000
```

### 方法3: Docker部署
```bash
# 使用Docker Compose
docker-compose up -d

# 訪問服務
http://localhost:5000
```

## 📱 手機App使用

1. **訪問Web界面**: 在手機瀏覽器中打開系統地址
2. **添加到主屏幕**: 點擊瀏覽器的"添加到主屏幕"
3. **完整功能**: 支援所有桌面版功能
   - 🚀 啟動/停止交易系統
   - 📊 實時查看交易統計
   - ⚙️ 修改交易配置
   - 🚨 緊急停止功能
   - 📈 查看交易記錄

## 🛡️ 安全功能

### 多重停止機制
- **Web界面控制**: 啟動/停止按鈕
- **緊急停止按鈕**: 一鍵停止所有交易
- **緊急停止文件**: `python scripts/emergency_stop.py`
- **系統信號處理**: Ctrl+C 安全退出

### 風險控制
- **每日虧損限制**: 預設5,000 TWD
- **每日交易次數限制**: 預設5次
- **最大持倉時間**: 預設24小時
- **緊急停損**: 預設5%

### 模擬交易
- **安全測試**: 先用模擬模式測試策略
- **零風險**: 不會有實際資金損失
- **完整功能**: 所有功能都可以在模擬模式下測試

## 📊 技術指標

### 智能平衡策略使用的指標
- **MACD**: 主要交易信號
- **成交量分析**: 動態閾值調整
- **RSI**: 超買超賣確認
- **布林帶**: 價格位置分析
- **趨勢分析**: 多時間框架確認
- **市場強度**: 綜合評分系統

### 動態評分系統
- **基礎分數**: 根據市場條件調整
- **分級評分**: 不是簡單的通過/不通過
- **智能獎勵**: 強勢市場額外加分
- **風險調整**: 高風險時提高門檻

## 🌐 API接口

系統提供完整的RESTful API:

```bash
# 系統控制
GET  /api/status          # 獲取系統狀態
POST /api/start           # 啟動交易系統
POST /api/stop            # 停止交易系統
POST /api/emergency-stop  # 緊急停止

# 配置管理
GET  /api/config          # 獲取配置
POST /api/config          # 更新配置

# 數據查詢
GET  /api/trades          # 交易記錄
GET  /api/performance     # 績效統計
GET  /api/market-data     # 實時市場數據
```

## 💰 資金配置

### 靈活的資金設定
- **任意金額**: 可以從10,000 TWD開始
- **比例獲利**: 勝率和獲利比例保持不變
- **風險控制**: 根據資金量調整風險參數

### 獲利計算範例
```
如果你投入 50,000 TWD:
- 預期總獲利: 198,232 * (50,000/3,490,000) ≈ 2,840 TWD
- 平均每筆獲利: 28,319 * (50,000/3,490,000) ≈ 406 TWD
- 勝率依然是: 85.7%
```

## 🔧 系統架構

```
AImax/
├── src/
│   ├── core/                 # 核心交易策略
│   │   ├── smart_balanced_volume_macd_signals.py  # 智能平衡策略
│   │   ├── advanced_volume_macd_signals.py       # 進階策略
│   │   └── ...
│   ├── data/                 # 數據獲取
│   │   └── data_fetcher.py   # 實時數據獲取器
│   ├── trading/              # 交易管理
│   │   └── safe_trading_manager.py  # 安全交易管理器
│   ├── web/                  # Web界面
│   │   ├── trading_api.py    # API服務器
│   │   └── templates/        # Web模板
│   └── notifications/        # 通知系統
├── scripts/                  # 工具腳本
├── config/                   # 配置文件
└── docs/                     # 文檔
```

## 🌍 雲端部署

### 支援的雲端平台
- **AWS EC2**: t2.micro (免費層)
- **Google Cloud**: e2-micro (免費層)
- **DigitalOcean**: $5/月 Droplet
- **阿里雲**: 輕量應用服務器
- **Heroku**: 免費層支援

### 部署步驟
1. 運行 `python deploy_cloud.py` 準備部署文件
2. 將項目上傳到雲端服務器
3. 運行 `./deploy.sh` 自動部署
4. 在手機上訪問你的服務器IP

詳細部署說明請查看: [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md)

## 🔔 Telegram通知

### 設定Telegram機器人
1. 創建Telegram機器人
2. 配置 `config/telegram_config.py`
3. 啟動通知服務

### 通知功能
- 交易信號提醒
- 系統狀態更新
- 獲利統計報告
- 異常情況警告

## 🆘 故障排除

### 常見問題
1. **無法獲取數據**: 檢查網絡連接和API限制
2. **服務無法啟動**: 檢查端口占用和依賴安裝
3. **交易信號異常**: 檢查市場數據和策略參數

### 日誌查看
```bash
# 查看系統日誌
sudo journalctl -u trading-system -f

# 查看API日誌
tail -f logs/trading_api.log
```

### 緊急處理
```bash
# 緊急停止所有交易
python scripts/emergency_stop.py

# 重置系統狀態
python scripts/emergency_stop.py reset
```

## 📞 技術支持

### 開發團隊
- 核心策略開發
- 系統架構設計
- 雲端部署支援

### 社群支援
- GitHub Issues
- 技術文檔
- 使用指南

## 📄 許可證

本項目採用 MIT 許可證 - 詳見 [LICENSE](LICENSE) 文件

## ⚠️ 免責聲明

本系統僅供學習和研究使用。加密貨幣交易存在風險，請謹慎投資，並在充分了解風險的情況下使用本系統。開發者不對任何投資損失承擔責任。

---

**🚀 開始你的智能交易之旅！**

立即部署AImax，體驗85.7%勝率的智能交易策略！