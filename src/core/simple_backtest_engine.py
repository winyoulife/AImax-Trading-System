#!/usr/bin/env python3
"""
簡化版動態回測引擎 - 用於系統集成測試
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

from .dynamic_trading_config import DynamicTradingConfig

@dataclass
class SimpleBacktestResult:
    """簡化版回測結果"""
    start_date: datetime
    end_date: datetime
    total_trades: int = 0
    successful_trades: int = 0
    success_rate: float = 0.0
    total_improvement: float = 0.0
    average_improvement: float = 0.0
    best_improvement: float = 0.0
    worst_improvement: float = 0.0
    execution_time: float = 0.0

class SimpleBacktestEngine:
    """簡化版動態回測引擎"""
    
    def __init__(self, config: DynamicTradingConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SimpleBacktestEngine")
        self.logger.info("簡化版回測引擎初始化完成")
    
    def run_backtest(self, data: pd.DataFrame) -> SimpleBacktestResult:
        """執行回測"""
        try:
            start_time = datetime.now()
            
            # 數據預處理
            processed_data = self._preprocess_data(data)
            
            # 模擬交易執行
            trades = self._simulate_trading(processed_data)
            
            # 計算結果
            result = self._calculate_results(trades, start_time)
            
            self.logger.info(f"回測完成: {result.total_trades} 筆交易")
            return result
            
        except Exception as e:
            self.logger.error(f"回測執行失敗: {e}")
            raise
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """預處理數據"""
        if data.empty:
            raise ValueError("數據不能為空")
        
        # 檢查必要的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的數據列: {missing_columns}")
        
        # 確保時間索引
        if 'timestamp' in data.columns:
            data = data.set_index('timestamp')
        
        # 數據類型轉換和清理
        for col in required_columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 移除無效數據
        data = data.dropna()
        
        if data.empty:
            raise ValueError("處理後數據為空")
        
        return data
    
    def _simulate_trading(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """模擬交易執行"""
        trades = []
        
        # 簡單的模擬交易邏輯
        for i in range(0, len(data), 100):  # 每100個數據點模擬一筆交易
            if i + 50 < len(data):
                entry_price = data.iloc[i]['close']
                exit_price = data.iloc[i + 50]['close']
                
                # 隨機決定買入或賣出
                signal_type = np.random.choice(['buy', 'sell'])
                
                if signal_type == 'buy':
                    improvement = exit_price - entry_price
                else:
                    improvement = entry_price - exit_price
                
                trades.append({
                    'signal_type': signal_type,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'improvement': improvement,
                    'entry_time': data.index[i],
                    'exit_time': data.index[i + 50]
                })
        
        return trades
    
    def _calculate_results(self, trades: List[Dict[str, Any]], start_time: datetime) -> SimpleBacktestResult:
        """計算回測結果"""
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if not trades:
            return SimpleBacktestResult(
                start_date=start_time,
                end_date=end_time,
                execution_time=execution_time
            )
        
        # 計算統計指標
        improvements = [trade['improvement'] for trade in trades]
        successful_trades = sum(1 for imp in improvements if imp > 0)
        
        total_trades = len(trades)
        success_rate = (successful_trades / total_trades) * 100 if total_trades > 0 else 0
        total_improvement = sum(improvements)
        average_improvement = total_improvement / total_trades if total_trades > 0 else 0
        best_improvement = max(improvements) if improvements else 0
        worst_improvement = min(improvements) if improvements else 0
        
        return SimpleBacktestResult(
            start_date=start_time,
            end_date=end_time,
            total_trades=total_trades,
            successful_trades=successful_trades,
            success_rate=success_rate,
            total_improvement=total_improvement,
            average_improvement=average_improvement,
            best_improvement=best_improvement,
            worst_improvement=worst_improvement,
            execution_time=execution_time
        )
    
    def cleanup(self):
        """清理資源"""
        self.logger.info("回測引擎資源清理完成")