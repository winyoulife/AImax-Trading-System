# 📡 AImax 多交易對交易系統 API 文檔

## 📋 **文檔概述**
**API版本**: v1.0  
**更新時間**: 2025年7月27日  
**基礎URL**: `http://localhost:8080/api/v1`  

## 🎯 **API概述**

AImax API提供了完整的RESTful接口，支持系統狀態查詢、交易對數據獲取、策略管理、AI分析結果查詢等功能。所有API都支持JSON格式的請求和響應。

### **核心特性**
- 🔒 **安全認證**: API密鑰認證機制
- 📊 **實時數據**: 實時市場數據和分析結果
- 🎛️ **策略控制**: 完整的策略管理功能
- 🤖 **AI集成**: 五AI協作分析結果
- 📈 **歷史數據**: 豐富的歷史數據查詢
- ⚡ **高性能**: 優化的響應速度和併發處理

## 🔐 **認證機制**

### **API密鑰認證**
所有API請求都需要在請求頭中包含API密鑰：

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

## 📊 **系統狀態API**

### **獲取系統狀態**
```http
GET /api/v1/system/status
```

**響應示例**:
```json
{
  "status": "running",
  "uptime": 3600,
  "version": "1.0.0",
  "environment": "production",
  "active_pairs": 6,
  "active_strategies": 12,
  "system_health": "healthy",
  "last_update": "2025-01-27T10:00:00Z",
  "performance": {
    "cpu_usage": 45.2,
    "memory_usage": 62.8,
    "disk_usage": 35.1
  }
}
```

## 💱 **交易對數據API**

### **獲取支持的交易對列表**
```http
GET /api/v1/pairs
```

### **獲取交易對實時數據**
```http
GET /api/v1/pairs/{pair}/ticker
```

### **獲取K線數據**
```http
GET /api/v1/pairs/{pair}/klines?timeframe=5m&limit=50
```

## 🎛️ **策略管理API**

### **獲取策略列表**
```http
GET /api/v1/strategies
```

### **創建策略**
```http
POST /api/v1/strategies
```

### **啟動/停止策略**
```http
POST /api/v1/strategies/{strategy_id}/start
POST /api/v1/strategies/{strategy_id}/stop
```

## 🤖 **AI分析API**

### **獲取AI分析結果**
```http
GET /api/v1/ai/analysis/{pair}
```

### **獲取AI模型狀態**
```http
GET /api/v1/ai/models/status
```

## 📈 **交易記錄API**

### **獲取交易記錄**
```http
GET /api/v1/trades
```

### **獲取交易統計**
```http
GET /api/v1/trades/statistics
```

## 📊 **監控API**

### **獲取系統監控數據**
```http
GET /api/v1/monitoring/metrics
```

### **獲取活躍警報**
```http
GET /api/v1/monitoring/alerts
```

## 📚 **SDK使用示例**

### **Python SDK**
```python
from aimax_api import AImaxClient

client = AImaxClient(api_key="your_api_key")
status = client.system.get_status()
print(f"系統狀態: {status['status']}")
```

### **JavaScript SDK**
```javascript
const client = new AImaxClient({apiKey: 'your_api_key'});
const status = await client.system.getStatus();
console.log('系統狀態:', status.status);
```

---

**📚 本API文檔提供了AImax系統的完整API接口說明。**

*API版本: v1.0*  
*更新時間: 2025年7月27日*