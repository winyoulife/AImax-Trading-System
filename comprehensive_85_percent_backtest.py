#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 全面85%勝率策略長期回測系統
使用大量歷史數據驗證多時間框架MACD策略的真實勝率
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import asyncio

# 添加src目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data.live_macd_service import LiveMACDService
from core.multi_timeframe_trading_signals import detect_multi_timeframe_trading_signals

class Comprehensive85PercentBacktester:
    def __init__(self):
        self.service = None
        self.initial_balance = 1000000  # 100萬台幣
        self.current_balance = self.initial_balance
        self.btc_holdings = 0
        self.transaction_fee = 0.001  # 0.1%手續費
        
        # 交易記錄
        self.all_trades = []
        self.trade_pairs = []
        self.performance_stats = {}
        
    async def get_comprehensive_historical_data(self):
        """獲取全面的歷史數據"""
        print("📡 獲取全面歷史數據...")
        print("   這可能需要幾分鐘時間，請耐心等待...")
        
        self.service = LiveMACDService()
        
        try:
            # 獲取更多歷史數據
            print("   🕐 獲取1小時數據 (1000筆)...")
            hourly_klines = await self.service._fetch_klines("btctwd", "60", 1000)
            if hourly_klines is None:
                print("   ❌ 無法獲取1小時數據")
                return None, None
            
            hourly_df = self.service._calculate_macd(hourly_klines, 12, 26, 9)
            if hourly_df is None:
                print("   ❌ 無法計算1小時MACD")
                return None, None
            
            print(f"   ✅ 1小時數據: {len(hourly_df)} 筆")
            
            # 獲取其他時間框架數據
            timeframe_dfs = {}
            
            # 30分鐘數據 (實際用作1小時MA數據)
            print("   🕐 獲取30分鐘數據 (2000筆)...")
            thirty_klines = await self.service._fetch_klines("btctwd", "30", 2000)
            if thirty_klines is not None:
                thirty_df = self.service._calculate_macd(thirty_klines, 12, 26, 9)
                if thirty_df is not None:
                    # 添加MA指標
                    thirty_df['ma9'] = thirty_df['close'].rolling(window=9).mean()
                    thirty_df['ma25'] = thirty_df['close'].rolling(window=25).mean()
                    thirty_df['ma99'] = thirty_df['close'].rolling(window=99).mean()
                    
                    timeframe_dfs['30m'] = thirty_df.tail(1000).reset_index(drop=True)
                    print(f"   ✅ 30分鐘數據: {len(timeframe_dfs['30m'])} 筆")
            
            # 15分鐘數據
            print("   🕐 獲取15分鐘數據 (2000筆)...")
            fifteen_klines = await self.service._fetch_klines("btctwd", "15", 2000)
            if fifteen_klines is not None:
                fifteen_df = self.service._calculate_macd(fifteen_klines, 12, 26, 9)
                if fifteen_df is not None:
                    timeframe_dfs['15m'] = fifteen_df.tail(1000).reset_index(drop=True)
                    print(f"   ✅ 15分鐘數據: {len(timeframe_dfs['15m'])} 筆")
            
            # 5分鐘數據
            print("   🕐 獲取5分鐘數據 (2000筆)...")
            five_klines = await self.service._fetch_klines("btctwd", "5", 2000)
            if five_klines is not None:
                five_df = self.service._calculate_macd(five_klines, 12, 26, 9)
                if five_df is not None:
                    timeframe_dfs['5m'] = five_df.tail(1000).reset_index(drop=True)
                    print(f"   ✅ 5分鐘數據: {len(timeframe_dfs['5m'])} 筆")
            
            await self.service.close()
            
            print("✅ 歷史數據獲取完成！")
            return hourly_df, timeframe_dfs
            
        except Exception as e:
            print(f"❌ 獲取歷史數據失敗: {e}")
            if self.service:
                await self.service.close()
            return None, None
    
    def execute_comprehensive_backtest(self, hourly_df, timeframe_dfs):
        """執行全面回測"""
        print("\n🧪 開始執行全面回測...")
        print("=" * 60)
        
        # 執行多時間框架信號檢測
        print("🎯 執行多時間框架信號檢測...")
        signals_dict, statistics, tracker = detect_multi_timeframe_trading_signals(
            hourly_df.tail(800).reset_index(drop=True),  # 使用最近800個1小時數據點
            timeframe_dfs
        )
        
        print(f"✅ 信號檢測完成")
        
        # 分析每個時間框架的信號
        total_signals = 0
        for timeframe, signals_df in signals_dict.items():
            if not signals_df.empty:
                signal_count = len(signals_df)
                buy_count = len(signals_df[signals_df['signal_type'] == 'buy'])
                sell_count = len(signals_df[signals_df['signal_type'] == 'sell'])
                
                print(f"   {timeframe}: {signal_count} 個信號 (買:{buy_count}, 賣:{sell_count})")
                total_signals += signal_count
        
        print(f"   總信號數: {total_signals}")
        
        # 模擬交易執行
        self.simulate_trading(signals_dict)
        
        # 計算績效
        self.calculate_comprehensive_performance()
        
        return signals_dict, statistics, tracker
    
    def simulate_trading(self, signals_dict):
        """模擬交易執行"""
        print("\n💰 開始模擬交易執行...")
        
        # 收集所有交易信號並按時間排序
        all_signals = []
        
        for timeframe, signals_df in signals_dict.items():
            if signals_df.empty:
                continue
                
            for _, signal in signals_df.iterrows():
                if signal['signal_type'] in ['buy', 'sell'] and signal.get('trade_sequence', 0) > 0:
                    all_signals.append({
                        'datetime': signal['datetime'],
                        'price': signal['close'],
                        'type': signal['signal_type'],
                        'timeframe': timeframe,
                        'sequence': signal['trade_sequence'],
                        'signal_info': signal.get('hourly_signal', '')
                    })
        
        # 按時間排序
        all_signals.sort(key=lambda x: x['datetime'])
        
        print(f"   收集到 {len(all_signals)} 個有效交易信號")
        
        # 執行交易
        position = 0  # 0=空倉, 1=持倉
        entry_price = 0
        entry_time = None
        trade_count = 0
        
        for signal in all_signals:
            signal_type = signal['type']
            price = signal['price']
            timestamp = signal['datetime']
            timeframe = signal['timeframe']
            
            if signal_type == 'buy' and position == 0:
                # 執行買入
                position = 1
                entry_price = price
                entry_time = timestamp
                trade_count += 1
                
                trade_record = {
                    'trade_id': trade_count,
                    'type': 'buy',
                    'timestamp': timestamp,
                    'price': price,
                    'timeframe': timeframe,
                    'balance_before': self.current_balance,
                    'signal_info': signal['signal_info']
                }
                
                # 計算買入後的資金變化
                invest_amount = self.current_balance * 0.8  # 使用80%資金
                fee = invest_amount * self.transaction_fee
                self.btc_holdings = (invest_amount - fee) / price
                self.current_balance -= invest_amount
                
                trade_record['invest_amount'] = invest_amount
                trade_record['fee'] = fee
                trade_record['btc_amount'] = self.btc_holdings
                trade_record['balance_after'] = self.current_balance
                
                self.all_trades.append(trade_record)
                
                print(f"   ✅ 買入 #{trade_count}: {price:,.0f} TWD ({timeframe}) - 投資 {invest_amount:,.0f}")
                
            elif signal_type == 'sell' and position == 1:
                # 執行賣出
                position = 0
                
                # 計算賣出收益
                sell_amount = self.btc_holdings * price
                fee = sell_amount * self.transaction_fee
                net_amount = sell_amount - fee
                
                # 計算獲利
                profit = net_amount - (self.btc_holdings * entry_price)
                profit_percent = (profit / (self.btc_holdings * entry_price)) * 100
                
                # 計算持有時間
                hold_duration = timestamp - entry_time
                
                self.current_balance += net_amount
                
                trade_record = {
                    'trade_id': trade_count,
                    'type': 'sell',
                    'timestamp': timestamp,
                    'price': price,
                    'timeframe': timeframe,
                    'sell_amount': sell_amount,
                    'fee': fee,
                    'net_amount': net_amount,
                    'profit': profit,
                    'profit_percent': profit_percent,
                    'hold_duration': hold_duration,
                    'balance_after': self.current_balance,
                    'signal_info': signal['signal_info']
                }
                
                self.all_trades.append(trade_record)
                
                # 創建交易對記錄
                trade_pair = {
                    'pair_id': len(self.trade_pairs) + 1,
                    'buy_time': entry_time,
                    'sell_time': timestamp,
                    'buy_price': entry_price,
                    'sell_price': price,
                    'profit': profit,
                    'profit_percent': profit_percent,
                    'hold_duration': hold_duration,
                    'timeframe': timeframe,
                    'is_winning': profit > 0
                }
                
                self.trade_pairs.append(trade_pair)
                
                status = "✅" if profit > 0 else "❌"
                print(f"   {status} 賣出 #{trade_count}: {price:,.0f} TWD ({timeframe}) - 獲利 {profit:+,.0f} ({profit_percent:+.2f}%)")
                
                # 重置持倉狀態
                self.btc_holdings = 0
                entry_price = 0
                entry_time = None
        
        print(f"   模擬交易完成，共執行 {len(self.all_trades)} 筆交易")
    
    def calculate_comprehensive_performance(self):
        """計算全面績效分析"""
        print("\n📊 計算全面績效分析...")
        print("=" * 60)
        
        if not self.trade_pairs:
            print("❌ 沒有完整的交易對，無法計算績效")
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
        
        winning_profits = [t['profit'] for t in self.trade_pairs if t['is_winning']]
        losing_profits = [t['profit'] for t in self.trade_pairs if not t['is_winning']]
        
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0
        
        avg_winning_profit = sum(winning_profits) / len(winning_profits) if winning_profits else 0
        avg_losing_loss = sum(losing_profits) / len(losing_profits) if losing_profits else 0
        
        # 總體回報
        total_return = self.current_balance - self.initial_balance
        total_return_percent = (total_return / self.initial_balance) * 100
        
        # 持有時間分析
        hold_durations = [t['hold_duration'].total_seconds() / 3600 for t in self.trade_pairs]  # 轉換為小時
        avg_hold_time = sum(hold_durations) / len(hold_durations) if hold_durations else 0
        
        # 時間框架分析
        timeframe_stats = {}
        for timeframe in ['1h', '30m', '15m', '5m']:
            tf_trades = [t for t in self.trade_pairs if t['timeframe'] == timeframe]
            if tf_trades:
                tf_winning = len([t for t in tf_trades if t['is_winning']])
                tf_win_rate = (tf_winning / len(tf_trades)) * 100
                tf_profit = sum([t['profit'] for t in tf_trades])
                
                timeframe_stats[timeframe] = {
                    'trades': len(tf_trades),
                    'winning': tf_winning,
                    'win_rate': tf_win_rate,
                    'profit': tf_profit
                }
        
        # 保存績效統計
        self.performance_stats = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'avg_winning_profit': avg_winning_profit,
            'avg_losing_loss': avg_losing_loss,
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'avg_hold_time_hours': avg_hold_time,
            'timeframe_stats': timeframe_stats,
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance
        }
        
        # 顯示結果
        self.display_comprehensive_results()
    
    def display_comprehensive_results(self):
        """顯示全面結果"""
        stats = self.performance_stats
        
        print("🎯 85%勝率策略全面回測結果")
        print("=" * 60)
        
        print(f"📊 基本統計:")
        print(f"   總交易數: {stats['total_trades']}")
        print(f"   獲利交易: {stats['winning_trades']}")
        print(f"   虧損交易: {stats['losing_trades']}")
        print(f"   勝率: {stats['win_rate']:.1f}%")
        
        print(f"\n💰 獲利分析:")
        print(f"   總獲利: {stats['total_profit']:+,.0f} TWD")
        print(f"   平均每筆: {stats['avg_profit']:+,.0f} TWD")
        print(f"   最大獲利: {stats['max_profit']:+,.0f} TWD")
        print(f"   最大虧損: {stats['max_loss']:+,.0f} TWD")
        print(f"   平均獲利交易: {stats['avg_winning_profit']:+,.0f} TWD")
        print(f"   平均虧損交易: {stats['avg_losing_loss']:+,.0f} TWD")
        
        print(f"\n📈 總體表現:")
        print(f"   初始資金: {stats['initial_balance']:,.0f} TWD")
        print(f"   最終資金: {stats['final_balance']:,.0f} TWD")
        print(f"   總回報: {stats['total_return']:+,.0f} TWD ({stats['total_return_percent']:+.2f}%)")
        print(f"   平均持有時間: {stats['avg_hold_time_hours']:.1f} 小時")
        
        print(f"\n🕐 時間框架分析:")
        for timeframe, tf_stats in stats['timeframe_stats'].items():
            print(f"   {timeframe}: {tf_stats['trades']} 筆交易, "
                  f"勝率 {tf_stats['win_rate']:.1f}%, "
                  f"獲利 {tf_stats['profit']:+,.0f} TWD")
        
        # 85%勝率驗證
        print(f"\n🎯 85%勝率驗證:")
        if stats['win_rate'] >= 85:
            print(f"   🎉 恭喜！策略勝率 {stats['win_rate']:.1f}% 達到85%目標！")
            print(f"   ✅ 這確實是一個真正的85%勝率策略！")
        elif stats['win_rate'] >= 75:
            print(f"   🔥 策略勝率 {stats['win_rate']:.1f}% 接近85%目標！")
            print(f"   📈 表現優秀，可能需要更多數據或調整參數")
        elif stats['win_rate'] >= 60:
            print(f"   👍 策略勝率 {stats['win_rate']:.1f}% 表現良好")
            print(f"   🔧 還有提升空間，可以優化策略參數")
        else:
            print(f"   ⚠️ 策略勝率 {stats['win_rate']:.1f}% 需要改進")
            print(f"   🛠️ 建議重新檢視策略邏輯")
        
        # 顯示最近的交易記錄
        print(f"\n📋 最近10筆交易記錄:")
        for trade in self.trade_pairs[-10:]:
            status = "✅" if trade['is_winning'] else "❌"
            print(f"   {status} 交易#{trade['pair_id']}: "
                  f"{trade['buy_time'].strftime('%m-%d %H:%M')} -> "
                  f"{trade['sell_time'].strftime('%m-%d %H:%M')} | "
                  f"{trade['profit']:+,.0f} TWD ({trade['profit_percent']:+.2f}%) "
                  f"[{trade['timeframe']}]")
    
    def save_results(self):
        """保存結果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存績效統計
        stats_filename = f"data/comprehensive_85_percent_backtest_{timestamp}.json"
        
        try:
            os.makedirs('data', exist_ok=True)
            
            # 準備保存數據
            save_data = {
                'test_date': datetime.now().isoformat(),
                'strategy_name': '85%勝率多時間框架MACD策略',
                'performance_stats': self.performance_stats,
                'trade_pairs': [
                    {
                        **pair,
                        'buy_time': pair['buy_time'].isoformat(),
                        'sell_time': pair['sell_time'].isoformat(),
                        'hold_duration': str(pair['hold_duration'])
                    }
                    for pair in self.trade_pairs
                ],
                'all_trades': [
                    {
                        **trade,
                        'timestamp': trade['timestamp'].isoformat(),
                        'hold_duration': str(trade.get('hold_duration', '')) if trade.get('hold_duration') else ''
                    }
                    for trade in self.all_trades
                ]
            }
            
            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 回測結果已保存: {stats_filename}")
            
        except Exception as e:
            print(f"\n❌ 保存結果失敗: {e}")

async def main():
    """主函數"""
    print("🎯 85%勝率策略全面回測系統")
    print("=" * 60)
    print("這將使用大量歷史數據來驗證策略的真實勝率")
    print("預計需要5-10分鐘時間，請耐心等待...")
    
    try:
        # 初始化回測器
        backtester = Comprehensive85PercentBacktester()
        
        # 獲取歷史數據
        hourly_df, timeframe_dfs = await backtester.get_comprehensive_historical_data()
        
        if hourly_df is None or not timeframe_dfs:
            print("❌ 無法獲取足夠的歷史數據，回測終止")
            return 1
        
        # 執行回測
        signals_dict, statistics, tracker = backtester.execute_comprehensive_backtest(hourly_df, timeframe_dfs)
        
        # 保存結果
        backtester.save_results()
        
        print("\n🎉 全面回測完成！")
        
        # 最終總結
        win_rate = backtester.performance_stats.get('win_rate', 0)
        if win_rate >= 85:
            print(f"🏆 恭喜！你的策略確實達到了85%的勝率目標！")
            print(f"📈 這證明了多時間框架MACD策略的有效性！")
        else:
            print(f"📊 策略勝率為 {win_rate:.1f}%，雖然未達85%但仍有價值")
            print(f"🔧 可以考慮調整參數或增加更多確認條件")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 回測過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # 運行異步主函數
    exit(asyncio.run(main()))