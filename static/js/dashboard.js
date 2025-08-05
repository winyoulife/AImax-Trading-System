// AImax 智能交易控制面板 JavaScript

class DashboardManager {
    constructor() {
        this.isAuthenticated = false;
        this.updateInterval = null;
        this.githubAPI = new GitHubAPI();
        
        this.init();
    }
    
    init() {
        // 檢查認證狀態
        if (window.authManager && window.authManager.isAuthenticated()) {
            this.showDashboard();
        } else {
            this.showLogin();
        }
        
        // 綁定事件
        this.bindEvents();
        
        // 開始更新時間
        this.updateCurrentTime();
        setInterval(() => this.updateCurrentTime(), 1000);
    }
    
    bindEvents() {
        // 登入表單
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        // 登出按鈕
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }
        
        // 控制按鈕
        const triggerBtn = document.getElementById('triggerWorkflow');
        if (triggerBtn) {
            triggerBtn.addEventListener('click', () => this.triggerWorkflow());
        }
        
        const viewActionsBtn = document.getElementById('viewActions');
        if (viewActionsBtn) {
            viewActionsBtn.addEventListener('click', () => this.viewActions());
        }
        
        const downloadBtn = document.getElementById('downloadData');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => this.downloadData());
        }
        
        const emergencyBtn = document.getElementById('emergencyStop');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => this.emergencyStop());
        }
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('loginError');
        const lockoutDiv = document.getElementById('lockoutMessage');
        
        // 清除之前的錯誤信息
        errorDiv.style.display = 'none';
        lockoutDiv.style.display = 'none';
        
        try {
            // 檢查是否被鎖定
            if (window.authManager.isLockedOut()) {
                const remainingTime = window.authManager.getRemainingLockoutTime();
                const minutes = Math.ceil(remainingTime / 60000);
                lockoutDiv.textContent = `帳號已被鎖定，請等待 ${minutes} 分鐘後再試`;
                lockoutDiv.style.display = 'block';
                return;
            }
            
            // 嘗試認證
            await window.authManager.authenticate(username, password);
            
            // 認證成功
            this.addLog('用戶登入成功', 'success');
            this.showDashboard();
            
        } catch (error) {
            // 認證失敗
            errorDiv.textContent = error.message;
            errorDiv.style.display = 'block';
            
            // 檢查是否被鎖定
            if (window.authManager.isLockedOut()) {
                const remainingTime = window.authManager.getRemainingLockoutTime();
                const minutes = Math.ceil(remainingTime / 60000);
                lockoutDiv.textContent = `登入失敗次數過多，帳號已被鎖定 ${minutes} 分鐘`;
                lockoutDiv.style.display = 'block';
                errorDiv.style.display = 'none';
            }
        }
    }
    
    handleLogout() {
        if (confirm('確定要登出嗎？')) {
            window.authManager.logout();
            this.showLogin();
            this.addLog('用戶已登出', 'info');
        }
    }
    
    showLogin() {
        document.getElementById('loginContainer').style.display = 'flex';
        document.getElementById('dashboardContainer').style.display = 'none';
        
        // 停止數據更新
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    showDashboard() {
        document.getElementById('loginContainer').style.display = 'none';
        document.getElementById('dashboardContainer').style.display = 'block';
        
        // 開始數據更新
        this.startDataUpdates();
        
        // 立即更新一次數據
        this.updateDashboardData();
    }
    
    startDataUpdates() {
        // 每30秒更新一次數據
        this.updateInterval = setInterval(() => {
            this.updateDashboardData();
        }, 30000);
    }
    
    async updateDashboardData() {
        try {
            this.addLog('正在更新交易數據...', 'info');
            
            // 更新系統狀態
            await this.updateSystemStatus();
            
            // 更新交易數據
            await this.updateTradingData();
            
            // 更新交易歷史
            await this.updateTradingHistory();
            
            this.addLog('數據更新完成', 'success');
            
        } catch (error) {
            console.error('更新數據失敗:', error);
            this.addLog(`數據更新失敗: ${error.message}`, 'error');
        }
    }
    
    async updateSystemStatus() {
        try {
            // 檢查GitHub Actions狀態
            const workflowRuns = await this.githubAPI.getWorkflowRuns();
            const latestRun = workflowRuns[0];
            
            const systemIndicator = document.getElementById('systemIndicator');
            const systemStatus = document.getElementById('systemStatus');
            const lastUpdate = document.getElementById('lastUpdate');
            
            if (latestRun) {
                const isRunning = latestRun.status === 'in_progress';
                const isSuccess = latestRun.conclusion === 'success';
                
                systemIndicator.className = `status-indicator ${isRunning || isSuccess ? 'online' : 'offline'}`;
                systemStatus.textContent = isRunning ? '執行中' : (isSuccess ? '運行正常' : '已停止');
                
                const updateTime = new Date(latestRun.updated_at);
                lastUpdate.textContent = `更新時間: ${updateTime.toLocaleString('zh-TW')}`;
            } else {
                systemIndicator.className = 'status-indicator offline';
                systemStatus.textContent = '等待啟動';
                lastUpdate.textContent = '更新時間: --';
            }
            
        } catch (error) {
            console.error('更新系統狀態失敗:', error);
        }
    }
    
    async updateTradingData() {
        try {
            // 獲取模擬交易數據
            const simulationData = await this.githubAPI.getSimulationData();
            
            if (simulationData) {
                // 更新BTC價格
                if (simulationData.current_btc_price) {
                    const btcPrice = document.getElementById('btcPrice');
                    btcPrice.textContent = `$${simulationData.current_btc_price.toLocaleString()}`;
                }
                
                // 更新損益
                if (simulationData.portfolio) {
                    const totalPnl = document.getElementById('totalPnl');
                    const pnlPercentage = document.getElementById('pnlPercentage');
                    
                    const pnl = simulationData.portfolio.total_return || 0;
                    const pnlPct = simulationData.portfolio.return_percentage || 0;
                    
                    totalPnl.textContent = `$${pnl.toLocaleString()}`;
                    totalPnl.className = `status-value pnl ${pnl >= 0 ? 'positive' : 'negative'}`;
                    
                    pnlPercentage.textContent = `收益率: ${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`;
                }
                
                // 更新交易統計
                if (simulationData.portfolio) {
                    const totalTrades = document.getElementById('totalTrades');
                    totalTrades.textContent = simulationData.portfolio.total_trades || 0;
                }
                
                // 更新持倉
                if (simulationData.portfolio && simulationData.portfolio.positions) {
                    const currentPosition = document.getElementById('currentPosition');
                    const positionValue = document.getElementById('positionValue');
                    
                    const btcPosition = simulationData.portfolio.positions.BTCUSDT || 0;
                    if (btcPosition > 0) {
                        currentPosition.textContent = `${btcPosition.toFixed(6)} BTC`;
                        const value = btcPosition * (simulationData.current_btc_price || 0);
                        positionValue.textContent = `價值: $${value.toLocaleString()}`;
                    } else {
                        currentPosition.textContent = '無持倉';
                        positionValue.textContent = '價值: $0';
                    }
                }
            }
            
        } catch (error) {
            console.error('更新交易數據失敗:', error);
        }
    }
    
    async updateTradingHistory() {
        try {
            const trades = await this.githubAPI.getTradingHistory();
            const tableBody = document.getElementById('tradesTableBody');
            
            if (trades && trades.length > 0) {
                tableBody.innerHTML = '';
                
                // 顯示最近10筆交易
                trades.slice(-10).reverse().forEach(trade => {
                    const row = document.createElement('tr');
                    
                    const time = new Date(trade.timestamp).toLocaleString('zh-TW');
                    const action = trade.action.toUpperCase();
                    const price = `$${trade.price.toLocaleString()}`;
                    const quantity = trade.quantity ? trade.quantity.toFixed(6) : '--';
                    const confidence = trade.confidence ? `${(trade.confidence * 100).toFixed(1)}%` : '--';
                    const status = '已完成';
                    
                    row.innerHTML = `
                        <td>${time}</td>
                        <td><span class="trade-${trade.action}">${action}</span></td>
                        <td>${price}</td>
                        <td>${quantity}</td>
                        <td>${confidence}</td>
                        <td>${status}</td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            } else {
                tableBody.innerHTML = '<tr><td colspan="6" class="no-data">暫無交易記錄</td></tr>';
            }
            
        } catch (error) {
            console.error('更新交易歷史失敗:', error);
            const tableBody = document.getElementById('tradesTableBody');
            tableBody.innerHTML = '<tr><td colspan="6" class="no-data">載入交易記錄失敗</td></tr>';
        }
    }
    
    async triggerWorkflow() {
        try {
            this.showLoading(true);
            this.addLog('正在手動觸發交易工作流...', 'info');
            
            await this.githubAPI.triggerWorkflow();
            
            this.addLog('交易工作流已成功觸發', 'success');
            
            // 等待幾秒後更新數據
            setTimeout(() => {
                this.updateDashboardData();
            }, 3000);
            
        } catch (error) {
            console.error('觸發工作流失敗:', error);
            this.addLog(`觸發工作流失敗: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    viewActions() {
        // 打開GitHub Actions頁面
        const repoUrl = 'https://github.com/winyoulife/AImax-Trading-System/actions';
        window.open(repoUrl, '_blank');
        this.addLog('已打開GitHub Actions頁面', 'info');
    }
    
    async downloadData() {
        try {
            this.showLoading(true);
            this.addLog('正在準備下載交易數據...', 'info');
            
            const data = await this.githubAPI.getSimulationData();
            const trades = await this.githubAPI.getTradingHistory();
            
            const exportData = {
                timestamp: new Date().toISOString(),
                system_info: {
                    strategy: '終極優化MACD',
                    target_winrate: '85%+',
                    mode: 'simulation'
                },
                portfolio: data?.portfolio || {},
                trades: trades || [],
                summary: {
                    total_trades: trades?.length || 0,
                    current_btc_price: data?.current_btc_price || 0
                }
            };
            
            // 創建下載鏈接
            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `aimax-trading-data-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.addLog('交易數據下載完成', 'success');
            
        } catch (error) {
            console.error('下載數據失敗:', error);
            this.addLog(`下載數據失敗: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    emergencyStop() {
        if (confirm('⚠️ 確定要執行緊急停止嗎？\n\n這將停止所有自動交易活動。')) {
            this.addLog('🚨 用戶執行緊急停止', 'warning');
            alert('緊急停止已記錄。\n\n請到GitHub Actions頁面手動停止正在運行的工作流。');
            this.viewActions();
        }
    }
    
    updateCurrentTime() {
        const timeElement = document.getElementById('currentTime');
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = now.toLocaleString('zh-TW');
        }
    }
    
    addLog(message, type = 'info') {
        const logContent = document.getElementById('systemLog');
        if (logContent) {
            const timestamp = new Date().toLocaleTimeString('zh-TW');
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${type}`;
            logEntry.innerHTML = `<span class="timestamp">${timestamp}</span>${message}`;
            
            logContent.appendChild(logEntry);
            logContent.scrollTop = logContent.scrollHeight;
            
            // 限制日誌條數
            const entries = logContent.querySelectorAll('.log-entry');
            if (entries.length > 100) {
                entries[0].remove();
            }
        }
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});