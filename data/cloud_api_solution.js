
        // 雲端兼容的BTC價格獲取 (多重備援)
        async function fetchRealBTCPriceCloud() {
            const proxies = [
                {
                    name: 'CodeTabs', 
                    url: 'https://api.codetabs.com/v1/proxy?quest=',
                    format: 'direct'
                },
            ];
            
            const maxApiUrl = 'https://max-api.maicoin.com/api/v2/tickers/btctwd';
            
            for (const proxy of proxies) {
                try {
                    console.log(`🔗 嘗試使用 ${proxy.name} 代理...`);
                    
                    const fullUrl = proxy.url + encodeURIComponent(maxApiUrl);
                    const response = await fetch(fullUrl);
                    
                    if (response.ok) {
                        const data = await response.json();
                        
                        // 處理不同代理的響應格式
                        let actualData;
                        if (proxy.format === 'wrapped' && data.contents) {
                            actualData = JSON.parse(data.contents);
                        } else {
                            actualData = data;
                        }
                        
                        if (actualData && actualData.last) {
                            const btcPrice = parseFloat(actualData.last);
                            
                            // 更新顯示
                            document.getElementById('btc-price').textContent = `NT$ ${formatNumber(btcPrice)}`;
                            
                            // 更新後端狀態顯示
                            const backendPriceElement = document.getElementById('backend-btc-price');
                            if (backendPriceElement) {
                                backendPriceElement.textContent = `NT$ ${formatNumber(btcPrice)}`;
                            }
                            
                            // 更新持倉價值
                            const btcAmount = 0.010544;
                            const positionValue = btcPrice * btcAmount;
                            document.getElementById('position-value').textContent = `NT$ ${formatNumber(Math.round(positionValue))}`;
                            
                            console.log(`✅ 使用 ${proxy.name} 成功獲取BTC價格: NT$ ${formatNumber(btcPrice)}`);
                            return true;
                        }
                    }
                } catch (error) {
                    console.warn(`⚠️ ${proxy.name} 代理失敗:`, error);
                    continue;
                }
            }
            
            // 所有代理都失敗，使用備用價格
            console.error('❌ 所有CORS代理都失敗，使用備用價格');
            const fallbackPrice = 3491828;
            document.getElementById('btc-price').textContent = `NT$ ${formatNumber(fallbackPrice)} (備用)`;
            return false;
        }
    