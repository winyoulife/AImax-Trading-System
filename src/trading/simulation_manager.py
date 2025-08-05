#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模擬交易管理器
專門用於GitHub Actions雲端模擬交易
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SimulationTradingManager:
    """模擬交易管理器"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}
        self.trade_history = []
        self.simulation_data_dir = "data/simulation"
        
        # 確保數據目錄存在
        os.makedirs(self.simulation_data_dir, exist_ok=True)
        
        # 載入現有狀態
        self.load_simulation_state()
        
    def load_simulation_state(self):
        """載入模擬交易狀態"""
        try:
            state_file = os.path.join(self.simulation_data_dir, "portfolio_state.json")
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.current_balance = state.get('balance', self.initial_balance)
                    self.positions = state.get('positions', {})
                    logger.info(f"✅ 載入模擬狀態: 餘額 ${self.current_balance:.2f}")
            else:
                logger.info(f"🆕 初始化模擬交易: 初始資金 ${self.initial_balance:.2f}")
                
        except Exception as e:
            logger.error(f"❌ 載入模擬狀態失敗: {e}")
            
    def save_simulation_state(self):
        """保存模擬交易狀態"""
        try:
            state = {
                'balance': self.current_balance,
                'positions': self.positions,
                'last_update': datetime.now().isoformat(),
                'total_trades': len(self.trade_history)
            }
            
            state_file = os.path.join(self.simulation_data_dir, "portfolio_state.json")
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
            logger.info("✅ 模擬狀態已保存")
            
        except Exception as e:
            logger.error(f"❌ 保存模擬狀態失敗: {e}")
            
    def execute_simulation_trade(self, signal: Dict) -> Dict:
        """執行模擬交易"""
        try:
            action = signal['action']
            price = signal['price']
            symbol = signal.get('symbol', 'BTCUSDT')
            confidence = signal.get('confidence', 0.0)
            
            # 計算交易數量
            if action == 'buy':
                # 使用固定金額購買
                trade_amount = min(1000.0, self.current_balance * 0.1)  # 最多使用10%資金
                quantity = trade_amount / price
                
                if self.current_balance >= trade_amount:
                    # 執行買入
                    self.current_balance -= trade_amount
                    self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                    
                    trade_record = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'buy',
                        'symbol': symbol,
                        'price': price,
                        'quantity': quantity,
                        'amount': trade_amount,
                        'confidence': confidence,
                        'balance_after': self.current_balance,
                        'position_after': self.positions.get(symbol, 0)
                    }
                    
                    self.trade_history.append(trade_record)
                    self.save_trade_record(trade_record)
                    
                    logger.info(f"✅ 模擬買入: {quantity:.6f} {symbol} @ ${price:.2f}")
                    return {'success': True, 'trade': trade_record}
                else:
                    logger.warning(f"⚠️ 資金不足，無法買入 {symbol}")
                    return {'success': False, 'reason': '資金不足'}
                    
            elif action == 'sell':
                # 賣出持有的部分或全部
                current_position = self.positions.get(symbol, 0)
                
                if current_position > 0:
                    # 賣出50%持倉
                    sell_quantity = current_position * 0.5
                    sell_amount = sell_quantity * price
                    
                    # 執行賣出
                    self.current_balance += sell_amount
                    self.positions[symbol] = current_position - sell_quantity
                    
                    trade_record = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'sell',
                        'symbol': symbol,
                        'price': price,
                        'quantity': sell_quantity,
                        'amount': sell_amount,
                        'confidence': confidence,
                        'balance_after': self.current_balance,
                        'position_after': self.positions.get(symbol, 0)
                    }
                    
                    self.trade_history.append(trade_record)
                    self.save_trade_record(trade_record)
                    
                    logger.info(f"✅ 模擬賣出: {sell_quantity:.6f} {symbol} @ ${price:.2f}")
                    return {'success': True, 'trade': trade_record}
                else:
                    logger.warning(f"⚠️ 無持倉，無法賣出 {symbol}")
                    return {'success': False, 'reason': '無持倉'}
                    
            # 保存狀態
            self.save_simulation_state()
            
        except Exception as e:
            logger.error(f"❌ 模擬交易執行失敗: {e}")
            return {'success': False, 'reason': str(e)}
            
    def save_trade_record(self, trade_record: Dict):
        """保存交易記錄"""
        try:
            trades_file = os.path.join(self.simulation_data_dir, "trades.jsonl")
            with open(trades_file, 'a') as f:
                f.write(json.dumps(trade_record) + '\n')
                
        except Exception as e:
            logger.error(f"❌ 保存交易記錄失敗: {e}")
            
    def get_portfolio_summary(self) -> Dict:
        """獲取投資組合摘要"""
        try:
            # 計算當前總價值（需要當前價格）
            total_value = self.current_balance
            
            # 簡化版本：假設BTC價格
            btc_position = self.positions.get('BTCUSDT', 0)
            if btc_position > 0:
                # 這裡應該獲取實時價格，暫時使用固定價格
                estimated_btc_price = 95000.0  # 估算價格
                total_value += btc_position * estimated_btc_price
                
            total_return = total_value - self.initial_balance
            return_pct = (total_return / self.initial_balance) * 100
            
            # 計算交易統計
            total_trades = len(self.trade_history)
            buy_trades = len([t for t in self.trade_history if t['action'] == 'buy'])
            sell_trades = len([t for t in self.trade_history if t['action'] == 'sell'])
            
            return {
                'initial_balance': self.initial_balance,
                'current_balance': self.current_balance,
                'positions': self.positions,
                'total_value': total_value,
                'total_return': total_return,
                'return_percentage': return_pct,
                'total_trades': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades,
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取投資組合摘要失敗: {e}")
            return {}
            
    def get_performance_report(self) -> str:
        """生成性能報告"""
        try:
            summary = self.get_portfolio_summary()
            
            report = f"""
📊 === AImax 模擬交易性能報告 ===
🕐 報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 初始資金: ${summary.get('initial_balance', 0):,.2f}
💵 當前現金: ${summary.get('current_balance', 0):,.2f}
📈 總價值: ${summary.get('total_value', 0):,.2f}
💹 總收益: ${summary.get('total_return', 0):,.2f} ({summary.get('return_percentage', 0):+.2f}%)

📊 交易統計:
🔢 總交易次數: {summary.get('total_trades', 0)}
📈 買入次數: {summary.get('buy_trades', 0)}
📉 賣出次數: {summary.get('sell_trades', 0)}

💼 當前持倉:
"""
            
            positions = summary.get('positions', {})
            if positions:
                for symbol, quantity in positions.items():
                    if quantity > 0:
                        report += f"   {symbol}: {quantity:.6f}\n"
            else:
                report += "   無持倉\n"
                
            report += "\n🎯 策略: 終極優化MACD (目標勝率85%+)"
            report += "\n🔄 模式: 雲端模擬交易"
            report += "\n✅ 系統狀態: 正常運行"
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成性能報告失敗: {e}")
            return f"❌ 報告生成失敗: {e}"