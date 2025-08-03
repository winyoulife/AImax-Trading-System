#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真實MAX API交易連接器
實現真實訂單執行、狀態監控和實時價格數據流同步
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import base64
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """訂單類型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    """訂單方向"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """訂單狀態"""
    WAIT = "wait"           # 等待成交
    DONE = "done"           # 完全成交
    CANCEL = "cancel"       # 已取消
    FINALIZING = "finalizing"  # 結算中

@dataclass
class OrderRequest:
    """訂單請求"""
    market: str
    side: OrderSide
    order_type: OrderType
    volume: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    client_oid: Optional[str] = None

@dataclass
class OrderResponse:
    """訂單回應"""
    id: int
    market: str
    side: str
    order_type: str
    volume: float
    price: Optional[float]
    state: str
    created_at: datetime
    trades_count: int
    remaining_volume: float
    executed_volume: float
    avg_price: Optional[float]
    client_oid: Optional[str] = None

@dataclass
class TradeExecution:
    """交易執行記錄"""
    id: int
    order_id: int
    market: str
    side: str
    volume: float
    price: float
    fee: float
    fee_currency: str
    created_at: datetime

class LiveMAXAPIConnector:
    """真實MAX API連接器"""
    
    def __init__(self, api_key: str = "", secret_key: str = "", 
                 base_url: str = "https://max-api.maicoin.com"):
        """
        初始化MAX API連接器
        
        Args:
            api_key: API密鑰
            secret_key: 密鑰
            base_url: API基礎URL
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        
        # 連接狀態
        self.is_connected = False
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 訂單追蹤
        self.active_orders: Dict[int, OrderResponse] = {}
        self.order_history: List[OrderResponse] = []
        self.trade_executions: List[TradeExecution] = []
        
        # 實時數據
        self.current_prices: Dict[str, float] = {}
        self.account_balance: Dict[str, float] = {}
        
        # 安全設置
        self.max_order_value_twd = 1000.0  # 最大單筆訂單價值
        self.daily_trade_limit = 10        # 每日交易次數限制
        self.daily_trade_count = 0
        
        logger.info("🔗 MAX API連接器初始化完成")
    
    async def connect(self) -> bool:
        """建立API連接"""
        try:
            # 創建HTTP會話
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # 測試API連接
            if await self._test_connection():
                self.is_connected = True
                
                # 獲取初始數據
                await self._fetch_account_info()
                await self._fetch_current_prices()
                
                logger.info("✅ MAX API連接成功")
                return True
            else:
                logger.error("❌ MAX API連接測試失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ MAX API連接失敗: {e}")
            return False
    
    async def disconnect(self) -> None:
        """斷開API連接"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.is_connected = False
            logger.info("🔌 MAX API連接已斷開")
            
        except Exception as e:
            logger.error(f"❌ 斷開連接失敗: {e}")
    
    async def _test_connection(self) -> bool:
        """測試API連接"""
        try:
            # 測試公開API
            url = f"{self.base_url}/api/v2/markets"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"📊 獲取到 {len(data)} 個交易市場")
                    return True
                else:
                    logger.error(f"❌ API測試失敗，狀態碼: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 連接測試異常: {e}")
            return False
    
    def _generate_signature(self, method: str, path: str, params: Dict[str, Any] = None) -> Dict[str, str]:
        """生成API簽名"""
        try:
            nonce = str(int(time.time() * 1000))
            
            # 構建查詢字符串
            query_string = ""
            if params:
                query_string = urlencode(sorted(params.items()))
            
            # 構建簽名字符串
            payload = f"{method}|{path}|{query_string}|{nonce}"
            
            # 生成簽名
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return {
                'X-MAX-ACCESSKEY': self.api_key,
                'X-MAX-NONCE': nonce,
                'X-MAX-SIGNATURE': signature
            }
            
        except Exception as e:
            logger.error(f"❌ 生成簽名失敗: {e}")
            return {}
    
    async def _fetch_account_info(self) -> bool:
        """獲取帳戶信息"""
        try:
            if not self.api_key or not self.secret_key:
                logger.warning("⚠️ 未配置API密鑰，使用模擬模式")
                # 模擬帳戶餘額
                self.account_balance = {
                    'twd': 10000.0,  # 10000 TWD
                    'btc': 0.0
                }
                return True
            
            # 實際API調用（需要有效的API密鑰）
            path = "/api/v2/members/accounts"
            headers = self._generate_signature("GET", path)
            
            if not headers:
                return False
            
            url = f"{self.base_url}{path}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    accounts = await response.json()
                    
                    # 更新帳戶餘額
                    for account in accounts:
                        currency = account['currency']
                        balance = float(account['balance'])
                        self.account_balance[currency] = balance
                    
                    logger.info(f"💰 帳戶餘額更新: {self.account_balance}")
                    return True
                else:
                    logger.error(f"❌ 獲取帳戶信息失敗，狀態碼: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 獲取帳戶信息異常: {e}")
            return False
    
    async def _fetch_current_prices(self) -> bool:
        """獲取當前價格"""
        try:
            url = f"{self.base_url}/api/v2/tickers"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    tickers = await response.json()
                    
                    # 更新價格數據
                    for market, ticker in tickers.items():
                        if 'last' in ticker:
                            self.current_prices[market] = float(ticker['last'])
                    
                    logger.info(f"📈 價格數據更新: {len(self.current_prices)} 個市場")
                    return True
                else:
                    logger.error(f"❌ 獲取價格失敗，狀態碼: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 獲取價格異常: {e}")
            return False
    
    async def place_order(self, order_request: OrderRequest) -> Tuple[bool, Optional[OrderResponse], str]:
        """
        下單
        
        Args:
            order_request: 訂單請求
            
        Returns:
            (成功標誌, 訂單回應, 錯誤信息)
        """
        try:
            # 安全檢查
            safety_check, safety_message = self._safety_check_order(order_request)
            if not safety_check:
                return False, None, safety_message
            
            # 如果沒有API密鑰，使用模擬模式
            if not self.api_key or not self.secret_key:
                return await self._simulate_order(order_request)
            
            # 實際下單
            return await self._place_real_order(order_request)
            
        except Exception as e:
            logger.error(f"❌ 下單異常: {e}")
            return False, None, str(e)
    
    def _safety_check_order(self, order_request: OrderRequest) -> Tuple[bool, str]:
        """訂單安全檢查"""
        try:
            # 檢查連接狀態
            if not self.is_connected:
                return False, "API未連接"
            
            # 檢查每日交易限制
            if self.daily_trade_count >= self.daily_trade_limit:
                return False, f"已達每日交易限制 ({self.daily_trade_limit})"
            
            # 檢查訂單價值
            if order_request.market in self.current_prices:
                current_price = self.current_prices[order_request.market]
                order_value = order_request.volume * current_price
                
                if order_value > self.max_order_value_twd:
                    return False, f"訂單價值超限 ({order_value:.2f} > {self.max_order_value_twd})"
            
            # 檢查帳戶餘額
            if order_request.side == OrderSide.BUY:
                required_twd = order_request.volume * (order_request.price or self.current_prices.get(order_request.market, 0))
                available_twd = self.account_balance.get('twd', 0)
                
                if required_twd > available_twd:
                    return False, f"TWD餘額不足 ({required_twd:.2f} > {available_twd:.2f})"
            
            return True, "安全檢查通過"
            
        except Exception as e:
            logger.error(f"❌ 安全檢查異常: {e}")
            return False, str(e)
    
    async def _simulate_order(self, order_request: OrderRequest) -> Tuple[bool, Optional[OrderResponse], str]:
        """模擬下單（用於測試）"""
        try:
            # 生成模擬訂單ID
            order_id = int(time.time() * 1000) % 1000000
            
            # 獲取當前價格
            current_price = self.current_prices.get(order_request.market, 3500000.0)  # 默認BTC價格
            execution_price = order_request.price or current_price
            
            # 創建訂單回應
            order_response = OrderResponse(
                id=order_id,
                market=order_request.market,
                side=order_request.side.value,
                order_type=order_request.order_type.value,
                volume=order_request.volume,
                price=execution_price,
                state=OrderStatus.DONE.value,  # 模擬立即成交
                created_at=datetime.now(),
                trades_count=1,
                remaining_volume=0.0,
                executed_volume=order_request.volume,
                avg_price=execution_price,
                client_oid=order_request.client_oid
            )
            
            # 更新帳戶餘額（模擬）
            if order_request.side == OrderSide.BUY:
                cost = order_request.volume * execution_price
                self.account_balance['twd'] = self.account_balance.get('twd', 0) - cost
                self.account_balance['btc'] = self.account_balance.get('btc', 0) + order_request.volume
            else:  # SELL
                revenue = order_request.volume * execution_price
                self.account_balance['twd'] = self.account_balance.get('twd', 0) + revenue
                self.account_balance['btc'] = self.account_balance.get('btc', 0) - order_request.volume
            
            # 記錄訂單
            self.order_history.append(order_response)
            self.daily_trade_count += 1
            
            # 創建交易執行記錄
            trade_execution = TradeExecution(
                id=order_id + 1,
                order_id=order_id,
                market=order_request.market,
                side=order_request.side.value,
                volume=order_request.volume,
                price=execution_price,
                fee=order_request.volume * execution_price * 0.001,  # 0.1% 手續費
                fee_currency='twd',
                created_at=datetime.now()
            )
            self.trade_executions.append(trade_execution)
            
            logger.info(f"📝 模擬訂單執行成功 - ID: {order_id}, {order_request.side.value} {order_request.volume} @ {execution_price:.0f}")
            return True, order_response, "模擬訂單執行成功"
            
        except Exception as e:
            logger.error(f"❌ 模擬下單失敗: {e}")
            return False, None, str(e)
    
    async def _place_real_order(self, order_request: OrderRequest) -> Tuple[bool, Optional[OrderResponse], str]:
        """實際下單"""
        try:
            path = "/api/v2/orders"
            
            # 構建訂單參數
            params = {
                'market': order_request.market,
                'side': order_request.side.value,
                'ord_type': order_request.order_type.value,
                'volume': str(order_request.volume)
            }
            
            if order_request.price:
                params['price'] = str(order_request.price)
            
            if order_request.stop_price:
                params['stop_price'] = str(order_request.stop_price)
            
            if order_request.client_oid:
                params['client_oid'] = order_request.client_oid
            
            # 生成簽名
            headers = self._generate_signature("POST", path, params)
            if not headers:
                return False, None, "簽名生成失敗"
            
            headers['Content-Type'] = 'application/json'
            
            url = f"{self.base_url}{path}"
            
            async with self.session.post(url, headers=headers, json=params) as response:
                if response.status == 201:  # 創建成功
                    order_data = await response.json()
                    
                    # 解析訂單回應
                    order_response = OrderResponse(
                        id=order_data['id'],
                        market=order_data['market'],
                        side=order_data['side'],
                        order_type=order_data['ord_type'],
                        volume=float(order_data['volume']),
                        price=float(order_data['price']) if order_data.get('price') else None,
                        state=order_data['state'],
                        created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00')),
                        trades_count=order_data.get('trades_count', 0),
                        remaining_volume=float(order_data.get('remaining_volume', 0)),
                        executed_volume=float(order_data.get('executed_volume', 0)),
                        avg_price=float(order_data['avg_price']) if order_data.get('avg_price') else None,
                        client_oid=order_data.get('client_oid')
                    )
                    
                    # 記錄訂單
                    self.active_orders[order_response.id] = order_response
                    self.order_history.append(order_response)
                    self.daily_trade_count += 1
                    
                    logger.info(f"✅ 真實訂單提交成功 - ID: {order_response.id}")
                    return True, order_response, "訂單提交成功"
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ 下單失敗，狀態碼: {response.status}, 錯誤: {error_text}")
                    return False, None, f"下單失敗: {error_text}"
                    
        except Exception as e:
            logger.error(f"❌ 真實下單異常: {e}")
            return False, None, str(e)
    
    async def get_order_status(self, order_id: int) -> Tuple[bool, Optional[OrderResponse], str]:
        """查詢訂單狀態"""
        try:
            # 如果沒有API密鑰，從本地記錄查找
            if not self.api_key or not self.secret_key:
                for order in self.order_history:
                    if order.id == order_id:
                        return True, order, "訂單狀態查詢成功"
                return False, None, "訂單不存在"
            
            # 實際API查詢
            path = f"/api/v2/orders/{order_id}"
            headers = self._generate_signature("GET", path)
            
            if not headers:
                return False, None, "簽名生成失敗"
            
            url = f"{self.base_url}{path}"
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    order_data = await response.json()
                    
                    order_response = OrderResponse(
                        id=order_data['id'],
                        market=order_data['market'],
                        side=order_data['side'],
                        order_type=order_data['ord_type'],
                        volume=float(order_data['volume']),
                        price=float(order_data['price']) if order_data.get('price') else None,
                        state=order_data['state'],
                        created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00')),
                        trades_count=order_data.get('trades_count', 0),
                        remaining_volume=float(order_data.get('remaining_volume', 0)),
                        executed_volume=float(order_data.get('executed_volume', 0)),
                        avg_price=float(order_data['avg_price']) if order_data.get('avg_price') else None,
                        client_oid=order_data.get('client_oid')
                    )
                    
                    # 更新本地記錄
                    if order_id in self.active_orders:
                        self.active_orders[order_id] = order_response
                    
                    return True, order_response, "訂單狀態查詢成功"
                else:
                    error_text = await response.text()
                    return False, None, f"查詢失敗: {error_text}"
                    
        except Exception as e:
            logger.error(f"❌ 查詢訂單狀態異常: {e}")
            return False, None, str(e)
    
    async def cancel_order(self, order_id: int) -> Tuple[bool, str]:
        """取消訂單"""
        try:
            # 如果沒有API密鑰，模擬取消
            if not self.api_key or not self.secret_key:
                if order_id in self.active_orders:
                    order = self.active_orders[order_id]
                    order.state = OrderStatus.CANCEL.value
                    del self.active_orders[order_id]
                    logger.info(f"📝 模擬取消訂單 - ID: {order_id}")
                    return True, "模擬取消成功"
                return False, "訂單不存在"
            
            # 實際取消訂單
            path = f"/api/v2/orders/{order_id}"
            headers = self._generate_signature("DELETE", path)
            
            if not headers:
                return False, "簽名生成失敗"
            
            url = f"{self.base_url}{path}"
            
            async with self.session.delete(url, headers=headers) as response:
                if response.status == 200:
                    # 從活躍訂單中移除
                    if order_id in self.active_orders:
                        del self.active_orders[order_id]
                    
                    logger.info(f"✅ 訂單取消成功 - ID: {order_id}")
                    return True, "訂單取消成功"
                else:
                    error_text = await response.text()
                    return False, f"取消失敗: {error_text}"
                    
        except Exception as e:
            logger.error(f"❌ 取消訂單異常: {e}")
            return False, str(e)
    
    async def get_trade_history(self, market: str = "btctwd", limit: int = 50) -> List[TradeExecution]:
        """獲取交易歷史"""
        try:
            # 如果沒有API密鑰，返回本地記錄
            if not self.api_key or not self.secret_key:
                return [trade for trade in self.trade_executions if trade.market == market][-limit:]
            
            # 實際API查詢
            path = "/api/v2/trades/my"
            params = {'market': market, 'limit': limit}
            headers = self._generate_signature("GET", path, params)
            
            if not headers:
                return []
            
            url = f"{self.base_url}{path}"
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    trades_data = await response.json()
                    
                    trades = []
                    for trade_data in trades_data:
                        trade = TradeExecution(
                            id=trade_data['id'],
                            order_id=trade_data['order_id'],
                            market=trade_data['market'],
                            side=trade_data['side'],
                            volume=float(trade_data['volume']),
                            price=float(trade_data['price']),
                            fee=float(trade_data['fee']),
                            fee_currency=trade_data['fee_currency'],
                            created_at=datetime.fromisoformat(trade_data['created_at'].replace('Z', '+00:00'))
                        )
                        trades.append(trade)
                    
                    return trades
                else:
                    logger.error(f"❌ 獲取交易歷史失敗，狀態碼: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ 獲取交易歷史異常: {e}")
            return []
    
    def get_account_balance(self) -> Dict[str, float]:
        """獲取帳戶餘額"""
        return self.account_balance.copy()
    
    def get_current_price(self, market: str) -> Optional[float]:
        """獲取當前價格"""
        return self.current_prices.get(market)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """獲取連接狀態"""
        return {
            'is_connected': self.is_connected,
            'api_configured': bool(self.api_key and self.secret_key),
            'active_orders': len(self.active_orders),
            'daily_trade_count': self.daily_trade_count,
            'daily_trade_limit': self.daily_trade_limit,
            'account_balance': self.account_balance,
            'tracked_markets': len(self.current_prices)
        }


# 創建全局連接器實例
def create_live_connector(api_key: str = "", secret_key: str = "") -> LiveMAXAPIConnector:
    """創建MAX API連接器實例"""
    return LiveMAXAPIConnector(api_key, secret_key)


# 測試代碼
if __name__ == "__main__":
    async def test_live_connector():
        """測試MAX API連接器"""
        print("🧪 測試MAX API連接器...")
        
        # 創建連接器（使用空密鑰進行模擬測試）
        connector = create_live_connector()
        
        try:
            # 建立連接
            print("\n🔗 建立API連接...")
            connected = await connector.connect()
            
            if connected:
                print("✅ API連接成功")
                
                # 顯示連接狀態
                status = connector.get_connection_status()
                print(f"\n📊 連接狀態:")
                print(f"   連接狀態: {'✅ 已連接' if status['is_connected'] else '❌ 未連接'}")
                print(f"   API配置: {'✅ 已配置' if status['api_configured'] else '⚠️ 模擬模式'}")
                print(f"   帳戶餘額: {status['account_balance']}")
                
                # 測試下單
                print(f"\n💰 測試下單...")
                order_request = OrderRequest(
                    market="btctwd",
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    volume=0.0001,  # 0.0001 BTC
                    client_oid="test_order_001"
                )
                
                success, order_response, message = await connector.place_order(order_request)
                
                if success and order_response:
                    print(f"✅ 下單成功 - ID: {order_response.id}")
                    print(f"   市場: {order_response.market}")
                    print(f"   方向: {order_response.side}")
                    print(f"   數量: {order_response.volume}")
                    print(f"   價格: {order_response.avg_price}")
                    print(f"   狀態: {order_response.state}")
                    
                    # 查詢訂單狀態
                    print(f"\n🔍 查詢訂單狀態...")
                    success, updated_order, message = await connector.get_order_status(order_response.id)
                    
                    if success and updated_order:
                        print(f"✅ 訂單狀態: {updated_order.state}")
                        print(f"   已執行數量: {updated_order.executed_volume}")
                        print(f"   剩餘數量: {updated_order.remaining_volume}")
                    
                else:
                    print(f"❌ 下單失敗: {message}")
                
                # 獲取交易歷史
                print(f"\n📋 獲取交易歷史...")
                trades = await connector.get_trade_history("btctwd", 5)
                print(f"✅ 獲取到 {len(trades)} 筆交易記錄")
                
                for trade in trades[-3:]:  # 顯示最近3筆
                    print(f"   交易ID: {trade.id}, {trade.side} {trade.volume} @ {trade.price:.0f}")
                
                # 顯示最終帳戶狀態
                final_balance = connector.get_account_balance()
                print(f"\n💰 最終帳戶餘額: {final_balance}")
                
            else:
                print("❌ API連接失敗")
                
        finally:
            await connector.disconnect()
            print("\n🔌 連接已斷開")
    
    # 運行測試
    asyncio.run(test_live_connector())