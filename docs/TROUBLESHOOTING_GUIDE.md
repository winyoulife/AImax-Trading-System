# 🔧 AImax 多交易對交易系統故障排除指南

## 📋 **文檔概述**
**文檔版本**: 1.0  
**更新時間**: 2025年7月27日  
**適用版本**: AImax v1.0+  

## 🎯 **故障排除概述**

本指南提供了AImax多交易對交易系統常見問題的診斷和解決方案，幫助用戶快速定位和解決系統運行中遇到的各種問題。

## 🚨 **緊急故障處理**

### **系統緊急停止**
```bash
# 立即停止所有交易
python scripts/emergency_stop.py

# 停止系統服務
sudo systemctl stop aimax

# 終止所有相關進程
pkill -f "aimax"
```

### **數據緊急備份**
```bash
# 緊急備份數據庫
python scripts/emergency_backup.py

# 備份配置文件
cp -r config/ backup/config_$(date +%Y%m%d_%H%M%S)/

# 備份日誌文件
cp -r logs/ backup/logs_$(date +%Y%m%d_%H%M%S)/
```

## 🔍 **常見問題診斷**

### **1. 系統啟動問題**

#### **問題**: 系統無法啟動
**症狀**:
- 啟動腳本執行失敗
- 進程立即退出
- 無法連接到API

**診斷步驟**:
```bash
# 檢查Python環境
python --version
which python

# 檢查依賴
pip list | grep -E "(pandas|numpy|requests)"

# 檢查配置文件
python -c "import json; json.load(open('config/trading_system.json'))"

# 檢查日誌
tail -n 50 logs/aimax.log
```

**解決方案**:
```bash
# 重新安裝依賴
pip install -r requirements.txt --force-reinstall

# 修復配置文件
python scripts/validate_config.py --fix

# 清理緩存
rm -rf __pycache__/
rm -rf .pytest_cache/
```

#### **問題**: 端口被占用
**症狀**:
- "Address already in use" 錯誤
- API服務無法啟動

**診斷步驟**:
```bash
# 檢查端口使用
netstat -tulpn | grep 8080
lsof -i :8080
```

**解決方案**:
```bash
# 終止占用進程
sudo kill -9 $(lsof -t -i:8080)

# 或修改配置使用其他端口
sed -i 's/"port": 8080/"port": 8081/' config/trading_system.json
```

### **2. AI模型問題**

#### **問題**: Ollama連接失敗
**症狀**:
- AI分析功能不工作
- "Connection refused" 錯誤
- 模型響應超時

**診斷步驟**:
```bash
# 檢查Ollama服務
ollama list
ollama ps

# 測試模型連接
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b",
  "prompt": "test"
}'
```

**解決方案**:
```bash
# 啟動Ollama服務
ollama serve

# 重新下載模型
ollama pull qwen2.5:7b

# 重啟Ollama服務
sudo systemctl restart ollama
```

#### **問題**: AI分析結果異常
**症狀**:
- 分析結果不合理
- 信心度異常低
- 決策不一致

**診斷步驟**:
```bash
# 檢查AI模型狀態
python scripts/test_ai_models.py

# 查看AI分析日誌
grep "AI_ANALYSIS" logs/aimax.log

# 測試單個AI模型
python scripts/test_individual_ai.py --model market_scanner
```

**解決方案**:
```bash
# 重置AI模型配置
cp config/ai_models.json.template config/ai_models.json

# 清理AI緩存
rm -rf data/ai_cache/

# 重新訓練模型 (如果需要)
python scripts/retrain_models.py
```

### **3. 數據問題**

#### **問題**: 市場數據獲取失敗
**症狀**:
- 價格數據不更新
- API請求失敗
- 數據延遲嚴重

**診斷步驟**:
```bash
# 測試API連接
python scripts/test_api_connection.py

# 檢查網絡連接
ping max-api.maicoin.com
curl -I https://max-api.maicoin.com/api/v2/tickers

# 查看數據更新日誌
grep "DATA_UPDATE" logs/aimax.log
```

**解決方案**:
```bash
# 重置API連接
python scripts/reset_api_connection.py

# 清理數據緩存
rm -rf data/cache/

# 使用備用數據源
python scripts/switch_data_source.py --source backup
```

#### **問題**: 數據庫錯誤
**症狀**:
- SQLite錯誤
- 數據查詢失敗
- 數據庫鎖定

**診斷步驟**:
```bash
# 檢查數據庫文件
ls -la data/*.db
sqlite3 data/market_history.db ".schema"

# 檢查數據庫完整性
python scripts/check_database_integrity.py

# 查看數據庫錯誤日誌
grep "DATABASE_ERROR" logs/aimax.log
```

**解決方案**:
```bash
# 修復數據庫
python scripts/repair_database.py

# 重建數據庫索引
python scripts/rebuild_indexes.py

# 從備份恢復
python scripts/restore_database.py --backup latest
```

### **4. 策略執行問題**

#### **問題**: 策略無法啟動
**症狀**:
- 策略狀態顯示錯誤
- 策略配置無效
- 權限不足

**診斷步驟**:
```bash
# 檢查策略配置
python scripts/validate_strategy_config.py

# 查看策略日誌
grep "STRATEGY" logs/aimax.log

# 測試策略邏輯
python scripts/test_strategy.py --strategy grid_btc_001
```

**解決方案**:
```bash
# 重置策略配置
python scripts/reset_strategy_config.py --strategy grid_btc_001

# 清理策略緩存
rm -rf data/strategy_cache/

# 重新創建策略
python scripts/recreate_strategy.py --config strategy_config.json
```

#### **問題**: 交易執行失敗
**症狀**:
- 訂單提交失敗
- 餘額不足
- 交易權限問題

**診斷步驟**:
```bash
# 檢查賬戶餘額
python scripts/check_balance.py

# 檢查交易權限
python scripts/check_trading_permissions.py

# 查看交易日誌
grep "TRADE_EXECUTION" logs/aimax.log
```

**解決方案**:
```bash
# 更新API權限
python scripts/update_api_permissions.py

# 調整倉位大小
python scripts/adjust_position_size.py --reduce 50

# 重新同步賬戶狀態
python scripts/sync_account_status.py
```

### **5. 性能問題**

#### **問題**: 系統響應緩慢
**症狀**:
- GUI更新延遲
- API響應時間長
- CPU使用率高

**診斷步驟**:
```bash
# 檢查系統資源
htop
free -h
df -h

# 分析性能瓶頸
python scripts/performance_profiler.py

# 檢查線程狀態
python scripts/check_thread_status.py
```

**解決方案**:
```bash
# 優化系統配置
python scripts/optimize_performance.py

# 清理系統緩存
python scripts/clear_system_cache.py

# 重啟系統服務
sudo systemctl restart aimax
```

#### **問題**: 內存使用過高
**症狀**:
- 內存使用率超過85%
- 系統變慢
- 進程被終止

**診斷步驟**:
```bash
# 檢查內存使用
python scripts/memory_analyzer.py

# 查看內存洩漏
python scripts/detect_memory_leaks.py

# 分析對象引用
python scripts/analyze_object_references.py
```

**解決方案**:
```bash
# 調整內存限制
sed -i 's/"memory_limit_mb": 2048/"memory_limit_mb": 4096/' config/trading_system.json

# 啟用垃圾回收
python scripts/force_garbage_collection.py

# 重啟系統釋放內存
sudo systemctl restart aimax
```

## 🔧 **診斷工具**

### **1. 系統診斷腳本**
```bash
#!/bin/bash
# system_diagnosis.sh

echo "=== AImax系統診斷報告 ==="
echo "時間: $(date)"
echo

echo "1. 系統狀態檢查"
python scripts/health_check.py

echo "2. 進程狀態檢查"
ps aux | grep aimax

echo "3. 端口狀態檢查"
netstat -tulpn | grep -E "(8080|11434)"

echo "4. 磁盤空間檢查"
df -h

echo "5. 內存使用檢查"
free -h

echo "6. 日誌錯誤檢查"
tail -n 100 logs/aimax.log | grep -E "(ERROR|CRITICAL)"

echo "診斷完成"
```

### **2. 性能監控腳本**
```python
#!/usr/bin/env python3
# performance_monitor.py

import psutil
import time
import json
from datetime import datetime

def monitor_performance():
    """監控系統性能"""
    while True:
        stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict()
        }
        
        print(json.dumps(stats, indent=2))
        
        # 檢查異常情況
        if stats['cpu_percent'] > 80:
            print("⚠️  CPU使用率過高!")
        if stats['memory_percent'] > 85:
            print("⚠️  內存使用率過高!")
        if stats['disk_percent'] > 90:
            print("⚠️  磁盤空間不足!")
        
        time.sleep(60)

if __name__ == "__main__":
    monitor_performance()
```

### **3. 日誌分析工具**
```python
#!/usr/bin/env python3
# log_analyzer.py

import re
from collections import Counter
from datetime import datetime, timedelta

def analyze_logs(log_file='logs/aimax.log', hours=24):
    """分析日誌文件"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    errors = []
    warnings = []
    patterns = {
        'api_errors': r'API.*ERROR',
        'database_errors': r'DATABASE.*ERROR',
        'strategy_errors': r'STRATEGY.*ERROR',
        'ai_errors': r'AI.*ERROR'
    }
    
    with open(log_file, 'r') as f:
        for line in f:
            # 解析時間戳
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                log_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                if log_time < cutoff_time:
                    continue
            
            # 分類錯誤
            if 'ERROR' in line:
                errors.append(line.strip())
            elif 'WARNING' in line:
                warnings.append(line.strip())
    
    # 統計錯誤類型
    error_types = Counter()
    for error in errors:
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, error):
                error_types[pattern_name] += 1
    
    print(f"=== 日誌分析報告 (最近{hours}小時) ===")
    print(f"錯誤總數: {len(errors)}")
    print(f"警告總數: {len(warnings)}")
    print("\n錯誤類型統計:")
    for error_type, count in error_types.most_common():
        print(f"  {error_type}: {count}")
    
    if errors:
        print("\n最近的錯誤:")
        for error in errors[-5:]:
            print(f"  {error}")

if __name__ == "__main__":
    analyze_logs()
```

## 📚 **維護建議**

### **1. 定期維護任務**
```bash
# 每日維護
0 2 * * * /path/to/aimax/scripts/daily_maintenance.sh

# 每週維護
0 3 * * 0 /path/to/aimax/scripts/weekly_maintenance.sh

# 每月維護
0 4 1 * * /path/to/aimax/scripts/monthly_maintenance.sh
```

### **2. 監控告警設置**
```json
{
  "alerts": {
    "cpu_threshold": 80,
    "memory_threshold": 85,
    "disk_threshold": 90,
    "error_rate_threshold": 10,
    "response_time_threshold": 1000
  }
}
```

### **3. 備份策略**
```bash
# 數據庫備份
0 1 * * * /path/to/aimax/scripts/backup_database.py

# 配置備份
0 2 * * * /path/to/aimax/scripts/backup_config.py

# 日誌歸檔
0 3 * * * /path/to/aimax/scripts/archive_logs.py
```

## 🆘 **緊急聯繫**

### **技術支持**
- **郵箱**: support@aimax.com
- **電話**: +886-2-1234-5678
- **在線支持**: https://support.aimax.com

### **社區支持**
- **GitHub Issues**: https://github.com/aimax/issues
- **Discord**: https://discord.gg/aimax
- **論壇**: https://forum.aimax.com

---

**📚 本故障排除指南提供了AImax系統常見問題的診斷和解決方案。**

*文檔版本: 1.0*  
*更新時間: 2025年7月27日*  
*維護者: AImax開發團隊*