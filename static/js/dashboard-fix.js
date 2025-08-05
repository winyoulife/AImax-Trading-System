// AImax 儀表板數據更新修正

// 修正BTC價格顯示問題
function fixBTCPriceDisplay() {
    // 覆蓋原有的updateTradingData方法
    if (window.dashboardManager) {
        window.dashboardManager.updateTradingData = async function() {
            try {
                // 獲取模擬交易數據
                const simulationData = await this.githubAPI.getSimulationData();
                
                if (simulationData) {
                    // 更新BTC價格 - 修正版本
                    if (simulationData.current_btc_price) {
                        const btcPrice = document.getElementById('btcPrice');
                        const priceChange = document.getElementById('priceChange');
                        
                        if (btcPrice) {
                            btcPrice.textContent = `$${simulationData.current_btc_price.toLocaleString()}`;
                        }
                        
                        // 顯示價格變化
                        if (priceChange) {
                            priceChange.textContent = '變化: 即時更新';
                        }
                    }
                    
                    // 更新損益
                    if (simulationData.portfolio) {
                        const totalPnl = document.getElementById('totalPnl');
                        const pnlPercentage = document.getElementById('pnlPercentage');
                        
                        if (totalPnl && pnlPercentage) {
                            const pnl = simulationData.portfolio.total_return || 0;
                            const pnlPct = simulationData.portfolio.return_percentage || 0;
                            
                            totalPnl.textContent = `$${pnl.toLocaleString()}`;
                            totalPnl.className = `status-value pnl ${pnl >= 0 ? 'positive' : 'negative'}`;
                            
                            pnlPercentage.textContent = `收益率: ${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`;
                        }
                    }
                    
                    // 更新交易統計
                    const totalTrades = document.getElementById('totalTrades');
                    if (totalTrades) {
                        totalTrades.textContent = simulationData.total_trades || 0;
                    }
                    
                    // 更新當前策略
                    const currentStrategy = document.getElementById('currentStrategy');
                    if (currentStrategy) {
                        currentStrategy.textContent = simulationData.strategy || '終極優化MACD';
                    }
                    
                    // 更新持倉
                    if (simulationData.portfolio && simulationData.portfolio.positions) {
                        const currentPosition = document.getElementById('currentPosition');
                        const positionValue = document.getElementById('positionValue');
                        
                        if (currentPosition && positionValue) {
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
                }
                
            } catch (error) {
                console.error('更新交易數據失敗:', error);
                this.addLog(`數據更新失敗: ${error.message}`, 'error');
            }
        };
    }
}

// 頁面載入後執行修正
document.addEventListener('DOMContentLoaded', () => {
    // 等待原始dashboard載入
    setTimeout(() => {
        fixBTCPriceDisplay();
        console.log('✅ BTC價格顯示已修正');
    }, 1000);
});

// 如果dashboard已經載入，立即執行修正
if (window.dashboardManager) {
    fixBTCPriceDisplay();
}