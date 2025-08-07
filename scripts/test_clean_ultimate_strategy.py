#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Clean Ultimate策略的實際表現
驗證是否真的能達到85%勝率
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import logging

# 導入策略模組
from src.data.live_macd_service import LiveMACDService
from src.core.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_strategy_performance(signals, df):
    """計算策略績效"""
    print("\n" + "="*60)
    print("📊 Clean Ultimate 策略績效分析")
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
        avg_buy_confidence = sum(t['buy_confidence'] for t in trades) / len(trades)
        avg_sell_confidence = sum(t['sell_confidence'] for t in trades) / len(trades)
        
        print(f"\n🎯 整體績效統計:")
        print(f"   總交易數: {len(trades)}")
        print(f"   獲利交易: {winning_trades}")
        print(f"   虧損交易: {len(trades) - winning_trades}")
        print(f"   勝率: {win_rate:.1f}%")
        print(f"   總獲利: {total_profit:+,.0f} TWD")
        print(f"   平均每筆: {avg_profit:+,.0f} TWD")
        print(f"   平均買入信心度: {avg_buy_confidence:.1%}")
        print(f"   平均賣出信心度: {avg_sell_confidence:.1%}")
        
        # 評估策略表現
        print(f"\n🏆 策略評估:")
        if win_rate >= 85:
            print(f"   🎉 優秀！達到85%勝率目標！")
        elif win_rate >= 80:
            print(f"   🔥 很好！接近85%目標")
        elif win_rate >= 70:
            print(f"   👍 良好，還有提升空間")
        elif win_rate >= 60:
            print(f"   ⚠️ 一般，需要優化")
        else:
            print(f"   ❌ 表現不佳，需要重新設計")
        
        return {
            'trades': len(trades),
            'profit': total_profit,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'winning_trades': winning_trades,
            'avg_buy_confidence': avg_buy_confidence,
            'avg_sell_confidence': avg_sell_confidence
        }
    
    return {'trades': 0, 'profit': 0, 'win_rate': 0}

async def test_clean_ultimate_strategy():
    """測試Clean Ultimate策略"""
    print("🚀 測試Clean Ultimate 85%勝率策略")
    print("="*50)
    
    try:
        # 初始化服務和策略
        service = LiveMACDService()
        strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
        
        print(f"📊 策略配置:")
        print(f"   最低信心度: {strategy.min_confidence:.1%}")
        print(f"   目標勝率: 85%+")
        
        # 獲取歷史數據
        print(f"\n📈 獲取歷史數據...")
        klines = await service._fetch_klines("btctwd", "60", 1000)  # 1000個1小時數據
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
        signals = strategy.detect_signals(df)
        
        # 計算策略績效
        performance = calculate_strategy_performance(signals, df)
        
        # 顯示最終結果
        print(f"\n🎊 測試結果總結:")
        if performance['trades'] > 0:
            if performance['win_rate'] >= 85:
                print(f"   🏆 策略成功！勝率 {performance['win_rate']:.1f}% 達到85%目標")
                print(f"   💰 總獲利: {performance['profit']:+,.0f} TWD")
                print(f"   📈 交易次數: {performance['trades']}")
            else:
                print(f"   📊 策略勝率: {performance['win_rate']:.1f}%")
                print(f"   💰 總獲利: {performance['profit']:+,.0f} TWD")
                print(f"   📈 交易次數: {performance['trades']}")
                print(f"   ⚠️ 未達到85%目標，需要進一步優化")
        else:
            print(f"   ❌ 沒有產生任何交易，策略過於保守")
        
        return performance
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        logger.error(f"策略測試錯誤: {e}")
        return None

def main():
    """主函數"""
    print("🎯 Clean Ultimate 85%勝率策略測試")
    print("="*50)
    
    # 運行異步測試
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        performance = loop.run_until_complete(test_clean_ultimate_strategy())
        
        if performance and performance['trades'] > 0:
            print(f"\n✅ 測試完成！")
            if performance['win_rate'] >= 85:
                print(f"🎉 恭喜！Clean Ultimate策略確實達到了85%的高勝率！")
                print(f"這證明了我們的策略設計是有效的！")
            else:
                print(f"📈 策略表現: {performance['win_rate']:.1f}%勝率")
                print(f"雖然未達到85%，但仍有優化潛力")
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