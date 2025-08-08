#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 測試85%勝率策略的真實表現
使用歷史數據回測驗證策略勝率
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

class Strategy85PercentTester:
    def __init__(self):
        self.strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
        self.data_fetcher = DataFetcher()
        
        # 回測參數
        self.initial_balance = 100000  # 10萬台幣
        self.transaction_fee = 0.001   # 0.1%手續費
        
        # 交易記錄
        self.trades = []
        self.balance = self.initial_balance
        self.btc_holdings = 0
        self.position_open = False
        self.entry_price = 0
        
    def get_historical_data(self, days=30):
        """獲取歷史數據"""
        print(f"📡 獲取最近{days}天的歷史數據...")
        
        try:
            # 獲取1小時K線數據
            df = self.data_fetcher.get_kline_data('btctwd', '1h', limit=days*24)
            
            if df is None or len(df) < 100:
                print("❌ 歷史數據不足")
                return None
            
            print(f"✅ 成功獲取 {len(df)} 筆歷史數據")
            print(f"📅 時間範圍: {df.index[0]} 到 {df.index[-1]}")
            print(f"💰 價格範圍: NT$ {df['low'].min():,.0f} - NT$ {df['high'].max():,.0f}")
            
            return df
            
        except Exception as e:
            print(f"❌ 獲取歷史數據失敗: {e}")
            return None
    
    def backtest_strategy(self, df):
        """回測85%勝率策略"""
        print("\n🧪 開始回測85%勝率策略...")
        print("=" * 50)
        
        # 計算技術指標
        print("📊 計算技術指標...")
        df_with_indicators = self.strategy.calculate_indicators(df)
        
        # 檢測所有信號
        print("🔍 檢測交易信號...")
        signals = self.strategy.detect_signals(df_with_indicators)
        
        print(f"📋 檢測到 {len(signals)} 個信號")
        
        if len(signals) == 0:
            print("⚠️ 沒有檢測到符合85%標準的信號")
            print("   這可能表示:")
            print("   1. 策略非常保守，只在最佳時機出手")
            print("   2. 最近市場條件不符合策略標準")
            print("   3. 需要更長的歷史數據來測試")
            return
        
        # 模擬交易
        print("\n💰 開始模擬交易...")
        
        for i, signal in enumerate(signals):
            self.process_signal(signal, i+1)
        
        # 如果還有持倉，按最後價格平倉
        if self.position_open:
            last_price = df['close'].iloc[-1]
            self.close_position(last_price, len(signals)+1, "回測結束強制平倉")
        
        # 分析結果
        self.analyze_results()
    
    def process_signal(self, signal, signal_num):
        """處理交易信號"""
        signal_type = signal['action']
        price = signal['price']
        confidence = signal['confidence']
        timestamp = signal.get('timestamp', 'Unknown')
        
        print(f"\n📊 信號 #{signal_num}: {signal_type}")
        print(f"   價格: NT$ {price:,.0f}")
        print(f"   信心度: {confidence*100:.1f}%")
        print(f"   時間: {timestamp}")
        
        if signal_type == 'buy' and not self.position_open:
            self.open_position(price, signal_num, confidence)
        elif signal_type == 'sell' and self.position_open:
            self.close_position(price, signal_num, confidence)
        else:
            print(f"   ⏭️ 跳過信號 (當前狀態不符合)")
    
    def open_position(self, price, signal_num, confidence):
        """開倉買入"""
        if self.balance < 1000:  # 最小交易金額
            print(f"   ❌ 餘額不足，無法買入")
            return
        
        # 計算買入數量 (使用80%資金)
        invest_amount = self.balance * 0.8
        fee = invest_amount * self.transaction_fee
        net_amount = invest_amount - fee
        btc_amount = net_amount / price
        
        # 執行買入
        self.btc_holdings = btc_amount
        self.balance -= invest_amount
        self.position_open = True
        self.entry_price = price
        
        # 記錄交易
        trade = {
            'signal_num': signal_num,
            'type': 'buy',
            'price': price,
            'amount': btc_amount,
            'invest_amount': invest_amount,
            'fee': fee,
            'confidence': confidence,
            'balance_after': self.balance,
            'timestamp': datetime.now().isoformat()
        }
        self.trades.append(trade)
        
        print(f"   ✅ 買入執行")
        print(f"      投資金額: NT$ {invest_amount:,.0f}")
        print(f"      BTC數量: {btc_amount:.6f}")
        print(f"      手續費: NT$ {fee:.0f}")
        print(f"      剩餘現金: NT$ {self.balance:,.0f}")
    
    def close_position(self, price, signal_num, confidence):
        """平倉賣出"""
        if not self.position_open or self.btc_holdings <= 0:
            print(f"   ❌ 無持倉，無法賣出")
            return
        
        # 計算賣出金額
        sell_amount = self.btc_holdings * price
        fee = sell_amount * self.transaction_fee
        net_amount = sell_amount - fee
        
        # 計算獲利
        profit = net_amount - (self.btc_holdings * self.entry_price)
        profit_percent = (profit / (self.btc_holdings * self.entry_price)) * 100
        
        # 執行賣出
        self.balance += net_amount
        self.btc_holdings = 0
        self.position_open = False
        
        # 記錄交易
        trade = {
            'signal_num': signal_num,
            'type': 'sell',
            'price': price,
            'amount': self.btc_holdings,
            'sell_amount': sell_amount,
            'fee': fee,
            'confidence': confidence if isinstance(confidence, float) else 0.85,
            'profit': profit,
            'profit_percent': profit_percent,
            'entry_price': self.entry_price,
            'balance_after': self.balance,
            'timestamp': datetime.now().isoformat()
        }
        self.trades.append(trade)
        
        print(f"   ✅ 賣出執行")
        print(f"      賣出金額: NT$ {sell_amount:,.0f}")
        print(f"      手續費: NT$ {fee:.0f}")
        print(f"      獲利: NT$ {profit:,.0f} ({profit_percent:+.2f}%)")
        print(f"      總餘額: NT$ {self.balance:,.0f}")
    
    def analyze_results(self):
        """分析回測結果"""
        print("\n" + "=" * 50)
        print("📊 回測結果分析")
        print("=" * 50)
        
        if len(self.trades) == 0:
            print("❌ 沒有執行任何交易")
            return
        
        # 基本統計
        buy_trades = [t for t in self.trades if t['type'] == 'buy']
        sell_trades = [t for t in self.trades if t['type'] == 'sell']
        
        print(f"📋 交易統計:")
        print(f"   總信號數: {len(self.trades)}")
        print(f"   買入次數: {len(buy_trades)}")
        print(f"   賣出次數: {len(sell_trades)}")
        print(f"   完整交易對: {min(len(buy_trades), len(sell_trades))}")
        
        # 獲利分析
        if sell_trades:
            profits = [t['profit'] for t in sell_trades]
            profit_percents = [t['profit_percent'] for t in sell_trades]
            
            winning_trades = [p for p in profits if p > 0]
            losing_trades = [p for p in profits if p <= 0]
            
            win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
            
            print(f"\n💰 獲利分析:")
            print(f"   勝率: {win_rate:.1f}% ({len(winning_trades)}/{len(sell_trades)})")
            print(f"   平均獲利: NT$ {np.mean(profits):,.0f}")
            print(f"   總獲利: NT$ {sum(profits):,.0f}")
            print(f"   最大獲利: NT$ {max(profits):,.0f} ({max(profit_percents):+.2f}%)")
            print(f"   最大虧損: NT$ {min(profits):,.0f} ({min(profit_percents):+.2f}%)")
            
            # 85%勝率驗證
            print(f"\n🎯 85%勝率驗證:")
            if win_rate >= 85:
                print(f"   ✅ 策略勝率 {win_rate:.1f}% >= 85% 目標")
                print(f"   🎉 策略達到預期表現！")
            elif win_rate >= 75:
                print(f"   ⚠️ 策略勝率 {win_rate:.1f}% 接近85%目標")
                print(f"   📈 表現良好，可能需要更多數據驗證")
            else:
                print(f"   ❌ 策略勝率 {win_rate:.1f}% 低於85%目標")
                print(f"   🔧 可能需要調整策略參數")
        
        # 總體表現
        total_return = self.balance - self.initial_balance
        total_return_percent = (total_return / self.initial_balance) * 100
        
        print(f"\n📈 總體表現:")
        print(f"   初始資金: NT$ {self.initial_balance:,.0f}")
        print(f"   最終餘額: NT$ {self.balance:,.0f}")
        print(f"   總獲利: NT$ {total_return:,.0f} ({total_return_percent:+.2f}%)")
        
        if total_return > 0:
            print(f"   🎉 策略獲利！")
        else:
            print(f"   📉 策略虧損")
        
        # 保存詳細結果
        self.save_results(win_rate, total_return_percent)
    
    def save_results(self, win_rate, total_return_percent):
        """保存測試結果"""
        results = {
            'test_date': datetime.now().isoformat(),
            'strategy_name': '85%勝率終極優化MACD策略',
            'initial_balance': self.initial_balance,
            'final_balance': self.balance,
            'total_return': self.balance - self.initial_balance,
            'total_return_percent': total_return_percent,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'buy_trades': len([t for t in self.trades if t['type'] == 'buy']),
            'sell_trades': len([t for t in self.trades if t['type'] == 'sell']),
            'trades': self.trades
        }
        
        filename = f"data/85_percent_strategy_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            os.makedirs('data', exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 測試結果已保存: {filename}")
        except Exception as e:
            print(f"\n❌ 保存結果失敗: {e}")

def main():
    """主函數"""
    print("🧪 85%勝率策略回測系統")
    print("=" * 50)
    
    try:
        # 初始化測試器
        tester = Strategy85PercentTester()
        
        # 獲取歷史數據 (測試最近7天)
        df = tester.get_historical_data(days=7)
        
        if df is None:
            print("❌ 無法獲取歷史數據，測試終止")
            return 1
        
        # 執行回測
        tester.backtest_strategy(df)
        
        print("\n🎉 85%勝率策略回測完成！")
        print("\n💡 重要說明:")
        print("   • 這是基於歷史數據的回測")
        print("   • 實際交易結果可能不同")
        print("   • 策略保守，信號較少是正常的")
        print("   • 85%勝率是長期目標，短期可能有波動")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 回測過程發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    exit(main())