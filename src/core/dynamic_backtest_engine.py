#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 回測引擎集成
整合動態追蹤策略與現有回測系統
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, field

from .dynamic_trading_config import DynamicTradingConfig
from .dynamic_trading_signals import DynamicTradingSignals
from .dynamic_trading_data_structures import (
    DynamicTradeResult, TrackingStatistics, SignalType, ExecutionReason
)
from ..data.tracking_data_manager import TrackingDataManager
from ..data.historical_data_manager import HistoricalDataManager

logger = logging.getLogger(__name__)

@dataclass
class BacktestResult:
    """回測結果數據結構"""
    start_date: datetime
    end_date: datetime
    total_trades: int = 0
    successful_trades: int = 0
    total_profit: float = 0.0
    total_improvement: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    average_trade_duration: timedelta = field(default_factory=lambda: timedelta(0))
    
    # 動態策略特有指標
    dynamic_trades: List[DynamicTradeResult] = field(default_factory=list)
    tracking_statistics: Optional[TrackingStatistics] = None
    strategy_comparison: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取回測摘要"""
        return {
            'period': {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat(),
                'duration_days': (self.end_date - self.start_date).days
            },
            'performance': {
                'total_trades': self.total_trades,
                'successful_trades': self.successful_trades,
                'win_rate': self.win_rate,
                'total_profit': self.total_profit,
                'total_improvement': self.total_improvement,
                'max_drawdown': self.max_drawdown,
                'sharpe_ratio': self.sharpe_ratio,
                'average_trade_duration_hours': self.average_trade_duration.total_seconds() / 3600
            },
            'dynamic_metrics': {
                'dynamic_trades_count': len(self.dynamic_trades),
                'tracking_success_rate': self.tracking_statistics.get_success_rate() if self.tracking_statistics else 0,
                'average_improvement': self.tracking_statistics.average_improvement if self.tracking_statistics else 0
            }
        }

class DynamicBacktestEngine:
    """動態回測引擎 - 整合動態追蹤策略的回測系統"""
    
    def __init__(self, config: DynamicTradingConfig):
        self.config = config
        self.dynamic_signals = DynamicTradingSignals(config)
        self.data_manager = TrackingDataManager(config.performance_config)
        self.historical_data_manager = HistoricalDataManager()
        
        # 回測狀態
        self.is_running = False
        self.current_backtest_id = None
        self.progress_callback = None
        
        logger.info("動態回測引擎初始化完成")
    
    def run_backtest(self, 
                    symbol: str,
                    start_date: datetime,
                    end_date: datetime,
                    initial_capital: float = 1000000.0,
                    progress_callback: Optional[callable] = None) -> BacktestResult:
        """執行動態策略回測"""
        
        self.is_running = True
        self.progress_callback = progress_callback
        self.current_backtest_id = f"backtest_{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        try:
            logger.info(f"開始動態策略回測: {symbol} ({start_date} - {end_date})")
            
            # 1. 獲取歷史數據
            self._update_progress(0, "正在獲取歷史數據...")
            historical_data = self._get_historical_data(symbol, start_date, end_date)
            
            if historical_data.empty:
                raise ValueError(f"無法獲取 {symbol} 的歷史數據")
            
            # 2. 初始化回測環境
            self._update_progress(10, "正在初始化回測環境...")
            backtest_result = BacktestResult(
                start_date=start_date,
                end_date=end_date
            )
            
            # 3. 執行動態策略回測
            self._update_progress(20, "正在執行動態策略回測...")
            dynamic_results = self._run_dynamic_strategy_backtest(historical_data, initial_capital)
            
            # 4. 執行原始策略回測（比較基準）
            self._update_progress(60, "正在執行原始策略回測...")
            original_results = self._run_original_strategy_backtest(historical_data, initial_capital)
            
            # 5. 計算性能指標
            self._update_progress(80, "正在計算性能指標...")
            backtest_result = self._calculate_performance_metrics(
                backtest_result, dynamic_results, original_results, historical_data
            )
            
            # 6. 生成策略比較
            self._update_progress(90, "正在生成策略比較...")
            backtest_result.strategy_comparison = self._compare_strategies(
                dynamic_results, original_results
            )
            
            # 7. 保存回測結果
            self._update_progress(95, "正在保存回測結果...")
            self._save_backtest_results(backtest_result)
            
            self._update_progress(100, "回測完成")
            logger.info(f"動態策略回測完成: 總交易 {backtest_result.total_trades}, 改善 {backtest_result.total_improvement:,.0f} TWD")
            
            return backtest_result
            
        except Exception as e:
            logger.error(f"回測執行失敗: {e}")
            raise
        finally:
            self.is_running = False
    
    def _get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """獲取歷史數據"""
        try:
            # 嘗試從歷史數據管理器獲取
            data = self.historical_data_manager.get_data(symbol, start_date, end_date)
            
            if data is None or data.empty:
                # 生成模擬數據
                logger.warning(f"無法獲取 {symbol} 真實數據，使用模擬數據")
                data = self._generate_mock_data(symbol, start_date, end_date)
            
            return data
            
        except Exception as e:
            logger.warning(f"獲取歷史數據失敗: {e}，使用模擬數據")
            return self._generate_mock_data(symbol, start_date, end_date)
    
    def _generate_mock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """生成模擬歷史數據"""
        # 計算數據點數量（每分鐘一個數據點）
        total_minutes = int((end_date - start_date).total_seconds() / 60)
        
        # 生成時間序列
        timestamps = pd.date_range(start=start_date, end=end_date, freq='1min')[:total_minutes]
        
        # 基礎價格（根據交易對設定）
        base_prices = {
            'BTCTWD': 3400000,
            'ETHTWD': 120000,
            'ADATWD': 15,
            'DOTTWD': 200
        }
        base_price = base_prices.get(symbol, 3400000)
        
        # 生成價格數據（隨機遊走 + 趨勢）
        np.random.seed(42)  # 確保可重現
        returns = np.random.normal(0, 0.001, len(timestamps))  # 0.1% 標準差
        
        # 添加一些趨勢和週期性
        trend = np.sin(np.arange(len(timestamps)) * 2 * np.pi / (24 * 60)) * 0.0005  # 日內週期
        returns += trend
        
        # 計算價格
        prices = base_price * np.exp(np.cumsum(returns))
        
        # 生成 OHLCV 數據
        data = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.0005, len(prices)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.0005, len(prices)))),
            'close': prices,
            'volume': np.random.randint(100, 1000, len(prices))
        })
        
        # 確保 high >= close >= low 和 high >= open >= low
        data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
        data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
        
        data.set_index('timestamp', inplace=True)
        
        logger.info(f"生成模擬數據: {len(data)} 個數據點，價格範圍 {data['close'].min():,.0f} - {data['close'].max():,.0f}")
        return data
    
    def _run_dynamic_strategy_backtest(self, data: pd.DataFrame, initial_capital: float) -> List[DynamicTradeResult]:
        """執行動態策略回測"""
        dynamic_results = []
        
        try:
            # 重置動態信號系統
            self.dynamic_signals = DynamicTradingSignals(self.config)
            
            total_rows = len(data)
            processed = 0
            
            for timestamp, row in data.iterrows():
                if not self.is_running:
                    break
                
                # 準備價格數據
                price_data = {
                    'timestamp': timestamp,
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }
                
                # 處理動態信號
                signal_result = self.dynamic_signals.process_price_update(price_data)
                
                if signal_result:
                    dynamic_results.append(signal_result)
                    logger.debug(f"動態交易: {signal_result.trade_id}, 改善: {signal_result.price_improvement:,.0f}")
                
                # 更新進度
                processed += 1
                if processed % 1000 == 0:
                    progress = 20 + (processed / total_rows) * 40  # 20-60% 進度
                    self._update_progress(progress, f"處理動態策略: {processed}/{total_rows}")
            
            logger.info(f"動態策略回測完成: {len(dynamic_results)} 筆交易")
            return dynamic_results
            
        except Exception as e:
            logger.error(f"動態策略回測失敗: {e}")
            return []
    
    def _run_original_strategy_backtest(self, data: pd.DataFrame, initial_capital: float) -> List[Dict[str, Any]]:
        """執行原始策略回測（簡化版）"""
        original_results = []
        
        try:
            # 計算 MACD
            close_prices = data['close']
            ema12 = close_prices.ewm(span=12).mean()
            ema26 = close_prices.ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            # 生成交易信號
            position = 0  # 0: 無持倉, 1: 持倉
            entry_price = 0
            
            for i in range(1, len(data)):
                if not self.is_running:
                    break
                
                current_time = data.index[i]
                current_price = data.iloc[i]['close']
                
                # 買入信號：MACD 線上穿信號線
                if (position == 0 and 
                    macd_line.iloc[i] > signal_line.iloc[i] and 
                    macd_line.iloc[i-1] <= signal_line.iloc[i-1]):
                    
                    position = 1
                    entry_price = current_price
                    
                    original_results.append({
                        'type': 'buy',
                        'timestamp': current_time,
                        'price': current_price,
                        'signal': 'macd_cross_up'
                    })
                
                # 賣出信號：MACD 線下穿信號線
                elif (position == 1 and 
                      macd_line.iloc[i] < signal_line.iloc[i] and 
                      macd_line.iloc[i-1] >= signal_line.iloc[i-1]):
                    
                    position = 0
                    profit = current_price - entry_price
                    
                    original_results.append({
                        'type': 'sell',
                        'timestamp': current_time,
                        'price': current_price,
                        'entry_price': entry_price,
                        'profit': profit,
                        'signal': 'macd_cross_down'
                    })
            
            logger.info(f"原始策略回測完成: {len(original_results)} 筆信號")
            return original_results
            
        except Exception as e:
            logger.error(f"原始策略回測失敗: {e}")
            return []
    
    def _calculate_performance_metrics(self, 
                                     backtest_result: BacktestResult,
                                     dynamic_results: List[DynamicTradeResult],
                                     original_results: List[Dict[str, Any]],
                                     data: pd.DataFrame) -> BacktestResult:
        """計算性能指標"""
        
        # 動態策略指標
        backtest_result.dynamic_trades = dynamic_results
        backtest_result.total_trades = len(dynamic_results)
        
        if dynamic_results:
            backtest_result.successful_trades = sum(1 for r in dynamic_results if r.price_improvement > 0)
            backtest_result.total_improvement = sum(r.price_improvement for r in dynamic_results)
            backtest_result.win_rate = (backtest_result.successful_trades / backtest_result.total_trades) * 100
            
            # 計算平均交易持續時間
            durations = [r.tracking_duration for r in dynamic_results]
            if durations:
                avg_duration_seconds = sum(d.total_seconds() for d in durations) / len(durations)
                backtest_result.average_trade_duration = timedelta(seconds=avg_duration_seconds)
        
        # 計算追蹤統計
        tracking_stats = TrackingStatistics()
        for result in dynamic_results:
            tracking_stats.update_with_result(result)
        backtest_result.tracking_statistics = tracking_stats
        
        # 計算風險指標（簡化）
        if dynamic_results:
            improvements = [r.price_improvement for r in dynamic_results]
            if len(improvements) > 1:
                # 簡化的最大回撤計算
                cumulative_pnl = np.cumsum(improvements)
                running_max = np.maximum.accumulate(cumulative_pnl)
                drawdowns = running_max - cumulative_pnl
                backtest_result.max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
                
                # 簡化的夏普比率計算
                if np.std(improvements) > 0:
                    backtest_result.sharpe_ratio = np.mean(improvements) / np.std(improvements)
        
        return backtest_result
    
    def _compare_strategies(self, 
                          dynamic_results: List[DynamicTradeResult],
                          original_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """比較動態策略與原始策略"""
        
        # 計算原始策略獲利
        original_profit = 0.0
        original_trades = 0
        
        for i in range(0, len(original_results), 2):  # 買賣成對
            if i + 1 < len(original_results):
                buy_signal = original_results[i]
                sell_signal = original_results[i + 1]
                
                if buy_signal['type'] == 'buy' and sell_signal['type'] == 'sell':
                    profit = sell_signal['profit']
                    original_profit += profit
                    original_trades += 1
        
        # 計算動態策略獲利
        dynamic_profit = sum(r.price_improvement for r in dynamic_results)
        dynamic_trades = len(dynamic_results)
        
        # 計算改善
        improvement = dynamic_profit - original_profit
        improvement_percentage = (improvement / max(abs(original_profit), 1)) * 100
        
        comparison = {
            'original_strategy': {
                'total_trades': original_trades,
                'total_profit': original_profit,
                'average_per_trade': original_profit / max(original_trades, 1)
            },
            'dynamic_strategy': {
                'total_trades': dynamic_trades,
                'total_profit': dynamic_profit,
                'average_per_trade': dynamic_profit / max(dynamic_trades, 1)
            },
            'improvement': {
                'absolute': improvement,
                'percentage': improvement_percentage,
                'successful_improvements': sum(1 for r in dynamic_results if r.price_improvement > 0),
                'success_rate': (sum(1 for r in dynamic_results if r.price_improvement > 0) / max(dynamic_trades, 1)) * 100
            }
        }
        
        return comparison
    
    def _save_backtest_results(self, backtest_result: BacktestResult):
        """保存回測結果"""
        try:
            # 保存動態交易結果到數據管理器
            for trade_result in backtest_result.dynamic_trades:
                self.data_manager.store_trade_result(trade_result)
            
            # 保存統計信息
            if backtest_result.tracking_statistics:
                self.data_manager.store_daily_statistics(
                    backtest_result.end_date, 
                    backtest_result.tracking_statistics
                )
            
            logger.info(f"回測結果已保存: {len(backtest_result.dynamic_trades)} 筆交易")
            
        except Exception as e:
            logger.error(f"保存回測結果失敗: {e}")
    
    def _update_progress(self, progress: float, message: str):
        """更新進度"""
        if self.progress_callback:
            self.progress_callback(progress, message)
        logger.debug(f"回測進度: {progress:.1f}% - {message}")
    
    def stop_backtest(self):
        """停止回測"""
        self.is_running = False
        logger.info("回測已停止")
    
    def get_backtest_status(self) -> Dict[str, Any]:
        """獲取回測狀態"""
        return {
            'is_running': self.is_running,
            'current_backtest_id': self.current_backtest_id,
            'config_summary': {
                'buy_window_hours': self.config.window_config.buy_window_hours,
                'sell_window_hours': self.config.window_config.sell_window_hours,
                'reversal_threshold': self.config.detection_config.reversal_threshold,
                'max_concurrent_windows': self.config.window_config.max_concurrent_windows
            }
        }
    
    def run_parameter_optimization(self, 
                                 symbol: str,
                                 start_date: datetime,
                                 end_date: datetime,
                                 parameter_ranges: Dict[str, List[float]]) -> Dict[str, Any]:
        """參數優化回測"""
        
        logger.info(f"開始參數優化: {len(parameter_ranges)} 個參數")
        
        best_result = None
        best_params = None
        best_improvement = float('-inf')
        
        optimization_results = []
        
        try:
            # 生成參數組合
            param_combinations = self._generate_parameter_combinations(parameter_ranges)
            
            for i, params in enumerate(param_combinations):
                if not self.is_running:
                    break
                
                # 更新配置
                test_config = self._create_config_with_params(params)
                original_config = self.config
                self.config = test_config
                self.dynamic_signals = DynamicTradingSignals(test_config)
                
                try:
                    # 執行回測
                    result = self.run_backtest(symbol, start_date, end_date)
                    
                    # 評估結果
                    improvement = result.total_improvement
                    
                    optimization_results.append({
                        'parameters': params,
                        'improvement': improvement,
                        'win_rate': result.win_rate,
                        'total_trades': result.total_trades,
                        'sharpe_ratio': result.sharpe_ratio
                    })
                    
                    # 更新最佳結果
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_result = result
                        best_params = params
                    
                    logger.info(f"參數組合 {i+1}/{len(param_combinations)}: 改善 {improvement:,.0f}")
                    
                except Exception as e:
                    logger.error(f"參數組合 {i+1} 回測失敗: {e}")
                
                finally:
                    # 恢復原始配置
                    self.config = original_config
                    self.dynamic_signals = DynamicTradingSignals(original_config)
            
            return {
                'best_parameters': best_params,
                'best_result': best_result.get_summary() if best_result else None,
                'best_improvement': best_improvement,
                'all_results': optimization_results,
                'optimization_summary': {
                    'total_combinations': len(param_combinations),
                    'completed_combinations': len(optimization_results),
                    'best_improvement': best_improvement
                }
            }
            
        except Exception as e:
            logger.error(f"參數優化失敗: {e}")
            return {'error': str(e)}
    
    def _generate_parameter_combinations(self, parameter_ranges: Dict[str, List[float]]) -> List[Dict[str, float]]:
        """生成參數組合"""
        import itertools
        
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        
        combinations = []
        for combo in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combo))
            combinations.append(param_dict)
        
        return combinations
    
    def _create_config_with_params(self, params: Dict[str, float]) -> DynamicTradingConfig:
        """根據參數創建配置"""
        from .dynamic_trading_config import TrackingWindowConfig, ExtremeDetectionConfig
        
        # 複製當前配置
        new_config = DynamicTradingConfig(
            window_config=TrackingWindowConfig(
                buy_window_hours=params.get('buy_window_hours', self.config.window_config.buy_window_hours),
                sell_window_hours=params.get('sell_window_hours', self.config.window_config.sell_window_hours),
                max_concurrent_windows=int(params.get('max_concurrent_windows', self.config.window_config.max_concurrent_windows))
            ),
            detection_config=ExtremeDetectionConfig(
                reversal_threshold=params.get('reversal_threshold', self.config.detection_config.reversal_threshold),
                confirmation_periods=int(params.get('confirmation_periods', self.config.detection_config.confirmation_periods)),
                sensitivity=params.get('sensitivity', self.config.detection_config.sensitivity)
            ),
            risk_config=self.config.risk_config,
            performance_config=self.config.performance_config,
            ui_config=self.config.ui_config
        )
        
        return new_config


# 工具函數
def create_dynamic_backtest_engine(config: Optional[DynamicTradingConfig] = None) -> DynamicBacktestEngine:
    """創建動態回測引擎"""
    if config is None:
        config = DynamicTradingConfig()
    
    return DynamicBacktestEngine(config)


def run_quick_backtest(symbol: str = "BTCTWD", 
                      days: int = 7,
                      config: Optional[DynamicTradingConfig] = None) -> BacktestResult:
    """快速回測函數"""
    if config is None:
        config = DynamicTradingConfig()
    
    engine = DynamicBacktestEngine(config)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return engine.run_backtest(symbol, start_date, end_date)