#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
85%策略交易歷史分析模組
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

class TradingAnalytics:
    """交易分析器"""
    
    def __init__(self):
        self.trade_history = []
        self.analysis_cache = {}
    
    def update_trade_history(self, trade_history: List[Dict]):
        """更新交易歷史"""
        self.trade_history = trade_history
        self.analysis_cache = {}  # 清空緩存
    
    def get_basic_stats(self) -> Dict:
        """獲取基本統計信息"""
        if not self.trade_history:
            return self._empty_stats()
        
        # 分離買入和賣出交易
        buy_trades = [t for t in self.trade_history if t['type'] == 'buy']
        sell_trades = [t for t in self.trade_history if t['type'] == 'sell']
        
        # 計算完整交易對
        completed_trades = min(len(buy_trades), len(sell_trades))
        
        # 計算獲利
        total_profit = sum(t.get('profit', 0) for t in sell_trades)
        profitable_trades = len([t for t in sell_trades if t.get('profit', 0) > 0])
        
        # 計算勝率
        win_rate = (profitable_trades / max(len(sell_trades), 1)) * 100
        
        # 計算平均獲利
        avg_profit = total_profit / max(len(sell_trades), 1)
        
        # 計算最大獲利和虧損
        profits = [t.get('profit', 0) for t in sell_trades]
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0
        
        return {
            'total_trades': len(self.trade_history),
            'completed_pairs': completed_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'win_rate': win_rate,
            'profitable_trades': profitable_trades,
            'losing_trades': len(sell_trades) - profitable_trades
        }
    
    def get_daily_performance(self) -> Dict:
        """獲取每日績效分析"""
        if not self.trade_history:
            return {}
        
        daily_stats = {}
        
        for trade in self.trade_history:
            trade_date = datetime.fromisoformat(trade['timestamp']).date()
            date_str = trade_date.strftime('%Y-%m-%d')
            
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    'trades': 0,
                    'profit': 0,
                    'buy_volume': 0,
                    'sell_volume': 0
                }
            
            daily_stats[date_str]['trades'] += 1
            
            if trade['type'] == 'buy':
                daily_stats[date_str]['buy_volume'] += trade.get('total_cost', 0)
            else:
                daily_stats[date_str]['sell_volume'] += trade.get('net_income', 0)
                daily_stats[date_str]['profit'] += trade.get('profit', 0)
        
        return daily_stats
    
    def get_hourly_performance(self) -> Dict:
        """獲取小時績效分析"""
        if not self.trade_history:
            return {}
        
        hourly_stats = {}
        
        for trade in self.trade_history:
            hour = datetime.fromisoformat(trade['timestamp']).hour
            
            if hour not in hourly_stats:
                hourly_stats[hour] = {
                    'trades': 0,
                    'profit': 0,
                    'avg_price': 0,
                    'prices': []
                }
            
            hourly_stats[hour]['trades'] += 1
            hourly_stats[hour]['prices'].append(trade['price'])
            
            if trade['type'] == 'sell':
                hourly_stats[hour]['profit'] += trade.get('profit', 0)
        
        # 計算平均價格
        for hour in hourly_stats:
            prices = hourly_stats[hour]['prices']
            hourly_stats[hour]['avg_price'] = sum(prices) / len(prices)
            del hourly_stats[hour]['prices']  # 移除原始價格列表
        
        return hourly_stats
    
    def get_profit_distribution(self) -> Dict:
        """獲取獲利分布分析"""
        sell_trades = [t for t in self.trade_history if t['type'] == 'sell']
        
        if not sell_trades:
            return {}
        
        profits = [t.get('profit', 0) for t in sell_trades]
        
        # 分類獲利
        profit_ranges = {
            'huge_profit': len([p for p in profits if p > 10000]),      # >1萬
            'big_profit': len([p for p in profits if 5000 < p <= 10000]), # 5千-1萬
            'medium_profit': len([p for p in profits if 1000 < p <= 5000]), # 1千-5千
            'small_profit': len([p for p in profits if 0 < p <= 1000]),   # 0-1千
            'break_even': len([p for p in profits if p == 0]),           # 打平
            'small_loss': len([p for p in profits if -1000 <= p < 0]),   # 0到-1千
            'medium_loss': len([p for p in profits if -5000 <= p < -1000]), # -1千到-5千
            'big_loss': len([p for p in profits if p < -5000])           # <-5千
        }
        
        return {
            'distribution': profit_ranges,
            'total_trades': len(profits),
            'avg_profit': np.mean(profits),
            'median_profit': np.median(profits),
            'std_profit': np.std(profits),
            'profit_ratio': len([p for p in profits if p > 0]) / len(profits)
        }
    
    def get_strategy_performance(self) -> Dict:
        """獲取策略績效指標"""
        if not self.trade_history:
            return self._empty_performance()
        
        sell_trades = [t for t in self.trade_history if t['type'] == 'sell']
        profits = [t.get('profit', 0) for t in sell_trades]
        
        if not profits:
            return self._empty_performance()
        
        # 計算夏普比率 (簡化版)
        avg_return = np.mean(profits)
        std_return = np.std(profits)
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        
        # 計算最大回撤
        cumulative_profits = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative_profits)
        drawdowns = running_max - cumulative_profits
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        # 計算連續獲利/虧損
        consecutive_wins = self._get_consecutive_count(profits, lambda x: x > 0)
        consecutive_losses = self._get_consecutive_count(profits, lambda x: x < 0)
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_return': avg_return,
            'return_std': std_return,
            'max_consecutive_wins': consecutive_wins['max'],
            'current_consecutive_wins': consecutive_wins['current'],
            'max_consecutive_losses': consecutive_losses['max'],
            'current_consecutive_losses': consecutive_losses['current'],
            'profit_factor': self._calculate_profit_factor(profits),
            'recovery_factor': avg_return / max_drawdown if max_drawdown > 0 else float('inf')
        }
    
    def get_recent_performance(self, days: int = 7) -> Dict:
        """獲取最近N天的績效"""
        if not self.trade_history:
            return {}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_trades = [
            t for t in self.trade_history 
            if datetime.fromisoformat(t['timestamp']) >= cutoff_date
        ]
        
        if not recent_trades:
            return {}
        
        # 臨時更新交易歷史進行分析
        original_history = self.trade_history
        self.trade_history = recent_trades
        
        recent_stats = self.get_basic_stats()
        recent_stats['period_days'] = days
        recent_stats['trades_per_day'] = len(recent_trades) / days
        
        # 恢復原始交易歷史
        self.trade_history = original_history
        
        return recent_stats
    
    def _empty_stats(self) -> Dict:
        """空統計數據"""
        return {
            'total_trades': 0,
            'completed_pairs': 0,
            'buy_trades': 0,
            'sell_trades': 0,
            'total_profit': 0,
            'avg_profit': 0,
            'max_profit': 0,
            'max_loss': 0,
            'win_rate': 0,
            'profitable_trades': 0,
            'losing_trades': 0
        }
    
    def _empty_performance(self) -> Dict:
        """空績效數據"""
        return {
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'avg_return': 0,
            'return_std': 0,
            'max_consecutive_wins': 0,
            'current_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'current_consecutive_losses': 0,
            'profit_factor': 0,
            'recovery_factor': 0
        }
    
    def _get_consecutive_count(self, values: List[float], condition) -> Dict:
        """計算連續符合條件的次數"""
        max_count = 0
        current_count = 0
        
        for value in values:
            if condition(value):
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return {'max': max_count, 'current': current_count}
    
    def _calculate_profit_factor(self, profits: List[float]) -> float:
        """計算獲利因子"""
        gross_profit = sum(p for p in profits if p > 0)
        gross_loss = abs(sum(p for p in profits if p < 0))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def generate_report(self) -> str:
        """生成分析報告"""
        basic_stats = self.get_basic_stats()
        performance = self.get_strategy_performance()
        profit_dist = self.get_profit_distribution()
        recent_perf = self.get_recent_performance(7)
        
        report = f"""
📊 85%勝率策略交易分析報告
{'='*50}

📈 基本統計:
• 總交易次數: {basic_stats['total_trades']}筆
• 完整交易對: {basic_stats['completed_pairs']}對
• 總獲利: NT$ {basic_stats['total_profit']:+,.0f}
• 平均獲利: NT$ {basic_stats['avg_profit']:+,.0f}
• 勝率: {basic_stats['win_rate']:.1f}%
• 最大獲利: NT$ {basic_stats['max_profit']:+,.0f}
• 最大虧損: NT$ {basic_stats['max_loss']:+,.0f}

🎯 策略績效:
• 夏普比率: {performance['sharpe_ratio']:.2f}
• 最大回撤: NT$ {performance['max_drawdown']:,.0f}
• 獲利因子: {performance['profit_factor']:.2f}
• 最大連勝: {performance['max_consecutive_wins']}次
• 最大連敗: {performance['max_consecutive_losses']}次

📊 最近7天表現:
• 交易次數: {recent_perf.get('total_trades', 0)}筆
• 獲利: NT$ {recent_perf.get('total_profit', 0):+,.0f}
• 勝率: {recent_perf.get('win_rate', 0):.1f}%
• 日均交易: {recent_perf.get('trades_per_day', 0):.1f}筆

⏰ 報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return report