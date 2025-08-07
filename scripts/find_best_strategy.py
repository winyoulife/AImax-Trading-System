#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尋找最佳策略 - 測試所有可用策略並找出85%獲利率的策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import logging

# 導入所有策略模組
from src.data.live_macd_service import LiveMACDService

# 設置日誌
logging.basicConfig(level=logging.WARNING)  # 減少日誌輸出
logger = logging.getLogger(__name__)

def test_clean_macd_strategy(df):
    """測試乾淨版MACD策略"""
    try:
        from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
        
        detector = SmartBalancedVolumeEnhancedMACDSignals()
        signals = detector.detect_smart_balanced_signals(df)
        
        # 計算績效
        if not signals:
            return {'name': 'Clean MACD', 'trades': 0, 'profit': 0, 'win_rate': 0}
        
        # 簡單配對買賣信號
        buy_signals = [s for s in signals if s['action'] == 'buy']
        sell_signals = [s for s in signals if s['action'] == 'sell']
        
        trades = []
        total_profit = 0
        
        for i, buy in enumerate(buy_signals):
            if i < len(sell_signals):
                sell = sell_signals[i]
                profit = sell['price'] - buy['price']
                total_profit += profit
                trades.append({
                    'buy_price': buy['price'],
                    'sell_price': sell['price'],
                    'profit': profit,
                    'win': profit > 0
                })
        
        win_rate = (sum(1 for t in trades if t['win']) / len(trades) * 100) if trades else 0
        
        return {
            'name': 'Clean MACD',
            'trades': len(trades),
            'profit': total_profit,
            'win_rate': win_rate,
            'avg_profit': total_profit / len(trades) if trades else 0
        }
        
    except Exception as e:
        return {'name': 'Clean MACD', 'error': str(e), 'trades': 0, 'profit': 0, 'win_rate': 0}

def test_volume_enhanced_strategy(df):
    """測試成交量增強策略"""
    try:
        from src.core.volume_enhanced_macd_signals import VolumeEnhancedMACDSignals
        
        detector = VolumeEnhancedMACDSignals()
        signals = detector.detect_smart_balanced_signals(df)
        
        if not signals:
            return {'name': 'Volume Enhanced', 'trades': 0, 'profit': 0, 'win_rate': 0}
        
        # 計算績效
        buy_signals = [s for s in signals if s['action'] == 'buy']
        sell_signals = [s for s in signals if s['action'] == 'sell']
        
        trades = []
        total_profit = 0
        
        for i, buy in enumerate(buy_signals):
            if i < len(sell_signals):
                sell = sell_signals[i]
                profit = sell['price'] - buy['price']
                total_profit += profit
                trades.append({'profit': profit, 'win': profit > 0})
        
        win_rate = (sum(1 for t in trades if t['win']) / len(trades) * 100) if trades else 0
        
        return {
            'name': 'Volume Enhanced',
            'trades': len(trades),
            'profit': total_profit,
            'win_rate': win_rate,
            'avg_profit': total_profit / len(trades) if trades else 0
        }
        
    except Exception as e:
        return {'name': 'Volume Enhanced', 'error': str(e), 'trades': 0, 'profit': 0, 'win_rate': 0}

def test_simple_macd_strategy(df):
    """測試簡單MACD策略 - 可能是我們85%獲利率的策略"""
    try:
        # 計算MACD
        df = df.copy()
        
        # 計算EMA
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        
        # 計算MACD
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 檢測金叉死叉
        signals = []
        position = 0  # 0=空倉, 1=持倉
        
        for i in range(1, len(df)):
            prev_hist = df.iloc[i-1]['macd_hist']
            curr_hist = df.iloc[i]['macd_hist']
            
            # 金叉買入
            if prev_hist <= 0 and curr_hist > 0 and position == 0:
                signals.append({
                    'action': 'buy',
                    'price': df.iloc[i]['close'],
                    'timestamp': df.iloc[i]['datetime'] if 'datetime' in df.columns else i
                })
                position = 1
            
            # 死叉賣出
            elif prev_hist >= 0 and curr_hist < 0 and position == 1:
                signals.append({
                    'action': 'sell',
                    'price': df.iloc[i]['close'],
                    'timestamp': df.iloc[i]['datetime'] if 'datetime' in df.columns else i
                })
                position = 0
        
        # 計算績效
        buy_signals = [s for s in signals if s['action'] == 'buy']
        sell_signals = [s for s in signals if s['action'] == 'sell']
        
        trades = []
        total_profit = 0
        
        for i, buy in enumerate(buy_signals):
            if i < len(sell_signals):
                sell = sell_signals[i]
                profit = sell['price'] - buy['price']
                total_profit += profit
                trades.append({
                    'buy_price': buy['price'],
                    'sell_price': sell['price'],
                    'profit': profit,
                    'win': profit > 0
                })
        
        win_rate = (sum(1 for t in trades if t['win']) / len(trades) * 100) if trades else 0
        
        return {
            'name': 'Simple MACD',
            'trades': len(trades),
            'profit': total_profit,
            'win_rate': win_rate,
            'avg_profit': total_profit / len(trades) if trades else 0,
            'details': trades[-5:] if trades else []  # 最近5筆交易
        }
        
    except Exception as e:
        return {'name': 'Simple MACD', 'error': str(e), 'trades': 0, 'profit': 0, 'win_rate': 0}

def test_optimized_parameters_strategy(df):
    """測試優化參數策略 - 嘗試找到83.3%勝率的參數組合"""
    best_result = {'name': 'Optimized MACD', 'trades': 0, 'profit': 0, 'win_rate': 0}
    
    # 測試不同的MACD參數組合
    parameter_sets = [
        (8, 21, 5),   # 快速參數
        (12, 26, 9),  # 標準參數
        (19, 39, 9),  # 慢速參數
        (5, 35, 5),   # 極端參數
        (10, 30, 10), # 平衡參數
    ]
    
    for fast, slow, signal in parameter_sets:
        try:
            df_test = df.copy()
            
            # 計算MACD
            ema_fast = df_test['close'].ewm(span=fast).mean()
            ema_slow = df_test['close'].ewm(span=slow).mean()
            
            df_test['macd'] = ema_fast - ema_slow
            df_test['macd_signal'] = df_test['macd'].ewm(span=signal).mean()
            df_test['macd_hist'] = df_test['macd'] - df_test['macd_signal']
            
            # 添加過濾條件
            df_test['rsi'] = calculate_rsi(df_test['close'])
            df_test['volume_ma'] = df_test['volume'].rolling(window=20).mean()
            df_test['volume_ratio'] = df_test['volume'] / df_test['volume_ma']
            
            # 檢測信號（加入過濾條件）
            signals = []
            position = 0
            
            for i in range(20, len(df_test)):  # 從第20個數據點開始，確保指標穩定
                prev_hist = df_test.iloc[i-1]['macd_hist']
                curr_hist = df_test.iloc[i]['macd_hist']
                rsi = df_test.iloc[i]['rsi']
                vol_ratio = df_test.iloc[i]['volume_ratio']
                
                # 金叉買入（加入過濾條件）
                if (prev_hist <= 0 and curr_hist > 0 and position == 0 and
                    rsi < 70 and vol_ratio > 1.2):  # RSI不超買，成交量放大
                    signals.append({
                        'action': 'buy',
                        'price': df_test.iloc[i]['close'],
                        'confidence': min(vol_ratio, 3.0) / 3.0  # 信心度基於成交量
                    })
                    position = 1
                
                # 死叉賣出（加入過濾條件）
                elif (prev_hist >= 0 and curr_hist < 0 and position == 1 and
                      rsi > 30):  # RSI不超賣
                    signals.append({
                        'action': 'sell',
                        'price': df_test.iloc[i]['close'],
                        'confidence': 0.8
                    })
                    position = 0
            
            # 計算績效
            buy_signals = [s for s in signals if s['action'] == 'buy']
            sell_signals = [s for s in signals if s['action'] == 'sell']
            
            trades = []
            total_profit = 0
            
            for i, buy in enumerate(buy_signals):
                if i < len(sell_signals):
                    sell = sell_signals[i]
                    profit = sell['price'] - buy['price']
                    total_profit += profit
                    trades.append({'profit': profit, 'win': profit > 0})
            
            if trades:
                win_rate = (sum(1 for t in trades if t['win']) / len(trades) * 100)
                
                # 如果這個參數組合表現更好，更新最佳結果
                if win_rate > best_result['win_rate']:
                    best_result = {
                        'name': f'Optimized MACD ({fast},{slow},{signal})',
                        'trades': len(trades),
                        'profit': total_profit,
                        'win_rate': win_rate,
                        'avg_profit': total_profit / len(trades),
                        'parameters': (fast, slow, signal)
                    }
                    
        except Exception as e:
            continue
    
    return best_result

def calculate_rsi(prices, period=14):
    """計算RSI指標"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

async def main():
    """主函數 - 測試所有策略找出最佳表現"""
    print("🔍 尋找85%獲利率策略...")
    print("="*60)
    
    try:
        # 獲取數據
        service = LiveMACDService()
        
        # 獲取更多歷史數據進行測試
        klines = await service._fetch_klines("btctwd", "60", 1000)
        if klines is None:
            print("❌ 無法獲取數據")
            return
        
        df = service._calculate_macd(klines, 12, 26, 9)
        if df is None:
            print("❌ 無法計算MACD")
            return
        
        await service.close()
        
        print(f"📊 測試數據: {len(df)} 個1小時數據點")
        print(f"時間範圍: {df.iloc[0]['datetime']} 至 {df.iloc[-1]['datetime']}")
        
        # 測試所有策略
        strategies = [
            test_simple_macd_strategy,
            test_optimized_parameters_strategy,
            test_clean_macd_strategy,
            test_volume_enhanced_strategy,
        ]
        
        results = []
        
        print(f"\n🧪 開始測試 {len(strategies)} 個策略...")
        
        for i, strategy_func in enumerate(strategies, 1):
            print(f"\n測試策略 {i}/{len(strategies)}...")
            result = strategy_func(df)
            results.append(result)
            
            if 'error' in result:
                print(f"❌ {result['name']}: {result['error']}")
            else:
                print(f"✅ {result['name']}: {result['trades']} 筆交易, "
                      f"勝率 {result['win_rate']:.1f}%, "
                      f"總獲利 {result['profit']:+,.0f} TWD")
        
        # 排序結果
        valid_results = [r for r in results if 'error' not in r and r['trades'] > 0]
        valid_results.sort(key=lambda x: x['win_rate'], reverse=True)
        
        # 顯示結果
        print(f"\n" + "="*60)
        print(f"📊 策略績效排行榜")
        print(f"="*60)
        
        for i, result in enumerate(valid_results, 1):
            status = "🏆" if result['win_rate'] >= 85 else "🔥" if result['win_rate'] >= 75 else "👍" if result['win_rate'] >= 60 else "⚠️"
            
            print(f"{status} 第{i}名: {result['name']}")
            print(f"   勝率: {result['win_rate']:.1f}%")
            print(f"   交易數: {result['trades']}")
            print(f"   總獲利: {result['profit']:+,.0f} TWD")
            print(f"   平均獲利: {result['avg_profit']:+,.0f} TWD")
            
            if 'parameters' in result:
                print(f"   最佳參數: {result['parameters']}")
            
            if result['win_rate'] >= 85:
                print(f"   🎉 找到85%獲利率策略！")
            
            print()
        
        # 總結
        if valid_results and valid_results[0]['win_rate'] >= 85:
            best = valid_results[0]
            print(f"🎊 成功找到85%獲利率策略！")
            print(f"最佳策略: {best['name']}")
            print(f"勝率: {best['win_rate']:.1f}%")
            print(f"這就是我們一直在尋找的高獲利策略！")
        else:
            print(f"📈 目前最佳策略勝率: {valid_results[0]['win_rate']:.1f}%")
            print(f"還需要繼續優化以達到85%目標")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == '__main__':
    asyncio.run(main())