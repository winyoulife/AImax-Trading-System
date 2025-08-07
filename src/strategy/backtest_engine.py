#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 策略回測引擎 - 任務12實現
提供策略回測和性能分析功能
"""

import sys
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.strategy.strategy_config_manager import StrategyConfig, strategy_config_manager
from src.data.simple_data_fetcher import DataFetcher

logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    """回測交易記錄"""
    timestamp: datetime
    symbol: str
    action: str  # buy/sell
    price: float
    quantity: float
    amount: float
    confidence: float
    profit_loss: float = 0.0
    cumulative_pnl: float = 0.0

@dataclass
class BacktestResult:
    """回測結果"""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    total_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[BacktestTrade] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)

class BacktestEngine:
    """策略回測引擎"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.project_root = Path(__file__).parent.parent.parent
        
    def run_backtest(self, strategy_id: str, symbol: str = 'BTCUSDT', 
                    days: int = 30, initial_balance: float = 10000.0) -> Optional[BacktestResult]:
        """運行策略回測"""
        strategy = strategy_config_manager.get_strategy(strategy_id)
        if not strategy:
            logger.error(f"❌ 策略不存在: {strategy_id}")
            return None
        
        logger.info(f"🔄 開始回測策略: {strategy.strategy_name} ({symbol}, {days}天)")
        
        try:
            # 獲取歷史數據
            df = self.data_fetcher.get_historical_data(symbol, '1h', days * 24)
            if df.empty:
                logger.error("❌ 無法獲取歷史數據")
                return None
            
            # 初始化回測環境
            balance = initial_balance
            position = 0.0  # 持倉數量
            trades = []
            equity_curve = []
            daily_returns = []
            
            # 生成交易信號
            signals = self._generate_signals(df, strategy)
            
            # 執行回測
            for i, signal in enumerate(signals):
                trade_result = self._execute_backtest_trade(
                    signal, balance, position, strategy
                )
                
                if trade_result:
                    trade, new_balance, new_position = trade_result
                    trades.append(trade)
                    balance = new_balance
                    position = new_position
                    
                    # 記錄權益曲線
                    equity_curve.append((trade.timestamp, balance))
            
            # 計算性能指標
            result = self._calculate_performance_metrics(
                strategy_id, df.index[0], df.index[-1], 
                initial_balance, balance, trades, equity_curve
            )
            
            # 保存回測結果
            self._save_backtest_result(result)
            
            logger.info(f"✅ 回測完成: 總回報 {result.total_return:.2f}%, 勝率 {result.win_rate:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 回測失敗: {e}")
            return None    

    def _generate_signals(self, df: pd.DataFrame, strategy: StrategyConfig) -> List[Dict[str, Any]]:
        """生成交易信號"""
        try:
            # 根據策略類型生成信號
            if strategy.strategy_type.value == 'macd':
                from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
                signal_generator = SmartBalancedVolumeEnhancedMACDSignals()
                
                # 應用策略配置
                signal_generator.min_confidence = strategy.macd_config.min_confidence
                
                signals = signal_generator.detect_smart_balanced_signals(df)
                
                # 過濾信號
                filtered_signals = []
                for signal in signals:
                    if signal.get('confidence', 0) >= strategy.macd_config.min_confidence:
                        filtered_signals.append(signal)
                
                return filtered_signals
            
            else:
                # 其他策略類型的信號生成
                logger.warning(f"⚠️ 暫不支持的策略類型: {strategy.strategy_type.value}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 生成信號失敗: {e}")
            return []
    
    def _execute_backtest_trade(self, signal: Dict[str, Any], balance: float, 
                               position: float, strategy: StrategyConfig) -> Optional[Tuple[BacktestTrade, float, float]]:
        """執行回測交易"""
        try:
            action = signal.get('action')
            price = signal.get('price', 0)
            confidence = signal.get('confidence', 0)
            timestamp = signal.get('timestamp', datetime.now())
            
            if not action or price <= 0:
                return None
            
            # 計算交易數量
            if action == 'buy' and position == 0:
                # 買入
                max_amount = balance * strategy.risk_config.max_position_size
                max_amount = min(max_amount, strategy.trading_limits.max_trade_amount)
                
                if max_amount < strategy.trading_limits.min_trade_amount:
                    return None
                
                quantity = max_amount / price
                amount = quantity * price
                
                new_balance = balance - amount
                new_position = quantity
                
                trade = BacktestTrade(
                    timestamp=timestamp,
                    symbol=signal.get('symbol', 'BTCUSDT'),
                    action=action,
                    price=price,
                    quantity=quantity,
                    amount=amount,
                    confidence=confidence
                )
                
                return trade, new_balance, new_position
            
            elif action == 'sell' and position > 0:
                # 賣出
                amount = position * price
                profit_loss = amount - (position * signal.get('buy_price', price))
                
                new_balance = balance + amount
                new_position = 0.0
                
                trade = BacktestTrade(
                    timestamp=timestamp,
                    symbol=signal.get('symbol', 'BTCUSDT'),
                    action=action,
                    price=price,
                    quantity=position,
                    amount=amount,
                    confidence=confidence,
                    profit_loss=profit_loss
                )
                
                return trade, new_balance, new_position
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 執行回測交易失敗: {e}")
            return None
    
    def _calculate_performance_metrics(self, strategy_id: str, start_date: datetime, 
                                     end_date: datetime, initial_balance: float, 
                                     final_balance: float, trades: List[BacktestTrade],
                                     equity_curve: List[Tuple[datetime, float]]) -> BacktestResult:
        """計算性能指標"""
        total_return = ((final_balance - initial_balance) / initial_balance) * 100
        total_trades = len(trades)
        
        # 計算勝負交易
        winning_trades = len([t for t in trades if t.profit_loss > 0])
        losing_trades = len([t for t in trades if t.profit_loss < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 計算最大回撤
        max_drawdown = self._calculate_max_drawdown(equity_curve, initial_balance)
        
        # 計算夏普比率
        returns = [t.profit_loss / initial_balance for t in trades if t.action == 'sell']
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        
        # 計算每日回報
        daily_returns = self._calculate_daily_returns(equity_curve)
        
        return BacktestResult(
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            final_balance=final_balance,
            total_return=total_return,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades,
            daily_returns=daily_returns,
            equity_curve=equity_curve
        )
    
    def _calculate_max_drawdown(self, equity_curve: List[Tuple[datetime, float]], 
                               initial_balance: float) -> float:
        """計算最大回撤"""
        if not equity_curve:
            return 0.0
        
        peak = initial_balance
        max_drawdown = 0.0
        
        for timestamp, balance in equity_curve:
            if balance > peak:
                peak = balance
            
            drawdown = (peak - balance) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown * 100
    
    def _calculate_sharpe_ratio(self, returns: List[float]) -> float:
        """計算夏普比率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 假設無風險利率為0
        sharpe_ratio = mean_return / std_return
        return sharpe_ratio
    
    def _calculate_daily_returns(self, equity_curve: List[Tuple[datetime, float]]) -> List[float]:
        """計算每日回報率"""
        if len(equity_curve) < 2:
            return []
        
        daily_returns = []
        prev_balance = equity_curve[0][1]
        
        for timestamp, balance in equity_curve[1:]:
            daily_return = (balance - prev_balance) / prev_balance
            daily_returns.append(daily_return)
            prev_balance = balance
        
        return daily_returns
    
    def _save_backtest_result(self, result: BacktestResult):
        """保存回測結果"""
        try:
            # 更新策略的回測結果
            strategy = strategy_config_manager.get_strategy(result.strategy_id)
            if strategy:
                # 保存回測結果到策略配置
                backtest_data = {
                    'start_date': result.start_date.isoformat(),
                    'end_date': result.end_date.isoformat(),
                    'initial_balance': result.initial_balance,
                    'final_balance': result.final_balance,
                    'total_return': result.total_return,
                    'total_trades': result.total_trades,
                    'win_rate': result.win_rate,
                    'max_drawdown': result.max_drawdown,
                    'sharpe_ratio': result.sharpe_ratio,
                    'backtest_time': datetime.now().isoformat()
                }
                
                strategy.backtest_results = backtest_data
                strategy.performance_metrics = {
                    'total_return': result.total_return,
                    'win_rate': result.win_rate,
                    'max_drawdown': result.max_drawdown,
                    'sharpe_ratio': result.sharpe_ratio,
                    'total_trades': result.total_trades
                }
                
                strategy_config_manager.save_strategy(result.strategy_id)
            
            # 保存詳細回測報告
            reports_dir = self.project_root / "reports" / "backtests"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"backtest_{result.strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # 轉換為可序列化的格式
            report_data = {
                'strategy_id': result.strategy_id,
                'start_date': result.start_date.isoformat(),
                'end_date': result.end_date.isoformat(),
                'initial_balance': result.initial_balance,
                'final_balance': result.final_balance,
                'total_return': result.total_return,
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'win_rate': result.win_rate,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'trades': [
                    {
                        'timestamp': trade.timestamp.isoformat(),
                        'symbol': trade.symbol,
                        'action': trade.action,
                        'price': trade.price,
                        'quantity': trade.quantity,
                        'amount': trade.amount,
                        'confidence': trade.confidence,
                        'profit_loss': trade.profit_loss
                    }
                    for trade in result.trades
                ],
                'equity_curve': [
                    {
                        'timestamp': timestamp.isoformat(),
                        'balance': balance
                    }
                    for timestamp, balance in result.equity_curve
                ],
                'daily_returns': result.daily_returns
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 回測報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存回測結果失敗: {e}")
    
    def compare_strategies(self, strategy_ids: List[str], symbol: str = 'BTCUSDT', 
                          days: int = 30) -> Dict[str, Any]:
        """比較多個策略的回測結果"""
        logger.info(f"📊 開始策略比較: {len(strategy_ids)} 個策略")
        
        comparison_results = {}
        
        for strategy_id in strategy_ids:
            result = self.run_backtest(strategy_id, symbol, days)
            if result:
                comparison_results[strategy_id] = {
                    'strategy_name': strategy_config_manager.get_strategy(strategy_id).strategy_name,
                    'total_return': result.total_return,
                    'win_rate': result.win_rate,
                    'max_drawdown': result.max_drawdown,
                    'sharpe_ratio': result.sharpe_ratio,
                    'total_trades': result.total_trades
                }
        
        # 排序結果
        sorted_results = sorted(
            comparison_results.items(),
            key=lambda x: x[1]['total_return'],
            reverse=True
        )
        
        comparison_report = {
            'comparison_time': datetime.now().isoformat(),
            'symbol': symbol,
            'backtest_days': days,
            'strategies_compared': len(strategy_ids),
            'results': dict(sorted_results),
            'best_strategy': sorted_results[0] if sorted_results else None,
            'summary': {
                'avg_return': np.mean([r['total_return'] for r in comparison_results.values()]) if comparison_results else 0,
                'avg_win_rate': np.mean([r['win_rate'] for r in comparison_results.values()]) if comparison_results else 0,
                'avg_drawdown': np.mean([r['max_drawdown'] for r in comparison_results.values()]) if comparison_results else 0
            }
        }
        
        # 保存比較報告
        self._save_comparison_report(comparison_report)
        
        return comparison_report
    
    def _save_comparison_report(self, comparison_report: Dict[str, Any]):
        """保存策略比較報告"""
        try:
            reports_dir = self.project_root / "reports" / "strategy_comparisons"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = reports_dir / f"strategy_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(comparison_report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 策略比較報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存比較報告失敗: {e}")

# 全局回測引擎實例
backtest_engine = BacktestEngine()

# 便捷函數
def run_strategy_backtest(strategy_id: str, symbol: str = 'BTCUSDT', days: int = 30) -> Optional[BacktestResult]:
    """運行策略回測"""
    return backtest_engine.run_backtest(strategy_id, symbol, days)

def compare_strategies(strategy_ids: List[str], symbol: str = 'BTCUSDT', days: int = 30) -> Dict[str, Any]:
    """比較策略性能"""
    return backtest_engine.compare_strategies(strategy_ids, symbol, days)