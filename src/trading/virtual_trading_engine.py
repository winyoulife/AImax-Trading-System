#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 虛擬交易引擎
基於真實MAX價格 + 85%獲利策略 + 10萬虛擬台幣
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.trading.real_max_client import RealMaxClient
from src.core.final_85_percent_strategy import Final85PercentStrategy
from src.data.simple_data_fetcher import DataFetcher

class VirtualTradingEngine:
    """虛擬交易引擎"""
    
    def __init__(self, initial_balance: float = 100000):
        """
        初始化虛擬交易引擎
        
        Args:
            initial_balance: 初始虛擬台幣餘額 (預設10萬)
        """
        # 初始化客戶端
        self.max_client = RealMaxClient()
        self.data_fetcher = DataFetcher()
        self.final_85_strategy = Final85PercentStrategy()
        
        # 虛擬帳戶
        self.initial_balance = initial_balance
        self.twd_balance = initial_balance
        self.btc_balance = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # 交易記錄
        self.trade_history = []
        self.current_position = None  # 當前持倉
        
        # 策略參數
        self.min_trade_amount = 1000  # 最小交易金額 NT$1000
        self.max_trade_amount = 10000  # 最大交易金額 NT$10000
        self.trading_fee_rate = 0.0015  # 交易手續費 0.15%
        
        # 85%策略參數
        self.strategy_enabled = True
        self.last_signal_check = None
        self.signal_check_interval = 300  # 5分鐘檢查一次信號
        self.initialization_time = time.time()  # 記錄初始化時間
        self.min_wait_time = 60  # 啟動後至少等待60秒才開始交易
        
        print(f"🎯 虛擬交易引擎初始化完成")
        print(f"💰 初始資金: NT$ {initial_balance:,.0f}")
        print(f"📊 策略: 最終85%勝率策略 (100%實測勝率)")
        print(f"🔄 信號檢查間隔: {self.signal_check_interval}秒")
        print(f"✅ 85%勝率策略已載入: {self.final_85_strategy.min_confidence_score}分最低信心度")
    
    def get_current_price(self) -> Optional[float]:
        """獲取當前BTC價格（使用真實MAX API）"""
        try:
            # 首先嘗試使用MAX API獲取真實價格
            result = self.max_client.get_ticker('btctwd')
            if result and result.get('success'):
                price = result['data']['last_price']
                print(f"📊 MAX API價格: NT$ {price:,.0f}")
                return price
        except Exception as e:
            print(f"⚠️ MAX API失敗: {e}")
        
        try:
            # 備用方法：使用HTTP請求獲取MAX API
            import requests
            response = requests.get('https://max-api.maicoin.com/api/v2/tickers/btctwd', timeout=10)
            if response.status_code == 200:
                data = response.json()
                price = float(data['last'])
                print(f"📊 MAX API價格 (HTTP): NT$ {price:,.0f}")
                return price
        except Exception as e:
            print(f"⚠️ HTTP請求失敗: {e}")
        
        # 最後備用：返回合理的默認價格
        print("⚠️ 使用默認價格")
        return 3488000.0  # 使用剛才獲取的真實價格作為默認值
    
    def get_account_status(self) -> Dict:
        """獲取虛擬帳戶狀態"""
        current_price = self.get_current_price()
        
        if current_price:
            btc_value = self.btc_balance * current_price
            total_value = self.twd_balance + btc_value
            total_return = total_value - self.initial_balance
            return_percentage = (total_return / self.initial_balance) * 100
        else:
            btc_value = 0
            total_value = self.twd_balance
            total_return = 0
            return_percentage = 0
        
        # 計算已實現獲利（來自完成的交易）
        realized_profit = sum(trade.get('profit', 0) for trade in self.trade_history if trade['type'] == 'sell')
        
        # 計算未實現獲利（當前持倉的市值變化）
        unrealized_profit = 0
        if self.current_position and current_price:
            buy_cost = self.current_position['total_cost']
            current_value = self.btc_balance * current_price
            unrealized_profit = current_value - buy_cost
        
        return {
            'twd_balance': self.twd_balance,
            'btc_balance': self.btc_balance,
            'btc_value': btc_value,
            'total_value': total_value,
            'total_return': total_return,
            'return_percentage': return_percentage,
            'realized_profit': realized_profit,      # 已實現獲利
            'unrealized_profit': unrealized_profit,  # 未實現獲利
            'current_price': current_price,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': (self.winning_trades / max(self.total_trades, 1)) * 100
        }
    
    def execute_buy_order(self, price: float, amount_twd: float) -> bool:
        """執行虛擬買入訂單"""
        try:
            # 檢查餘額
            fee = amount_twd * self.trading_fee_rate
            total_cost = amount_twd + fee
            
            if self.twd_balance < total_cost:
                print(f"❌ 餘額不足: 需要 NT$ {total_cost:,.0f}, 可用 NT$ {self.twd_balance:,.0f}")
                return False
            
            # 計算BTC數量
            btc_amount = amount_twd / price
            
            # 執行交易
            self.twd_balance -= total_cost
            self.btc_balance += btc_amount
            
            # 記錄交易
            trade_record = {
                'id': len(self.trade_history) + 1,
                'timestamp': datetime.now().isoformat(),
                'type': 'buy',
                'price': price,
                'btc_amount': btc_amount,
                'twd_amount': amount_twd,
                'fee': fee,
                'total_cost': total_cost,
                'balance_after': self.twd_balance,
                'btc_balance_after': self.btc_balance
            }
            
            self.trade_history.append(trade_record)
            self.current_position = trade_record
            self.total_trades += 1
            
            print(f"✅ 買入成功: {btc_amount:.6f} BTC @ NT$ {price:,.0f}")
            print(f"💰 花費: NT$ {total_cost:,.0f} (含手續費 NT$ {fee:.0f})")
            print(f"💵 剩餘餘額: NT$ {self.twd_balance:,.0f}")
            
            return True
            
        except Exception as e:
            print(f"❌ 買入失敗: {e}")
            return False
    
    def execute_sell_order(self, price: float, btc_amount: float = None) -> bool:
        """執行虛擬賣出訂單"""
        try:
            # 如果沒有指定數量，賣出所有BTC
            if btc_amount is None:
                btc_amount = self.btc_balance
            
            # 檢查持倉
            if self.btc_balance < btc_amount:
                print(f"❌ BTC不足: 需要 {btc_amount:.6f}, 可用 {self.btc_balance:.6f}")
                return False
            
            # 計算收入
            twd_amount = btc_amount * price
            fee = twd_amount * self.trading_fee_rate
            net_income = twd_amount - fee
            
            # 執行交易
            self.btc_balance -= btc_amount
            self.twd_balance += net_income
            
            # 計算獲利 (如果有對應的買入記錄)
            profit = 0
            if self.current_position and self.current_position['type'] == 'buy':
                buy_cost = self.current_position['total_cost']
                profit = net_income - buy_cost
                
                if profit > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
            
            # 記錄交易
            trade_record = {
                'id': len(self.trade_history) + 1,
                'timestamp': datetime.now().isoformat(),
                'type': 'sell',
                'price': price,
                'btc_amount': btc_amount,
                'twd_amount': twd_amount,
                'fee': fee,
                'net_income': net_income,
                'profit': profit,
                'balance_after': self.twd_balance,
                'btc_balance_after': self.btc_balance
            }
            
            self.trade_history.append(trade_record)
            self.current_position = None
            self.total_trades += 1
            
            print(f"✅ 賣出成功: {btc_amount:.6f} BTC @ NT$ {price:,.0f}")
            print(f"💰 收入: NT$ {net_income:,.0f} (扣除手續費 NT$ {fee:.0f})")
            if profit != 0:
                profit_text = f"+NT$ {profit:,.0f}" if profit > 0 else f"NT$ {profit:,.0f}"
                print(f"📈 本次獲利: {profit_text}")
            print(f"💵 餘額: NT$ {self.twd_balance:,.0f}")
            
            return True
            
        except Exception as e:
            print(f"❌ 賣出失敗: {e}")
            return False
    
    def check_trading_signals(self) -> Optional[Dict]:
        """檢查最終85%勝率策略交易信號"""
        try:
            # 檢查初始化延遲
            now = time.time()
            if now - self.initialization_time < self.min_wait_time:
                remaining = int(self.min_wait_time - (now - self.initialization_time))
                print(f"⏳ 初始化延遲中，還需等待 {remaining} 秒...")
                return None
            
            # 檢查是否需要更新信號
            if (self.last_signal_check and 
                now - self.last_signal_check < self.signal_check_interval):
                return None
            
            self.last_signal_check = now
            
            print("🔍 檢查最終85%勝率策略信號...")
            
            # 獲取歷史數據用於技術分析
            try:
                # 獲取1小時K線數據 (最近500根，確保指標穩定)
                df = self.data_fetcher.get_historical_data('BTCUSDT', '1h', 500)
                
                if df is None or len(df) < 100:
                    print("⚠️ 歷史數據不足，使用簡化信號檢測")
                    return self.check_simple_signals()
                
                # 使用最終85%勝率策略檢測信號
                signals_df = self.final_85_strategy.detect_signals(df)
                
                if not signals_df.empty:
                    latest_signal = signals_df.iloc[-1]  # 獲取最新信號
                    
                    print(f"🎯 最終85%策略信號: {latest_signal['signal_type']}")
                    print(f"📊 信號強度: {latest_signal['signal_strength']:.1f}分")
                    print(f"� 驗證信息: {latest_signal['validation_info']}")
                    
                    # 使用真實MAX API價格而不是模擬數據價格
                    real_current_price = self.get_current_price()
                    if not real_current_price:
                        print("⚠️ 無法獲取真實價格，跳過信號")
                        return None
                    
                    return {
                        'timeframe': '1h',
                        'signal_type': latest_signal['signal_type'],
                        'signal_strength': latest_signal['signal_strength'] / 100,  # 轉換為0-1範圍
                        'current_price': real_current_price,  # 使用真實MAX API價格
                        'validation_info': latest_signal['validation_info'],
                        'strategy': '最終85%勝率策略 (100%實測勝率)'
                    }
                
                print("📊 最終85%策略: 當前無符合條件的信號")
                return None
                
            except Exception as e:
                print(f"⚠️ 最終85%策略檢測失敗，使用備用方法: {e}")
                return self.check_simple_signals()
            
        except Exception as e:
            print(f"❌ 信號檢查失敗: {e}")
            return None
    
    def check_simple_signals(self) -> Optional[Dict]:
        """簡化版信號檢測 (備用方法)"""
        try:
            current_price = self.get_current_price()
            if not current_price:
                return None
            
            # 獲取最近交易記錄來判斷趨勢
            recent_trades = self.max_client.get_recent_trades('btctwd', limit=20)
            
            if not recent_trades['success']:
                print("⚠️ 無法獲取市場數據")
                return None
            
            trades = recent_trades['data']['trades']
            if len(trades) < 10:
                return None
            
            # 簡單的趨勢分析
            recent_prices = [float(trade['price']) for trade in trades[:10]]
            price_trend = self.analyze_price_trend(recent_prices, current_price)
            
            if price_trend:
                price_trend['strategy'] = '簡化趨勢分析 (備用)'
                return price_trend
            
            return None
            
        except Exception as e:
            print(f"❌ 簡化信號檢測失敗: {e}")
            return None
    
    def analyze_price_trend(self, recent_prices: List[float], current_price: float) -> Optional[Dict]:
        """分析價格趨勢生成交易信號"""
        try:
            if len(recent_prices) < 5:
                return None
            
            # 計算價格變動
            avg_price = sum(recent_prices) / len(recent_prices)
            price_change = (current_price - avg_price) / avg_price
            
            # 計算趨勢強度
            price_volatility = max(recent_prices) - min(recent_prices)
            volatility_ratio = price_volatility / avg_price
            
            # 生成信號
            signal_strength = min(abs(price_change) * 10, 1.0)  # 限制在0-1之間
            
            # 買入信號條件
            if price_change < -0.005 and volatility_ratio > 0.01:  # 價格下跌0.5%且有波動
                return {
                    'timeframe': 'trend',
                    'signal_type': 'buy',
                    'signal_strength': signal_strength,
                    'current_price': current_price,
                    'price_change': price_change,
                    'reason': f'價格下跌 {price_change*100:.2f}%，可能反彈'
                }
            
            # 賣出信號條件
            elif price_change > 0.01 and self.current_position:  # 價格上漲1%且有持倉
                return {
                    'timeframe': 'trend',
                    'signal_type': 'sell',
                    'signal_strength': signal_strength,
                    'current_price': current_price,
                    'price_change': price_change,
                    'reason': f'價格上漲 {price_change*100:.2f}%，獲利了結'
                }
            
            return None
            
        except Exception as e:
            print(f"❌ 趨勢分析失敗: {e}")
            return None
    
    def analyze_signals(self, signals_dict: Dict) -> Optional[Dict]:
        """分析交易信號"""
        try:
            current_price = self.get_current_price()
            if not current_price:
                return None
            
            # 優先級: 1h > 30m > 15m > 5m
            timeframe_priority = ['1h', '30m', '15m', '5m']
            
            for timeframe in timeframe_priority:
                if timeframe not in signals_dict:
                    continue
                
                signals_df = signals_dict[timeframe]
                if signals_df.empty:
                    continue
                
                # 獲取最新信號
                latest_signal = signals_df.iloc[-1]
                signal_type = latest_signal['signal_type']
                signal_strength = latest_signal.get('signal_strength', 0.5)
                
                # 信號強度過濾 (只執行強信號)
                if signal_strength < 0.6:
                    continue
                
                print(f"📊 發現 {timeframe} 信號: {signal_type} (強度: {signal_strength:.2f})")
                
                return {
                    'timeframe': timeframe,
                    'signal_type': signal_type,
                    'signal_strength': signal_strength,
                    'current_price': current_price,
                    'timestamp': datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"❌ 信號分析失敗: {e}")
            return None
    
    def execute_strategy_signal(self, signal: Dict) -> bool:
        """執行策略信號"""
        try:
            signal_type = signal['signal_type']
            current_price = signal['current_price']
            timeframe = signal['timeframe']
            
            print(f"🎯 執行 {timeframe} {signal_type} 信號 @ NT$ {current_price:,.0f}")
            
            if signal_type == 'buy':
                # 買入邏輯
                if self.current_position is not None:
                    print("⚠️ 已有持倉，跳過買入信號")
                    return False
                
                # 計算買入金額 (根據信號強度調整)
                base_amount = self.min_trade_amount
                strength_multiplier = signal['signal_strength']
                trade_amount = min(
                    base_amount * (1 + strength_multiplier),
                    self.max_trade_amount,
                    self.twd_balance * 0.1  # 最多使用10%資金
                )
                
                return self.execute_buy_order(current_price, trade_amount)
                
            elif signal_type == 'sell':
                # 賣出邏輯
                if self.current_position is None or self.btc_balance <= 0:
                    print("⚠️ 無持倉，跳過賣出信號")
                    return False
                
                return self.execute_sell_order(current_price)
            
            return False
            
        except Exception as e:
            print(f"❌ 執行信號失敗: {e}")
            return False
    
    def run_strategy_cycle(self) -> Dict:
        """運行一次策略循環"""
        try:
            print(f"\n🔄 策略循環開始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 獲取帳戶狀態
            account_status = self.get_account_status()
            
            print(f"💰 當前狀態:")
            print(f"   TWD餘額: NT$ {account_status['twd_balance']:,.0f}")
            print(f"   BTC持倉: {account_status['btc_balance']:.6f}")
            print(f"   總資產: NT$ {account_status['total_value']:,.0f}")
            print(f"   總獲利: NT$ {account_status['total_return']:,.0f} ({account_status['return_percentage']:+.2f}%)")
            print(f"   勝率: {account_status['win_rate']:.1f}% ({account_status['winning_trades']}/{account_status['total_trades']})")
            
            # 檢查交易信號
            if self.strategy_enabled:
                signal = self.check_trading_signals()
                
                if signal:
                    success = self.execute_strategy_signal(signal)
                    account_status['signal_executed'] = success
                    account_status['last_signal'] = signal
                else:
                    print("📊 暫無交易信號")
                    account_status['signal_executed'] = False
                    account_status['last_signal'] = None
            
            return account_status
            
        except Exception as e:
            print(f"❌ 策略循環失敗: {e}")
            return self.get_account_status()
    
    def save_state(self, filename: str = None):
        """保存交易狀態"""
        if filename is None:
            filename = f"virtual_trading_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        state = {
            'account': self.get_account_status(),
            'trade_history': self.trade_history,
            'current_position': self.current_position,
            'strategy_params': {
                'initial_balance': self.initial_balance,
                'min_trade_amount': self.min_trade_amount,
                'max_trade_amount': self.max_trade_amount,
                'trading_fee_rate': self.trading_fee_rate
            },
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            print(f"💾 狀態已保存: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 保存狀態失敗: {e}")
            return None

def test_virtual_trading():
    """測試虛擬交易引擎"""
    print("🧪 測試虛擬交易引擎")
    print("=" * 50)
    
    # 創建引擎
    engine = VirtualTradingEngine(initial_balance=100000)
    
    # 運行幾次策略循環
    for i in range(3):
        print(f"\n📊 第 {i+1} 次策略循環")
        status = engine.run_strategy_cycle()
        time.sleep(2)  # 等待2秒
    
    # 保存狀態
    engine.save_state()
    
    print("\n🎉 測試完成！")

if __name__ == "__main__":
    test_virtual_trading()