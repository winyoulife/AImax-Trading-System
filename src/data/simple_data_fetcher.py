#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化數據獲取器
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    """簡化數據獲取器"""
    
    def __init__(self):
        pass
        
    def get_current_price(self, symbol: str = 'BTCUSDT') -> float:
        """獲取當前價格（模擬）"""
        base_price = 95000 if 'BTC' in symbol else 1000
        variation = np.random.uniform(-0.02, 0.02)
        price = base_price * (1 + variation)
        print(f"{symbol} 當前價格: ${price:,.2f}")
        return price
    
    def get_historical_data(self, symbol: str = 'BTCUSDT', interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """獲取歷史數據（模擬）"""
        print(f"生成 {symbol} 模擬數據...")
        
        # 生成時間序列
        end_time = datetime.now()
        timestamps = pd.date_range(end=end_time, periods=limit, freq='H')
        
        # 生成價格數據
        base_price = 95000 if 'BTC' in symbol else 1000
        np.random.seed(42)  # 固定種子確保一致性
        
        prices = [base_price]
        for i in range(1, limit):
            change = np.random.normal(0, 0.01)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, base_price * 0.9))
        
        # 創建DataFrame
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, prices)):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data, index=timestamps)
        print(f"生成 {len(df)} 條記錄")
        return df