#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對MAX API客戶端 - 支持同時監控多個加密貨幣交易對
基於本地AI + MAX歷史數據 + 超進化Python的核心理念
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TradingPairConfig:
    """交易對配置"""
    pair: str
    min_order_size: float
    max_position_size: float
    risk_weight: float
    enabled: bool = True
    api_rate_limit: float = 0.1  # 秒
    max_retries: int = 3
    timeout: int = 10
    
    # MAX API特定配置
    precision: int = 0
    tick_size: float = 1.0
    min_notional: float = 100.0

@dataclass
class PairStatus:
    """交易對狀態"""
    pair: str
    last_update: datetime
    status: str  # 'active', 'error', 'paused'
    error_count: int = 0
    last_error: Optional[str] = None
    data_quality: float = 1.0  # 0-1
    api_latency: float = 0.0

class MultiPairMAXClient:
    """多交易對MAX API客戶端"""
    
    def __init__(self, base_url: str = "https://max-api.maicoin.com/api/v2"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 支持的交易對配置
        self.pair_configs: Dict[str, TradingPairConfig] = {}
        self.pair_status: Dict[str, PairStatus] = {}
        
        # 全局設置
        self.global_rate_limit = 0.05  # 全局API調用間隔
        self.max_concurrent_requests = 10
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # 數據緩存
        self.data_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 30  # 緩存30秒
        
        # 錯誤恢復設置
        self.error_threshold = 5
        self.recovery_delay = 60  # 60秒後重試
        
        logger.info("🚀 多交易對MAX客戶端初始化完成")
    
    def initialize_default_pairs(self):
        """初始化默認支持的交易對"""
        default_pairs = {
            'BTCTWD': TradingPairConfig(
                pair='BTCTWD',
                min_order_size=0.0001,
                max_position_size=0.01,
                risk_weight=0.4,
                precision=0,
                tick_size=1.0,
                min_notional=100.0
            ),
            'ETHTWD': TradingPairConfig(
                pair='ETHTWD', 
                min_order_size=0.001,
                max_position_size=0.1,
                risk_weight=0.3,
                precision=0,
                tick_size=1.0,
                min_notional=50.0
            ),
            'LTCTWD': TradingPairConfig(
                pair='LTCTWD',
                min_order_size=0.01,
                max_position_size=1.0,
                risk_weight=0.2,
                precision=0,
                tick_size=1.0,
                min_notional=20.0
            ),
            'BCHTWD': TradingPairConfig(
                pair='BCHTWD',
                min_order_size=0.001,
                max_position_size=0.1,
                risk_weight=0.1,
                precision=0,
                tick_size=1.0,
                min_notional=20.0
            )
        }
        
        for pair, config in default_pairs.items():
            self.add_trading_pair(config)
        
        logger.info(f"✅ 初始化 {len(default_pairs)} 個默認交易對")
    
    def add_trading_pair(self, config: TradingPairConfig):
        """添加交易對"""
        self.pair_configs[config.pair] = config
        self.pair_status[config.pair] = PairStatus(
            pair=config.pair,
            last_update=datetime.now(),
            status='active'
        )
        logger.info(f"➕ 添加交易對: {config.pair}")
    
    def remove_trading_pair(self, pair: str):
        """移除交易對"""
        if pair in self.pair_configs:
            del self.pair_configs[pair]
            del self.pair_status[pair]
            if pair in self.data_cache:
                del self.data_cache[pair]
            logger.info(f"➖ 移除交易對: {pair}")
    
    def get_active_pairs(self) -> List[str]:
        """獲取活躍的交易對列表"""
        return [
            pair for pair, config in self.pair_configs.items()
            if config.enabled and self.pair_status[pair].status == 'active'
        ]
    
    async def get_multi_pair_market_data(self, pairs: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        並行獲取多個交易對的市場數據
        
        Args:
            pairs: 指定交易對列表，None則獲取所有活躍交易對
            
        Returns:
            {pair: market_data} 格式的字典
        """
        if pairs is None:
            pairs = self.get_active_pairs()
        
        if not pairs:
            logger.warning("⚠️ 沒有活躍的交易對")
            return {}
        
        logger.info(f"📊 開始獲取 {len(pairs)} 個交易對的市場數據")
        
        # 檢查緩存
        cached_results = {}
        pairs_to_fetch = []
        
        for pair in pairs:
            if self._is_cache_valid(pair):
                cached_results[pair] = self.data_cache[pair]
                logger.debug(f"💾 使用緩存數據: {pair}")
            else:
                pairs_to_fetch.append(pair)
        
        # 並行獲取需要更新的數據
        if pairs_to_fetch:
            fresh_results = await self._fetch_pairs_data_parallel(pairs_to_fetch)
            cached_results.update(fresh_results)
        
        # 更新交易對狀態
        self._update_pair_status(cached_results)
        
        logger.info(f"✅ 成功獲取 {len(cached_results)} 個交易對數據")
        return cached_results
    
    async def _fetch_pairs_data_parallel(self, pairs: List[str]) -> Dict[str, Dict[str, Any]]:
        """並行獲取多個交易對數據"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # 創建並發任務
        tasks = []
        for pair in pairs:
            task = self._fetch_single_pair_data(pair)
            tasks.append(task)
        
        # 執行並發請求
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        pair_data = {}
        for i, result in enumerate(results):
            pair = pairs[i]
            if isinstance(result, Exception):
                logger.error(f"❌ 獲取 {pair} 數據失敗: {result}")
                self._handle_pair_error(pair, str(result))
            elif result:
                pair_data[pair] = result
                self._update_cache(pair, result)
                logger.debug(f"✅ 成功獲取 {pair} 數據")
            else:
                logger.warning(f"⚠️ {pair} 返回空數據")
        
        return pair_data
    
    async def _fetch_single_pair_data(self, pair: str) -> Optional[Dict[str, Any]]:
        """獲取單個交易對的完整數據"""
        async with self.semaphore:  # 限制並發數
            try:
                config = self.pair_configs[pair]
                
                # 應用速率限制
                await asyncio.sleep(config.api_rate_limit)
                
                start_time = time.time()
                
                # 並行獲取多種數據
                tasks = [
                    self._get_ticker(pair),
                    self._get_klines(pair, period=1, limit=100),   # 1分鐘
                    self._get_klines(pair, period=5, limit=50),    # 5分鐘
                    self._get_klines(pair, period=60, limit=24),   # 1小時
                ]
                
                ticker, klines_1m, klines_5m, klines_1h = await asyncio.gather(
                    *tasks, return_exceptions=True
                )
                
                # 檢查結果
                if isinstance(ticker, Exception) or not ticker:
                    raise Exception(f"Ticker獲取失敗: {ticker}")
                
                # 計算API延遲
                api_latency = time.time() - start_time
                
                # 構建增強數據
                enhanced_data = self._build_enhanced_data(
                    pair, ticker, klines_1m, klines_5m, klines_1h
                )
                
                # 添加元數據
                enhanced_data.update({
                    'pair': pair,
                    'fetch_time': datetime.now(),
                    'api_latency': api_latency,
                    'data_source': 'MAX_API'
                })
                
                return enhanced_data
                
            except Exception as e:
                logger.error(f"❌ 獲取 {pair} 數據失敗: {e}")
                self._handle_pair_error(pair, str(e))
                return None
    
    async def _get_ticker(self, pair: str) -> Optional[Dict]:
        """獲取ticker數據"""
        try:
            url = f"{self.base_url}/tickers/{pair.lower()}"
            config = self.pair_configs[pair]
            
            async with self.session.get(url, timeout=config.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': pair,
                        'timestamp': datetime.now(),
                        'last_price': float(data['last']),
                        'volume': float(data['vol']),
                        'high': float(data['high']),
                        'low': float(data['low']),
                        'open': float(data['open']),
                        'bid': float(data.get('buy', data['last'])),
                        'ask': float(data.get('sell', data['last']))
                    }
                else:
                    raise Exception(f"HTTP {response.status}")
                    
        except Exception as e:
            raise Exception(f"Ticker API錯誤: {e}")
    
    async def _get_klines(self, pair: str, period: int, limit: int) -> Optional[pd.DataFrame]:
        """獲取K線數據"""
        try:
            url = f"{self.base_url}/k"
            params = {
                'market': pair.lower(),
                'period': period,
                'limit': limit
            }
            config = self.pair_configs[pair]
            
            async with self.session.get(url, params=params, timeout=config.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and isinstance(data, list):
                        df = pd.DataFrame(data, columns=[
                            'timestamp', 'open', 'high', 'low', 'close', 'volume'
                        ])
                        
                        # 數據類型轉換
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        df = df.sort_values('timestamp').reset_index(drop=True)
                        return df
                    else:
                        return None
                else:
                    raise Exception(f"HTTP {response.status}")
                    
        except Exception as e:
            logger.debug(f"K線獲取失敗 {pair} {period}m: {e}")
            return None
    
    def _build_enhanced_data(self, pair: str, ticker: Dict, 
                           klines_1m: pd.DataFrame, klines_5m: pd.DataFrame, 
                           klines_1h: pd.DataFrame) -> Dict[str, Any]:
        """構建增強的市場數據"""
        try:
            current_price = ticker['last_price']
            
            # 基礎數據
            enhanced_data = {
                'current_price': current_price,
                'timestamp': ticker['timestamp'],
                'volume_24h': ticker['volume'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'open_24h': ticker['open'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread': ticker['ask'] - ticker['bid'],
                'spread_pct': ((ticker['ask'] - ticker['bid']) / current_price * 100) if current_price > 0 else 0
            }
            
            # 價格變化（基於1分鐘數據）
            if klines_1m is not None and len(klines_1m) >= 5:
                prices_1m = klines_1m['close'].values
                enhanced_data.update({
                    'price_change_1m': ((current_price - prices_1m[-2]) / prices_1m[-2] * 100) if len(prices_1m) > 1 else 0,
                    'price_change_5m': ((current_price - prices_1m[-6]) / prices_1m[-6] * 100) if len(prices_1m) > 5 else 0,
                    'price_change_15m': ((current_price - prices_1m[-16]) / prices_1m[-16] * 100) if len(prices_1m) > 15 else 0,
                })
            
            # 技術指標（基於5分鐘數據）
            if klines_5m is not None and len(klines_5m) >= 20:
                tech_indicators = self._calculate_technical_indicators(klines_5m)
                enhanced_data.update(tech_indicators)
            
            # 趨勢指標（基於1小時數據）
            if klines_1h is not None and len(klines_1h) >= 10:
                trend_indicators = self._calculate_trend_indicators(klines_1h)
                enhanced_data.update(trend_indicators)
            
            # 市場微觀結構
            if klines_1m is not None and len(klines_1m) >= 10:
                micro_data = self._calculate_market_microstructure(klines_1m)
                enhanced_data.update(micro_data)
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ 構建 {pair} 增強數據失敗: {e}")
            return {
                'current_price': ticker['last_price'],
                'timestamp': ticker['timestamp'],
                'error': str(e)
            }
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算技術指標"""
        try:
            indicators = {}
            
            # RSI
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
            
            # 移動平均線
            if len(df) >= 20:
                indicators['sma_10'] = float(df['close'].rolling(10).mean().iloc[-1])
                indicators['sma_20'] = float(df['close'].rolling(20).mean().iloc[-1])
                indicators['ema_10'] = float(df['close'].ewm(span=10).mean().iloc[-1])
                indicators['ema_20'] = float(df['close'].ewm(span=20).mean().iloc[-1])
            
            # MACD
            if len(df) >= 26:
                ema_12 = df['close'].ewm(span=12).mean()
                ema_26 = df['close'].ewm(span=26).mean()
                macd_line = ema_12 - ema_26
                signal_line = macd_line.ewm(span=9).mean()
                histogram = macd_line - signal_line
                
                indicators['macd'] = float(macd_line.iloc[-1])
                indicators['macd_signal'] = float(signal_line.iloc[-1])
                indicators['macd_histogram'] = float(histogram.iloc[-1])
            
            # 布林帶
            if len(df) >= 20:
                sma_20 = df['close'].rolling(20).mean()
                std_20 = df['close'].rolling(20).std()
                upper_band = sma_20 + (std_20 * 2)
                lower_band = sma_20 - (std_20 * 2)
                
                current_price = df['close'].iloc[-1]
                indicators['bollinger_upper'] = float(upper_band.iloc[-1])
                indicators['bollinger_lower'] = float(lower_band.iloc[-1])
                indicators['bollinger_middle'] = float(sma_20.iloc[-1])
                
                # 布林帶位置
                bb_position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
                indicators['bollinger_position'] = float(bb_position)
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ 計算技術指標失敗: {e}")
            return {}
    
    def _calculate_trend_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算趨勢指標"""
        try:
            trend_data = {}
            
            if len(df) >= 10:
                # 價格趨勢
                prices = df['close'].values
                recent_trend = np.polyfit(range(len(prices[-10:])), prices[-10:], 1)[0]
                trend_data['price_trend_slope'] = float(recent_trend)
                trend_data['price_trend'] = "上升" if recent_trend > 0 else "下降"
                
                # 成交量趨勢
                volumes = df['volume'].values
                volume_trend = np.polyfit(range(len(volumes[-10:])), volumes[-10:], 1)[0]
                trend_data['volume_trend_slope'] = float(volume_trend)
                trend_data['volume_trend'] = "增加" if volume_trend > 0 else "減少"
                
                # 波動率
                returns = df['close'].pct_change().dropna()
                if len(returns) > 0:
                    volatility = returns.std() * np.sqrt(24)  # 日化波動率
                    trend_data['volatility'] = float(volatility)
                    trend_data['volatility_level'] = "高" if volatility > 0.05 else "中" if volatility > 0.02 else "低"
            
            return trend_data
            
        except Exception as e:
            logger.error(f"❌ 計算趨勢指標失敗: {e}")
            return {}
    
    def _calculate_market_microstructure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算市場微觀結構數據"""
        try:
            micro_data = {}
            
            if len(df) >= 10:
                # 成交量分析
                volumes = df['volume'].values
                avg_volume = np.mean(volumes[-10:])
                current_volume = volumes[-1]
                
                micro_data['volume_ratio'] = float(current_volume / avg_volume) if avg_volume > 0 else 1.0
                micro_data['volume_spike'] = current_volume > avg_volume * 1.5
                
                # 價格跳躍分析
                price_changes = df['close'].pct_change().abs()
                avg_change = price_changes.mean()
                recent_change = price_changes.iloc[-1]
                
                micro_data['price_jump_ratio'] = float(recent_change / avg_change) if avg_change > 0 else 1.0
                micro_data['price_jump'] = recent_change > avg_change * 2
            
            return micro_data
            
        except Exception as e:
            logger.error(f"❌ 計算市場微觀結構失敗: {e}")
            return {}
    
    def _is_cache_valid(self, pair: str) -> bool:
        """檢查緩存是否有效"""
        if pair not in self.data_cache:
            return False
        
        cache_data = self.data_cache[pair]
        if 'fetch_time' not in cache_data:
            return False
        
        cache_age = (datetime.now() - cache_data['fetch_time']).total_seconds()
        return cache_age < self.cache_ttl
    
    def _update_cache(self, pair: str, data: Dict[str, Any]):
        """更新數據緩存"""
        self.data_cache[pair] = data
    
    def _handle_pair_error(self, pair: str, error: str):
        """處理交易對錯誤"""
        if pair in self.pair_status:
            status = self.pair_status[pair]
            status.error_count += 1
            status.last_error = error
            status.last_update = datetime.now()
            
            # 如果錯誤次數過多，暫停該交易對
            if status.error_count >= self.error_threshold:
                status.status = 'error'
                logger.warning(f"⚠️ 交易對 {pair} 錯誤次數過多，暫停監控")
    
    def _update_pair_status(self, results: Dict[str, Dict[str, Any]]):
        """更新交易對狀態"""
        for pair in self.pair_configs:
            if pair in results:
                # 成功獲取數據
                status = self.pair_status[pair]
                status.status = 'active'
                status.last_update = datetime.now()
                status.error_count = max(0, status.error_count - 1)  # 逐漸恢復
                
                # 更新API延遲
                if 'api_latency' in results[pair]:
                    status.api_latency = results[pair]['api_latency']
    
    def get_pair_status_summary(self) -> Dict[str, Any]:
        """獲取交易對狀態摘要"""
        active_pairs = []
        error_pairs = []
        paused_pairs = []
        
        for pair, status in self.pair_status.items():
            if status.status == 'active':
                active_pairs.append(pair)
            elif status.status == 'error':
                error_pairs.append(pair)
            elif status.status == 'paused':
                paused_pairs.append(pair)
        
        return {
            'total_pairs': len(self.pair_configs),
            'active_pairs': active_pairs,
            'error_pairs': error_pairs,
            'paused_pairs': paused_pairs,
            'active_count': len(active_pairs),
            'error_count': len(error_pairs),
            'paused_count': len(paused_pairs)
        }
    
    async def close(self):
        """關閉連接"""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("🔒 多交易對MAX客戶端已關閉")


# 創建全局多交易對客戶端實例
def create_multi_pair_client() -> MultiPairMAXClient:
    """創建多交易對MAX客戶端實例"""
    client = MultiPairMAXClient()
    client.initialize_default_pairs()
    return client


# 測試代碼
if __name__ == "__main__":
    async def test_multi_pair_client():
        """測試多交易對客戶端"""
        print("🧪 測試多交易對MAX客戶端...")
        
        client = create_multi_pair_client()
        
        try:
            # 獲取狀態摘要
            status = client.get_pair_status_summary()
            print(f"📊 交易對狀態: {status}")
            
            # 獲取多交易對數據
            print("📊 開始獲取多交易對數據...")
            start_time = time.time()
            
            market_data = await client.get_multi_pair_market_data()
            
            elapsed_time = time.time() - start_time
            print(f"⏱️ 獲取耗時: {elapsed_time:.2f}秒")
            
            if market_data:
                print(f"✅ 成功獲取 {len(market_data)} 個交易對數據")
                
                for pair, data in market_data.items():
                    price = data.get('current_price', 0)
                    change_1m = data.get('price_change_1m', 0)
                    rsi = data.get('rsi', 50)
                    print(f"  {pair}: {price:,.0f} TWD ({change_1m:+.2f}%) RSI:{rsi:.1f}")
            else:
                print("❌ 獲取多交易對數據失敗")
                
        finally:
            await client.close()
    
    # 運行測試
    asyncio.run(test_multi_pair_client())