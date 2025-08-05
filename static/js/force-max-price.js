// 強制MAX API價格顯示 - 緊急修正版本

console.log('🚀 強制MAX API價格修正器已載入');

// 立即執行價格修正
function forceMaxPrice() {
    console.log('🔧 開始強制修正BTC價格顯示...');
    
    // 獲取MAX API價格
    fetch('https://max-api.maicoin.com/api/v2/tickers/btctwd')
        .then(response => response.json())
        .then(data => {
            console.log('📊 MAX API響應:', data);
            
            let price = null;
            
            // 嘗試不同的格式
            if (data.ticker && data.ticker.last) {
                price = parseFloat(data.ticker.last);
                console.log('✅ 從ticker.last獲取價格:', price);
            } else if (data.last) {
                price = parseFloat(data.last);
                console.log('✅ 從last獲取價格:', price);
            }
            
            if (price && price > 0) {
                // 強制更新價格顯示
                const btcPriceElement = document.getElementById('btcPrice');
                if (btcPriceElement) {
                    btcPriceElement.textContent = `NT$${price.toLocaleString()}`;
                    btcPriceElement.style.color = '#2ed573';
                    btcPriceElement.style.fontWeight = 'bold';
                    console.log('💰 MAX API即時價格已更新為:', `NT$${price.toLocaleString()}`);
                    
                    // 添加閃爍效果表示更新
                    btcPriceElement.style.transition = 'all 0.3s ease';
                    btcPriceElement.style.transform = 'scale(1.05)';
                    setTimeout(() => {
                        btcPriceElement.style.transform = 'scale(1)';
                    }, 300);
                }
                
                // 更新變化指示器
                const priceChange = document.getElementById('priceChange');
                if (priceChange) {
                    priceChange.textContent = '變化: MAX API即時';
                    priceChange.style.color = '#2ed573';
                }
                
                // 更新最後更新時間
                const lastUpdate = document.getElementById('lastUpdate');
                if (lastUpdate) {
                    lastUpdate.textContent = `更新時間: ${new Date().toLocaleString('zh-TW')} (MAX API強制)`;
                }
            } else {
                console.error('❌ 無法從MAX API獲取有效價格');
                // 使用預設的台幣價格
                const btcPriceElement = document.getElementById('btcPrice');
                if (btcPriceElement) {
                    btcPriceElement.textContent = 'NT$3,050,000';
                    btcPriceElement.style.color = '#ffa502';
                }
            }
        })
        .catch(error => {
            console.error('❌ MAX API請求失敗:', error);
            console.log('🔄 嘗試使用CORS代理獲取價格...');
            
            // 嘗試使用CORS代理
            fetch('https://api.allorigins.win/raw?url=' + encodeURIComponent('https://max-api.maicoin.com/api/v2/tickers/btctwd'))
                .then(response => response.json())
                .then(data => {
                    console.log('📊 代理MAX API響應:', data);
                    let price = null;
                    
                    if (data.ticker && data.ticker.last) {
                        price = parseFloat(data.ticker.last);
                    } else if (data.last) {
                        price = parseFloat(data.last);
                    }
                    
                    if (price && price > 0) {
                        const btcPriceElement = document.getElementById('btcPrice');
                        if (btcPriceElement) {
                            btcPriceElement.textContent = `NT$${price.toLocaleString()}`;
                            btcPriceElement.style.color = '#2ed573';
                            console.log('💰 通過代理獲取MAX API價格:', `NT$${price.toLocaleString()}`);
                        }
                    } else {
                        throw new Error('代理也無法獲取有效價格');
                    }
                })
                .catch(proxyError => {
                    console.error('❌ 代理請求也失敗:', proxyError);
                    // 最後使用預設的台幣價格
                    const btcPriceElement = document.getElementById('btcPrice');
                    if (btcPriceElement) {
                        btcPriceElement.textContent = 'NT$3,050,000';
                        btcPriceElement.style.color = '#ffa502';
                        
                        const priceChange = document.getElementById('priceChange');
                        if (priceChange) {
                            priceChange.textContent = '變化: 連線失敗，使用預設價格';
                        }
                    }
                });
        });
}

// 頁面載入後立即執行
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 頁面已載入，開始強制價格修正');
    
    // 立即執行一次
    setTimeout(forceMaxPrice, 500);
    
    // 每10秒強制更新一次
    setInterval(forceMaxPrice, 10000);
    
    // 覆蓋其他可能的價格更新函數
    setTimeout(() => {
        // 禁用其他價格更新邏輯
        if (window.dashboardManager && window.dashboardManager.updateTradingData) {
            const originalUpdate = window.dashboardManager.updateTradingData;
            window.dashboardManager.updateTradingData = async function() {
                console.log('🚫 攔截dashboard價格更新，保持MAX API價格');
                // 執行原始更新但跳過價格部分
                try {
                    await originalUpdate.call(this);
                } catch (e) {
                    console.log('⚠️ 原始更新失敗，繼續使用MAX API價格');
                }
                // 強制恢復MAX API價格
                setTimeout(forceMaxPrice, 100);
            };
        }
        
        console.log('🛡️ 價格保護機制已啟動');
    }, 2000);
});

// 提供手動刷新功能
window.forceRefreshMaxPrice = forceMaxPrice;

console.log('🔒 強制MAX API價格修正器已就緒');