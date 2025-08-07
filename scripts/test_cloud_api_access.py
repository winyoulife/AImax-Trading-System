#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試雲端API訪問能力
模擬GitHub Pages環境的限制
"""

import requests
import json
from datetime import datetime

def test_github_pages_environment():
    """模擬GitHub Pages環境測試"""
    print("🌐 模擬GitHub Pages環境測試")
    print("=" * 50)
    
    # GitHub Pages的限制：
    # 1. 只能運行前端JavaScript
    # 2. 受到瀏覽器CORS政策限制
    # 3. 無法直接調用外部API
    
    print("🚨 GitHub Pages環境限制：")
    print("• 只能運行前端JavaScript")
    print("• 受到瀏覽器CORS政策限制")
    print("• 無法直接調用MAX API")
    print("• 必須使用CORS代理或其他解決方案")
    
    return True

def test_cors_proxies_reliability():
    """測試CORS代理的可靠性"""
    print("\n🔍 測試CORS代理可靠性...")
    
    proxies = [
        {
            "name": "AllOrigins",
            "url": "https://api.allorigins.win/get?url=",
            "format": "wrapped"
        },
        {
            "name": "CORS Anywhere",
            "url": "https://cors-anywhere.herokuapp.com/",
            "format": "direct"
        },
        {
            "name": "CodeTabs",
            "url": "https://api.codetabs.com/v1/proxy?quest=",
            "format": "direct"
        }
    ]
    
    max_url = "https://max-api.maicoin.com/api/v2/tickers/btctwd"
    results = []
    
    for proxy in proxies:
        try:
            print(f"\n🔗 測試 {proxy['name']}...")
            
            if proxy['format'] == 'wrapped':
                full_url = proxy['url'] + max_url
            else:
                full_url = proxy['url'] + max_url
            
            response = requests.get(full_url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # 處理包裝格式
                    if proxy['format'] == 'wrapped' and 'contents' in data:
                        actual_data = json.loads(data['contents'])
                    else:
                        actual_data = data
                    
                    if 'last' in actual_data:
                        price = float(actual_data['last'])
                        print(f"✅ {proxy['name']}: NT$ {price:,.0f}")
                        results.append({
                            "proxy": proxy['name'],
                            "success": True,
                            "price": price,
                            "url": proxy['url']
                        })
                    else:
                        print(f"❌ {proxy['name']}: 數據格式錯誤")
                        results.append({
                            "proxy": proxy['name'],
                            "success": False,
                            "error": "數據格式錯誤"
                        })
                        
                except Exception as e:
                    print(f"❌ {proxy['name']}: 解析錯誤 - {e}")
                    results.append({
                        "proxy": proxy['name'],
                        "success": False,
                        "error": f"解析錯誤: {e}"
                    })
            else:
                print(f"❌ {proxy['name']}: HTTP {response.status_code}")
                results.append({
                    "proxy": proxy['name'],
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ {proxy['name']}: 請求失敗 - {e}")
            results.append({
                "proxy": proxy['name'],
                "success": False,
                "error": f"請求失敗: {e}"
            })
    
    return results

def create_cloud_compatible_solution(proxy_results):
    """創建雲端兼容的解決方案"""
    print("\n🔧 創建雲端兼容解決方案...")
    
    # 找到可用的代理
    working_proxies = [r for r in proxy_results if r.get('success', False)]
    
    if not working_proxies:
        print("❌ 沒有可用的CORS代理")
        return create_fallback_solution()
    
    print(f"✅ 找到 {len(working_proxies)} 個可用代理")
    
    # 創建多重備援的API調用代碼
    api_code = '''
        // 雲端兼容的BTC價格獲取 (多重備援)
        async function fetchRealBTCPriceCloud() {
            const proxies = ['''
    
    for proxy in working_proxies:
        if proxy['proxy'] == 'AllOrigins':
            api_code += '''
                {
                    name: 'AllOrigins',
                    url: 'https://api.allorigins.win/get?url=',
                    format: 'wrapped'
                },'''
        elif proxy['proxy'] == 'CodeTabs':
            api_code += '''
                {
                    name: 'CodeTabs', 
                    url: 'https://api.codetabs.com/v1/proxy?quest=',
                    format: 'direct'
                },'''
    
    api_code += '''
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
    '''
    
    return api_code

def create_fallback_solution():
    """創建備用解決方案"""
    print("🔄 創建備用解決方案...")
    
    # 如果所有代理都失敗，使用GitHub Actions定期更新價格
    fallback_code = '''
        // 備用方案：使用GitHub Actions定期更新的價格數據
        async function fetchBTCPriceFallback() {
            try {
                // 嘗試從GitHub倉庫獲取定期更新的價格數據
                const response = await fetch('https://raw.githubusercontent.com/winyoulife/AImax-Trading-System/main/data/latest_btc_price.json');
                
                if (response.ok) {
                    const data = await response.json();
                    const btcPrice = parseFloat(data.price);
                    
                    document.getElementById('btc-price').textContent = `NT$ ${formatNumber(btcPrice)} (GitHub)`;
                    console.log(`✅ 使用GitHub數據獲取BTC價格: NT$ ${formatNumber(btcPrice)}`);
                    return true;
                }
            } catch (error) {
                console.warn('⚠️ GitHub數據獲取失敗:', error);
            }
            
            // 最終備用價格
            const fallbackPrice = 3491828;
            document.getElementById('btc-price').textContent = `NT$ ${formatNumber(fallbackPrice)} (備用)`;
            console.log('使用最終備用價格');
            return false;
        }
    '''
    
    return fallback_code

def main():
    """主函數"""
    print("🔍 雲端API訪問能力測試")
    print("=" * 60)
    
    # 測試GitHub Pages環境
    test_github_pages_environment()
    
    # 測試CORS代理
    proxy_results = test_cors_proxies_reliability()
    
    # 創建解決方案
    solution_code = create_cloud_compatible_solution(proxy_results)
    
    # 保存解決方案
    with open('data/cloud_api_solution.js', 'w', encoding='utf-8') as f:
        f.write(solution_code)
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)
    
    working_count = sum(1 for r in proxy_results if r.get('success', False))
    total_count = len(proxy_results)
    
    print(f"🔗 可用代理: {working_count}/{total_count}")
    
    for result in proxy_results:
        status = "✅" if result.get('success', False) else "❌"
        proxy_name = result['proxy']
        if result.get('success', False):
            price = result.get('price', 0)
            print(f"  {status} {proxy_name}: NT$ {price:,.0f}")
        else:
            error = result.get('error', '未知錯誤')
            print(f"  {status} {proxy_name}: {error}")
    
    if working_count > 0:
        print(f"\n✅ 雲端可以獲取真實BTC價格")
        print(f"🎯 83.3%勝率策略可以基於真實數據運行")
    else:
        print(f"\n🚨 雲端無法獲取真實BTC價格")
        print(f"⚠️ 需要使用GitHub Actions定期更新價格數據")
    
    print(f"\n📋 解決方案已保存: data/cloud_api_solution.js")

if __name__ == "__main__":
    main()