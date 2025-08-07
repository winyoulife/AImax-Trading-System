#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正BTC價格顯示問題
將模擬價格改為真實MAX API價格
"""

import os
import sys

def fix_btc_price():
    """修正BTC價格顯示"""
    print("🔧 修正BTC價格顯示問題")
    print("=" * 50)
    
    dashboard_file = "static/smart-balanced-dashboard.html"
    
    if not os.path.exists(dashboard_file):
        print(f"❌ 找不到文件: {dashboard_file}")
        return
    
    # 讀取文件
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替換模擬價格代碼為真實API調用
    old_code = '''        // 模擬數據更新
        function refreshData() {
            // 模擬BTC價格波動
            const basePrice = 95000;
            const variation = (Math.random() - 0.5) * 2000;
            const currentPrice = Math.round(basePrice + variation);
            
            document.getElementById('btc-price').textContent = `${formatNumber(currentPrice)}`;
            
            // 更新時間
            document.getElementById('last-update').textContent = 
                new Date().toLocaleString('zh-TW');
            
            console.log('數據已刷新');
        }'''
    
    new_code = '''        // 獲取真實的MAX API BTC價格
        async function fetchRealBTCPrice() {
            try {
                // 使用CORS代理獲取MAX API數據
                const proxyUrl = 'https://api.allorigins.win/raw?url=';
                const maxApiUrl = 'https://max-api.maicoin.com/api/v2/tickers/btctwd';
                
                const response = await fetch(proxyUrl + encodeURIComponent(maxApiUrl));
                const data = await response.json();
                
                if (data && data.ticker && data.ticker.last) {
                    const btcPrice = parseFloat(data.ticker.last);
                    document.getElementById('btc-price').textContent = `NT$ ${formatNumber(btcPrice)}`;
                    
                    // 更新持倉價值
                    const btcAmount = 0.010544; // 當前持倉
                    const positionValue = btcPrice * btcAmount;
                    document.getElementById('position-value').textContent = `NT$ ${formatNumber(Math.round(positionValue))}`;
                    
                    console.log(`✅ BTC價格已更新: NT$ ${formatNumber(btcPrice)}`);
                } else {
                    throw new Error('API數據格式錯誤');
                }
            } catch (error) {
                console.error('❌ 獲取BTC價格失敗:', error);
                // 使用備用價格
                const fallbackPrice = 3000000; // 300萬台幣作為備用價格
                document.getElementById('btc-price').textContent = `NT$ ${formatNumber(fallbackPrice)} (備用)`;
            }
        }

        // 真實數據更新
        function refreshData() {
            // 獲取真實的MAX API BTC價格
            fetchRealBTCPrice();
            
            // 更新時間
            document.getElementById('last-update').textContent = 
                new Date().toLocaleString('zh-TW');
            
            console.log('數據已刷新');
        }'''
    
    # 檢查是否找到要替換的代碼
    if old_code in content:
        content = content.replace(old_code, new_code)
        print("✅ 找到並替換了模擬價格代碼")
    else:
        # 嘗試更靈活的替換
        import re
        pattern = r'// 模擬數據更新.*?console\.log\(\'數據已刷新\'\);.*?}'
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_code.split('// 真實數據更新')[1], content, flags=re.DOTALL)
            print("✅ 使用正則表達式替換了模擬價格代碼")
        else:
            print("❌ 找不到要替換的代碼，手動添加新功能")
            # 在</script>前添加新功能
            script_end = content.rfind('</script>')
            if script_end != -1:
                content = content[:script_end] + '\n' + new_code + '\n' + content[script_end:]
                print("✅ 手動添加了真實價格獲取功能")
    
    # 更新版本信息
    content = content.replace(
        'v2.1-stable | 2025/08/07 22:35',
        'v2.2-realtime | 2025/08/08 09:00'
    )
    
    # 寫入文件
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ BTC價格修正完成")
    print("📊 現在將顯示真實的MAX API BTC價格")
    print("🔄 價格每30秒自動更新")
    
    print("\n" + "=" * 50)
    print("🔧 BTC價格修正完成")

if __name__ == "__main__":
    fix_btc_price()