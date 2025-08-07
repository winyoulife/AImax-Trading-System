#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試真實BTC價格獲取
確認後端是否能獲取到真實數據
"""

import requests
import json
from datetime import datetime

def test_max_api():
    """測試MAX API"""
    print("🔍 測試MAX API直接調用...")
    
    try:
        url = "https://max-api.maicoin.com/api/v2/tickers/btctwd"
        response = requests.get(url, timeout=10)
        
        print(f"📡 API URL: {url}")
        print(f"📊 HTTP狀態碼: {response.status_code}")
        print(f"📋 響應頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📄 原始響應: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if 'ticker' in data and 'last' in data['ticker']:
                    price = float(data['ticker']['last'])
                    print(f"✅ 成功獲取BTC價格: NT$ {price:,.0f}")
                    return price
                else:
                    print("❌ 響應格式不正確，缺少ticker.last")
                    return None
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失敗: {e}")
                print(f"📄 原始響應文本: {response.text[:500]}")
                return None
        else:
            print(f"❌ API調用失敗")
            print(f"📄 錯誤響應: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ 請求異常: {e}")
        return None

def test_cors_proxy():
    """測試CORS代理"""
    print("\n🔍 測試CORS代理...")
    
    proxies = [
        "https://api.allorigins.win/get?url=",
        "https://api.codetabs.com/v1/proxy?quest="
    ]
    
    max_url = "https://max-api.maicoin.com/api/v2/tickers/btctwd"
    
    for proxy in proxies:
        try:
            print(f"\n🔗 測試代理: {proxy}")
            full_url = proxy + max_url
            
            response = requests.get(full_url, timeout=10)
            print(f"📊 HTTP狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # 處理allorigins.win的包裝格式
                    if 'contents' in data:
                        actual_data = json.loads(data['contents'])
                    else:
                        actual_data = data
                    
                    print(f"📄 解析後數據: {json.dumps(actual_data, indent=2, ensure_ascii=False)}")
                    
                    if 'ticker' in actual_data and 'last' in actual_data['ticker']:
                        price = float(actual_data['ticker']['last'])
                        print(f"✅ 代理成功獲取BTC價格: NT$ {price:,.0f}")
                        return price
                    else:
                        print("❌ 代理響應格式不正確")
                        
                except Exception as e:
                    print(f"❌ 代理數據解析失敗: {e}")
                    print(f"📄 原始響應: {response.text[:500]}")
            else:
                print(f"❌ 代理調用失敗: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ 代理請求異常: {e}")
    
    return None

def create_price_status_file(direct_price, proxy_price):
    """創建價格狀態文件"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "direct_api": {
            "success": direct_price is not None,
            "price": direct_price
        },
        "proxy_api": {
            "success": proxy_price is not None,
            "price": proxy_price
        },
        "recommendation": ""
    }
    
    if direct_price:
        status["recommendation"] = "建議使用直接API調用"
        status["best_price"] = direct_price
    elif proxy_price:
        status["recommendation"] = "建議使用CORS代理"
        status["best_price"] = proxy_price
    else:
        status["recommendation"] = "所有API都失敗，需要檢查網路或使用備用數據源"
        status["best_price"] = None
    
    # 保存狀態文件
    import os
    os.makedirs("data", exist_ok=True)
    
    with open("data/btc_price_status.json", 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    
    return status

def main():
    """主函數"""
    print("🔍 BTC價格獲取測試")
    print("=" * 50)
    print("測試後端是否能獲取到真實的BTC價格")
    print("=" * 50)
    
    # 測試直接API
    direct_price = test_max_api()
    
    # 測試代理API
    proxy_price = test_cors_proxy()
    
    # 創建狀態報告
    status = create_price_status_file(direct_price, proxy_price)
    
    # 顯示總結
    print("\n" + "=" * 50)
    print("📊 測試總結")
    print("=" * 50)
    
    print(f"🔗 直接API: {'✅ 成功' if direct_price else '❌ 失敗'}")
    if direct_price:
        print(f"   價格: NT$ {direct_price:,.0f}")
    
    print(f"🔗 代理API: {'✅ 成功' if proxy_price else '❌ 失敗'}")
    if proxy_price:
        print(f"   價格: NT$ {proxy_price:,.0f}")
    
    print(f"\n💡 建議: {status['recommendation']}")
    
    if status['best_price']:
        print(f"✅ 最佳價格: NT$ {status['best_price']:,.0f}")
        print("\n🎯 結論: 後端可以獲取到真實BTC價格")
        print("   83.3%勝率策略可以基於真實數據運行")
    else:
        print("\n🚨 警告: 無法獲取真實BTC價格")
        print("   83.3%勝率策略可能無法基於真實數據運行")
        print("   建議檢查網路連接或使用備用數據源")
    
    print(f"\n📋 狀態報告已保存: data/btc_price_status.json")

if __name__ == "__main__":
    main()