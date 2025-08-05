#!/usr/bin/env python3
"""
測試 MAX API 連接
基於官方文檔驗證 API 使用方式
"""

import requests
import json
import time
from max_api_client import MAXAPIClient

def test_direct_api():
    """直接測試 MAX API"""
    print("🔍 直接測試 MAX API...")
    print("=" * 40)
    
    # 官方 API 端點
    api_url = "https://max-api.maicoin.com/api/v2/tickers/btctwd"
    
    try:
        # 使用官方推薦的請求方式
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'AImax-Trading-System/3.0'
        }
        
        print(f"📡 請求 URL: {api_url}")
        print(f"📋 請求標頭: {headers}")
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        print(f"📊 HTTP 狀態碼: {response.status_code}")
        print(f"📋 響應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 響應成功")
            print(f"📄 響應數據結構:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 解析價格
            if 'last' in data:
                price = float(data['last'])
                print(f"💰 BTC/TWD 價格: NT${price:,.0f}")
                
                # 檢查其他字段
                if 'buy' in data:
                    print(f"💵 買入價: NT${float(data['buy']):,.0f}")
                if 'sell' in data:
                    print(f"💸 賣出價: NT${float(data['sell']):,.0f}")
                if 'vol' in data:
                    print(f"📈 成交量: {data['vol']}")
                if 'at' in data:
                    timestamp = data['at']
                    print(f"⏰ 時間戳: {timestamp}")
                    
                return True
            else:
                print("❌ 響應中沒有 'last' 價格字段")
                return False
        else:
            print(f"❌ API 請求失敗: HTTP {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 請求異常: {e}")
        return False

def test_api_client():
    """測試 MAX API 客戶端"""
    print("\n🔧 測試 MAX API 客戶端...")
    print("=" * 40)
    
    try:
        client = MAXAPIClient()
        
        # 測試連接
        test_result = client.test_connection()
        print(f"連接測試結果: {json.dumps(test_result, indent=2, ensure_ascii=False)}")
        
        if test_result["success"]:
            # 獲取價格
            price_data = client.get_btc_twd_price()
            print(f"價格數據: {json.dumps(price_data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 客戶端測試失敗: {test_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 客戶端測試異常: {e}")
        return False

def test_proxy_server():
    """測試代理服務器"""
    print("\n🌐 測試代理服務器...")
    print("=" * 40)
    
    proxy_url = "http://localhost:5000/api/btc-price"
    
    try:
        print(f"📡 請求代理: {proxy_url}")
        response = requests.get(proxy_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 代理響應成功")
            print(f"📄 代理數據:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get("success"):
                print(f"💰 通過代理獲取的價格: {data.get('formatted_price')}")
                return True
            else:
                print(f"❌ 代理返回錯誤: {data.get('error')}")
                return False
        else:
            print(f"❌ 代理請求失敗: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️ 代理服務器未運行，請先啟動: python max_api_proxy.py")
        return False
    except Exception as e:
        print(f"❌ 代理測試異常: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 MAX API 連接測試")
    print("基於官方文檔: https://max.maicoin.com/documents/api")
    print("WebSocket 文檔: https://maicoin.github.io/max-websocket-docs/#/")
    print("=" * 60)
    
    results = []
    
    # 測試 1: 直接 API 調用
    results.append(("直接 API", test_direct_api()))
    
    # 測試 2: API 客戶端
    results.append(("API 客戶端", test_api_client()))
    
    # 測試 3: 代理服務器
    results.append(("代理服務器", test_proxy_server()))
    
    # 總結
    print("\n📋 測試總結")
    print("=" * 40)
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 所有測試通過！MAX API 連接正常。")
    else:
        print("\n⚠️ 部分測試失敗，請檢查網路連接和 API 狀態。")
    
    return all_passed

if __name__ == "__main__":
    main()