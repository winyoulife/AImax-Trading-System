#!/usr/bin/env python3
"""
🔥 立即獲取真實MAX API BTC/TWD價格
"""
import requests
import json
from datetime import datetime

def get_real_btc_price():
    """獲取真實BTC價格"""
    try:
        print("🔍 正在獲取MAX API真實BTC/TWD價格...")
        
        # 直接調用MAX API
        url = "https://max-api.maicoin.com/api/v2/tickers/btctwd"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 API響應: {json.dumps(data, indent=2)}")
            
            # 提取價格信息
            current_price = float(data['last'])
            buy_price = float(data['buy'])
            sell_price = float(data['sell'])
            high_24h = float(data['high'])
            low_24h = float(data['low'])
            volume_24h = float(data['vol'])
            
            print("\n" + "="*50)
            print("📊 MAX API 真實BTC/TWD價格")
            print("="*50)
            print(f"💰 當前價格: NT$ {current_price:,.0f}")
            print(f"💵 買入價格: NT$ {buy_price:,.0f}")
            print(f"💸 賣出價格: NT$ {sell_price:,.0f}")
            print(f"📈 24小時最高: NT$ {high_24h:,.0f}")
            print(f"📉 24小時最低: NT$ {low_24h:,.0f}")
            print(f"📊 24小時成交量: {volume_24h:.4f} BTC")
            print(f"⏰ 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*50)
            
            return current_price
            
    except Exception as e:
        print(f"❌ 獲取價格失敗: {e}")
        return None

if __name__ == "__main__":
    price = get_real_btc_price()
    if price:
        print(f"\n🎯 結果: 真實BTC價格 = NT$ {price:,.0f}")
    else:
        print("\n❌ 無法獲取真實價格")