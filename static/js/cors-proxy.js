// CORS代理解決方案 - 用於GitHub Pages環境

class CORSProxy {
    constructor() {
        // 使用支持CORS的代理服務
        this.proxies = [
            'https://api.allorigins.win/raw?url=',
            'https://cors-anywhere.herokuapp.com/',
            'https://api.codetabs.com/v1/proxy?quest='
        ];
        this.currentProxyIndex = 0;
    }
    
    async fetchWithProxy(url, options = {}) {
        // 嘗試直接請求（某些API支持CORS）
        try {
            const response = await fetch(url, {
                ...options,
                mode: 'cors'
            });
            if (response.ok) {
                return response;
            }
        } catch (e) {
            console.log('直接請求失敗，嘗試代理...');
        }
        
        // 使用代理服務
        for (let i = 0; i < this.proxies.length; i++) {
            try {
                const proxyUrl = this.proxies[this.currentProxyIndex] + encodeURIComponent(url);
                console.log(`嘗試代理 ${this.currentProxyIndex + 1}: ${proxyUrl}`);
                
                const response = await fetch(proxyUrl, {
                    ...options,
                    mode: 'cors'
                });
                
                if (response.ok) {
                    console.log(`代理 ${this.currentProxyIndex + 1} 成功`);
                    return response;
                }
            } catch (e) {
                console.warn(`代理 ${this.currentProxyIndex + 1} 失敗:`, e.message);
            }
            
            // 切換到下一個代理
            this.currentProxyIndex = (this.currentProxyIndex + 1) % this.proxies.length;
        }
        
        throw new Error('所有代理都失敗了');
    }
}

// 創建全局代理實例
window.corsProxy = new CORSProxy();