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
        # 使用更合理的BTC價格範圍
        if 'BTC' in symbol:
            base_price = 95000  # 基準價格 95,000 TWD
            variation = np.random.uniform(-0.01, 0.01)  # ±1% 波動
            price = base_price * (1 + variation)
            # 確保價格在合理範圍內 (90,000 - 100,000)
            price = max(90000, min(100000, price))
        else:
            price = 1000
        
        return price
    
    def get_historical_data(self, symbol: str = 'BTCUSDT', interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """獲取歷史數據（模擬）- 包含更多波動和趨勢"""
        print(f"生成 {symbol} 模擬數據...")
        
        # 生成時間序列
        end_time = datetime.now()
        timestamps = pd.date_range(end=end_time, periods=limit, freq='H')
        
        # 生成價格數據 - 更真實的波動
        base_price = 95000 if 'BTC' in symbol else 1000
        np.random.seed(42)  # 固定種子確保一致性
        
        prices = [base_price]
        volumes = []
        
        # 創建多個趨勢階段
        trend_changes = [0, limit//4, limit//2, 3*limit//4, limit]
        trend_directions = [1, -1, 1, -1]  # 上漲、下跌、上漲、下跌
        
        for i in range(1, limit):
            # 確定當前趨勢
            current_trend = 0
            for j, change_point in enumerate(trend_changes[1:]):
                if i <= change_point:
                    current_trend = trend_directions[j]
                    break
            
            # 基於趨勢的價格變化
            trend_factor = current_trend * 0.002  # 趨勢影響
            random_factor = np.random.normal(0, 0.015)  # 隨機波動
            
            change = trend_factor + random_factor
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, base_price * 0.7))  # 防止價格過低
            
            # 成交量與價格變化相關
            price_change = abs(change)
            base_volume = np.random.uniform(500, 1500)
            volume_multiplier = 1 + price_change * 10  # 價格變化大時成交量增加
            volumes.append(base_volume * volume_multiplier)
        
        # 創建DataFrame
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, prices)):
            open_price = prices[i-1] if i > 0 else close
            
            # 更真實的高低價
            price_range = abs(open_price - close)
            high = max(open_price, close) + price_range * np.random.uniform(0, 0.5)
            low = min(open_price, close) - price_range * np.random.uniform(0, 0.5)
            
            volume = volumes[i] if i < len(volumes) else np.random.uniform(500, 1500)
            
            data.append({
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data, index=timestamps)
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'timestamp'}, inplace=True)
        print(f"生成 {len(df)} 條記錄，價格範圍: {df['close'].min():,.0f} - {df['close'].max():,.0f}")
        return df