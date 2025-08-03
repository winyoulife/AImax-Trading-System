#!/usr/bin/env python3
"""
快速測試不同觀察時間設置
使用現有的動態策略GUI來測試1、2、3、4小時觀察時間
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import pandas as pd
from datetime import datetime
import json
import glob

from src.data.live_macd_service import LiveMACDService
from src.core.dynamic_trading_signals import detect_dynamic_trading_signals

async def test_observation_time(observation_hours):
    """測試特定觀察時間的表現"""
    print(f"🔍 測試 {observation_hours} 小時觀察時間...")
    
    try:
        # 創建MACD服務
        macd_service = LiveMACDService()
        
        # 獲取7天數據（使用5分鐘時間週期）
        timeframe_minutes = 5
        total_data_points = (7 * 24 * 60) // timeframe_minutes  # 7天數據點數
        
        klines = await macd_service._fetch_klines(
            market="btctwd",
            period=str(timeframe_minutes),
            limit=total_data_points
        )
        
        if klines is None or klines.empty:
            print(f"❌ 無法獲取數據用於 {observation_hours} 小時測試")
            return None
        
        # 添加datetime列
        klines['datetime'] = pd.to_datetime(klines['open_time'], unit='ms')
        
        # 計算MACD
        df = macd_service._calculate_macd(klines, 12, 26, 9)
        
        # 檢測動態交易信號
        observation_minutes = observation_hours * 60
        signals_df, stats = detect_dynamic_trading_signals(df, observation_minutes)
        
        # 分析結果
        result = analyze_results(signals_df, observation_hours)
        
        print(f"✅ {observation_hours} 小時測試完成")
        print(f"   總交易: {result['total_trades']}, 獲利交易: {result['profitable_trades']}")
        print(f"   勝率: {result['win_rate']:.1f}%, 總利潤: {result['total_profit']:.0f}")
        
        return result
        
    except Exception as e:
        print(f"❌ {observation_hours} 小時測試失敗: {e}")
        return None

def analyze_results(signals_df, observation_hours):
    """分析交易結果"""
    if signals_df is None or signals_df.empty:
        return {
            'observation_hours': observation_hours,
            'total_trades': 0,
            'profitable_trades': 0,
            'win_rate': 0,
            'total_profit': 0,
            'avg_profit': 0,
            'max_drawdown': 0
        }
    
    # 獲取交易信號
    buy_signals = signals_df[signals_df['signal_type'] == 'buy']
    sell_signals = signals_df[signals_df['signal_type'] == 'sell']
    
    total_trades = len(buy_signals) + len(sell_signals)
    
    # 計算利潤
    profits = []
    current_position = None
    entry_price = None
    
    for _, row in signals_df.iterrows():
        if row['signal_type'] == 'buy' and current_position is None:
            current_position = 'long'
            entry_price = row['close']
        elif row['signal_type'] == 'sell' and current_position == 'long':
            if entry_price is not None:
                profit = row['close'] - entry_price
                profits.append(profit)
            current_position = None
            entry_price = None
    
    total_profit = sum(profits) if profits else 0
    profitable_trades = len([p for p in profits if p > 0])
    win_rate = (profitable_trades / len(profits) * 100) if profits else 0
    avg_profit = total_profit / len(profits) if profits else 0
    
    # 計算最大回撤
    max_drawdown = 0
    if profits:
        cumulative = 0
        peak = 0
        for profit in profits:
            cumulative += profit
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown
    
    return {
        'observation_hours': observation_hours,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'avg_profit': avg_profit,
        'max_drawdown': max_drawdown
    }

async def main():
    """主函數"""
    print("🚀 開始測試不同觀察時間設置...")
    print("=" * 60)
    
    results = {}
    observation_times = [1, 2, 3, 4]
    
    for obs_time in observation_times:
        result = await test_observation_time(obs_time)
        if result:
            results[obs_time] = result
        print("-" * 40)
    
    # 生成比較報告
    if results:
        print("\n" + "=" * 60)
        print("📊 觀察時間設置比較報告")
        print("=" * 60)
        
        print(f"{'觀察時間':<8} {'總交易':<6} {'獲利交易':<6} {'勝率':<6} {'總利潤':<10} {'平均利潤':<10} {'最大回撤':<10}")
        print("-" * 70)
        
        best_profit = float('-inf')
        best_obs_time = None
        
        for obs_time in sorted(results.keys()):
            result = results[obs_time]
            print(f"{obs_time}小時    {result['total_trades']:<6} {result['profitable_trades']:<6} "
                  f"{result['win_rate']:<6.1f}% {result['total_profit']:<10.0f} "
                  f"{result['avg_profit']:<10.0f} {result['max_drawdown']:<10.0f}")
            
            if result['total_profit'] > best_profit:
                best_profit = result['total_profit']
                best_obs_time = obs_time
        
        print("-" * 70)
        print(f"🏆 最佳表現: {best_obs_time}小時觀察時間 (總利潤: {best_profit:.0f})")
        
        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"AImax/reports/quick_observation_test_{timestamp}.json"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細報告已保存: {report_path}")
    else:
        print("❌ 沒有成功的測試結果")

if __name__ == "__main__":
    asyncio.run(main()) 