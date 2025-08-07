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
import sys

# 添加配置路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config.max_exchange_config import MAX_EXCHANGE_CONFIG, get_trading_fee, calculate_trading_cost

# 添加雲端數據管理器
try:
    from scripts.cloud_data_manager import CloudDataManager
    CLOUD_ENABLED = True
except ImportError:
    CLOUD_ENABLED = False
    logger.warning("⚠️ 雲端數據管理器未載入，使用本地模式")

logger = logging.getLogger(__name__)

class SimulationTradingManager:
    """模擬交易管理器"""
    
    def __init__(self, initial_balance: float = 100000.0):  # 10萬台幣
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}
        self.trade_history = []
        self.simulation_data_dir = "data/simulation"
        
        # 初始化雲端數據管理器
        if CLOUD_ENABLED:
            self.cloud_manager = CloudDataManager()
            logger.info("✅ 雲端數據管理器已啟用")
        else:
            self.cloud_manager = None
            logger.info("📝 使用本地數據模式")
        
        # 確保數據目錄存在
        os.makedirs(self.simulation_data_dir, exist_ok=True)
        
        # 載入現有狀態
        self.load_simulation_state()
        
    def load_simulation_state(self):
        """載入模擬交易狀態"""
        try:
            # 優先使用雲端數據管理器
            if self.cloud_manager:
                state = self.cloud_manager.load_portfolio_state()
                self.current_balance = state.get('balance', self.initial_balance)
                self.positions = state.get('positions', {})
                logger.info(f"✅ 從雲端載入模擬狀態: 餘額 {self.current_balance:,.0f} TWD")
                return
            
            # 本地模式
            state_file = os.path.join(self.simulation_data_dir, "portfolio_state.json")
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.current_balance = state.get('balance', self.initial_balance)
                    self.positions = state.get('positions', {})
                    logger.info(f"✅ 載入本地模擬狀態: 餘額 {self.current_balance:,.0f} TWD")
            else:
                logger.info(f"🆕 初始化模擬交易: 初始資金 {self.initial_balance:,.0f} TWD")
                
        except Exception as e:
            logger.error(f"❌ 載入模擬狀態失敗: {e}")
            
    def save_simulation_state(self):
        """保存模擬交易狀態"""
        try:
            state = {
                'balance': self.current_balance,
                'positions': self.positions,
                'last_update': datetime.now().isoformat(),
                'total_trades': len(self.trade_history),
                'initial_balance': self.initial_balance,
                'currency': 'TWD',
                'exchange': 'MAX',
                'strategy_version': 'v1.0-smart-balanced'
            }
            
            # 優先保存到雲端
            if self.cloud_manager:
                success = self.cloud_manager.save_portfolio_state(state)
                if success:
                    logger.info("✅ 模擬狀態已保存到雲端")
                else:
                    logger.warning("⚠️ 雲端保存失敗，使用本地保存")
            
            # 本地備份
            state_file = os.path.join(self.simulation_data_dir, "portfolio_state.json")
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
            logger.info("✅ 模擬狀態已保存")
            
        except Exception as e:
            logger.error(f"❌ 保存模擬狀態失敗: {e}")
            
    def execute_simulation_trade(self, signal: Dict) -> Dict:
        """執行模擬交易 - 嚴格的一買一賣配對邏輯"""
        try:
            action = signal['action']
            price = signal['price']
            symbol = signal.get('symbol', 'BTCUSDT')
            confidence = signal.get('confidence', 0.0)
            
            current_position = self.positions.get(symbol, 0)
            
            # 計算交易數量
            if action == 'buy':
                # 🚨 重要：只有在無持倉時才能買入
                if current_position > 0:
                    logger.warning(f"⚠️ 已有持倉 {current_position:.6f} {symbol}，跳過買入信號")
                    return {'success': False, 'reason': f'已有持倉 {current_position:.6f} {symbol}，跳過買入信號'}
                # 使用固定金額購買 (台幣計價)
                trade_amount = min(10000.0, self.current_balance * 0.1)  # 最多使用10%資金，單筆最多1萬
                
                # 計算手續費
                fee_rate = get_trading_fee('taker')  # 使用MAX實際手續費 0.15%
                fee_amount = trade_amount * fee_rate
                total_cost = trade_amount + fee_amount
                
                if self.current_balance >= total_cost:
                    # 計算實際購買數量 (扣除手續費後)
                    quantity = trade_amount / price
                    
                    # 執行買入
                    self.current_balance -= total_cost
                    self.positions[symbol] = quantity  # 直接設定，不累加
                    
                    trade_record = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'buy',
                        'symbol': symbol,
                        'price': price,
                        'quantity': quantity,
                        'amount': trade_amount,
                        'fee_rate': fee_rate,
                        'fee_amount': fee_amount,
                        'total_cost': total_cost,
                        'confidence': confidence,
                        'balance_after': self.current_balance,
                        'position_after': self.positions.get(symbol, 0),
                        'exchange': 'MAX',
                        'currency': 'TWD'
                    }
                    
                    self.trade_history.append(trade_record)
                    self.save_trade_record(trade_record)
                    
                    logger.info(f"✅ 模擬買入: {quantity:.6f} {symbol} @ ${price:.2f}")
                    return {'success': True, 'trade': trade_record}
                else:
                    logger.warning(f"⚠️ 資金不足，無法買入 {symbol}")
                    return {'success': False, 'reason': '資金不足'}
                    
            elif action == 'sell':
                # 🚨 重要：只有在有持倉時才能賣出
                if current_position <= 0:
                    logger.warning(f"⚠️ 無持倉，跳過賣出信號")
                    return {'success': False, 'reason': '無持倉，跳過賣出信號'}
                
                # 賣出全部持倉 (完整的交易週期)
                sell_quantity = current_position
                sell_amount = sell_quantity * price
                
                # 計算手續費
                fee_rate = get_trading_fee('taker')  # 使用MAX實際手續費 0.15%
                fee_amount = sell_amount * fee_rate
                net_proceeds = sell_amount - fee_amount
                
                # 執行賣出
                self.current_balance += net_proceeds
                self.positions[symbol] = 0  # 清空持倉
                
                trade_record = {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'sell',
                        'symbol': symbol,
                        'price': price,
                        'quantity': sell_quantity,
                        'amount': sell_amount,
                        'fee_rate': fee_rate,
                        'fee_amount': fee_amount,
                        'net_proceeds': net_proceeds,
                        'confidence': confidence,
                        'balance_after': self.current_balance,
                        'position_after': self.positions.get(symbol, 0),
                        'exchange': 'MAX',
                        'currency': 'TWD'
                }
                
                self.trade_history.append(trade_record)
                self.save_trade_record(trade_record)
                
                logger.info(f"✅ 模擬賣出: {sell_quantity:.6f} {symbol} @ ${price:.2f}")
                return {'success': True, 'trade': trade_record}
                    
            # 保存狀態
            self.save_simulation_state()
            
        except Exception as e:
            logger.error(f"❌ 模擬交易執行失敗: {e}")
            return {'success': False, 'reason': str(e)}
            
    def save_trade_record(self, trade_record: Dict):
        """保存交易記錄"""
        try:
            # 優先保存到雲端
            if self.cloud_manager:
                success = self.cloud_manager.save_trade_record(trade_record)
                if success:
                    logger.info("✅ 交易記錄已保存到雲端")
                else:
                    logger.warning("⚠️ 雲端保存失敗，使用本地保存")
            
            # 本地備份
            trades_file = os.path.join(self.simulation_data_dir, "trades.jsonl")
            with open(trades_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade_record, ensure_ascii=False) + '\n')
                
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