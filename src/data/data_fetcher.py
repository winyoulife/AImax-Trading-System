#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據獲取器 - 為Telegram機器人提供數據支持
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DataFetcher:
    """數據獲取器"""
    
    def __init__(self, base_url: str = "https://max-api.maicoin.com/api/v2"):
        self.base_url = base_url
    
    def fetch_data(self, symbol: str = 'BTCTWD', timeframe: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        獲取K線數據
        
        Args:
            symbol: 交易對 (BTCTWD, BTCUSDT等)
            timeframe: 時間框架 (1h, 5m等)
            limit: 數據條數
            
        Returns:
            包含OHLCV數據的DataFrame
        """
        try:
            # 轉換symbol格式
            if symbol.upper() == 'BTCUSDT':
                market = 'btctwd'  # MAX交易所使用btctwd
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
            
            # 構建API URL
            url = f"{self.base_url}/k"
            params = {
                'market': market,
                'period': period,
                'limit': limit
            }
            
            # 發送請求
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.error("API返回空數據")
                return None
            
            # 轉換為DataFrame
            df = pd.DataFrame(data)
            
            # 重命名列
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            # 轉換數據類型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 按時間排序
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"成功獲取 {len(df)} 條 {market} {timeframe} 數據")
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"網絡請求錯誤: {e}")
            return None
        except Exception as e:
            logger.error(f"獲取數據時發生錯誤: {e}")
            return None
    
    def get_latest_price(self, symbol: str = 'BTCTWD') -> Optional[float]:
        """
        獲取最新價格
        
        Args:
            symbol: 交易對
            
        Returns:
            最新價格
        """
        try:
            df = self.fetch_data(symbol, '1h', 1)
            if df is not None and not df.empty:
                return float(df['close'].iloc[-1])
            return None
        except Exception as e:
            logger.error(f"獲取最新價格時發生錯誤: {e}")
            return None