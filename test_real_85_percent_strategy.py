#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 測試真正的85%勝率策略
使用UltimateOptimizedVolumeEnhancedMACDSignals類
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 添加src目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals
from data.data_fetcher import DataFetcher

class Real85PercentStrategyTester:
    def __init__(self):
        self.strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
        self.data_fetcher = DataFetcher()
        
        # 交易參數
        self.initial_balance = 100000  # 10萬台幣
        self.current_balance = self.initial_balance
        self.btc_holdings = 0
        self.transaction_fee = 0.001  # 0.1%手續費
        
        # 交易記錄
        self.trades = []
        self.trade_pairs = []
        self.position = 0  # 0=空倉, 1=持倉
        
    def get_historical_data(self, days=60):
        """獲取歷史數據"""
        print(f"📡 獲取最近{days}天的歷史數據...")
        
        try:
            # 獲取更多數據以確保有足夠的信號
            df = self.data_fetcher.get_kline_data('btctwd', '1h', limit=days*24)
            
            if df is None or len(df) < 100:
                print("❌ 歷史數據不足")
                return None
            
            print(f"✅ 成功獲取 {len(df)} 筆歷史數據")
            print(f"📅 時間範圍: {df.index[0] if hasattr(df, 'index') else 'N/A'} 到 {df.index[-1] if hasattr(df, 'index') else 'N/A'}")
            print(f"💰 價格範圍: NT$ {df['low'].min():,.0f} - NT$ {df['high'].max():,.0f}")
            
            return df
            
        except Exception as e:
            print(f"❌ 獲取歷史數據失敗: {e}")
            return None
    
    def test_strategy_performance(self, df):
        """測試策略表現"""
        print("\n🧪 開始測試真正的85%勝率策略...")
        print("=" * 60)
        
        # 檢測信號
        print("🔍 檢測交易信號...")
        signals = self.strategy.detect_signals(df)
        
        print(f"📋 檢測到 {len(signals)} 個信號")
        
        if len(signals) == 0:
            print("⚠️ 沒有檢測到符合85%標準的信號")
            print("   這表示策略非常保守，只在最佳時機出手")
            return
        
        # 分析信號品質
        self.analyze_signal_quality(signals)
        
        # 模擬交易
        print("\n💰 開始模擬交易...")
        self.simulate_trading(signals)
        
        # 分析結果
        self.analyze_results()
    
    def analyze_signal_quality(self, signals):
        """分析信號品質"""
        print("\n📊 信號品質分析:")
        
        buy_signals = [s for s in signals if s['action'] == 'buy']
        sell_signals = [s for s in signals if s['action'] == 'sell']
        
        print(f"   買入信號: {len(buy_signals)} 個")
        print(f"   賣出信號: {len(sell_signals)} 個")
        
        # 信心度分析
        if signals:
            confidences = [s['confidence'] for s in signals]
            avg_confidence = np.mean(confidences)
            min_confidence = min(confidences)
            max_confidence = max(confidences)
            
            print(f"   平均信心度: {avg_confidence*100:.1f}%")
            print(f"   最低信心度: {min_confidence*100:.1f}%")
            print(f"   最高信心度: {max_confidence*100:.1f}%")
            
            # 顯示前5個信號的詳細信息
            print(f"\n🔍 前5個信號詳情:")
            for i, signal in enumerate(signals[:5]):
                print(f"   信號 #{i+1}: {signal['action']} @ NT$ {signal['price']:,.0f}")
                print(f"            信心度: {signal['confidence']*100:.1f}%")
                print(f"            原因: {', '.join(signal['reasons'])}")
    
    def simulate_trading(self, signals):
        """模擬交易執行"""
        # 按時間排序信號
        signals_sorted = sorted(signals, key=lambda x: x['timestamp'])
        
        for i, signal in enumerate(signals_sorted):
            signal_type = signal['action']
            price = signal['price']
            confidence = signal['confidence']
            timestamp = signal['timestamp']
            
            print(f"\n📊 處理信號 #{i+1}: {signal_type}")
            print(f"   時間: {timestamp}")
            print(f"   價格: NT$ {price:,.0f}")
            print(f"   信心度: {confidence*100:.1f}%")
            
            if signal_type == 'buy' and self.position == 0:
                self.execute_buy(price, timestamp, confidence, signal['reasons'])
            elif signal_type == 'sell' and self.position == 1:
                self.execute_sell(price, timestamp, confidence, signal['reasons'])
            else:
                status = "已持倉" if self.position == 1 else "已空倉"
                print(f"   ⏭️ 跳過信號 ({status})")
    
    def execute_buy(self, price, timestamp, confidence, reasons):
        """執行買入"""
        # 使用80%資金買入
        invest_amount = self.current_balance * 0.8
        fee = invest_amount * self.transaction_fee
        net_amount = invest_amount - fee
        btc_amount = net_amount / price
        
        # 更新狀態
        self.btc_holdings = btc_amount
        self.current_balance -= invest_amount
        self.position = 1
        
        # 記錄交易
        trade = {
            'id': len(self.trades) + 1,
            'type': 'buy',
            'timestamp': timestamp,
            'price': price,
            'amount': btc_amount,
            'invest_amount': invest_amount,
            'fee': fee,
            'confidence': confidence,
            'reasons': reasons,
            'balance_after': self.current_balance
        }
        
        self.trades.append(trade)
        
        print(f"   ✅ 買入執行")
        print(f"      投資金額: NT$ {invest_amount:,.0f}")
        print(f"      BTC數量: {btc_amount:.6f}")
        print(f"      手續費: NT$ {fee:.0f}")
        print(f"      剩餘現金: NT$ {self.current_balance:,.0f}")
    
    def execute_sell(self, price, timestamp, confidence, reasons):
        """執行賣出"""
        # 計算賣出收益
        sell_amount = self.btc_holdings * price
        fee = sell_amount * self.transaction_fee
        net_amount = sell_amount - fee
        
        # 找到對應的買入交易
        buy_trade = None
        for trade in reversed(self.trades):
            if trade['type'] == 'buy':
                buy_trade = trade
                break
        
        # 計算獲利
        if buy_trade:
            profit = net_amount - buy_trade['invest_amount']
            profit_percent = (profit / buy_trade['invest_amount']) * 100
            hold_duration = timestamp - buy_trade['timestamp']
        else:
            profit = 0
            profit_percent = 0
            hold_duration = timedelta(0)
        
        # 更新狀態
        self.current_balance += net_amount
        self.btc_holdings = 0
        self.position = 0
        
        # 記錄交易
        trade = {
            'id': len(self.trades) + 1,
            'type': 'sell',
            'timestamp': timestamp,
            'price': price,
            'sell_amount': sell_amount,
            'fee': fee,
            'net_amount': net_amount,
            'profit': profit,
            'profit_percent': profit_percent,
            'confidence': confidence,
            'reasons': reasons,
            'balance_after': self.current_balance
        }
        
        self.trades.append(trade)
        
        # 創建交易對
        if buy_trade:
            trade_pair = {
                'pair_id': len(self.trade_pairs) + 1,
                'buy_trade': buy_trade,
                'sell_trade': trade,
                'profit': profit,
                'profit_percent': profit_percent,
                'hold_duration': hold_duration,
                'is_winning': profit > 0
            }
            
            self.trade_pairs.append(trade_pair)
        
        status = "✅" if profit > 0 else "❌"
        print(f"   {status} 賣出執行")
        print(f"      賣出金額: NT$ {sell_amount:,.0f}")
        print(f"      手續費: NT$ {fee:.0f}")
        print(f"      獲利: NT$ {profit:+,.0f} ({profit_percent:+.2f}%)")
        print(f"      總餘額: NT$ {self.current_balance:,.0f}")
    
    def analyze_results(self):
        """分析結果"""
        print("\n" + "=" * 60)
        print("📊 真正85%勝率策略測試結果")
        print("=" * 60)
        
        if not self.trade_pairs:
            print("❌ 沒有完整的交易對")
            return
        
        # 基本統計
        total_trades = len(self.trade_pairs)
        winning_trades = len([t for t in self.trade_pairs if t['is_winning']])
        losing_trades = total_trades - winning_trades
        
        # 勝率計算
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # 獲利統計
        profits = [t['profit'] for t in self.trade_pairs]
        total_profit = sum(profits)
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0
        
        # 總體回報
        total_return = self.current_balance - self.initial_balance
        total_return_percent = (total_return / self.initial_balance) * 100
        
        print(f"📋 交易統計:")
        print(f"   總交易對: {total_trades}")
        print(f"   獲利交易: {winning_trades}")
        print(f"   虧損交易: {losing_trades}")
        print(f"   勝率: {win_rate:.1f}%")
        
        print(f"\n💰 獲利分析:")
        print(f"   總獲利: NT$ {total_profit:+,.0f}")
        print(f"   平均每筆: NT$ {avg_profit:+,.0f}")
        print(f"   最大獲利: NT$ {max_profit:+,.0f}")
        print(f"   最大虧損: NT$ {max_loss:+,.0f}")
        
        print(f"\n📈 總體表現:")
        print(f"   初始資金: NT$ {self.initial_balance:,.0f}")
        print(f"   最終資金: NT$ {self.current_balance:,.0f}")
        print(f"   總回報: NT$ {total_return:+,.0f} ({total_return_percent:+.2f}%)")
        
        # 85%勝率驗證
        print(f"\n🎯 85%勝率驗證:")
        if win_rate >= 85:
            print(f"   🎉 恭喜！策略勝率 {win_rate:.1f}% 達到85%目標！")
            print(f"   ✅ 這確實是一個真正的85%勝率策略！")
        elif win_rate >= 75:
            print(f"   🔥 策略勝率 {win_rate:.1f}% 接近85%目標！")
            print(f"   📈 表現優秀，可能需要更多數據驗證")
        elif win_rate >= 60:
            print(f"   👍 策略勝率 {win_rate:.1f}% 表現良好")
            print(f"   🔧 還有提升空間")
        else:
            print(f"   ⚠️ 策略勝率 {win_rate:.1f}% 需要改進")
            print(f"   🛠️ 建議檢查策略參數")
        
        # 顯示交易記錄
        print(f"\n📋 交易記錄:")
        for pair in self.trade_pairs:
            status = "✅" if pair['is_winning'] else "❌"
            buy_time = pair['buy_trade']['timestamp']
            sell_time = pair['sell_trade']['timestamp']
            
            print(f"   {status} 交易對#{pair['pair_id']}: "
                  f"{buy_time.strftime('%m-%d %H:%M') if hasattr(buy_time, 'strftime') else buy_time} -> "
                  f"{sell_time.strftime('%m-%d %H:%M') if hasattr(sell_time, 'strftime') else sell_time} | "
                  f"NT$ {pair['profit']:+,.0f} ({pair['profit_percent']:+.2f}%)")
        
        # 保存結果
        self.save_results(win_rate, total_return_percent)
    
    def save_results(self, win_rate, total_return_percent):
        """保存測試結果"""
        results = {
            'test_date': datetime.now().isoformat(),
            'strategy_name': '真正的85%勝率終極優化MACD策略',
            'strategy_class': 'UltimateOptimizedVolumeEnhancedMACDSignals',
            'min_confidence': self.strategy.min_confidence,
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'total_return': self.current_balance - self.initial_balance,
            'total_return_percent': total_return_percent,
            'win_rate': win_rate,
            'total_trades': len(self.trade_pairs),
            'winning_trades': len([t for t in self.trade_pairs if t['is_winning']]),
            'losing_trades': len([t for t in self.trade_pairs if not t['is_winning']]),
            'trade_pairs': [
                {
                    'pair_id': pair['pair_id'],
                    'buy_price': pair['buy_trade']['price'],
                    'sell_price': pair['sell_trade']['price'],
                    'profit': pair['profit'],
                    'profit_percent': pair['profit_percent'],
                    'buy_confidence': pair['buy_trade']['confidence'],
                    'sell_confidence': pair['sell_trade']['confidence'],
                    'is_winning': pair['is_winning']
                }
                for pair in self.trade_pairs
            ]
        }
        
        filename = f"data/real_85_percent_strategy_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            os.makedirs('data', exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 測試結果已保存: {filename}")
        except Exception as e:
            print(f"\n❌ 保存結果失敗: {e}")

def main():
    """主函數"""
    print("🎯 真正的85%勝率策略測試")
    print("=" * 60)
    print("策略: UltimateOptimizedVolumeEnhancedMACDSignals")
    print("特點: 85%最低信心度 + 多重技術指標確認")
    
    try:
        # 初始化測試器
        tester = Real85PercentStrategyTester()
        
        # 獲取歷史數據
        df = tester.get_historical_data(days=90)  # 使用90天數據
        
        if df is None:
            print("❌ 無法獲取歷史數據，測試終止")
            return 1
        
        # 執行測試
        tester.test_strategy_performance(df)
        
        print("\n🎉 真正的85%勝率策略測試完成！")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())