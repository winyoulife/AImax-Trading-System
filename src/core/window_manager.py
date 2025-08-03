#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 時間窗口管理器
處理追蹤窗口的生命週期管理，包括窗口超時檢測和自動關閉機制
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Set
import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from .dynamic_trading_data_structures import (
    TrackingWindow, WindowStatus, ExecutionReason, SignalType
)
from .dynamic_trading_config import TrackingWindowConfig

logger = logging.getLogger(__name__)

class WindowPriority(Enum):
    """窗口優先級"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class WindowSchedule:
    """窗口調度信息"""
    window_id: str
    expected_end_time: datetime
    priority: WindowPriority
    signal_type: SignalType
    created_time: datetime
    last_update_time: datetime
    timeout_callback: Optional[Callable] = None

class WindowManager:
    """時間窗口管理器 - 處理追蹤窗口的生命週期管理"""
    
    def __init__(self, config: TrackingWindowConfig):
        self.config = config
        
        # 窗口調度存儲
        self.active_schedules: Dict[str, WindowSchedule] = {}
        self.completed_schedules: Dict[str, WindowSchedule] = {}
        
        # 線程安全鎖
        self._lock = threading.RLock()
        
        # 監控線程
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._monitoring_interval = 30  # 30秒檢查一次
        
        # 回調函數
        self.on_window_timeout: Optional[Callable[[str, WindowSchedule], None]] = None
        self.on_window_warning: Optional[Callable[[str, WindowSchedule, float], None]] = None
        self.on_schedule_created: Optional[Callable[[WindowSchedule], None]] = None
        self.on_schedule_updated: Optional[Callable[[WindowSchedule], None]] = None
        
        # 統計信息
        self.stats = {
            'total_windows_scheduled': 0,
            'active_windows': 0,
            'completed_windows': 0,
            'timeout_windows': 0,
            'warning_issued': 0,
            'average_window_duration_minutes': 0.0
        }
        
        # 警告設置
        self.warning_threshold_minutes = 30  # 窗口結束前30分鐘發出警告
        self.issued_warnings: Set[str] = set()  # 已發出警告的窗口ID
        
        logger.info("時間窗口管理器初始化完成")
    
    def create_window(self, window_id: str, signal_type: SignalType, 
                     start_time: datetime, duration: timedelta,
                     priority: WindowPriority = WindowPriority.NORMAL,
                     timeout_callback: Optional[Callable] = None) -> bool:
        """
        創建追蹤窗口調度
        
        Args:
            window_id: 窗口ID
            signal_type: 信號類型
            start_time: 開始時間
            duration: 持續時間
            priority: 窗口優先級
            timeout_callback: 超時回調函數
            
        Returns:
            是否創建成功
        """
        with self._lock:
            try:
                # 檢查窗口是否已存在
                if window_id in self.active_schedules:
                    logger.warning(f"窗口調度已存在: {window_id}")
                    return False
                
                # 計算結束時間
                end_time = start_time + duration
                
                # 創建窗口調度
                schedule = WindowSchedule(
                    window_id=window_id,
                    expected_end_time=end_time,
                    priority=priority,
                    signal_type=signal_type,
                    created_time=start_time,
                    last_update_time=start_time,
                    timeout_callback=timeout_callback
                )
                
                # 存儲調度
                self.active_schedules[window_id] = schedule
                
                # 更新統計
                self.stats['total_windows_scheduled'] += 1
                self.stats['active_windows'] = len(self.active_schedules)
                
                logger.info(f"創建窗口調度: {window_id}, 類型: {signal_type.value}, "
                          f"結束時間: {end_time.strftime('%H:%M:%S')}, 優先級: {priority.name}")
                
                # 觸發創建回調
                if self.on_schedule_created:
                    self.on_schedule_created(schedule)
                
                # 啟動監控線程（如果尚未啟動）
                self._ensure_monitoring_started()
                
                return True
                
            except Exception as e:
                logger.error(f"創建窗口調度失敗: {e}")
                return False
    
    def update_window_activity(self, window_id: str, current_time: datetime) -> bool:
        """
        更新窗口活動時間
        
        Args:
            window_id: 窗口ID
            current_time: 當前時間
            
        Returns:
            是否更新成功
        """
        with self._lock:
            try:
                if window_id not in self.active_schedules:
                    logger.warning(f"窗口調度不存在: {window_id}")
                    return False
                
                schedule = self.active_schedules[window_id]
                schedule.last_update_time = current_time
                
                # 觸發更新回調
                if self.on_schedule_updated:
                    self.on_schedule_updated(schedule)
                
                return True
                
            except Exception as e:
                logger.error(f"更新窗口活動失敗: {e}")
                return False
    
    def is_window_expired(self, window_id: str, current_time: Optional[datetime] = None) -> bool:
        """
        檢查窗口是否過期
        
        Args:
            window_id: 窗口ID
            current_time: 當前時間（可選，默認使用當前時間）
            
        Returns:
            是否過期
        """
        with self._lock:
            if window_id not in self.active_schedules:
                return False
            
            if current_time is None:
                current_time = datetime.now()
            
            schedule = self.active_schedules[window_id]
            return current_time > schedule.expected_end_time
    
    def get_time_remaining(self, window_id: str, current_time: Optional[datetime] = None) -> Optional[timedelta]:
        """
        獲取窗口剩餘時間
        
        Args:
            window_id: 窗口ID
            current_time: 當前時間（可選）
            
        Returns:
            剩餘時間或None（如果窗口不存在）
        """
        with self._lock:
            if window_id not in self.active_schedules:
                return None
            
            if current_time is None:
                current_time = datetime.now()
            
            schedule = self.active_schedules[window_id]
            remaining = schedule.expected_end_time - current_time
            return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def close_window(self, window_id: str, reason: ExecutionReason) -> bool:
        """
        關閉追蹤窗口
        
        Args:
            window_id: 窗口ID
            reason: 關閉原因
            
        Returns:
            是否關閉成功
        """
        with self._lock:
            try:
                if window_id not in self.active_schedules:
                    logger.warning(f"窗口調度不存在: {window_id}")
                    return False
                
                schedule = self.active_schedules[window_id]
                
                # 移動到已完成列表
                self.completed_schedules[window_id] = schedule
                del self.active_schedules[window_id]
                
                # 從警告列表中移除
                self.issued_warnings.discard(window_id)
                
                # 更新統計
                self.stats['active_windows'] = len(self.active_schedules)
                self.stats['completed_windows'] = len(self.completed_schedules)
                
                if reason == ExecutionReason.WINDOW_TIMEOUT:
                    self.stats['timeout_windows'] += 1
                
                logger.info(f"關閉窗口調度: {window_id}, 原因: {reason.value}")
                return True
                
            except Exception as e:
                logger.error(f"關閉窗口調度失敗: {e}")
                return False
    
    def get_expired_windows(self, current_time: Optional[datetime] = None) -> List[str]:
        """
        獲取所有過期的窗口ID
        
        Args:
            current_time: 當前時間（可選）
            
        Returns:
            過期窗口ID列表
        """
        with self._lock:
            if current_time is None:
                current_time = datetime.now()
            
            expired_windows = []
            for window_id, schedule in self.active_schedules.items():
                if current_time > schedule.expected_end_time:
                    expired_windows.append(window_id)
            
            return expired_windows
    
    def get_windows_near_expiry(self, warning_minutes: Optional[int] = None,
                              current_time: Optional[datetime] = None) -> List[str]:
        """
        獲取即將過期的窗口ID
        
        Args:
            warning_minutes: 警告時間（分鐘）
            current_time: 當前時間（可選）
            
        Returns:
            即將過期的窗口ID列表
        """
        with self._lock:
            if current_time is None:
                current_time = datetime.now()
            
            if warning_minutes is None:
                warning_minutes = self.warning_threshold_minutes
            
            warning_threshold = timedelta(minutes=warning_minutes)
            near_expiry_windows = []
            
            for window_id, schedule in self.active_schedules.items():
                time_remaining = schedule.expected_end_time - current_time
                if timedelta(0) < time_remaining <= warning_threshold:
                    near_expiry_windows.append(window_id)
            
            return near_expiry_windows
    
    def get_window_schedule(self, window_id: str) -> Optional[WindowSchedule]:
        """獲取窗口調度信息"""
        with self._lock:
            return (self.active_schedules.get(window_id) or 
                   self.completed_schedules.get(window_id))
    
    def get_all_active_schedules(self) -> Dict[str, WindowSchedule]:
        """獲取所有活躍的窗口調度"""
        with self._lock:
            return self.active_schedules.copy()
    
    def get_all_completed_schedules(self) -> Dict[str, WindowSchedule]:
        """獲取所有已完成的窗口調度"""
        with self._lock:
            return self.completed_schedules.copy()
    
    def _ensure_monitoring_started(self):
        """確保監控線程已啟動"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_monitoring.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                name="WindowManager-Monitor",
                daemon=True
            )
            self._monitor_thread.start()
            logger.info("窗口監控線程已啟動")
    
    def _monitoring_loop(self):
        """監控循環"""
        logger.info("開始窗口監控循環")
        
        while not self._stop_monitoring.wait(self._monitoring_interval):
            try:
                current_time = datetime.now()
                
                # 檢查過期窗口
                expired_windows = self.get_expired_windows(current_time)
                for window_id in expired_windows:
                    self._handle_window_timeout(window_id, current_time)
                
                # 檢查即將過期的窗口
                near_expiry_windows = self.get_windows_near_expiry(current_time=current_time)
                for window_id in near_expiry_windows:
                    if window_id not in self.issued_warnings:
                        self._handle_window_warning(window_id, current_time)
                
                # 清理舊的已完成調度
                self._cleanup_old_schedules(current_time)
                
            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
        
        logger.info("窗口監控循環結束")
    
    def _handle_window_timeout(self, window_id: str, current_time: datetime):
        """處理窗口超時"""
        try:
            with self._lock:
                schedule = self.active_schedules.get(window_id)
                if not schedule:
                    return
                
                logger.warning(f"窗口超時: {window_id}, 超時時間: "
                             f"{(current_time - schedule.expected_end_time).total_seconds():.1f} 秒")
                
                # 觸發超時回調
                if self.on_window_timeout:
                    self.on_window_timeout(window_id, schedule)
                
                # 執行窗口特定的超時回調
                if schedule.timeout_callback:
                    try:
                        schedule.timeout_callback(window_id, schedule)
                    except Exception as e:
                        logger.error(f"執行窗口超時回調失敗: {e}")
                
                # 關閉窗口
                self.close_window(window_id, ExecutionReason.WINDOW_TIMEOUT)
                
        except Exception as e:
            logger.error(f"處理窗口超時失敗: {e}")
    
    def _handle_window_warning(self, window_id: str, current_time: datetime):
        """處理窗口警告"""
        try:
            with self._lock:
                schedule = self.active_schedules.get(window_id)
                if not schedule:
                    return
                
                time_remaining = schedule.expected_end_time - current_time
                remaining_minutes = time_remaining.total_seconds() / 60
                
                logger.info(f"窗口即將過期警告: {window_id}, 剩餘時間: {remaining_minutes:.1f} 分鐘")
                
                # 記錄已發出警告
                self.issued_warnings.add(window_id)
                self.stats['warning_issued'] += 1
                
                # 觸發警告回調
                if self.on_window_warning:
                    self.on_window_warning(window_id, schedule, remaining_minutes)
                
        except Exception as e:
            logger.error(f"處理窗口警告失敗: {e}")
    
    def _cleanup_old_schedules(self, current_time: datetime, retention_hours: int = 24):
        """清理舊的已完成調度"""
        try:
            cutoff_time = current_time - timedelta(hours=retention_hours)
            old_schedules = []
            
            with self._lock:
                for window_id, schedule in self.completed_schedules.items():
                    if schedule.expected_end_time < cutoff_time:
                        old_schedules.append(window_id)
                
                for window_id in old_schedules:
                    del self.completed_schedules[window_id]
                
                if old_schedules:
                    self.stats['completed_windows'] = len(self.completed_schedules)
                    logger.info(f"清理了 {len(old_schedules)} 個舊的已完成調度")
                
        except Exception as e:
            logger.error(f"清理舊調度失敗: {e}")
    
    def set_monitoring_interval(self, interval_seconds: int):
        """設置監控間隔"""
        if interval_seconds < 1:
            logger.warning("監控間隔不能小於1秒")
            return
        
        self._monitoring_interval = interval_seconds
        logger.info(f"監控間隔設置為 {interval_seconds} 秒")
    
    def set_warning_threshold(self, threshold_minutes: int):
        """設置警告閾值"""
        if threshold_minutes < 1:
            logger.warning("警告閾值不能小於1分鐘")
            return
        
        self.warning_threshold_minutes = threshold_minutes
        logger.info(f"警告閾值設置為 {threshold_minutes} 分鐘")
    
    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        with self._lock:
            # 計算平均窗口持續時間
            if self.completed_schedules:
                total_duration = 0
                for schedule in self.completed_schedules.values():
                    duration = schedule.expected_end_time - schedule.created_time
                    total_duration += duration.total_seconds()
                
                avg_duration_minutes = (total_duration / len(self.completed_schedules)) / 60
                self.stats['average_window_duration_minutes'] = avg_duration_minutes
            
            # 按信號類型統計
            active_buy_windows = sum(1 for s in self.active_schedules.values() 
                                   if s.signal_type == SignalType.BUY)
            active_sell_windows = len(self.active_schedules) - active_buy_windows
            
            # 按優先級統計
            priority_stats = defaultdict(int)
            for schedule in self.active_schedules.values():
                priority_stats[schedule.priority.name] += 1
            
            return {
                **self.stats,
                'monitoring_active': self._monitor_thread is not None and self._monitor_thread.is_alive(),
                'monitoring_interval_seconds': self._monitoring_interval,
                'warning_threshold_minutes': self.warning_threshold_minutes,
                'active_windows_by_type': {
                    'buy': active_buy_windows,
                    'sell': active_sell_windows
                },
                'active_windows_by_priority': dict(priority_stats),
                'pending_warnings': len(self.issued_warnings)
            }
    
    def get_window_summary(self, window_id: str) -> Optional[Dict]:
        """獲取窗口摘要信息"""
        with self._lock:
            schedule = self.get_window_schedule(window_id)
            if not schedule:
                return None
            
            current_time = datetime.now()
            is_active = window_id in self.active_schedules
            
            if is_active:
                time_remaining = self.get_time_remaining(window_id, current_time)
                is_expired = self.is_window_expired(window_id, current_time)
            else:
                time_remaining = timedelta(0)
                is_expired = True
            
            return {
                'window_id': window_id,
                'signal_type': schedule.signal_type.value,
                'priority': schedule.priority.name,
                'created_time': schedule.created_time,
                'expected_end_time': schedule.expected_end_time,
                'last_update_time': schedule.last_update_time,
                'is_active': is_active,
                'is_expired': is_expired,
                'time_remaining_minutes': time_remaining.total_seconds() / 60 if time_remaining else 0,
                'has_timeout_callback': schedule.timeout_callback is not None,
                'warning_issued': window_id in self.issued_warnings
            }
    
    def set_callbacks(self, on_timeout: Optional[Callable] = None,
                     on_warning: Optional[Callable] = None,
                     on_created: Optional[Callable] = None,
                     on_updated: Optional[Callable] = None):
        """設置回調函數"""
        self.on_window_timeout = on_timeout
        self.on_window_warning = on_warning
        self.on_schedule_created = on_created
        self.on_schedule_updated = on_updated
        
        logger.info("窗口管理器回調函數設置完成")
    
    def shutdown(self):
        """關閉窗口管理器"""
        logger.info("正在關閉窗口管理器...")
        
        # 停止監控線程
        self._stop_monitoring.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        
        with self._lock:
            # 關閉所有活躍窗口
            active_window_ids = list(self.active_schedules.keys())
            for window_id in active_window_ids:
                self.close_window(window_id, ExecutionReason.SYSTEM_ERROR)
            
            # 清空警告列表
            self.issued_warnings.clear()
        
        logger.info("窗口管理器已關閉")

# 工具函數
def create_window_manager(config: Optional[TrackingWindowConfig] = None) -> WindowManager:
    """創建窗口管理器"""
    if config is None:
        config = TrackingWindowConfig()
    return WindowManager(config)

class WindowScheduler:
    """窗口調度器 - 高級調度功能"""
    
    def __init__(self, manager: WindowManager):
        self.manager = manager
        self.scheduling_rules: List[Callable] = []
        
    def add_scheduling_rule(self, rule: Callable[[WindowSchedule], WindowPriority]):
        """添加調度規則"""
        self.scheduling_rules.append(rule)
        logger.info("添加了新的調度規則")
    
    def calculate_priority(self, schedule: WindowSchedule) -> WindowPriority:
        """根據規則計算窗口優先級"""
        max_priority = WindowPriority.NORMAL
        
        for rule in self.scheduling_rules:
            try:
                priority = rule(schedule)
                if priority.value > max_priority.value:
                    max_priority = priority
            except Exception as e:
                logger.error(f"執行調度規則失敗: {e}")
        
        return max_priority
    
    def get_priority_queue(self) -> List[WindowSchedule]:
        """獲取按優先級排序的窗口列表"""
        schedules = list(self.manager.get_all_active_schedules().values())
        return sorted(schedules, key=lambda s: s.priority.value, reverse=True)

# 預定義調度規則
def high_value_signal_rule(schedule: WindowSchedule) -> WindowPriority:
    """高價值信號規則"""
    # 這裡可以根據信號的價值來設定優先級
    # 例如：大額交易、重要時間點等
    return WindowPriority.NORMAL

def time_critical_rule(schedule: WindowSchedule) -> WindowPriority:
    """時間關鍵規則"""
    current_time = datetime.now()
    time_remaining = schedule.expected_end_time - current_time
    
    # 剩餘時間少於10分鐘的窗口設為高優先級
    if time_remaining.total_seconds() < 600:  # 10分鐘
        return WindowPriority.HIGH
    
    return WindowPriority.NORMAL