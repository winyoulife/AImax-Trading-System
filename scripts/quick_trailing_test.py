#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試移動停損策略
"""

import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.data.data_fetcher import DataFetcher
from src.core.improved_max_macd_calculator import ImprovedMaxMACDCalculator
from src.core.improved_trading_signals import SignalDetectionEngine
from src.core.trailing_stop_trading_signals import TrailingStopTradingSignals

def quick_test():
    """快速測試最佳參數"""
    print("⚡ 快速移動停損測試")
    
    # 獲取數據
    data_fetcher = DataFetcher()
    df = data_fetcher.fetch_data('BTCUSDT', '1h', 1000)  # 減少數據量
    
    # 計算MACD
    macd_calculator = ImprovedMaxMACDCalculator()
    prices = df['close'].tolist()
    timestamps = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    
    macd_line, signal_line, hist = macd_calculator.calculate_macd(prices, timestamps)
    
    macd_df = df.copy()
    macd_df['datetime'] = df['timestamp']
    
    macd_len = len(macd_line)
    total_len = len(df)
    
    macd_df['macd'] = [np.nan] * (total_len - macd_len) + macd_line
    macd_df['macd_signal'] = [np.nan] * (total_len - macd_len) + signal_line
    macd_df['macd_hist'] = [np.nan] * (total_len - macd_len) + hist
    
    macd_df = macd_df.dropna().reset_index(drop=True)
    
    # 原始策略
    original_engine = SignalDetectionEngine()
    original_results = original_engine.detect_signals(macd_df)
    
    original_trades = []
    position = None
    
    for idx, row in original_results.iterrows():
        if row['signal_type'] == 'buy' and position is None:
            position = {'buy_price': row['close']}
        elif row['signal_type'] == 'sell' and position is not None:
            profit = row['close'] - position['buy_price']
            original_trades.append({'profit': profit})
            position = None
    
    original_total = sum(t['profit'] for t in original_trades)
    
    print(f"🔵 原始MACD: ${original_total:,.0f} ({len(original_trades)}對)")
    
    # 測試激進移動停損
    trailing_engine = TrailingStopTradingSignals(
        stop_loss_pct=0.02,      # 2% 停損
        profit_trigger_pct=0.01, # 1% 啟動移動停損
        trailing_pct=0.008       # 0.8% 移動幅度
    )
    
    trailing_results = trailing_engine.detect_signals(macd_df)
    stats = trailing_engine.get_statistics()
    
    print(f"🟢 移動停損: ${stats['total_profit']:,.0f} ({stats['complete_pairs']}對)")
    print(f"   🛑 停損: {stats['stop_loss_count']}次")
    print(f"   🔴 MACD: {stats['macd_sell_count']}次")
    
    if stats['total_profit'] > original_total:
        improvement = ((stats['total_profit'] - original_total) / abs(original_total)) * 100
        print(f"✅ 改進: +{improvement:.1f}%")
    else:
        decline = ((original_total - stats['total_profit']) / abs(original_total)) * 100
        print(f"❌ 下降: -{decline:.1f}%")

if __name__ == "__main__":
    quick_test()