#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 價格追蹤器
管理多個並發的價格追蹤窗口，實現智能的價格追蹤和極值點記錄
"""

import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
import logging
from collections import defaultdict
import time

from .dynamic_trading_data_structures import (
    TrackingWindow, PricePoint, SignalType, WindowStatus, 
    ExecutionReason, create_window_id
)
from .dynamic_trading_config import TrackingWindowConfig, PerformanceConfig
from .extreme_point_detector import ExtremePointDetector, ReversalSignal

logger = logging.getLogger(__name__)

class PriceTracker:
    """價格追蹤器 - 管理多個並發的價格追蹤窗口"""
    
    def __init__(self, window_config: TrackingWindowConfig, 
                 performance_config: PerformanceConfig):
        self.window_config = window_config
        self.performance_config = performance_config
        
        # 追蹤窗口存儲
        self.active_windows: Dict[str, TrackingWindow] = {}
        self.completed_windows: Dict[str, TrackingWindow] = {}
        
        # 極值檢測器存儲
        self.detectors: Dict[str, ExtremePointDetector] = {}
        
        # 線程安全鎖
        self._lock = threading.RLock()
        
        # 回調函數
        self.on_window_created: Optional[Callable[[TrackingWindow], None]] = None
        self.on_window_updated: Optional[Callable[[TrackingWindow], None]] = None
        self.on_window_completed: Optional[Callable[[TrackingWindow], None]] = None
        self.on_reversal_detected: Optional[Callable[[str, ReversalSignal], None]] = None
        
        # 統計信息
        self.stats = {
            'total_windows_created': 0,
            'active_windows_count': 0,
            'completed_windows_count': 0,
            'total_price_points_processed': 0,
            'memory_usage_mb': 0.0
        }
        
        logger.info("價格追蹤器初始化完成")
    
    def start_tracking(self, signal_type: SignalType, start_price: float, 
                      start_time: datetime, detector_config) -> str:
        """
        開始價格追蹤
        
        Args:
            signal_type: 信號類型 (買入/賣出)
            start_price: 起始價格
            start_time: 開始時間
            detector_config: 極值檢測器配置
            
        Returns:
            追蹤窗口 ID
        """
        with self._lock:
            try:
                # 檢查並發窗口限制（從配置中獲取）
                max_windows = getattr(self.window_config, 'max_concurrent_windows', 20)
                if len(self.active_windows) >= max_windows:
                    logger.warning(f"達到最大並發窗口數限制: {max_windows}")
                    return ""
                
                # 創建窗口 ID
                window_id = create_window_id(signal_type, start_time)
                
                # 確定窗口持續時間
                if signal_type == SignalType.BUY:
                    duration = self.window_config.get_buy_window_duration()
                else:
                    duration = self.window_config.get_sell_window_duration()
                
                end_time = start_time + duration
                
                # 創建追蹤窗口
                window = TrackingWindow(
                    window_id=window_id,
                    signal_type=signal_type,
                    start_time=start_time,
                    end_time=end_time,
                    start_price=start_price,
                    current_extreme_price=start_price,
                    extreme_time=start_time
                )
                
                # 創建極值檢測器
                detector = ExtremePointDetector(detector_config)
                detector.reset(signal_type)
                
                # 添加起始價格點
                start_point = PricePoint(
                    timestamp=start_time,
                    price=start_price,
                    volume=0.0  # 起始點沒有成交量數據
                )
                window.add_price_point(start_point)
                detector.add_price_point(start_point)
                
                # 存儲窗口和檢測器
                self.active_windows[window_id] = window
                self.detectors[window_id] = detector
                
                # 更新統計
                self.stats['total_windows_created'] += 1
                self.stats['active_windows_count'] = len(self.active_windows)
                
                logger.info(f"開始追蹤窗口: {window_id}, 類型: {signal_type.value}, "
                          f"起始價格: {start_price:,.0f}, 持續時間: {duration}")
                
                # 觸發回調
                if self.on_window_created:
                    self.on_window_created(window)
                
                return window_id
                
            except Exception as e:
                logger.error(f"開始追蹤失敗: {e}")
                return ""
    
    def update_price(self, window_id: str, current_price: float, 
                    current_time: datetime, volume: float = 0.0) -> bool:
        """
        更新價格數據
        
        Args:
            window_id: 窗口 ID
            current_price: 當前價格
            current_time: 當前時間
            volume: 成交量
            
        Returns:
            是否更新成功
        """
        with self._lock:
            try:
                # 檢查窗口是否存在
                if window_id not in self.active_windows:
                    logger.warning(f"窗口不存在: {window_id}")
                    return False
                
                window = self.active_windows[window_id]
                detector = self.detectors[window_id]
                
                # 檢查窗口是否已過期
                if current_time > window.end_time:
                    logger.info(f"窗口已過期: {window_id}")
                    self._complete_window(window_id, ExecutionReason.WINDOW_TIMEOUT)
                    return False
                
                # 創建價格點
                price_point = PricePoint(
                    timestamp=current_time,
                    price=current_price,
                    volume=volume
                )
                
                # 添加到窗口
                window.add_price_point(price_point)
                
                # 添加到檢測器並檢查是否為極值
                is_extreme = detector.add_price_point(price_point)
                
                # 檢測反轉信號
                reversal = detector.detect_price_reversal()
                if reversal:
                    logger.info(f"窗口 {window_id} 檢測到反轉信號")
                    
                    # 觸發反轉回調
                    if self.on_reversal_detected:
                        self.on_reversal_detected(window_id, reversal)
                    
                    # 完成窗口
                    self._complete_window(window_id, ExecutionReason.REVERSAL_DETECTED)
                    return True
                
                # 更新統計
                self.stats['total_price_points_processed'] += 1
                
                # 觸發更新回調
                if self.on_window_updated:
                    self.on_window_updated(window)
                
                return True
                
            except Exception as e:
                logger.error(f"更新價格失敗: {e}")
                return False
    
    def _complete_window(self, window_id: str, reason: ExecutionReason):
        """完成追蹤窗口"""
        try:
            if window_id not in self.active_windows:
                return
            
            window = self.active_windows[window_id]
            
            # 更新窗口狀態
            window.status = WindowStatus.COMPLETED
            window.execution_reason = reason
            
            # 計算最終統計
            window.price_volatility = window.calculate_volatility()
            
            # 移動到完成列表
            self.completed_windows[window_id] = window
            del self.active_windows[window_id]
            del self.detectors[window_id]
            
            # 更新統計
            self.stats['active_windows_count'] = len(self.active_windows)
            self.stats['completed_windows_count'] = len(self.completed_windows)
            
            logger.info(f"窗口完成: {window_id}, 原因: {reason.value}, "
                       f"價格改善: {window.get_price_improvement():,.0f}")
            
            # 觸發完成回調
            if self.on_window_completed:
                self.on_window_completed(window)
                
        except Exception as e:
            logger.error(f"完成窗口失敗: {e}")
    
    def get_active_window(self, window_id: str) -> Optional[TrackingWindow]:
        """獲取活躍窗口"""
        with self._lock:
            return self.active_windows.get(window_id)
    
    def get_completed_window(self, window_id: str) -> Optional[TrackingWindow]:
        """獲取已完成窗口"""
        with self._lock:
            return self.completed_windows.get(window_id)
    
    def get_all_active_windows(self) -> Dict[str, TrackingWindow]:
        """獲取所有活躍窗口"""
        with self._lock:
            return self.active_windows.copy()
    
    def get_all_completed_windows(self) -> Dict[str, TrackingWindow]:
        """獲取所有已完成窗口"""
        with self._lock:
            return self.completed_windows.copy()
    
    def get_extreme_point(self, window_id: str) -> Optional[PricePoint]:
        """獲取窗口的當前極值點"""
        with self._lock:
            if window_id in self.detectors:
                return self.detectors[window_id].get_current_extreme()
            elif window_id in self.active_windows:
                window = self.active_windows[window_id]
                # 從價格歷史中找到極值點
                for point in reversed(window.price_history):
                    if point.is_extreme:
                        return point
            return None
    
    def force_complete_window(self, window_id: str, 
                            reason: ExecutionReason = ExecutionReason.MANUAL_OVERRIDE) -> bool:
        """強制完成窗口"""
        with self._lock:
            if window_id in self.active_windows:
                self._complete_window(window_id, reason)
                return True
            return False
    
    def cleanup_expired_windows(self, current_time: datetime) -> int:
        """清理過期窗口"""
        with self._lock:
            expired_windows = []
            
            for window_id, window in self.active_windows.items():
                if current_time > window.end_time:
                    expired_windows.append(window_id)
            
            for window_id in expired_windows:
                self._complete_window(window_id, ExecutionReason.WINDOW_TIMEOUT)
            
            logger.info(f"清理了 {len(expired_windows)} 個過期窗口")
            return len(expired_windows)
    
    def cleanup_old_completed_windows(self, retention_hours: int = 24) -> int:
        """清理舊的已完成窗口"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            old_windows = []
            
            for window_id, window in self.completed_windows.items():
                if window.end_time < cutoff_time:
                    old_windows.append(window_id)
            
            for window_id in old_windows:
                del self.completed_windows[window_id]
            
            # 更新統計
            self.stats['completed_windows_count'] = len(self.completed_windows)
            
            logger.info(f"清理了 {len(old_windows)} 個舊的已完成窗口")
            return len(old_windows)
    
    def get_statistics(self) -> Dict:
        """獲取追蹤器統計信息"""
        with self._lock:
            # 計算內存使用情況
            memory_usage = self._estimate_memory_usage()
            self.stats['memory_usage_mb'] = memory_usage
            
            # 計算窗口類型分布
            active_buy_windows = sum(1 for w in self.active_windows.values() 
                                   if w.signal_type == SignalType.BUY)
            active_sell_windows = len(self.active_windows) - active_buy_windows
            
            completed_buy_windows = sum(1 for w in self.completed_windows.values() 
                                      if w.signal_type == SignalType.BUY)
            completed_sell_windows = len(self.completed_windows) - completed_buy_windows
            
            # 計算平均追蹤時間
            avg_tracking_time = 0.0
            if self.completed_windows:
                total_time = sum(w.get_tracking_duration().total_seconds() 
                               for w in self.completed_windows.values())
                avg_tracking_time = total_time / len(self.completed_windows) / 60  # 分鐘
            
            return {
                **self.stats,
                'active_windows': {
                    'total': len(self.active_windows),
                    'buy_windows': active_buy_windows,
                    'sell_windows': active_sell_windows
                },
                'completed_windows': {
                    'total': len(self.completed_windows),
                    'buy_windows': completed_buy_windows,
                    'sell_windows': completed_sell_windows
                },
                'performance': {
                    'average_tracking_time_minutes': avg_tracking_time,
                    'memory_usage_mb': memory_usage
                }
            }
    
    def _estimate_memory_usage(self) -> float:
        """估算內存使用量（MB）"""
        try:
            # 簡單估算：每個窗口約 1KB，每個價格點約 100 bytes
            window_memory = (len(self.active_windows) + len(self.completed_windows)) * 1024
            
            price_point_memory = 0
            for window in list(self.active_windows.values()) + list(self.completed_windows.values()):
                price_point_memory += len(window.price_history) * 100
            
            total_bytes = window_memory + price_point_memory
            return total_bytes / (1024 * 1024)  # 轉換為 MB
            
        except Exception as e:
            logger.error(f"估算內存使用失敗: {e}")
            return 0.0
    
    def get_window_summary(self, window_id: str) -> Optional[Dict]:
        """獲取窗口摘要信息"""
        with self._lock:
            window = self.active_windows.get(window_id) or self.completed_windows.get(window_id)
            if not window:
                return None
            
            extreme_point = self.get_extreme_point(window_id)
            
            return {
                'window_id': window_id,
                'signal_type': window.signal_type.value,
                'status': window.status.value,
                'start_time': window.start_time,
                'end_time': window.end_time,
                'start_price': window.start_price,
                'current_extreme_price': window.current_extreme_price,
                'price_improvement': window.get_price_improvement(),
                'improvement_percentage': window.get_improvement_percentage(),
                'tracking_duration': window.get_tracking_duration(),
                'price_points_count': len(window.price_history),
                'volatility': window.price_volatility,
                'execution_reason': window.execution_reason.value if window.execution_reason else None,
                'extreme_point': {
                    'price': extreme_point.price if extreme_point else None,
                    'timestamp': extreme_point.timestamp if extreme_point else None
                } if extreme_point else None
            }
    
    def set_callbacks(self, on_created: Optional[Callable] = None,
                     on_updated: Optional[Callable] = None,
                     on_completed: Optional[Callable] = None,
                     on_reversal: Optional[Callable] = None):
        """設置回調函數"""
        self.on_window_created = on_created
        self.on_window_updated = on_updated
        self.on_window_completed = on_completed
        self.on_reversal_detected = on_reversal
        
        logger.info("回調函數設置完成")
    
    def shutdown(self):
        """關閉追蹤器"""
        with self._lock:
            # 強制完成所有活躍窗口
            active_window_ids = list(self.active_windows.keys())
            for window_id in active_window_ids:
                self._complete_window(window_id, ExecutionReason.SYSTEM_ERROR)
            
            logger.info("價格追蹤器已關閉")

# 工具函數
def create_price_tracker(window_config: Optional[TrackingWindowConfig] = None,
                        performance_config: Optional[PerformanceConfig] = None) -> PriceTracker:
    """創建價格追蹤器"""
    if window_config is None:
        from .dynamic_trading_config import TrackingWindowConfig
        window_config = TrackingWindowConfig()
    
    if performance_config is None:
        from .dynamic_trading_config import PerformanceConfig
        performance_config = PerformanceConfig()
    
    return PriceTracker(window_config, performance_config)

class TrackingManager:
    """追蹤管理器 - 高級追蹤功能的封裝"""
    
    def __init__(self, tracker: PriceTracker):
        self.tracker = tracker
        self.auto_cleanup_enabled = True
        self.cleanup_interval = 300  # 5分鐘
        self.last_cleanup_time = datetime.now()
        
    def auto_cleanup(self, current_time: datetime):
        """自動清理過期窗口"""
        if not self.auto_cleanup_enabled:
            return
        
        if (current_time - self.last_cleanup_time).total_seconds() >= self.cleanup_interval:
            expired_count = self.tracker.cleanup_expired_windows(current_time)
            old_count = self.tracker.cleanup_old_completed_windows(24)
            
            if expired_count > 0 or old_count > 0:
                logger.info(f"自動清理完成: 過期窗口 {expired_count}, 舊窗口 {old_count}")
            
            self.last_cleanup_time = current_time
    
    def get_performance_metrics(self) -> Dict:
        """獲取性能指標"""
        stats = self.tracker.get_statistics()
        
        # 計算額外的性能指標
        total_windows = stats['total_windows_created']
        active_ratio = stats['active_windows_count'] / max(total_windows, 1) * 100
        
        return {
            'total_windows_created': total_windows,
            'active_windows_ratio': active_ratio,
            'memory_usage_mb': stats['memory_usage_mb'],
            'average_tracking_time': stats['performance']['average_tracking_time_minutes'],
            'price_points_per_window': stats['total_price_points_processed'] / max(total_windows, 1)
        }
    
    def enable_auto_cleanup(self, interval_seconds: int = 300):
        """啟用自動清理"""
        self.auto_cleanup_enabled = True
        self.cleanup_interval = interval_seconds
        logger.info(f"自動清理已啟用，間隔: {interval_seconds} 秒")
    
    def disable_auto_cleanup(self):
        """禁用自動清理"""
        self.auto_cleanup_enabled = False
        logger.info("自動清理已禁用")