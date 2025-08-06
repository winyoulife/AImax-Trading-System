# AImax 故障排除指南

## 🔧 快速診斷工具

在開始詳細故障排除之前，請先使用以下快速診斷清單：

### ✅ 基礎檢查清單

- [ ] 網路連接正常
- [ ] 瀏覽器為最新版本
- [ ] 已清除瀏覽器緩存
- [ ] GitHub服務狀態正常
- [ ] 使用正確的網址訪問
- [ ] 帳號密碼輸入正確

---

## 🚨 常見問題快速解決

### 1. 🔐 登入問題

#### 問題: 無法登入系統
**症狀**: 輸入帳號密碼後無反應或顯示錯誤

**解決步驟**:
```bash
# 步驟1: 清除瀏覽器數據
1. 按 Ctrl+Shift+Delete (Windows) 或 Cmd+Shift+Delete (Mac)
2. 選擇"所有時間"
3. 勾選"Cookie和其他網站數據"、"緩存的圖片和文件"
4. 點擊"清除數據"

# 步驟2: 檢查帳號密碼
1. 確認帳號大小寫正確
2. 確認密碼沒有多餘空格
3. 嘗試複製貼上密碼

# 步驟3: 嘗試無痕模式
1. Chrome: Ctrl+Shift+N
2. Firefox: Ctrl+Shift+P
3. Safari: Cmd+Shift+N
```

**高級解決方案**:
如果仍無法登入，可能需要重新生成密碼哈希：

```python
# 生成新密碼哈希
import hashlib
password = "您的新密碼"
hash_value = hashlib.sha256(password.encode()).hexdigest()
print(f"新密碼哈希: {hash_value}")
```

然後更新 `static/secure-login-fixed.html` 中的哈希值。

#### 問題: 登入後立即跳轉回登入頁面
**症狀**: 成功登入後又回到登入頁面

**解決步驟**:
1. **檢查瀏覽器設置**:
   - 確保允許Cookie
   - 確保允許JavaScript
   - 關閉嚴格的隱私設置

2. **檢查網址**:
   - 確保使用HTTPS而不是HTTP
   - 確保網址完整正確

3. **時間同步**:
   - 確保設備時間正確
   - 會話過期基於時間戳

### 2. 📊 數據顯示問題

#### 問題: BTC價格顯示"載入中..."或"無法連接"
**症狀**: 價格數據無法更新

**診斷步驟**:
```javascript
// 在瀏覽器控制台執行以下代碼進行診斷
console.log("開始診斷價格API...");

// 測試CORS代理
fetch('https://api.allorigins.win/get?url=' + 
      encodeURIComponent('https://max-api.maicoin.com/api/v2/tickers/btctwd'))
  .then(response => response.json())
  .then(data => {
    console.log("CORS代理測試成功:", data);
    if (data.status.http_code === 200) {
      const btcData = JSON.parse(data.contents);
      console.log("BTC價格:", btcData.last);
    }
  })
  .catch(error => {
    console.error("CORS代理測試失敗:", error);
  });
```

**解決方案**:
1. **網路問題**:
   - 檢查防火牆設置
   - 嘗試關閉VPN
   - 檢查DNS設置

2. **API問題**:
   - 檢查MAX API狀態: https://max.maicoin.com/
   - 檢查CORS代理狀態: https://api.allorigins.win/
   - 嘗試手動刷新數據

3. **瀏覽器問題**:
   - 禁用廣告攔截器
   - 禁用瀏覽器擴展
   - 嘗試其他瀏覽器

#### 問題: GitHub Actions狀態顯示異常
**症狀**: 系統狀態卡片顯示錯誤或無數據

**診斷代碼**:
```javascript
// 測試GitHub API連接
async function testGitHubAPI() {
  const url = 'https://api.github.com/repos/您的用戶名/倉庫名/actions/runs';
  try {
    const response = await fetch(url);
    const data = await response.json();
    console.log("GitHub API測試結果:", data);
    
    if (response.status === 403) {
      console.log("可能遇到API限制，請稍後重試");
    } else if (response.status === 404) {
      console.log("倉庫不存在或無權限訪問");
    }
  } catch (error) {
    console.error("GitHub API測試失敗:", error);
  }
}

testGitHubAPI();
```

**解決方案**:
1. **權限問題**:
   - 確保倉庫為公開或有適當權限
   - 檢查GitHub Actions是否啟用

2. **API限制**:
   - GitHub API有頻率限制
   - 等待一段時間後重試
   - 考慮使用Personal Access Token

3. **倉庫配置**:
   - 確認倉庫名稱正確
   - 確認工作流文件存在且正確

### 3. ⚙️ GitHub Actions問題

#### 問題: 工作流執行失敗
**症狀**: GitHub Actions顯示紅色X或失敗狀態

**診斷步驟**:
1. **查看執行日誌**:
   - 訪問 `https://github.com/用戶名/倉庫名/actions`
   - 點擊失敗的工作流
   - 查看詳細錯誤信息

2. **常見錯誤類型**:
   - **依賴安裝失敗**: Python包安裝問題
   - **API調用失敗**: 網路或API問題
   - **權限錯誤**: Secrets配置問題
   - **語法錯誤**: YAML文件格式問題

**解決方案**:

**依賴問題**:
```yaml
# 在工作流中添加更詳細的依賴安裝
- name: 安裝依賴
  run: |
    python -m pip install --upgrade pip
    pip install requests pandas numpy pytz --timeout=60
    pip list  # 顯示已安裝的包
```

**API調用問題**:
```python
# 添加重試邏輯
import time
import requests

def fetch_with_retry(url, max_retries=3):
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"嘗試 {i+1} 失敗: {e}")
            if i < max_retries - 1:
                time.sleep(2 ** i)  # 指數退避
    return None
```

**Secrets配置問題**:
```yaml
# 檢查Secrets是否正確配置
- name: 檢查Secrets
  run: |
    echo "檢查必需的Secrets..."
    if [ -z "${{ secrets.ADMIN_USERNAME }}" ]; then
      echo "❌ ADMIN_USERNAME未配置"
      exit 1
    fi
    echo "✅ Secrets配置正常"
```

#### 問題: 工作流不執行
**症狀**: 定時任務沒有按預期執行

**檢查項目**:
1. **Cron表達式**:
   ```yaml
   # 檢查cron表達式是否正確
   schedule:
     - cron: '*/5 * * * *'  # 每5分鐘執行
   ```

2. **倉庫活躍度**:
   - GitHub會暫停不活躍倉庫的定時任務
   - 需要定期有提交活動

3. **工作流啟用狀態**:
   - 檢查工作流是否被禁用
   - 在Actions頁面重新啟用

### 4. 📱 移動端問題

#### 問題: 移動端顯示異常
**症狀**: 在手機或平板上界面錯亂

**解決步驟**:
1. **瀏覽器兼容性測試**:
   ```javascript
   // 檢查瀏覽器兼容性
   console.log("瀏覽器信息:", navigator.userAgent);
   console.log("螢幕尺寸:", window.screen.width + "x" + window.screen.height);
   console.log("視窗尺寸:", window.innerWidth + "x" + window.innerHeight);
   ```

2. **CSS媒體查詢測試**:
   ```css
   /* 檢查CSS媒體查詢是否生效 */
   @media (max-width: 768px) {
     body::before {
       content: "移動端CSS已載入";
       position: fixed;
       top: 0;
       left: 0;
       background: red;
       color: white;
       z-index: 9999;
     }
   }
   ```

**解決方案**:
- 清除移動瀏覽器緩存
- 嘗試橫屏和豎屏模式
- 檢查瀏覽器縮放設置
- 使用不同的移動瀏覽器測試

### 5. 🔒 安全問題

#### 問題: 懷疑帳號被盜用
**症狀**: 發現異常登入或交易活動

**緊急處理步驟**:
1. **立即更改密碼**:
   ```bash
   # 生成新的強密碼
   python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(16)))"
   ```

2. **撤銷API權限**:
   - 登入MAX交易所
   - 撤銷或重新生成API密鑰
   - 更新GitHub Secrets

3. **檢查活動日誌**:
   - 檢查GitHub Actions執行歷史
   - 檢查交易所交易記錄
   - 檢查異常IP訪問

4. **加強安全設置**:
   - 啟用兩步驗證
   - 設置IP白名單
   - 定期更換密碼

---

## 🔍 高級診斷工具

### 系統健康檢查腳本

創建以下腳本來全面檢查系統狀態：

```javascript
// 系統健康檢查腳本
async function systemHealthCheck() {
  console.log("🔍 開始系統健康檢查...");
  
  const checks = {
    localStorage: false,
    sessionStorage: false,
    fetch: false,
    maxAPI: false,
    githubAPI: false,
    authentication: false
  };
  
  // 檢查本地存儲
  try {
    localStorage.setItem('test', 'test');
    localStorage.removeItem('test');
    checks.localStorage = true;
    console.log("✅ localStorage 正常");
  } catch (e) {
    console.log("❌ localStorage 異常:", e);
  }
  
  // 檢查會話存儲
  try {
    sessionStorage.setItem('test', 'test');
    sessionStorage.removeItem('test');
    checks.sessionStorage = true;
    console.log("✅ sessionStorage 正常");
  } catch (e) {
    console.log("❌ sessionStorage 異常:", e);
  }
  
  // 檢查Fetch API
  try {
    if (typeof fetch !== 'undefined') {
      checks.fetch = true;
      console.log("✅ Fetch API 支援");
    }
  } catch (e) {
    console.log("❌ Fetch API 不支援:", e);
  }
  
  // 檢查MAX API
  try {
    const response = await fetch('https://api.allorigins.win/get?url=' + 
      encodeURIComponent('https://max-api.maicoin.com/api/v2/tickers/btctwd'));
    if (response.ok) {
      checks.maxAPI = true;
      console.log("✅ MAX API 連接正常");
    }
  } catch (e) {
    console.log("❌ MAX API 連接失敗:", e);
  }
  
  // 檢查認證狀態
  const auth = localStorage.getItem('aimax_authenticated');
  const expiry = localStorage.getItem('aimax_session_expiry');
  if (auth === 'true' && expiry) {
    const expiryDate = new Date(expiry);
    if (new Date() < expiryDate) {
      checks.authentication = true;
      console.log("✅ 認證狀態正常");
    } else {
      console.log("⚠️ 認證已過期");
    }
  } else {
    console.log("ℹ️ 未登入狀態");
  }
  
  // 生成報告
  const passedChecks = Object.values(checks).filter(Boolean).length;
  const totalChecks = Object.keys(checks).length;
  
  console.log(`\n📊 健康檢查報告: ${passedChecks}/${totalChecks} 項目正常`);
  
  if (passedChecks === totalChecks) {
    console.log("🎉 系統狀態良好！");
  } else {
    console.log("⚠️ 發現問題，請檢查上述錯誤信息");
  }
  
  return checks;
}

// 執行健康檢查
systemHealthCheck();
```

### 網路連接測試

```javascript
// 網路連接測試腳本
async function networkConnectivityTest() {
  console.log("🌐 開始網路連接測試...");
  
  const endpoints = [
    { name: 'GitHub API', url: 'https://api.github.com' },
    { name: 'MAX API', url: 'https://max-api.maicoin.com' },
    { name: 'CORS代理', url: 'https://api.allorigins.win' },
    { name: 'Google DNS', url: 'https://8.8.8.8' }
  ];
  
  for (const endpoint of endpoints) {
    try {
      const start = Date.now();
      const response = await fetch(endpoint.url, { 
        method: 'HEAD', 
        mode: 'no-cors',
        cache: 'no-cache'
      });
      const duration = Date.now() - start;
      console.log(`✅ ${endpoint.name}: ${duration}ms`);
    } catch (error) {
      console.log(`❌ ${endpoint.name}: ${error.message}`);
    }
  }
}

// 執行網路測試
networkConnectivityTest();
```

---

## 📞 獲取技術支持

如果以上故障排除步驟無法解決問題，請按以下方式獲取幫助：

### 1. 收集診斷信息

在尋求幫助前，請收集以下信息：

```javascript
// 生成診斷報告
function generateDiagnosticReport() {
  const report = {
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href,
    screenSize: `${window.screen.width}x${window.screen.height}`,
    windowSize: `${window.innerWidth}x${window.innerHeight}`,
    localStorage: {
      authenticated: localStorage.getItem('aimax_authenticated'),
      username: localStorage.getItem('aimax_username'),
      sessionExpiry: localStorage.getItem('aimax_session_expiry')
    },
    errors: []
  };
  
  // 檢查控制台錯誤
  const originalError = console.error;
  console.error = function(...args) {
    report.errors.push(args.join(' '));
    originalError.apply(console, args);
  };
  
  console.log("📋 診斷報告:", JSON.stringify(report, null, 2));
  return report;
}

generateDiagnosticReport();
```

### 2. 提交問題報告

在GitHub倉庫提交Issue時，請包含：

- **問題描述**: 詳細描述遇到的問題
- **重現步驟**: 如何重現問題的具體步驟
- **預期結果**: 您期望看到的結果
- **實際結果**: 實際發生的情況
- **診斷信息**: 上述診斷報告的內容
- **截圖**: 如果可能，提供錯誤截圖

### 3. 聯繫方式

- **GitHub Issues**: 在項目倉庫提交Issue
- **GitHub Discussions**: 參與社群討論
- **技術文檔**: 查看完整的技術文檔

---

## 🔄 系統恢復程序

### 完全重置系統

如果系統出現嚴重問題，可以執行完全重置：

```bash
# 1. 備份重要數據
git clone https://github.com/您的用戶名/倉庫名.git backup

# 2. 重新部署系統
python3 deploy_aimax.py

# 3. 恢復自定義配置
# 手動恢復之前的自定義設置

# 4. 測試系統功能
# 確保所有功能正常工作
```

### 回滾到之前版本

```bash
# 查看提交歷史
git log --oneline

# 回滾到特定版本
git reset --hard <commit-hash>

# 強制推送（謹慎使用）
git push --force-with-lease origin main
```

---

**🤖 AImax智能交易系統** - 專業的故障排除支持

*最後更新: 2025年1月*