#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 核心數據結構
定義系統中使用的所有數據類和枚舉
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

class SignalType(Enum):
    """交易信號類型"""
    BUY = "buy"
    SELL = "sell"

class WindowStatus(Enum):
    """追蹤窗口狀態"""
    ACTIVE = "active"           # 活躍追蹤中
    COMPLETED = "completed"     # 正常完成
    EXPIRED = "expired"         # 超時結束
    CANCELLED = "cancelled"     # 被取消

class ExecutionReason(Enum):
    """交易執行原因"""
    REVERSAL_DETECTED = "reversal"      # 檢測到價格反轉
    WINDOW_TIMEOUT = "timeout"          # 窗口超時
    RISK_CONTROL = "risk_control"       # 風險控制觸發
    MANUAL_OVERRIDE = "manual"          # 手動覆蓋
    SYSTEM_ERROR = "error"              # 系統錯誤

@dataclass
class PricePoint:
    """價格點數據結構"""
    timestamp: datetime
    price: float
    volume: float
    is_extreme: bool = False            # 是否為極值點
    reversal_strength: float = 0.0      # 反轉強度 (0-1)
    
    def __post_init__(self):
        """數據驗證"""
        if self.price <= 0:
            raise ValueError("價格必須大於 0")
        if self.volume < 0:
            raise ValueError("成交量不能為負數")
        if not 0 <= self.reversal_strength <= 1:
            raise ValueError("反轉強度必須在 0-1 之間")

@dataclass
class TrackingWindow:
    """追蹤窗口數據結構"""
    window_id: str
    signal_type: SignalType
    start_time: datetime
    end_time: datetime
    start_price: float
    current_extreme_price: float
    extreme_time: datetime
    price_history: List[PricePoint] = field(default_factory=list)
    status: WindowStatus = WindowStatus.ACTIVE
    execution_reason: Optional[ExecutionReason] = None
    
    # 統計數據
    max_price: float = 0.0
    min_price: float = float('inf')
    price_volatility: float = 0.0
    
    def __post_init__(self):
        """初始化後處理"""
        if self.start_price <= 0:
            raise ValueError("起始價格必須大於 0")
        
        # 初始化極值價格
        if self.current_extreme_price == 0:
            self.current_extreme_price = self.start_price
            
        # 初始化統計數據
        if self.max_price == 0.0:
            self.max_price = self.start_price
        if self.min_price == float('inf'):
            self.min_price = self.start_price
    
    def add_price_point(self, price_point: PricePoint):
        """添加價格點"""
        self.price_history.append(price_point)
        
        # 更新統計數據
        self.max_price = max(self.max_price, price_point.price)
        self.min_price = min(self.min_price, price_point.price)
        
        # 更新極值價格
        if self.signal_type == SignalType.BUY:
            # 買入信號：尋找最低點
            if price_point.price < self.current_extreme_price:
                self.current_extreme_price = price_point.price
                self.extreme_time = price_point.timestamp
        else:
            # 賣出信號：尋找最高點
            if price_point.price > self.current_extreme_price:
                self.current_extreme_price = price_point.price
                self.extreme_time = price_point.timestamp
    
    def get_price_improvement(self) -> float:
        """計算價格改善幅度"""
        if self.signal_type == SignalType.BUY:
            # 買入：起始價格 - 極值價格 = 節省的成本
            return self.start_price - self.current_extreme_price
        else:
            # 賣出：極值價格 - 起始價格 = 額外的收益
            return self.current_extreme_price - self.start_price
    
    def get_improvement_percentage(self) -> float:
        """計算價格改善百分比"""
        improvement = self.get_price_improvement()
        return (improvement / self.start_price) * 100
    
    def get_tracking_duration(self) -> timedelta:
        """獲取追蹤持續時間"""
        if self.price_history:
            last_point = self.price_history[-1]
            return last_point.timestamp - self.start_time
        return timedelta(0)
    
    def calculate_volatility(self) -> float:
        """計算價格波動率"""
        if len(self.price_history) < 2:
            return 0.0
        
        prices = [point.price for point in self.price_history]
        mean_price = sum(prices) / len(prices)
        variance = sum((price - mean_price) ** 2 for price in prices) / len(prices)
        return (variance ** 0.5) / mean_price * 100  # 百分比形式

@dataclass
class DynamicTradeResult:
    """動態交易結果數據結構"""
    trade_id: str
    signal_type: SignalType
    original_signal_time: datetime
    original_signal_price: float
    actual_execution_time: datetime
    actual_execution_price: float
    execution_reason: ExecutionReason
    
    # 性能指標
    price_improvement: float = 0.0
    improvement_percentage: float = 0.0
    tracking_duration: timedelta = field(default_factory=lambda: timedelta(0))
    
    # 關聯數據
    window_data: Optional[TrackingWindow] = None
    
    def __post_init__(self):
        """計算性能指標"""
        if self.signal_type == SignalType.BUY:
            self.price_improvement = self.original_signal_price - self.actual_execution_price
        else:
            self.price_improvement = self.actual_execution_price - self.original_signal_price
            
        if self.original_signal_price > 0:
            self.improvement_percentage = (self.price_improvement / self.original_signal_price) * 100
        
        self.tracking_duration = self.actual_execution_time - self.original_signal_time
    
    def is_improvement(self) -> bool:
        """判斷是否有改善"""
        return self.price_improvement > 0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        return {
            'trade_id': self.trade_id,
            'signal_type': self.signal_type.value,
            'price_improvement': self.price_improvement,
            'improvement_percentage': self.improvement_percentage,
            'tracking_duration_minutes': self.tracking_duration.total_seconds() / 60,
            'execution_reason': self.execution_reason.value,
            'is_improvement': self.is_improvement()
        }

@dataclass
class TrackingStatistics:
    """追蹤統計數據結構"""
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    
    # 成功改善統計
    improved_trades: int = 0
    total_improvement: float = 0.0
    average_improvement: float = 0.0
    best_improvement: float = 0.0
    worst_improvement: float = 0.0
    
    # 時間統計
    average_tracking_duration: timedelta = field(default_factory=lambda: timedelta(0))
    total_tracking_time: timedelta = field(default_factory=lambda: timedelta(0))
    
    # 執行原因統計
    reversal_executions: int = 0
    timeout_executions: int = 0
    risk_control_executions: int = 0
    
    def update_with_result(self, result: DynamicTradeResult):
        """使用交易結果更新統計"""
        self.total_signals += 1
        
        if result.signal_type == SignalType.BUY:
            self.buy_signals += 1
        else:
            self.sell_signals += 1
        
        # 更新改善統計
        if result.is_improvement():
            self.improved_trades += 1
            
        self.total_improvement += result.price_improvement
        self.average_improvement = self.total_improvement / self.total_signals
        
        self.best_improvement = max(self.best_improvement, result.price_improvement)
        if self.worst_improvement == 0.0:
            self.worst_improvement = result.price_improvement
        else:
            self.worst_improvement = min(self.worst_improvement, result.price_improvement)
        
        # 更新時間統計
        self.total_tracking_time += result.tracking_duration
        self.average_tracking_duration = timedelta(
            seconds=self.total_tracking_time.total_seconds() / self.total_signals
        )
        
        # 更新執行原因統計
        if result.execution_reason == ExecutionReason.REVERSAL_DETECTED:
            self.reversal_executions += 1
        elif result.execution_reason == ExecutionReason.WINDOW_TIMEOUT:
            self.timeout_executions += 1
        elif result.execution_reason == ExecutionReason.RISK_CONTROL:
            self.risk_control_executions += 1
    
    def get_success_rate(self) -> float:
        """獲取成功改善率"""
        if self.total_signals == 0:
            return 0.0
        return (self.improved_trades / self.total_signals) * 100
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取統計摘要"""
        return {
            'total_signals': self.total_signals,
            'buy_signals': self.buy_signals,
            'sell_signals': self.sell_signals,
            'improved_trades': self.improved_trades,
            'success_rate': self.get_success_rate(),
            'total_improvement': self.total_improvement,
            'average_improvement': self.average_improvement,
            'best_improvement': self.best_improvement,
            'worst_improvement': self.worst_improvement,
            'average_tracking_minutes': self.average_tracking_duration.total_seconds() / 60,
            'reversal_executions': self.reversal_executions,
            'timeout_executions': self.timeout_executions,
            'risk_control_executions': self.risk_control_executions
        }

# 工具函數
def create_window_id(signal_type: SignalType, timestamp: datetime) -> str:
    """創建窗口 ID"""
    return f"{signal_type.value}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

def create_trade_id(signal_type: SignalType, timestamp: datetime) -> str:
    """創建交易 ID"""
    return f"trade_{signal_type.value}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"