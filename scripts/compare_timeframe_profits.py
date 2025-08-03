#!/usr/bin/env python3
"""
多時間框架獲利比較分析
比較1小時、30分鐘、15分鐘、5分鐘各自的獲利表現
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
from src.core.multi_timeframe_trading_signals import MultiTimeframeSignalDetectionEngine
from src.data.live_macd_service import LiveMACDService
import logging
import asyncio

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_timeframe_profits(signals_df, timeframe_name):
    """計算單一時間框架的獲利統計"""
    if signals_df.empty:
        return {
            'timeframe': timeframe_name,
            'total_trades': 0,
            'total_profit': 0,
            'avg_profit_per_trade': 0,
            'win_rate': 0,
            'max_profit': 0,
            'max_loss': 0,
            'trades': []
        }
    
    # 按交易序號分組，計算每筆完整交易的獲利
    trades = []
    buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
    sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
    
    print(f"\n=== {timeframe_name} 交易分析 ===")
    print(f"買入信號數量: {len(buy_signals)}")
    print(f"賣出信號數量: {len(sell_signals)}")
    
    # 配對買賣信號
    for _, buy_row in buy_signals.iterrows():
        sequence = buy_row['trade_sequence']
        
        # 找到對應的賣出信號
        matching_sells = sell_signals[sell_signals['trade_sequence'] == sequence]
        
        if not matching_sells.empty:
            sell_row = matching_sells.iloc[0]  # 取第一個匹配的賣出信號
            
            buy_price = buy_row['close']
            sell_price = sell_row['close']
            profit = sell_price - buy_price
            profit_pct = (profit / buy_price) * 100
            
            trade_info = {
                'sequence': sequence,
                'buy_time': buy_row['datetime'],
                'sell_time': sell_row['datetime'],
                'buy_price': buy_price,
                'sell_price': sell_price,
                'profit': profit,
                'profit_pct': profit_pct,
                'duration': sell_row['datetime'] - buy_row['datetime']
            }
            trades.append(trade_info)
            
            print(f"交易{sequence}: 買入 {buy_price:,.0f} -> 賣出 {sell_price:,.0f} = 獲利 {profit:,.0f} ({profit_pct:+.2f}%)")
    
    # 計算統計數據
    if trades:
        total_profit = sum(t['profit'] for t in trades)
        avg_profit = total_profit / len(trades)
        win_trades = [t for t in trades if t['profit'] > 0]
        win_rate = len(win_trades) / len(trades) * 100
        max_profit = max(t['profit'] for t in trades)
        max_loss = min(t['profit'] for t in trades)
        
        return {
            'timeframe': timeframe_name,
            'total_trades': len(trades),
            'total_profit': total_profit,
            'avg_profit_per_trade': avg_profit,
            'win_rate': win_rate,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'trades': trades
        }
    else:
        return {
            'timeframe': timeframe_name,
            'total_trades': 0,
            'total_profit': 0,
            'avg_profit_per_trade': 0,
            'win_rate': 0,
            'max_profit': 0,
            'max_loss': 0,
            'trades': []
        }

async def get_multi_timeframe_data(service):
    """獲取多時間框架數據"""
    timeframe_dfs = {}
    
    # 1小時數據 - 作為基準點價格的來源
    hourly_klines = await service._fetch_klines("btctwd", "60", 400)
    if hourly_klines is not None:
        hourly_df = service._calculate_macd(hourly_klines, 12, 26, 9)
        if hourly_df is not None:
            timeframe_dfs['1h'] = hourly_df.tail(168).reset_index(drop=True)
    
    # 30分鐘數據
    thirty_klines = await service._fetch_klines("btctwd", "30", 2400)
    if thirty_klines is not None:
        thirty_df = service._calculate_macd(thirty_klines, 12, 26, 9)
        if thirty_df is not None:
            timeframe_dfs['30m'] = thirty_df.tail(336).reset_index(drop=True)
    
    # 15分鐘數據
    fifteen_klines = await service._fetch_klines("btctwd", "15", 2400)
    if fifteen_klines is not None:
        fifteen_df = service._calculate_macd(fifteen_klines, 12, 26, 9)
        if fifteen_df is not None:
            timeframe_dfs['15m'] = fifteen_df.tail(672).reset_index(drop=True)
    
    # 5分鐘數據
    five_klines = await service._fetch_klines("btctwd", "5", 2400)
    if five_klines is not None:
        five_df = service._calculate_macd(five_klines, 12, 26, 9)
        if five_df is not None:
            timeframe_dfs['5m'] = five_df.tail(2016).reset_index(drop=True)
    
    await service.close()
    return timeframe_dfs

async def main():
    print("🚀 開始多時間框架獲利比較分析...")
    
    # 初始化服務
    macd_service = LiveMACDService()
    signal_detector = MultiTimeframeSignalDetectionEngine()
    
    # 設定分析期間
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # 分析最近7天
    
    print(f"分析期間: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # 獲取多時間框架數據
        print("📊 獲取多時間框架數據...")
        timeframe_data = await get_multi_timeframe_data(macd_service)
        
        # 檢測信號
        print("🔍 檢測多時間框架交易信號...")
        if '1h' not in timeframe_data:
            print("❌ 缺少1小時數據")
            return
        
        hourly_df = timeframe_data['1h']
        signals = signal_detector.detect_signals(hourly_df, timeframe_data)
        
        # 分析每個時間框架的獲利
        results = []
        
        for timeframe in ['1h', '30m', '15m', '5m']:
            if timeframe in signals and not signals[timeframe].empty:
                result = calculate_timeframe_profits(signals[timeframe], timeframe)
                results.append(result)
            else:
                print(f"⚠️ {timeframe} 沒有交易信號")
                results.append({
                    'timeframe': timeframe,
                    'total_trades': 0,
                    'total_profit': 0,
                    'avg_profit_per_trade': 0,
                    'win_rate': 0,
                    'max_profit': 0,
                    'max_loss': 0,
                    'trades': []
                })
        
        # 顯示比較結果
        print("\n" + "="*80)
        print("📈 多時間框架獲利比較結果")
        print("="*80)
        
        # 創建比較表格
        comparison_data = []
        for result in results:
            comparison_data.append({
                '時間框架': result['timeframe'],
                '交易次數': result['total_trades'],
                '總獲利': f"{result['total_profit']:,.0f}",
                '平均獲利': f"{result['avg_profit_per_trade']:,.0f}",
                '勝率': f"{result['win_rate']:.1f}%",
                '最大獲利': f"{result['max_profit']:,.0f}",
                '最大虧損': f"{result['max_loss']:,.0f}"
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        print(df_comparison.to_string(index=False))
        
        # 找出最佳表現
        print("\n" + "="*50)
        print("🏆 最佳表現分析")
        print("="*50)
        
        # 按總獲利排序
        profit_ranking = sorted(results, key=lambda x: x['total_profit'], reverse=True)
        print("📊 總獲利排名:")
        for i, result in enumerate(profit_ranking, 1):
            print(f"{i}. {result['timeframe']}: {result['total_profit']:,.0f}")
        
        # 按平均獲利排序
        avg_profit_ranking = sorted(results, key=lambda x: x['avg_profit_per_trade'], reverse=True)
        print("\n💰 平均獲利排名:")
        for i, result in enumerate(avg_profit_ranking, 1):
            if result['total_trades'] > 0:
                print(f"{i}. {result['timeframe']}: {result['avg_profit_per_trade']:,.0f}")
        
        # 按勝率排序
        win_rate_ranking = sorted(results, key=lambda x: x['win_rate'], reverse=True)
        print("\n🎯 勝率排名:")
        for i, result in enumerate(win_rate_ranking, 1):
            if result['total_trades'] > 0:
                print(f"{i}. {result['timeframe']}: {result['win_rate']:.1f}%")
        
        # 綜合評分 (總獲利 * 勝率 / 100)
        comprehensive_ranking = []
        for result in results:
            if result['total_trades'] > 0:
                score = result['total_profit'] * (result['win_rate'] / 100)
                comprehensive_ranking.append((result['timeframe'], score, result))
        
        comprehensive_ranking.sort(key=lambda x: x[1], reverse=True)
        
        print("\n🌟 綜合評分排名 (總獲利 × 勝率):")
        for i, (timeframe, score, result) in enumerate(comprehensive_ranking, 1):
            print(f"{i}. {timeframe}: {score:,.0f} (獲利: {result['total_profit']:,.0f}, 勝率: {result['win_rate']:.1f}%)")
        
        # 詳細交易記錄
        print("\n" + "="*80)
        print("📋 詳細交易記錄")
        print("="*80)
        
        for result in results:
            if result['trades']:
                print(f"\n--- {result['timeframe']} 詳細交易 ---")
                for trade in result['trades']:
                    duration_hours = trade['duration'].total_seconds() / 3600
                    print(f"交易{trade['sequence']}: "
                          f"{trade['buy_time'].strftime('%m-%d %H:%M')} 買入 {trade['buy_price']:,.0f} -> "
                          f"{trade['sell_time'].strftime('%m-%d %H:%M')} 賣出 {trade['sell_price']:,.0f} "
                          f"= {trade['profit']:+,.0f} ({trade['profit_pct']:+.2f}%) "
                          f"持有 {duration_hours:.1f}小時")
        
    except Exception as e:
        logger.error(f"分析過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())