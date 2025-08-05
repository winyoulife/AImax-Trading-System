/**
 * GitHub API 適配器
 * 用於從 GitHub Pages 靜態 JSON 文件獲取 MAX API 數據
 * 提供與直接 MAX API 調用相同的接口
 */

class GitHubAPIAdapter {
    constructor() {
        this.baseUrl = this.detectBaseUrl();
        this.apiEndpoint = `${this.baseUrl}/api/btc-price.json`;
        this.cache = new Map();
        this.cacheTimeout = 30000; // 30秒緩存
        this.requestTimeout = 10000; // 10秒超時
        
        console.log('🔧 GitHub API 適配器初始化');
        console.log('📡 API 端點:', this.apiEndpoint);
    }
    
    /**
     * 自動檢測基礎 URL
     */
    detectBaseUrl() {
        const currentUrl = window.location.href;
        
        if (currentUrl.includes('github.io')) {
            // GitHub Pages 環境
            return 'https://winyoulife.github.io/AImax-Trading-System';
        } else if (currentUrl.includes('localhost') || currentUrl.includes('127.0.0.1')) {
            // 本地開發環境
            return window.location.origin;
        } else {
            // 其他環境，使用相對路徑
            return window.location.origin;
        }
    }
    
    /**
     * 獲取當前 BTC/TWD 價格
     * 兼容原有的 MAX API 調用接口
     */
    async getCurrentPrice() {
        try {
            console.log('📡 通過 GitHub API 適配器獲取價格數據...');
            
            const data = await this.fetchWithCache();
            
            if (data && data.success && data.data) {
                // 轉換為與原 MAX API 兼容的格式
                const compatibleData = {
                    last: data.data.price.toString(),
                    buy: data.data.buy_price?.toString() || data.data.price.toString(),
                    sell: data.data.sell_price?.toString() || data.data.price.toString(),
                    vol: data.data.volume?.toString() || "0",
                    timestamp: data.data.timestamp,
                    source: data.data.source,
                    // 添加額外的元數據
                    _meta: {
                        formatted_price: data.data.formatted_price,
                        data_age_seconds: data.meta?.data_age_seconds || 0,
                        api_response_time_ms: data.meta?.api_response_time_ms || 0,
                        fetch_method: 'github_static_api'
                    }
                };
                
                console.log('✅ 成功獲取價格數據:', compatibleData._meta.formatted_price);
                console.log('📊 數據年齡:', compatibleData._meta.data_age_seconds, '秒');
                
                return compatibleData;
            } else {
                throw new Error('數據格式無效或獲取失敗');
            }
            
        } catch (error) {
            console.error('❌ GitHub API 適配器獲取失敗:', error);
            
            // 嘗試從緩存獲取
            const cachedData = this.getCachedData();
            if (cachedData) {
                console.log('🔄 使用緩存數據');
                return cachedData;
            }
            
            // 返回錯誤格式，但保持接口兼容性
            throw new Error(`GitHub API 適配器失敗: ${error.message}`);
        }
    }
    
    /**
     * 帶緩存的數據獲取
     */
    async fetchWithCache() {
        const cacheKey = 'btc_price_data';
        const cached = this.cache.get(cacheKey);
        
        // 檢查緩存是否有效
        if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
            console.log('📦 使用緩存數據');
            return cached.data;
        }
        
        // 獲取新數據
        const data = await this.fetchFromAPI();
        
        // 更新緩存
        this.cache.set(cacheKey, {
            data: data,
            timestamp: Date.now()
        });
        
        return data;
    }
    
    /**
     * 從 API 獲取數據
     */
    async fetchFromAPI() {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);
        
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                },
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📊 從 GitHub API 獲取數據成功');
            
            return data;
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('請求超時');
            }
            
            throw error;
        }
    }
    
    /**
     * 獲取緩存數據
     */
    getCachedData() {
        const cached = this.cache.get('btc_price_data');
        if (cached) {
            // 轉換緩存數據為兼容格式
            const data = cached.data;
            if (data && data.success && data.data) {
                return {
                    last: data.data.price.toString(),
                    buy: data.data.buy_price?.toString() || data.data.price.toString(),
                    sell: data.data.sell_price?.toString() || data.data.price.toString(),
                    vol: data.data.volume?.toString() || "0",
                    timestamp: data.data.timestamp,
                    source: data.data.source + ' (cached)',
                    _meta: {
                        formatted_price: data.data.formatted_price,
                        data_age_seconds: data.meta?.data_age_seconds || 0,
                        fetch_method: 'cached'
                    }
                };
            }
        }
        return null;
    }
    
    /**
     * 獲取系統狀態信息
     */
    async getSystemStatus() {
        try {
            const data = await this.fetchWithCache();
            
            if (data && data.status) {
                return {
                    online: data.success,
                    status: data.status.message,
                    last_update: data.data?.timestamp,
                    data_age: data.meta?.data_age_seconds || 0,
                    consecutive_failures: data.status.consecutive_failures || 0,
                    api_response_time: data.meta?.api_response_time_ms || 0
                };
            }
            
            return {
                online: false,
                status: 'unknown',
                last_update: null,
                data_age: -1,
                consecutive_failures: -1,
                api_response_time: -1
            };
            
        } catch (error) {
            console.error('❌ 獲取系統狀態失敗:', error);
            return {
                online: false,
                status: 'error',
                error: error.message,
                last_update: null,
                data_age: -1,
                consecutive_failures: -1,
                api_response_time: -1
            };
        }
    }
    
    /**
     * 清除緩存
     */
    clearCache() {
        this.cache.clear();
        console.log('🗑️ 緩存已清除');
    }
    
    /**
     * 獲取適配器信息
     */
    getAdapterInfo() {
        return {
            name: 'GitHub API Adapter',
            version: '1.0.0',
            endpoint: this.apiEndpoint,
            cache_timeout: this.cacheTimeout,
            request_timeout: this.requestTimeout,
            cache_size: this.cache.size
        };
    }
}

/**
 * 智能 API 適配器
 * 自動選擇最佳的 API 連接方式
 */
class SmartAPIAdapter {
    constructor() {
        this.adapters = [];
        this.currentAdapter = null;
        this.fallbackData = null;
        
        this.initializeAdapters();
    }
    
    /**
     * 初始化所有可用的適配器
     */
    initializeAdapters() {
        // GitHub API 適配器（優先使用）
        this.adapters.push({
            name: 'GitHub Static API',
            adapter: new GitHubAPIAdapter(),
            priority: 1,
            available: true
        });
        
        console.log('🔧 智能 API 適配器初始化完成');
        console.log('📋 可用適配器:', this.adapters.length);
    }
    
    /**
     * 獲取當前價格（智能選擇適配器）
     */
    async getCurrentPrice() {
        // 按優先級排序適配器
        const sortedAdapters = this.adapters
            .filter(a => a.available)
            .sort((a, b) => a.priority - b.priority);
        
        for (const adapterInfo of sortedAdapters) {
            try {
                console.log(`🔄 嘗試使用 ${adapterInfo.name}...`);
                
                const result = await adapterInfo.adapter.getCurrentPrice();
                
                if (result && result.last) {
                    this.currentAdapter = adapterInfo;
                    this.fallbackData = result; // 保存作為備用數據
                    
                    console.log(`✅ ${adapterInfo.name} 成功`);
                    return result;
                }
                
            } catch (error) {
                console.warn(`⚠️ ${adapterInfo.name} 失敗:`, error.message);
                adapterInfo.available = false;
                
                // 標記為暫時不可用，5分鐘後重新嘗試
                setTimeout(() => {
                    adapterInfo.available = true;
                    console.log(`🔄 ${adapterInfo.name} 重新標記為可用`);
                }, 5 * 60 * 1000);
            }
        }
        
        // 所有適配器都失敗，使用備用數據
        if (this.fallbackData) {
            console.log('🔄 所有適配器失敗，使用備用數據');
            return {
                ...this.fallbackData,
                source: this.fallbackData.source + ' (fallback)',
                _meta: {
                    ...this.fallbackData._meta,
                    fetch_method: 'fallback'
                }
            };
        }
        
        // 沒有任何可用數據
        throw new Error('所有 API 適配器都不可用，且沒有備用數據');
    }
    
    /**
     * 獲取當前使用的適配器信息
     */
    getCurrentAdapterInfo() {
        if (this.currentAdapter) {
            return {
                name: this.currentAdapter.name,
                priority: this.currentAdapter.priority,
                available: this.currentAdapter.available,
                details: this.currentAdapter.adapter.getAdapterInfo?.() || {}
            };
        }
        return null;
    }
    
    /**
     * 強制刷新所有適配器
     */
    refreshAdapters() {
        this.adapters.forEach(adapter => {
            adapter.available = true;
            if (adapter.adapter.clearCache) {
                adapter.adapter.clearCache();
            }
        });
        console.log('🔄 所有適配器已刷新');
    }
}

// 導出適配器類
window.GitHubAPIAdapter = GitHubAPIAdapter;
window.SmartAPIAdapter = SmartAPIAdapter;

// 創建全局實例
window.smartAPIAdapter = new SmartAPIAdapter();

console.log('✅ GitHub API 適配器模塊加載完成');