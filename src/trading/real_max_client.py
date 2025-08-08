#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 真實MAX交易所API客戶端
連接台灣MAX交易所，獲取真實的交易數據
"""

import requests
import json
import time
import hmac
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

class RealMaxClient:
    """真實MAX交易所API客戶端"""
    
    def __init__(self, api_key: str = None, secret_key: str = None):
        self.base_url = "https://max-api.maicoin.com"
        self.api_key = api_key
        self.secret_key = secret_key
        
        # 公開API不需要認證
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AImax-Trading-System/1.0'
        })
    
    def get_ticker(self, market: str = "btctwd") -> Dict:
        """獲取實時價格數據"""
        try:
            url = f"{self.base_url}/api/v2/tickers/{market}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'data': {
                    'symbol': market.upper(),
                    'last_price': float(data['last']),
                    'bid_price': float(data['buy']),
                    'ask_price': float(data['sell']),
                    'high_24h': float(data['high']),
                    'low_24h': float(data['low']),
                    'volume_24h': float(data['vol']),
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_orderbook(self, market: str = "btctwd", limit: int = 10) -> Dict:
        """獲取訂單簿數據"""
        try:
            url = f"{self.base_url}/api/v2/depth"
            params = {
                'market': market,
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'success': True,
                'data': {
                    'symbol': market.upper(),
                    'bids': [[float(price), float(volume)] for price, volume in data['bids']],
                    'asks': [[float(price), float(volume)] for price, volume in data['asks']],
                    'timestamp': datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_recent_trades(self, market: str = "btctwd", limit: int = 50) -> Dict:
        """獲取最近交易記錄"""
        try:
            url = f"{self.base_url}/api/v2/trades"
            params = {
                'market': market,
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            trades = []
            
            for trade in data:
                trades.append({
                    'id': trade['id'],
                    'price': float(trade['price']),
                    'volume': float(trade['volume']),
                    'side': trade['side'],  # 'buy' or 'sell'
                    'timestamp': trade['created_at']
                })
            
            return {
                'success': True,
                'data': {
                    'symbol': market.upper(),
                    'trades': trades
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_signature(self, method: str, path: str, params: Dict = None) -> str:
        """生成API簽名 (私有API需要)"""
        if not self.secret_key:
            raise ValueError("Secret key required for private API")
        
        nonce = str(int(time.time() * 1000))
        
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
            payload = f"{method}|{path}|{query_string}|{nonce}"
        else:
            payload = f"{method}|{path}||{nonce}"
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature, nonce
    
    def get_account_info(self) -> Dict:
        """獲取帳戶信息 (需要API Key)"""
        if not self.api_key or not self.secret_key:
            return {
                'success': False,
                'error': 'API credentials required for account info'
            }
        
        try:
            path = "/api/v2/members/accounts"
            signature, nonce = self._generate_signature("GET", path)
            
            headers = {
                'X-MAX-ACCESSKEY': self.api_key,
                'X-MAX-PAYLOAD': signature,
                'X-MAX-NONCE': nonce
            }
            
            url = f"{self.base_url}{path}"
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            accounts = {}
            
            for account in data:
                currency = account['currency'].upper()
                accounts[currency] = {
                    'currency': currency,
                    'balance': float(account['balance']),
                    'locked': float(account['locked']),
                    'available': float(account['balance']) - float(account['locked'])
                }
            
            return {
                'success': True,
                'data': accounts
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_my_trades(self, market: str = "btctwd", limit: int = 100) -> Dict:
        """獲取我的交易記錄 (需要API Key)"""
        if not self.api_key or not self.secret_key:
            return {
                'success': False,
                'error': 'API credentials required for trade history'
            }
        
        try:
            path = "/api/v2/trades/my"
            params = {
                'market': market,
                'limit': limit
            }
            
            signature, nonce = self._generate_signature("GET", path, params)
            
            headers = {
                'X-MAX-ACCESSKEY': self.api_key,
                'X-MAX-PAYLOAD': signature,
                'X-MAX-NONCE': nonce
            }
            
            url = f"{self.base_url}{path}"
            response = self.session.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            trades = []
            
            for trade in data:
                trades.append({
                    'id': trade['id'],
                    'price': float(trade['price']),
                    'volume': float(trade['volume']),
                    'funds': float(trade['funds']),
                    'side': trade['side'],
                    'fee': float(trade['fee']),
                    'fee_currency': trade['fee_currency'],
                    'order_id': trade['order_id'],
                    'timestamp': trade['created_at']
                })
            
            return {
                'success': True,
                'data': {
                    'symbol': market.upper(),
                    'trades': trades
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

def test_max_client():
    """測試MAX API客戶端"""
    print("🧪 測試MAX API客戶端")
    print("=" * 50)
    
    client = RealMaxClient()
    
    # 測試公開API
    print("📊 測試實時價格...")
    ticker = client.get_ticker()
    if ticker['success']:
        data = ticker['data']
        print(f"✅ BTC價格: NT$ {data['last_price']:,.0f}")
        print(f"   買價: NT$ {data['bid_price']:,.0f}")
        print(f"   賣價: NT$ {data['ask_price']:,.0f}")
        print(f"   24H高: NT$ {data['high_24h']:,.0f}")
        print(f"   24H低: NT$ {data['low_24h']:,.0f}")
        print(f"   24H量: {data['volume_24h']:.4f} BTC")
    else:
        print(f"❌ 獲取價格失敗: {ticker['error']}")
    
    print("\n📈 測試最近交易...")
    trades = client.get_recent_trades(limit=5)
    if trades['success']:
        print("✅ 最近5筆交易:")
        for trade in trades['data']['trades'][:5]:
            side_emoji = "🟢" if trade['side'] == 'buy' else "🔴"
            print(f"   {side_emoji} {trade['side'].upper()}: NT$ {trade['price']:,.0f} × {trade['volume']:.6f}")
    else:
        print(f"❌ 獲取交易記錄失敗: {trades['error']}")
    
    print("\n📋 測試訂單簿...")
    orderbook = client.get_orderbook(limit=3)
    if orderbook['success']:
        data = orderbook['data']
        print("✅ 訂單簿 (前3檔):")
        print("   賣單:")
        for price, volume in reversed(data['asks']):
            print(f"     NT$ {price:,.0f} × {volume:.6f}")
        print("   買單:")
        for price, volume in data['bids']:
            print(f"     NT$ {price:,.0f} × {volume:.6f}")
    else:
        print(f"❌ 獲取訂單簿失敗: {orderbook['error']}")

if __name__ == "__main__":
    test_max_client()