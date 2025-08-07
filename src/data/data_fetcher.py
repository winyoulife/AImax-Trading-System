#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAX API 數據獲取器
提供統一的數據獲取接口，支持歷史數據和實時數據
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from typing import Optional, List, Dict, Any
import json
from pathlib import Path

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetcher:
    """MAX API 數據獲取器"""
    
    def __init__(self):
        self.base_url = "https://max-api.maicoin.com/api/v2"
        self.session = None
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """實施速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """發送API請求"""
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API請求失敗: {response.status} - {url}")
                    return None
        except Exception as e:
            logger.error(f"請求異常: {e}")
            return None
    
    async def get_klines(self, market: str, period: str, limit: int = 1000) -> Optional[pd.DataFrame]:
        """獲取K線數據
        
        Args:
            market: 交易對，如 'btctwd'
            period: 時間週期，如 '1', '5', '15', '30', '60', '240', '1440'
            limit: 數據筆數限制
            
        Returns:
            包含OHLCV數據的DataFrame
        """
        params = {
            'market': market,
            'period': period,
            'limit': limit
        }
        
        data = await self._make_request('k', params)
        
        if not data:
            return None
            
        try:
            # 轉換數據格式
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
            
            # 轉換數據類型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # 保留timestamp列並設置索引
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            # 重新添加timestamp列以兼容舊版本
            df.reset_index(inplace=True)
            
            logger.info(f"成功獲取 {len(df)} 筆 {market} {period}分鐘 K線數據")
            return df
            
        except Exception as e:
            logger.error(f"數據處理錯誤: {e}")
            return None
    
    async def get_ticker(self, market: str) -> Optional[Dict]:
        """獲取市場行情
        
        Args:
            market: 交易對，如 'btctwd'
            
        Returns:
            包含價格信息的字典
        """
        data = await self._make_request(f'tickers/{market}')
        
        if data:
            try:
                return {
                    'symbol': market,
                    'last': float(data['last']),
                    'high': float(data['high']),
                    'low': float(data['low']),
                    'volume': float(data['volume']),
                    'change': float(data['change']),
                    'change_percent': float(data['change_percent']),
                    'timestamp': datetime.now()
                }
            except Exception as e:
                logger.error(f"行情數據處理錯誤: {e}")
                return None
        
        return None
    
    def save_data(self, df: pd.DataFrame, filename: str, data_dir: str = "data"):
        """保存數據到文件
        
        Args:
            df: 要保存的DataFrame
            filename: 文件名
            data_dir: 數據目錄
        """
        try:
            # 確保數據目錄存在
            Path(data_dir).mkdir(exist_ok=True)
            
            filepath = Path(data_dir) / filename
            
            # 根據文件擴展名選擇保存格式
            if filename.endswith('.csv'):
                df.to_csv(filepath)
            elif filename.endswith('.json'):
                df.to_json(filepath, orient='records', date_format='iso')
            elif filename.endswith('.parquet'):
                df.to_parquet(filepath)
            else:
                # 默認保存為CSV
                df.to_csv(filepath)
            
            logger.info(f"數據已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存數據失敗: {e}")
    
    def load_data(self, filename: str, data_dir: str = "data") -> Optional[pd.DataFrame]:
        """從文件加載數據
        
        Args:
            filename: 文件名
            data_dir: 數據目錄
            
        Returns:
            加載的DataFrame
        """
        try:
            filepath = Path(data_dir) / filename
            
            if not filepath.exists():
                logger.warning(f"文件不存在: {filepath}")
                return None
            
            # 根據文件擴展名選擇加載格式
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            elif filename.endswith('.json'):
                df = pd.read_json(filepath)
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
            elif filename.endswith('.parquet'):
                df = pd.read_parquet(filepath)
            else:
                # 默認嘗試CSV格式
                df = pd.read_csv(filepath, index_col=0, parse_dates=True)
            
            logger.info(f"數據已加載: {filepath} ({len(df)} 筆記錄)")
            return df
            
        except Exception as e:
            logger.error(f"加載數據失敗: {e}")
            return None
    
    def fetch_data(self, symbol: str = 'BTCTWD', timeframe: str = '1h', limit: int = 1000) -> Optional[pd.DataFrame]:
        """同步獲取數據方法 - 兼容舊版本接口
        
        Args:
            symbol: 交易對 (BTCTWD, BTCUSDT等)
            timeframe: 時間框架 (1h, 5m等)
            limit: 數據條數
            
        Returns:
            包含OHLCV數據的DataFrame
        """
        # 轉換symbol格式
        if symbol.upper() == 'BTCTWD':
            market = 'btctwd'
        else:
            market = symbol.lower()
        
        # 轉換timeframe格式
        period_map = {
            '1m': '1',
            '5m': '5', 
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '4h': '240',
            '1d': '1440'
        }
        period = period_map.get(timeframe, '60')
        
        # 使用異步方法獲取數據
        return asyncio.run(self._fetch_data_async(market, period, limit))
    
    async def _fetch_data_async(self, market: str, period: str, limit: int) -> Optional[pd.DataFrame]:
        """內部異步獲取數據方法"""
        async with DataFetcher() as fetcher:
            return await fetcher.get_klines(market, period, limit)

# 便捷函數
async def fetch_btc_data(period: str = '60', limit: int = 1000) -> Optional[pd.DataFrame]:
    """快速獲取BTC數據
    
    Args:
        period: 時間週期
        limit: 數據筆數
        
    Returns:
        BTC K線數據
    """
    async with DataFetcher() as fetcher:
        return await fetcher.get_klines('btctwd', period, limit)

async def fetch_current_price(market: str = 'btctwd') -> Optional[float]:
    """獲取當前價格
    
    Args:
        market: 交易對
        
    Returns:
        當前價格
    """
    async with DataFetcher() as fetcher:
        ticker = await fetcher.get_ticker(market)
        return ticker['last'] if ticker else None

    def fetch_data(self, symbol: str = 'BTCTWD', timeframe: str = '1h', limit: int = 1000) -> Optional[pd.DataFrame]:
        """同步獲取數據方法 - 兼容舊版本接口
        
        Args:
            symbol: 交易對 (BTCTWD, BTCUSDT等)
            timeframe: 時間框架 (1h, 5m等)
            limit: 數據條數
            
        Returns:
            包含OHLCV數據的DataFrame
        """
        # 轉換symbol格式
        if symbol.upper() == 'BTCTWD':
            market = 'btctwd'
        else:
            market = symbol.lower()
        
        # 轉換timeframe格式
        period_map = {
            '1m': '1',
            '5m': '5', 
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '4h': '240',
            '1d': '1440'
        }
        period = period_map.get(timeframe, '60')
        
        # 使用異步方法獲取數據
        return asyncio.run(self._fetch_data_async(market, period, limit))
    
    async def _fetch_data_async(self, market: str, period: str, limit: int) -> Optional[pd.DataFrame]:
        """內部異步獲取數據方法"""
        async with DataFetcher() as fetcher:
            return await fetcher.get_klines(market, period, limit)

# 同步版本的便捷函數
def get_btc_data_sync(period: str = '60', limit: int = 1000) -> Optional[pd.DataFrame]:
    """同步獲取BTC數據"""
    return asyncio.run(fetch_btc_data(period, limit))

def get_current_price_sync(market: str = 'btctwd') -> Optional[float]:
    """同步獲取當前價格"""
    return asyncio.run(fetch_current_price(market))

if __name__ == "__main__":
    # 測試代碼
    async def test_fetcher():
        async with DataFetcher() as fetcher:
            # 測試獲取K線數據
            df = await fetcher.get_klines('btctwd', '60', 100)
            if df is not None:
                print(f"獲取到 {len(df)} 筆數據")
                print(df.head())
                
                # 保存數據
                fetcher.save_data(df, 'btc_test.csv')
            
            # 測試獲取行情
            ticker = await fetcher.get_ticker('btctwd')
            if ticker:
                print(f"當前BTC價格: {ticker['last']}")
    
    # 運行測試
    asyncio.run(test_fetcher())