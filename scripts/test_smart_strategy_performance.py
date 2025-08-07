#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Smart Balanced Volume MACD策略的實際表現
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
from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeAnalyzer

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartBalancedMACDSignals:
    """智能平衡MACD信號檢測器"""
    
    def __init__(self):
        self.analyzer = SmartBalancedVolumeAnalyzer()
        self.min_confidence = 0.75  # 75%最低信心度
        
    def calculate_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """計算MACD指標"""
        df = df.copy()
        
        # 計算EMA
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        
        # 計算MACD線
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def detect_signals(self, df: pd.DataFrame) -> List[Dict]:
        """檢測交易信號"""
        try:
            # 計算MACD
            df = self.calculate_macd(df)
            
            # 計算智能指標
            df = self.analyzer.calculate_smart_indicators(df)
            
            signals = []
            
            for i in range(50, len(df)):  # 從第50個數據點開始
                current = df.iloc[i]
                prev = df.iloc[i-1]
                
                # 檢測買入信號
                buy_signal = self._detect_buy_signal(current, prev, df.iloc[i-10:i+1])
                if buy_signal:
                    signals.append({
                        'timestamp': current.name if hasattr(current, 'name') else datetime.now(),
                        'action': 'buy',
                        'price': current['close'],
                        'confidence': buy_signal['confidence'],
                        'reasons': buy_signal['reasons'],
                        'symbol': 'BTCUSDT'
                    })
                
                # 檢測賣出信號
                sell_signal = self._detect_sell_signal(current, prev, df.iloc[i-10:i+1])
                if sell_signal:
                    signals.append({
                        'timestamp': current.name if hasattr(current, 'name') else datetime.now(),
                        'action': 'sell',
                        'price': current['close'],
                        'confidence': sell_signal['confidence'],
                        'reasons': sell_signal['reasons'],
                        'symbol': 'BTCUSDT'
                    })
            
            logger.info(f"檢測到 {len(signals)} 個交易信號")
            return signals
            
        except Exception as e:
            logger.error(f"信號檢測失敗: {e}")
            return []
    
    def _detect_buy_signal(self, current, prev, recent_data) -> Dict:
        """檢測買入信號"""
        try:
            confidence = 0.0
            reasons = []
            
            # 1. MACD金叉確認 (25分)
            if (current['macd'] > current['macd_signal'] and 
                prev['macd'] <= prev['macd_signal'] and
                current['macd_hist'] > 0):
                confidence += 0.25
                reasons.append("MACD金叉確認")
            
            # 2. 成交量智能確認 (20分)
            if (current['volume_ratio'] > 1.2 and 
                current['volume_trend'] > 0.05):
                confidence += 0.20
                reasons.append(f"成交量放大{current['volume_ratio']:.1f}倍且趨勢向上")
            
            # 3. RSI合理區間 (15分)
            if 30 <= current['rsi'] <= 50:
                confidence += 0.15
                reasons.append(f"RSI健康區間{current['rsi']:.1f}")
            
            # 4. 布林帶位置優勢 (15分)
            if (0.2 <= current['bb_position'] <= 0.4 and 
                current['bb_width'] > 0.02):
                confidence += 0.15
                reasons.append("布林帶下方支撐且波動充足")
            
            # 5. 趨勢強度確認 (10分)
            if current['trend_strength'] > -0.02:
                confidence += 0.10
                reasons.append("趨勢強度良好")
            
            # 6. 價格動能確認 (10分)
            price_momentum = (current['close'] - recent_data['close'].iloc[-3]) / recent_data['close'].iloc[-3]
            if price_momentum > 0.005:
                confidence += 0.10
                reasons.append("價格動能向上")
            
            # 7. MACD柱狀圖趨勢 (5分)
            if current['macd_hist'] > prev['macd_hist']:
                confidence += 0.05
                reasons.append("MACD柱狀圖增強")
            
            # 信心度達到門檻且有足夠理由才發出信號
            if confidence >= self.min_confidence and len(reasons) >= 4:
                return {
                    'confidence': confidence,
                    'reasons': reasons
                }
            
            return None
            
        except Exception as e:
            logger.error(f"買入信號檢測失敗: {e}")
            return None
    
    def _detect_sell_signal(self, current, prev, recent_data) -> Dict:
        """檢測賣出信號"""
        try:
            confidence = 0.0
            reasons = []
            
            # 1. MACD死叉確認 (25分)
            if (current['macd'] < current['macd_signal'] and 
                prev['macd'] >= prev['macd_signal'] and
                current['macd_hist'] < 0):
                confidence += 0.25
                reasons.append("MACD死叉確認")
            
            # 2. 成交量智能確認 (20分)
            if (current['volume_ratio'] > 1.1 and 
                current['volume_trend'] < -0.03):
                confidence += 0.20
                reasons.append(f"成交量放大{current['volume_ratio']:.1f}倍且趨勢向下")
            
            # 3. RSI合理區間 (15分)
            if 50 <= current['rsi'] <= 70:
                confidence += 0.15
                reasons.append(f"RSI健康區間{current['rsi']:.1f}")
            
            # 4. 布林帶位置優勢 (15分)
            if (0.6 <= current['bb_position'] <= 0.8 and 
                current['bb_width'] > 0.02):
                confidence += 0.15
                reasons.append("布林帶上方阻力且波動充足")
            
            # 5. 趨勢強度確認 (10分)
            if current['trend_strength'] < 0.02:
                confidence += 0.10
                reasons.append("趨勢強度轉弱")
            
            # 6. 價格動能確認 (10分)
            price_momentum = (current['close'] - recent_data['close'].iloc[-3]) / recent_data['close'].iloc[-3]
            if price_momentum < -0.005:
                confidence += 0.10
                reasons.append("價格動能向下")
            
            # 7. MACD柱狀圖趨勢 (5分)
            if current['macd_hist'] < prev['macd_hist']:
                confidence += 0.05
                reasons.append("MACD柱狀圖減弱")
            
            # 信心度達到門檻且有足夠理由才發出信號
            if confidence >= self.min_confidence and len(reasons) >= 4:
                return {
                    'confidence': confidence,
                    'reasons': reasons
                }
            
            return None
            
        except Exception as e:
            logger.error(f"賣出信號檢測失敗: {e}")
            return None

def calculate_strategy_performance(signals, df):
    """計算策略績效"""
    print("\n" + "="*60)
    print("📊 Smart Balanced Volume MACD 策略績效分析")
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
        print(f"   平均信號強度: {avg_confidence:.1f}/100")
        
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

async def test_smart_balanced_strategy():
    """測試Smart Balanced策略"""
    print("🚀 測試Smart Balanced Volume MACD策略")
    print("目標：驗證81.8%勝率表現")
    print("="*50)
    
    try:
        # 初始化服務和策略
        service = LiveMACDService()
        strategy = SmartBalancedMACDSignals()
        
        print(f"📊 策略配置:")
        print(f"   最低信心度: {strategy.min_confidence:.1%}")
        print(f"   目標勝率: 81.8%")
        
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
            print(f"   📊 策略勝率: {performance['win_rate']:.1f}%")
            print(f"   💰 總獲利: {performance['profit']:+,.0f} TWD")
            print(f"   📈 交易次數: {performance['trades']}")
            print(f"   🎯 平均信號強度: {performance['avg_confidence']:.1f}/100")
            
            if performance['win_rate'] >= 81:
                print(f"   🏆 優秀！達到81.8%勝率目標！")
            elif performance['win_rate'] >= 75:
                print(f"   🔥 良好！接近目標表現！")
            else:
                print(f"   ⚠️ 需要進一步優化")
        else:
            print(f"   ❌ 沒有產生任何交易")
        
        return performance
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        logger.error(f"策略測試錯誤: {e}")
        return None

def main():
    """主函數"""
    print("🎯 Smart Balanced Volume MACD 策略驗證")
    print("="*50)
    
    # 運行異步測試
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        performance = loop.run_until_complete(test_smart_balanced_strategy())
        
        if performance and performance['trades'] > 0:
            print(f"\n✅ 測試完成！")
            if performance['win_rate'] >= 81:
                print(f"🎉 驗證成功！Smart Balanced策略確實能達到高勝率！")
                print(f"這個策略可以用於雲端部署！")
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