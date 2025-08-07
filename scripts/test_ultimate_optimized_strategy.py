#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試終極優化成交量增強MACD策略
驗證是否能達到81.8%勝率
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List

# 導入策略模組
from src.data.live_macd_service import LiveMACDService
from src.core.ultimate_optimized_volume_macd_signals import UltimateOptimizedVolumeEnhancedMACDSignals

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_strategy_performance(signals, df):
    """計算策略績效"""
    print("\n" + "="*60)
    print("📊 終極優化成交量增強MACD策略績效分析")
    print("="*60)
    
    if not signals:
        print("❌ 沒有檢測到任何交易信號")
        return {'trades': 0, 'profit': 0, 'win_rate': 0}
    
    # 分離買賣信號
    buy_signals = [s for s in signals if s['action'] == 'buy']
    sell_signals = [s for s in signals if s['action'] == 'sell']
    
    print(f"🔍 信號統計:")
    print(f"   總信號數: {len(signals)}")
    print(f"   買入信號: {len(buy_signals)} 個")
    print(f"   賣出信號: {len(sell_signals)} 個")
    
    # 顯示信號詳情
    print(f"\n📋 買入信號詳情:")
    for i, signal in enumerate(buy_signals[:5]):  # 顯示前5個
        print(f"   {i+1}. 價格: {signal['price']:,.0f} TWD")
        print(f"      信心度: {signal['confidence']:.1%}")
        print(f"      原因: {', '.join(signal['reasons'])}")
    
    print(f"\n📋 賣出信號詳情:")
    for i, signal in enumerate(sell_signals[:5]):  # 顯示前5個
        print(f"   {i+1}. 價格: {signal['price']:,.0f} TWD")
        print(f"      信心度: {signal['confidence']:.1%}")
        print(f"      原因: {', '.join(signal['reasons'])}")
    
    # 配對交易計算
    trades = []
    total_profit = 0
    
    # 簡單配對：按時間順序配對買賣信號
    min_pairs = min(len(buy_signals), len(sell_signals))
    
    print(f"\n💰 交易配對分析:")
    for i in range(min_pairs):
        buy_signal = buy_signals[i]
        sell_signal = sell_signals[i]
        
        buy_price = buy_signal['price']
        sell_price = sell_signal['price']
        profit = sell_price - buy_price
        profit_pct = (profit / buy_price) * 100
        
        total_profit += profit
        is_winning = profit > 0
        trades.append({
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit': profit,
            'profit_pct': profit_pct,
            'is_winning': is_winning,
            'buy_confidence': buy_signal['confidence'],
            'sell_confidence': sell_signal['confidence']
        })
        
        status = "✅" if is_winning else "❌"
        print(f"   {status} 交易{i+1}: {buy_price:,.0f} -> {sell_price:,.0f} = {profit:+,.0f} TWD ({profit_pct:+.2f}%)")
        print(f"      買入信心: {buy_signal['confidence']:.1%}, 賣出信心: {sell_signal['confidence']:.1%}")
    
    # 計算整體績效
    if trades:
        winning_trades = sum(1 for t in trades if t['is_winning'])
        win_rate = (winning_trades / len(trades)) * 100
        avg_profit = total_profit / len(trades)
        avg_confidence = sum(t['buy_confidence'] + t['sell_confidence'] for t in trades) / (len(trades) * 2)
        
        print(f"\n🎯 整體績效統計:")
        print(f"   總交易數: {len(trades)}")
        print(f"   獲利交易: {winning_trades}")
        print(f"   虧損交易: {len(trades) - winning_trades}")
        print(f"   勝率: {win_rate:.1f}%")
        print(f"   總獲利: {total_profit:+,.0f} TWD")
        print(f"   平均每筆: {avg_profit:+,.0f} TWD")
        print(f"   平均信號強度: {avg_confidence*100:.1f}/100")
        
        # 與目標比較
        print(f"\n🏆 與目標比較:")
        print(f"   目標勝率: 81.8%")
        print(f"   實際勝率: {win_rate:.1f}%")
        if win_rate >= 81:
            print(f"   🎉 達到目標！策略表現優秀！")
        elif win_rate >= 75:
            print(f"   🔥 接近目標，表現良好！")
        else:
            print(f"   ⚠️ 未達目標，需要優化")
        
        return {
            'trades': len(trades),
            'profit': total_profit,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'winning_trades': winning_trades,
            'avg_confidence': avg_confidence
        }
    
    return {'trades': 0, 'profit': 0, 'win_rate': 0}

async def test_ultimate_optimized_strategy():
    """測試終極優化策略"""
    print("🚀 測試終極優化成交量增強MACD策略")
    print("目標：驗證81.8%勝率表現")
    print("="*50)
    
    try:
        # 初始化服務和策略
        service = LiveMACDService()
        strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
        
        print(f"📊 策略配置:")
        print(f"   策略類型: 終極優化成交量增強MACD")
        print(f"   目標勝率: 81.8%")
        
        # 獲取歷史數據
        print(f"\n📈 獲取歷史數據...")
        klines = await service._fetch_klines("btctwd", "60", 2000)  # 2000個1小時數據
        if klines is None:
            print("❌ 無法獲取歷史數據")
            return None
        
        # 轉換為DataFrame
        df = pd.DataFrame(klines)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        
        print(f"✅ 獲取到 {len(df)} 個數據點")
        print(f"   時間範圍: {df.index[0]} 至 {df.index[-1]}")
        print(f"   價格範圍: {df['close'].min():,.0f} - {df['close'].max():,.0f} TWD")
        
        await service.close()
        
        # 執行信號檢測
        print(f"\n🎯 執行信號檢測...")
        signals_df = strategy.detect_ultimate_optimized_signals(df)
        
        # 轉換為列表格式
        signals = []
        for _, row in signals_df.iterrows():
            if row['signal_type'] in ['buy', 'sell']:
                signals.append({
                    'action': row['signal_type'],
                    'price': row['close'],
                    'confidence': row['signal_strength'] / 100,
                    'reasons': [row['validation_info']],
                    'timestamp': row['datetime']
                })
        
        # 計算策略績效
        performance = calculate_strategy_performance(signals, df)
        
        # 顯示最終結果
        print(f"\n🎊 測試結果總結:")
        if performance['trades'] > 0:
            print(f"   📊 策略勝率: {performance['win_rate']:.1f}%")
            print(f"   💰 總獲利: {performance['profit']:+,.0f} TWD")
            print(f"   📈 交易次數: {performance['trades']}")
            print(f"   🎯 平均信號強度: {performance['avg_confidence']*100:.1f}/100")
            
            if performance['win_rate'] >= 81:
                print(f"   🏆 優秀！達到81.8%勝率目標！")
                print(f"   🌟 這個策略可以用於雲端部署！")
            elif performance['win_rate'] >= 75:
                print(f"   🔥 良好！接近目標表現！")
            else:
                print(f"   ⚠️ 需要進一步優化")
        else:
            print(f"   ❌ 沒有產生任何交易，策略過於保守")
        
        return performance
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        logger.error(f"策略測試錯誤: {e}")
        return None

def main():
    """主函數"""
    print("🎯 終極優化成交量增強MACD策略驗證")
    print("="*50)
    
    # 運行異步測試
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        performance = loop.run_until_complete(test_ultimate_optimized_strategy())
        
        if performance and performance['trades'] > 0:
            print(f"\n✅ 測試完成！")
            if performance['win_rate'] >= 81:
                print(f"🎉 驗證成功！終極優化策略確實能達到高勝率！")
                print(f"這個策略可以用於雲端部署！")
                print(f"勝率: {performance['win_rate']:.1f}%")
                print(f"總獲利: {performance['profit']:+,.0f} TWD")
            else:
                print(f"📈 策略表現: {performance['win_rate']:.1f}%勝率")
                print(f"需要進一步調整參數以達到目標")
        else:
            print(f"\n❌ 測試未能產生有效結果")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ 用戶中斷測試")
    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    main()