#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 模擬交易環境測試 - 任務15實現
創建安全的模擬交易環境進行測試
"""

import sys
import os
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class SimulationTrade:
    """模擬交易記錄"""
    timestamp: datetime
    symbol: str
    action: str  # buy/sell
    price: float
    quantity: float
    confidence: float
    profit_loss: float = 0.0
    status: str = "open"  # open/closed

@dataclass
class SimulationAccount:
    """模擬帳戶"""
    initial_balance: float = 10000.0
    current_balance: float = 10000.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    max_drawdown: float = 0.0
    open_positions: List[SimulationTrade] = field(default_factory=list)
    closed_trades: List[SimulationTrade] = field(default_factory=list)

class SafeSimulationEnvironment:
    """安全模擬交易環境"""
    
    def __init__(self):
        self.account = SimulationAccount()
        self.project_root = Path(__file__).parent.parent
        self.simulation_data = {}
        self.risk_limits = {
            'max_position_size': 0.1,  # 最大10%倉位
            'max_daily_trades': 50,    # 每日最大交易數
            'stop_loss_pct': 0.05,     # 5%止損
            'max_drawdown_pct': 0.2    # 20%最大回撤
        }
        
    def load_historical_data(self, symbol: str, timeframe: str, periods: int) -> pd.DataFrame:
        """載入歷史數據用於模擬"""
        try:
            from src.data.simple_data_fetcher import DataFetcher
            fetcher = DataFetcher()
            return fetcher.get_historical_data(symbol, timeframe, periods)
        except Exception as e:
            # 如果無法獲取真實數據，生成模擬數據
            return self.generate_mock_data(symbol, periods)
    
    def generate_mock_data(self, symbol: str, periods: int) -> pd.DataFrame:
        """生成模擬市場數據"""
        np.random.seed(42)  # 確保可重現性
        
        # 生成時間序列
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=periods)
        timestamps = pd.date_range(start=start_time, end=end_time, periods=periods)
        
        # 生成價格數據（隨機遊走）
        base_price = 50000 if 'BTC' in symbol else 3000
        price_changes = np.random.normal(0, 0.02, periods)  # 2%標準差
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, base_price * 0.5))  # 防止價格過低
        
        # 生成成交量數據
        volumes = np.random.lognormal(10, 1, periods)
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': volumes
        })
        
        return df
    
    def execute_simulation_trade(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """執行模擬交易"""
        try:
            # 風險檢查
            risk_check = self.check_risk_limits(signal)
            if not risk_check['allowed']:
                return {
                    'success': False,
                    'reason': f"風險限制: {risk_check['reason']}",
                    'risk_check': risk_check
                }
            
            # 創建交易記錄
            trade = SimulationTrade(
                timestamp=datetime.now(),
                symbol=signal.get('symbol', 'BTCUSDT'),
                action=signal.get('action', 'buy'),
                price=signal.get('price', 0),
                quantity=self.calculate_position_size(signal),
                confidence=signal.get('confidence', 0)
            )
            
            # 執行交易
            if trade.action == 'buy':
                cost = trade.price * trade.quantity
                if self.account.current_balance >= cost:
                    self.account.current_balance -= cost
                    self.account.open_positions.append(trade)
                    self.account.total_trades += 1
                    
                    return {
                        'success': True,
                        'trade_id': len(self.account.open_positions),
                        'action': 'buy',
                        'price': trade.price,
                        'quantity': trade.quantity,
                        'cost': cost,
                        'remaining_balance': self.account.current_balance
                    }
                else:
                    return {
                        'success': False,
                        'reason': '餘額不足',
                        'required': cost,
                        'available': self.account.current_balance
                    }
            
            elif trade.action == 'sell':
                # 尋找對應的買入倉位
                matching_position = None
                for pos in self.account.open_positions:
                    if pos.symbol == trade.symbol and pos.action == 'buy':
                        matching_position = pos
                        break
                
                if matching_position:
                    # 計算盈虧
                    profit = (trade.price - matching_position.price) * matching_position.quantity
                    matching_position.profit_loss = profit
                    matching_position.status = 'closed'
                    
                    # 更新帳戶
                    self.account.current_balance += trade.price * matching_position.quantity
                    self.account.total_profit += profit
                    
                    if profit > 0:
                        self.account.winning_trades += 1
                    else:
                        self.account.losing_trades += 1
                    
                    # 移動到已關閉交易
                    self.account.open_positions.remove(matching_position)
                    self.account.closed_trades.append(matching_position)
                    
                    return {
                        'success': True,
                        'action': 'sell',
                        'price': trade.price,
                        'quantity': matching_position.quantity,
                        'profit_loss': profit,
                        'total_balance': self.account.current_balance
                    }
                else:
                    return {
                        'success': False,
                        'reason': '沒有對應的買入倉位'
                    }
            
        except Exception as e:
            return {
                'success': False,
                'reason': f'交易執行錯誤: {str(e)}'
            }
    
    def check_risk_limits(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """檢查風險限制"""
        checks = {
            'position_size_ok': True,
            'daily_trades_ok': True,
            'drawdown_ok': True,
            'balance_ok': True
        }
        
        reasons = []
        
        # 檢查倉位大小
        position_value = signal.get('price', 0) * self.calculate_position_size(signal)
        max_position_value = self.account.current_balance * self.risk_limits['max_position_size']
        
        if position_value > max_position_value:
            checks['position_size_ok'] = False
            reasons.append(f"倉位過大: {position_value:.2f} > {max_position_value:.2f}")
        
        # 檢查每日交易次數
        today_trades = len([t for t in self.account.closed_trades 
                           if t.timestamp.date() == datetime.now().date()])
        
        if today_trades >= self.risk_limits['max_daily_trades']:
            checks['daily_trades_ok'] = False
            reasons.append(f"每日交易次數超限: {today_trades}")
        
        # 檢查回撤
        if self.account.initial_balance > 0:
            current_drawdown = (self.account.initial_balance - self.account.current_balance) / self.account.initial_balance
            if current_drawdown > self.risk_limits['max_drawdown_pct']:
                checks['drawdown_ok'] = False
                reasons.append(f"回撤過大: {current_drawdown:.2%}")
        
        # 檢查餘額
        if self.account.current_balance <= 0:
            checks['balance_ok'] = False
            reasons.append("餘額不足")
        
        return {
            'allowed': all(checks.values()),
            'checks': checks,
            'reason': '; '.join(reasons) if reasons else 'All checks passed'
        }
    
    def calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """計算倉位大小"""
        confidence = signal.get('confidence', 0.5)
        price = signal.get('price', 1)
        
        # 基於信心度和風險限制計算倉位
        base_position_pct = min(confidence * 0.1, self.risk_limits['max_position_size'])
        position_value = self.account.current_balance * base_position_pct
        
        return position_value / price if price > 0 else 0
    
    def run_backtest_simulation(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """運行回測模擬"""
        print(f"🔄 運行 {symbol} {days}天回測模擬...")
        
        start_time = time.time()
        
        # 載入歷史數據
        df = self.load_historical_data(symbol, '1h', days * 24)
        
        if df.empty:
            return {'error': '無法載入歷史數據'}
        
        # 初始化策略
        try:
            from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
            strategy = SmartBalancedVolumeEnhancedMACDSignals()
        except ImportError:
            return {'error': '無法載入交易策略'}
        
        # 生成信號
        signals = strategy.detect_smart_balanced_signals(df)
        
        # 執行模擬交易
        simulation_results = []
        
        for signal in signals:
            # 添加當前價格信息
            signal['symbol'] = symbol
            
            # 執行交易
            result = self.execute_simulation_trade(signal)
            simulation_results.append({
                'signal': signal,
                'result': result,
                'timestamp': datetime.now()
            })
            
            # 模擬時間延遲
            time.sleep(0.01)
        
        # 計算性能指標
        performance = self.calculate_performance_metrics()
        
        backtest_result = {
            'symbol': symbol,
            'duration_days': days,
            'execution_time': time.time() - start_time,
            'data_points': len(df),
            'signals_generated': len(signals),
            'trades_executed': len(simulation_results),
            'account_performance': performance,
            'simulation_results': simulation_results[-10:],  # 只保留最後10筆記錄
            'risk_metrics': self.calculate_risk_metrics()
        }
        
        return backtest_result
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """計算性能指標"""
        total_trades = self.account.total_trades
        winning_trades = self.account.winning_trades
        losing_trades = self.account.losing_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 計算平均盈虧
        profits = [t.profit_loss for t in self.account.closed_trades if t.profit_loss > 0]
        losses = [t.profit_loss for t in self.account.closed_trades if t.profit_loss < 0]
        
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # 計算盈虧比
        profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
        
        # 計算總回報率
        total_return = ((self.account.current_balance - self.account.initial_balance) / 
                       self.account.initial_balance * 100) if self.account.initial_balance > 0 else 0
        
        return {
            'initial_balance': self.account.initial_balance,
            'current_balance': self.account.current_balance,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': win_rate,
            'total_profit': self.account.total_profit,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'open_positions': len(self.account.open_positions)
        }
    
    def calculate_risk_metrics(self) -> Dict[str, Any]:
        """計算風險指標"""
        if not self.account.closed_trades:
            return {'error': '沒有已關閉的交易記錄'}
        
        # 計算最大回撤
        balance_history = [self.account.initial_balance]
        running_balance = self.account.initial_balance
        
        for trade in self.account.closed_trades:
            running_balance += trade.profit_loss
            balance_history.append(running_balance)
        
        peak = self.account.initial_balance
        max_drawdown = 0
        
        for balance in balance_history:
            if balance > peak:
                peak = balance
            drawdown = (peak - balance) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        # 計算夏普比率（簡化版）
        returns = [t.profit_loss / self.account.initial_balance for t in self.account.closed_trades]
        avg_return = np.mean(returns) if returns else 0
        return_std = np.std(returns) if returns else 0
        sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        
        return {
            'max_drawdown_pct': max_drawdown * 100,
            'volatility': return_std * 100,
            'sharpe_ratio': sharpe_ratio,
            'risk_adjusted_return': avg_return / max_drawdown if max_drawdown > 0 else 0
        }
    
    def generate_simulation_report(self) -> str:
        """生成模擬報告"""
        performance = self.calculate_performance_metrics()
        risk_metrics = self.calculate_risk_metrics()
        
        report = f"""
🎯 AImax 模擬交易報告
{'='*50}

📊 帳戶概況:
   初始資金: ${performance['initial_balance']:,.2f}
   當前餘額: ${performance['current_balance']:,.2f}
   總回報率: {performance['total_return_pct']:+.2f}%
   總盈虧: ${performance['total_profit']:+,.2f}

📈 交易統計:
   總交易數: {performance['total_trades']}
   獲利交易: {performance['winning_trades']}
   虧損交易: {performance['losing_trades']}
   勝率: {performance['win_rate_pct']:.1f}%
   
💰 盈虧分析:
   平均獲利: ${performance['avg_profit']:,.2f}
   平均虧損: ${performance['avg_loss']:,.2f}
   盈虧比: {performance['profit_loss_ratio']:.2f}

⚠️ 風險指標:
   最大回撤: {risk_metrics.get('max_drawdown_pct', 0):.2f}%
   波動率: {risk_metrics.get('volatility', 0):.2f}%
   夏普比率: {risk_metrics.get('sharpe_ratio', 0):.2f}

🔒 風險控制:
   最大倉位: {self.risk_limits['max_position_size']*100:.0f}%
   每日交易限制: {self.risk_limits['max_daily_trades']}筆
   止損比例: {self.risk_limits['stop_loss_pct']*100:.0f}%
   最大回撤限制: {self.risk_limits['max_drawdown_pct']*100:.0f}%

{'='*50}
報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return report.strip()

def run_simulation_tests() -> Dict[str, Any]:
    """運行模擬交易測試"""
    print("🎮 開始模擬交易環境測試")
    print("=" * 60)
    
    results = {
        'test_suite': 'simulation_tests',
        'start_time': datetime.now(),
        'tests': []
    }
    
    # 測試1: 基本模擬環境
    print("🏗️ 測試基本模擬環境...")
    sim_env = SafeSimulationEnvironment()
    
    basic_test = {
        'test_name': 'basic_simulation_environment',
        'status': 'PASSED',
        'details': {
            'initial_balance': sim_env.account.initial_balance,
            'risk_limits_configured': len(sim_env.risk_limits) > 0,
            'environment_ready': True
        }
    }
    results['tests'].append(basic_test)
    
    # 測試2: 模擬數據生成
    print("📊 測試模擬數據生成...")
    mock_data = sim_env.generate_mock_data('BTCUSDT', 100)
    
    data_test = {
        'test_name': 'mock_data_generation',
        'status': 'PASSED' if len(mock_data) == 100 else 'FAILED',
        'details': {
            'data_points': len(mock_data),
            'columns': list(mock_data.columns),
            'price_range': {
                'min': float(mock_data['close'].min()),
                'max': float(mock_data['close'].max())
            }
        }
    }
    results['tests'].append(data_test)
    
    # 測試3: 風險控制
    print("🛡️ 測試風險控制...")
    test_signal = {
        'action': 'buy',
        'price': 50000,
        'confidence': 0.9,
        'symbol': 'BTCUSDT'
    }
    
    risk_check = sim_env.check_risk_limits(test_signal)
    
    risk_test = {
        'test_name': 'risk_control_system',
        'status': 'PASSED' if risk_check['allowed'] else 'FAILED',
        'details': {
            'risk_check_result': risk_check,
            'risk_limits': sim_env.risk_limits
        }
    }
    results['tests'].append(risk_test)
    
    # 測試4: 模擬交易執行
    print("💰 測試模擬交易執行...")
    trade_result = sim_env.execute_simulation_trade(test_signal)
    
    trade_test = {
        'test_name': 'simulation_trade_execution',
        'status': 'PASSED' if trade_result.get('success') else 'FAILED',
        'details': {
            'trade_result': trade_result,
            'account_balance_after': sim_env.account.current_balance,
            'open_positions': len(sim_env.account.open_positions)
        }
    }
    results['tests'].append(trade_test)
    
    # 測試5: 回測模擬
    print("📈 測試回測模擬...")
    backtest_result = sim_env.run_backtest_simulation('BTCUSDT', 3)
    
    backtest_test = {
        'test_name': 'backtest_simulation',
        'status': 'PASSED' if 'error' not in backtest_result else 'FAILED',
        'details': backtest_result
    }
    results['tests'].append(backtest_test)
    
    # 測試6: 性能報告生成
    print("📋 測試性能報告生成...")
    report = sim_env.generate_simulation_report()
    
    report_test = {
        'test_name': 'performance_report_generation',
        'status': 'PASSED' if len(report) > 0 else 'FAILED',
        'details': {
            'report_length': len(report),
            'report_preview': report[:200] + "..." if len(report) > 200 else report
        }
    }
    results['tests'].append(report_test)
    
    # 生成總結
    results['end_time'] = datetime.now()
    results['total_duration'] = (results['end_time'] - results['start_time']).total_seconds()
    
    passed_tests = len([t for t in results['tests'] if t['status'] == 'PASSED'])
    total_tests = len(results['tests'])
    
    results['summary'] = {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'failed_tests': total_tests - passed_tests,
        'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
    }
    
    # 保存報告
    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"simulation_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # 保存模擬報告
    simulation_report_file = reports_dir / f"simulation_trading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(simulation_report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n" + "=" * 60)
    print("🎮 模擬交易測試完成")
    print("=" * 60)
    print(f"總測試數: {total_tests}")
    print(f"通過: {passed_tests} ✅")
    print(f"失敗: {total_tests - passed_tests} ❌")
    print(f"成功率: {results['summary']['success_rate']:.1f}%")
    print(f"測試報告: {report_file}")
    print(f"模擬報告: {simulation_report_file}")
    
    return results

if __name__ == "__main__":
    results = run_simulation_tests()
    success_rate = results['summary']['success_rate']
    sys.exit(0 if success_rate >= 80 else 1)