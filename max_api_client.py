#!/usr/bin/env python3
"""
MAX Exchange API 客戶端
基於官方文檔: https://max.maicoin.com/documents/api
WebSocket 文檔: https://maicoin.github.io/max-websocket-docs/#/
"""

import requests
import json
import websocket
import threading
import time
from typing import Dict, Any, Optional, Callable

class MAXAPIClient:
    """MAX Exchange API 客戶端"""
    
    def __init__(self):
        # REST API 基礎 URL
        self.base_url = "https://max-api.maicoin.com"
        self.api_version = "v2"
        
        # WebSocket URL
        self.ws_url = "wss://max-stream.maicoin.com/ws"
        
        # 會話設置
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AImax-Trading-System/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # WebSocket 相關
        self.ws = None
        self.ws_connected = False
        self.price_callback = None
        
    def get_ticker(self, market: str = "btctwd") -> Dict[str, Any]:
        """
        獲取市場行情
        
        Args:
            market: 交易對，例如 'btctwd'
            
        Returns:
            包含價格信息的字典
        """
        try:
            url = f"{self.base_url}/api/{self.api_version}/tickers/{market}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 驗證響應格式
            if not isinstance(data, dict):
                raise ValueError("API 響應格式錯誤")
                
            return data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 請求失敗: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 解析失敗: {e}")
        except Exception as e:
            raise Exception(f"獲取行情失敗: {e}")
    
    def get_btc_twd_price(self) -> Dict[str, Any]:
        """
        獲取 BTC/TWD 價格
        
        Returns:
            包含價格和相關信息的字典
        """
        try:
            ticker_data = self.get_ticker("btctwd")
            
            # 根據官方文檔解析數據
            # 響應格式可能是: {"at": timestamp, "buy": "price", "sell": "price", "last": "price", ...}
            # 或者: {"ticker": {"at": timestamp, "buy": "price", "sell": "price", "last": "price", ...}}
            
            if "ticker" in ticker_data:
                # 如果有 ticker 包裝
                ticker = ticker_data["ticker"]
            else:
                # 直接是 ticker 數據
                ticker = ticker_data
            
            # 提取價格信息
            last_price = ticker.get("last")
            buy_price = ticker.get("buy") 
            sell_price = ticker.get("sell")
            volume = ticker.get("vol", ticker.get("volume"))
            timestamp = ticker.get("at")
            
            if not last_price:
                raise ValueError("無法獲取最新價格")
            
            # 轉換為數字
            try:
                last_price_float = float(last_price)
                buy_price_float = float(buy_price) if buy_price else None
                sell_price_float = float(sell_price) if sell_price else None
                volume_float = float(volume) if volume else None
            except (ValueError, TypeError) as e:
                raise ValueError(f"價格數據格式錯誤: {e}")
            
            return {
                "success": True,
                "market": "btctwd",
                "last_price": last_price_float,
                "buy_price": buy_price_float,
                "sell_price": sell_price_float,
                "volume": volume_float,
                "timestamp": timestamp,
                "formatted_price": f"NT${last_price_float:,.0f}",
                "raw_data": ticker_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "market": "btctwd",
                "timestamp": None
            }
    
    def get_all_tickers(self) -> Dict[str, Any]:
        """
        獲取所有市場行情
        
        Returns:
            所有市場的行情數據
        """
        try:
            url = f"{self.base_url}/api/{self.api_version}/tickers"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            raise Exception(f"獲取所有行情失敗: {e}")
    
    def start_websocket_price_stream(self, market: str = "btctwd", callback: Optional[Callable] = None):
        """
        啟動 WebSocket 價格流
        
        Args:
            market: 交易對
            callback: 價格更新回調函數
        """
        self.price_callback = callback
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if self.price_callback and data.get("channel") == "ticker":
                    self.price_callback(data)
            except Exception as e:
                print(f"WebSocket 消息處理錯誤: {e}")
        
        def on_error(ws, error):
            print(f"WebSocket 錯誤: {error}")
            self.ws_connected = False
        
        def on_close(ws, close_status_code, close_msg):
            print("WebSocket 連接已關閉")
            self.ws_connected = False
        
        def on_open(ws):
            print("WebSocket 連接已建立")
            self.ws_connected = True
            
            # 訂閱 ticker 頻道
            subscribe_msg = {
                "id": f"ticker_{market}",
                "action": "sub",
                "subscriptions": [
                    {
                        "channel": "ticker",
                        "market": market
                    }
                ]
            }
            ws.send(json.dumps(subscribe_msg))
        
        # 創建 WebSocket 連接
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        # 在後台線程中運行
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
    
    def stop_websocket(self):
        """停止 WebSocket 連接"""
        if self.ws:
            self.ws.close()
            self.ws_connected = False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        測試 API 連接
        
        Returns:
            連接測試結果
        """
        try:
            # 測試 REST API
            start_time = time.time()
            btc_data = self.get_btc_twd_price()
            rest_time = time.time() - start_time
            
            if btc_data["success"]:
                return {
                    "success": True,
                    "rest_api": {
                        "status": "正常",
                        "response_time": f"{rest_time:.2f}秒",
                        "price": btc_data["formatted_price"]
                    },
                    "websocket": {
                        "status": "支援" if self.ws_connected else "未連接"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": btc_data["error"]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"連接測試失敗: {e}"
            }

def main():
    """測試 MAX API 客戶端"""
    print("🚀 MAX API 客戶端測試")
    print("=" * 40)
    
    client = MAXAPIClient()
    
    # 測試連接
    print("📡 測試 API 連接...")
    test_result = client.test_connection()
    
    if test_result["success"]:
        print("✅ API 連接正常")
        print(f"💰 當前 BTC/TWD 價格: {test_result['rest_api']['price']}")
        print(f"⏱️ 響應時間: {test_result['rest_api']['response_time']}")
    else:
        print(f"❌ API 連接失敗: {test_result['error']}")
        return
    
    # 測試獲取詳細價格信息
    print("\n📊 獲取詳細價格信息...")
    price_data = client.get_btc_twd_price()
    
    if price_data["success"]:
        print(f"最新價格: {price_data['formatted_price']}")
        print(f"買入價格: NT${price_data['buy_price']:,.0f}" if price_data['buy_price'] else "買入價格: N/A")
        print(f"賣出價格: NT${price_data['sell_price']:,.0f}" if price_data['sell_price'] else "賣出價格: N/A")
        print(f"交易量: {price_data['volume']}" if price_data['volume'] else "交易量: N/A")
    else:
        print(f"❌ 獲取價格失敗: {price_data['error']}")
    
    # 測試 WebSocket (可選)
    print("\n🔌 測試 WebSocket 連接...")
    
    def price_update_callback(data):
        if data.get("ticker"):
            ticker = data["ticker"]
            price = ticker.get("last")
            if price:
                print(f"📈 WebSocket 價格更新: NT${float(price):,.0f}")
    
    try:
        client.start_websocket_price_stream(callback=price_update_callback)
        print("WebSocket 已啟動，等待價格更新...")
        time.sleep(10)  # 等待 10 秒接收數據
        client.stop_websocket()
        print("WebSocket 測試完成")
    except Exception as e:
        print(f"WebSocket 測試失敗: {e}")

if __name__ == "__main__":
    main()