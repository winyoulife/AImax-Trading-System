#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查最新的交易統計
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.data.data_fetcher import DataFetcher
from src.core.improved_max_macd_calculator import ImprovedMaxMACDCalculator
from src.core.improved_trading_signals import SignalDetectionEngine

def check_latest_trades():
    """檢查最新的交易統計"""
    print("📊 檢查最新交易統計...")
    print("=" * 50)
    
    try:
        # 初始化組件
        data_fetcher = DataFetcher()
        macd_calculator = ImprovedMaxMACDCalculator()
        signal_engine = SignalDetectionEngine()
        
        # 獲取更多歷史數據來確保有足夠的交易信號
        print("📡 獲取歷史數據...")
        df = data_fetcher.fetch_data('BTCUSDT', '1h', 2000)  # 獲取更多數據
        
        if df is None or df.empty:
            print("❌ 無法獲取數據")
            return
        
        print(f"✅ 獲取了 {len(df)} 條數據")
        print(f"📅 數據範圍: {df.index[0]} 到 {df.index[-1]}")
        
        # 計算MACD
        print("🔢 計算MACD指標...")
        prices = df['close'].tolist()
        timestamps = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        
        macd_line, signal_line, hist = macd_calculator.calculate_macd(prices, timestamps)
        
        # 創建包含MACD數據的DataFrame
        macd_df = df.copy()
        macd_df['datetime'] = df['timestamp']
        
        # 填充MACD數據（前面的數據用NaN填充）
        macd_len = len(macd_line)
        total_len = len(df)
        
        macd_df['macd'] = [np.nan] * (total_len - macd_len) + macd_line
        macd_df['macd_signal'] = [np.nan] * (total_len - macd_len) + signal_line
        macd_df['macd_hist'] = [np.nan] * (total_len - macd_len) + hist
        
        # 移除NaN行
        macd_df = macd_df.dropna().reset_index(drop=True)
        
        # 生成交易信號
        print("📡 生成交易信號...")
        signals_df = signal_engine.detect_smart_balanced_signals(macd_df)
        
        # 統計信號
        buy_signals = signals_df[signals_df['signal_type'] == 'buy']
        sell_signals = signals_df[signals_df['signal_type'] == 'sell']
        
        print(f"\n📊 信號統計:")
        print(f"🟢 買進信號: {len(buy_signals)} 個")
        print(f"🔴 賣出信號: {len(sell_signals)} 個")
        print(f"📈 總信號數: {len(buy_signals) + len(sell_signals)} 個")
        
        # 模擬交易配對
        print("\n💰 模擬交易配對...")
        
        # 簡單的交易配對邏輯
        trades = []
        position = None
        
        for idx, row in signals_df.iterrows():
            if row['signal_type'] == 'buy' and position is None:  # 買進信號且空倉
                position = {
                    'buy_time': row['datetime'],
                    'buy_price': row['close'],
                    'buy_index': idx
                }
            elif row['signal_type'] == 'sell' and position is not None:  # 賣出信號且持倉
                trade = {
                    'buy_time': position['buy_time'],
                    'sell_time': row['datetime'],
                    'buy_price': position['buy_price'],
                    'sell_price': row['close'],
                    'profit': row['close'] - position['buy_price'],
                    'profit_pct': ((row['close'] - position['buy_price']) / position['buy_price']) * 100,
                    'hold_hours': (row['datetime'] - position['buy_time']).total_seconds() / 3600
                }
                trades.append(trade)
                position = None
        
        print(f"✅ 完整交易對: {len(trades)} 對")
        
        if trades:
            # 計算統計
            total_profit = sum(trade['profit'] for trade in trades)
            winning_trades = [trade for trade in trades if trade['profit'] > 0]
            losing_trades = [trade for trade in trades if trade['profit'] <= 0]
            
            win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
            avg_profit = total_profit / len(trades) if trades else 0
            avg_hold_time = sum(trade['hold_hours'] for trade in trades) / len(trades) if trades else 0
            
            print(f"\n💰 交易統計:")
            print(f"📈 總獲利: ${total_profit:,.2f}")
            print(f"🎯 勝率: {win_rate:.1f}% ({len(winning_trades)}勝{len(losing_trades)}敗)")
            print(f"📊 平均獲利: ${avg_profit:,.2f}")
            print(f"⏱️ 平均持倉時間: {avg_hold_time:.1f} 小時")
            
            # 顯示最近的交易
            print(f"\n📋 最近5筆交易:")
            for i, trade in enumerate(trades[-5:], 1):
                profit_emoji = "🟢" if trade['profit'] > 0 else "🔴"
                print(f"{profit_emoji} 第{len(trades)-5+i}筆: "
                      f"${trade['profit']:+,.2f} ({trade['profit_pct']:+.2f}%) "
                      f"持倉{trade['hold_hours']:.1f}小時")
        
        # 檢查當前狀態
        latest = signals_df.iloc[-1]
        current_position = latest['position_status']
        
        print(f"\n📊 當前狀態:")
        print(f"💰 當前價格: ${latest['close']:,.2f}")
        print(f"📈 持倉狀態: {current_position}")
        print(f"🔢 下一交易序號: {len(trades) + 1}")
        
        if position:
            unrealized_profit = latest['close'] - position['buy_price']
            unrealized_pct = (unrealized_profit / position['buy_price']) * 100
            hold_time = (latest['datetime'] - position['buy_time']).total_seconds() / 3600
            
            print(f"💎 未實現損益: ${unrealized_profit:+,.2f} ({unrealized_pct:+.2f}%)")
            print(f"⏱️ 持倉時間: {hold_time:.1f} 小時")
        
        print(f"\n⏰ 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ 檢查交易統計時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_latest_trades()