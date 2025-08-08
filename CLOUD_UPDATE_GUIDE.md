# 🚀 AImax 雲端更新指南

## ⚠️ 重要提醒
**請務必使用指定的更新方法，不要隨意使用其他腳本！**

---

## 📋 正確的雲端更新方法

### 🎯 唯一推薦的更新命令
```bash
python scripts/ultimate_cloud_deploy.py
```

### ✅ 這個工具會自動處理：
- 🔄 版本號自動更新
- 📁 文件同步 (主文件 → 靜態文件 → 備份文件)
- 🚀 GitHub Actions 優化部署
- 🔍 自動驗證部署結果
- 💾 強制清除瀏覽器緩存
- 📊 創建多重訪問地址

---

## ❌ 不要使用的舊方法

### 已廢棄的腳本 (不要使用)：
- ❌ `scripts/quick_update.py` - 舊版本，有緩存問題
- ❌ `scripts/force_cache_clear.py` - 功能已整合
- ❌ `scripts/cloud_update_manager.py` - 已過時
- ❌ `scripts/force_github_pages_update.py` - 已過時
- ❌ `force_update_dashboard.py` - 臨時解決方案
- ❌ `quick_deploy.bat` - 用於全新部署，不是更新

### 已禁用的 GitHub Actions：
- ❌ `.github/workflows/simple-deploy.yml` - 已移至 disabled 目錄
- ✅ `.github/workflows/ultimate-deploy.yml` - 新的優化版本

---

## 🔧 使用步驟

### 1. 修改代碼後，執行更新：
```bash
cd AImax
python scripts/ultimate_cloud_deploy.py
```

### 2. 等待部署完成 (約1-2分鐘)

### 3. 訪問更新後的頁面：
工具會自動提供3個訪問地址，選擇任一個即可

---

## 📊 更新後的特性

### 🎯 混合高頻策略：
- 前端：每30秒 CORS代理實時數據
- 後端：每2分鐘 GitHub Actions備援
- 容錯：三層備援機制

### 🔄 版本管理：
- 自動版本號：`v3.0-ultimate-YYYYMMDDHHMMSS`
- 時間戳備份：防止緩存問題
- 多重訪問地址：確保可用性

### 💾 緩存控制：
- 強制清除瀏覽器緩存
- 禁用 Jekyll 處理
- 添加緩存控制標頭

---

## 🚨 故障排除

### 如果更新後看不到變化：
1. **等待2-3分鐘** - GitHub Pages需要時間更新
2. **按 Ctrl+F5** - 強制刷新頁面
3. **清除瀏覽器緩存** - 設置 → 隱私 → 清除數據
4. **使用無痕模式** - 避免緩存干擾
5. **嘗試備份地址** - 工具會提供多個URL

### 如果部署失敗：
1. 檢查網絡連接
2. 確認 Git 狀態正常
3. 重新運行部署工具
4. 查看 GitHub Actions 運行日誌

---

## 📝 更新日誌

### v3.0-ultimate (2025/08/08)
- ✅ 創建終極雲端部署系統
- ✅ 整合混合高頻策略
- ✅ 解決緩存更新問題
- ✅ 自動化部署驗證
- ✅ 多重備份機制

### v2.3-hybrid (2025/08/08)
- ✅ 實施混合高頻價格更新
- ✅ CORS代理 + GitHub Actions備援
- ✅ 每30秒前端更新

### v2.3-updated (2025/08/08)
- ✅ 基礎版本，存在緩存問題

---

## 🎯 重要提醒

### ⚠️ 請記住：
1. **只使用** `python scripts/ultimate_cloud_deploy.py`
2. **不要使用** 其他舊的更新腳本
3. **等待部署完成** 再檢查結果
4. **使用工具提供的URL** 訪問更新後的頁面

### 📞 如有問題：
- 檢查本指南的故障排除部分
- 查看 GitHub Actions 運行狀態
- 確認使用正確的更新命令

---

**記住：`python scripts/ultimate_cloud_deploy.py` 是唯一正確的更新方法！** 🚀