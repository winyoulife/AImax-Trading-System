// GitHub API 集成類

class GitHubAPI {
    constructor() {
        this.owner = 'winyoulife';
        this.repo = 'AImax-Trading-System';
        this.baseUrl = 'https://api.github.com';
        this.rawUrl = 'https://raw.githubusercontent.com';
    }
    
    async makeRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Accept': 'application/vnd.github.v3+json',
                    'User-Agent': 'AImax-Trading-Dashboard',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('GitHub API請求失敗:', error);
            throw error;
        }
    }
    
    async getRawFile(path, branch = 'main') {
        try {
            const url = `${this.rawUrl}/${this.owner}/${this.repo}/${branch}/${path}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                if (response.status === 404) {
                    return null; // 文件不存在
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const text = await response.text();
            
            // 嘗試解析JSON
            try {
                return JSON.parse(text);
            } catch {
                return text; // 返回原始文本
            }
        } catch (error) {
            console.error(`獲取文件失敗 ${path}:`, error);
            return null;
        }
    }
    
    async getWorkflowRuns() {
        try {
            const url = `${this.baseUrl}/repos/${this.owner}/${this.repo}/actions/runs`;
            const data = await this.makeRequest(url);
            return data.workflow_runs || [];
        } catch (error) {
            console.error('獲取工作流運行記錄失敗:', error);
            return [];
        }
    }
    
    async triggerWorkflow() {
        try {
            // 由於是靜態頁面，無法直接觸發GitHub Actions
            // 這裡提供一個替代方案：打開GitHub頁面讓用戶手動觸發
            const workflowUrl = `https://github.com/${this.owner}/${this.repo}/actions/workflows/main-trading.yml`;
            window.open(workflowUrl, '_blank');
            
            return { success: true, message: '已打開GitHub Actions頁面，請手動點擊 "Run workflow"' };
        } catch (error) {
            throw new Error('無法觸發工作流');
        }
    }
    
    async getSimulationData() {
        try {
            // 獲取執行狀態文件
            const statusData = await this.getRawFile('data/simulation/execution_status.json');
            
            // 獲取交易記錄
            const trades = await this.getTradingHistory();
            
            // 獲取當前BTC價格（從Binance API）
            let currentPrice = 95000; // 默認價格
            try {
                const priceResponse = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT');
                if (priceResponse.ok) {
                    const priceData = await priceResponse.json();
                    currentPrice = parseFloat(priceData.price);
                }
            } catch (e) {
                console.warn('無法獲取實時BTC價格，使用默認價格');
            }
            
            // 如果有狀態數據，使用它
            if (statusData) {
                return {
                    ...statusData,
                    current_btc_price: currentPrice,
                    trades: trades,
                    total_trades: trades.length,
                    last_update: new Date().toISOString()
                };
            }
            
            // 如果沒有狀態數據，構建基本結構
            return {
                current_btc_price: currentPrice,
                system_status: trades.length > 0 ? 'running' : 'stopped',
                trading_mode: 'simulation',
                strategy: 'smart_balanced_83.3%_winrate',
                executed_trades_this_cycle: 0,
                last_execution: trades.length > 0 ? trades[trades.length - 1].timestamp : null,
                github_actions: true,
                next_execution: '10 minutes',
                trades: trades,
                total_trades: trades.length,
                last_update: new Date().toISOString()
            };
        } catch (error) {
            console.error('獲取模擬數據失敗:', error);
            return null;
        }
    }
    
    async getTradingHistory() {
        try {
            // 獲取交易記錄文件
            const tradesData = await this.getRawFile('data/simulation/trades.jsonl');
            
            if (!tradesData) {
                return [];
            }
            
            // 如果是JSONL格式（每行一個JSON）
            if (typeof tradesData === 'string') {
                const lines = tradesData.trim().split('\n');
                const trades = [];
                
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            trades.push(JSON.parse(line));
                        } catch (e) {
                            console.warn('解析交易記錄失敗:', line);
                        }
                    }
                }
                
                return trades;
            }
            
            // 如果是JSON數組
            if (Array.isArray(tradesData)) {
                return tradesData;
            }
            
            return [];
        } catch (error) {
            console.error('獲取交易歷史失敗:', error);
            return [];
        }
    }
    
    async getRepositoryInfo() {
        try {
            const url = `${this.baseUrl}/repos/${this.owner}/${this.repo}`;
            return await this.makeRequest(url);
        } catch (error) {
            console.error('獲取倉庫信息失敗:', error);
            return null;
        }
    }
    
    async getLatestCommit() {
        try {
            const url = `${this.baseUrl}/repos/${this.owner}/${this.repo}/commits/main`;
            return await this.makeRequest(url);
        } catch (error) {
            console.error('獲取最新提交失敗:', error);
            return null;
        }
    }
    
    async getWorkflowStatus(workflowId = 'main-trading.yml') {
        try {
            const url = `${this.baseUrl}/repos/${this.owner}/${this.repo}/actions/workflows/${workflowId}`;
            return await this.makeRequest(url);
        } catch (error) {
            console.error('獲取工作流狀態失敗:', error);
            return null;
        }
    }
    
    // 模擬數據生成器（用於演示）
    generateMockData() {
        const now = new Date();
        const mockTrades = [];
        
        // 生成一些模擬交易記錄
        for (let i = 0; i < 5; i++) {
            const time = new Date(now.getTime() - (i * 3600000)); // 每小時一筆
            const action = Math.random() > 0.5 ? 'buy' : 'sell';
            const price = 95000 + (Math.random() - 0.5) * 2000;
            const quantity = 0.001 + Math.random() * 0.009;
            
            mockTrades.push({
                timestamp: time.toISOString(),
                action: action,
                price: price,
                quantity: quantity,
                confidence: 0.8 + Math.random() * 0.15,
                strategy: 'smart_balanced'
            });
        }
        
        return {
            current_btc_price: 95000 + (Math.random() - 0.5) * 1000,
            portfolio: {
                initial_balance: 10000,
                current_balance: 9500 + Math.random() * 1000,
                total_value: 10000 + (Math.random() - 0.3) * 500,
                total_return: (Math.random() - 0.3) * 500,
                return_percentage: (Math.random() - 0.3) * 5,
                total_trades: mockTrades.length,
                positions: {
                    BTCUSDT: Math.random() * 0.01
                }
            },
            trades: mockTrades,
            system_status: 'running',
            last_update: now.toISOString()
        };
    }
    
    // 檢查是否為演示模式
    isDemoMode() {
        return window.location.hostname === 'localhost' || 
               window.location.hostname === '127.0.0.1' ||
               window.location.search.includes('demo=true');
    }
    
    // 獲取數據的統一接口
    async getData() {
        if (this.isDemoMode()) {
            // 演示模式：返回模擬數據
            return this.generateMockData();
        } else {
            // 生產模式：從GitHub獲取真實數據
            return await this.getSimulationData();
        }
    }
}