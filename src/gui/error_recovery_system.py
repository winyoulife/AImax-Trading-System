#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
錯誤恢復系統 - 處理GUI和AI系統的錯誤恢復
提供自動重連、GUI重置和降級模式功能
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QMessageBox, QApplication


class ErrorType(Enum):
    """錯誤類型枚舉"""
    AI_CONNECTION_LOST = "ai_connection_lost"
    GUI_FREEZE = "gui_freeze"
    TRADING_ERROR = "trading_error"
    NETWORK_ERROR = "network_error"
    SYSTEM_ERROR = "system_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryAction(Enum):
    """恢復動作枚舉"""
    RECONNECT = "reconnect"
    RESTART_COMPONENT = "restart_component"
    RESET_GUI = "reset_gui"
    FALLBACK_MODE = "fallback_mode"
    NOTIFY_USER = "notify_user"
    LOG_ERROR = "log_error"
    IGNORE = "ignore"


@dataclass
class ErrorEvent:
    """錯誤事件"""
    error_type: ErrorType
    timestamp: datetime
    message: str
    component: str = ""
    severity: str = "medium"  # low, medium, high, critical
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


class ErrorRecovery(QObject):
    """錯誤恢復類別"""
    
    # 信號定義
    error_detected = pyqtSignal(object)  # ErrorEvent
    recovery_started = pyqtSignal(str, str)  # error_type, action
    recovery_completed = pyqtSignal(bool, str)  # success, message
    fallback_mode_activated = pyqtSignal(str)  # reason
    
    def __init__(self, ai_connector=None, main_window=None):
        super().__init__()
        
        self.ai_connector = ai_connector
        self.main_window = main_window
        
        # 錯誤歷史記錄
        self.error_history: List[ErrorEvent] = []
        self.max_history_size = 100
        
        # 恢復策略配置
        self.recovery_strategies = {
            ErrorType.AI_CONNECTION_LOST: [
                RecoveryAction.RECONNECT,
                RecoveryAction.FALLBACK_MODE,
                RecoveryAction.NOTIFY_USER
            ],
            ErrorType.GUI_FREEZE: [
                RecoveryAction.RESET_GUI,
                RecoveryAction.RESTART_COMPONENT,
                RecoveryAction.NOTIFY_USER
            ],
            ErrorType.TRADING_ERROR: [
                RecoveryAction.LOG_ERROR,
                RecoveryAction.NOTIFY_USER,
                RecoveryAction.FALLBACK_MODE
            ],
            ErrorType.NETWORK_ERROR: [
                RecoveryAction.RECONNECT,
                RecoveryAction.NOTIFY_USER
            ],
            ErrorType.SYSTEM_ERROR: [
                RecoveryAction.LOG_ERROR,
                RecoveryAction.RESTART_COMPONENT,
                RecoveryAction.NOTIFY_USER
            ],
            ErrorType.MEMORY_ERROR: [
                RecoveryAction.RESET_GUI,
                RecoveryAction.FALLBACK_MODE,
                RecoveryAction.NOTIFY_USER
            ]
        }
        
        # 恢復狀態
        self.is_in_fallback_mode = False
        self.recovery_in_progress = False
        self.last_recovery_time = None
        self.recovery_attempts = {}  # 記錄每種錯誤的恢復嘗試次數
        
        # 監控定時器
        self.health_monitor_timer = QTimer()
        self.health_monitor_timer.timeout.connect(self.check_system_health)
        self.health_monitor_timer.start(5000)  # 每5秒檢查一次
        
        # GUI凍結檢測
        self.gui_freeze_detector = GUIFreezeDetector()
        self.gui_freeze_detector.freeze_detected.connect(self.handle_gui_freeze)
        
        # AI連接監控
        self.ai_connection_monitor = AIConnectionMonitor(ai_connector)
        self.ai_connection_monitor.connection_lost.connect(self.handle_ai_disconnect)
        
    def handle_error(self, error_type: ErrorType, message: str, 
                    component: str = "", severity: str = "medium", 
                    context: Dict[str, Any] = None):
        """處理錯誤"""
        try:
            # 創建錯誤事件
            error_event = ErrorEvent(
                error_type=error_type,
                timestamp=datetime.now(),
                message=message,
                component=component,
                severity=severity,
                context=context or {}
            )
            
            # 添加到歷史記錄
            self.add_error_to_history(error_event)
            
            # 發送錯誤檢測信號
            self.error_detected.emit(error_event)
            
            # 執行恢復策略
            self.execute_recovery_strategy(error_event)
            
        except Exception as e:
            print(f"處理錯誤時發生異常: {e}")
    
    def add_error_to_history(self, error_event: ErrorEvent):
        """添加錯誤到歷史記錄"""
        try:
            self.error_history.append(error_event)
            
            # 限制歷史記錄大小
            if len(self.error_history) > self.max_history_size:
                self.error_history.pop(0)
                
        except Exception as e:
            print(f"添加錯誤歷史失敗: {e}")
    
    def execute_recovery_strategy(self, error_event: ErrorEvent):
        """執行恢復策略"""
        try:
            if self.recovery_in_progress:
                print("恢復正在進行中，跳過新的恢復請求")
                return
            
            self.recovery_in_progress = True
            error_type = error_event.error_type
            
            # 檢查恢復嘗試次數
            if self.should_skip_recovery(error_type):
                print(f"跳過恢復，{error_type.value} 嘗試次數過多")
                self.recovery_in_progress = False
                return
            
            # 獲取恢復策略
            strategies = self.recovery_strategies.get(error_type, [RecoveryAction.LOG_ERROR])
            
            # 執行恢復動作
            for action in strategies:
                try:
                    self.recovery_started.emit(error_type.value, action.value)
                    success = self.execute_recovery_action(action, error_event)
                    
                    if success:
                        self.recovery_completed.emit(True, f"恢復成功: {action.value}")
                        break
                    else:
                        print(f"恢復動作失敗: {action.value}")
                        
                except Exception as e:
                    print(f"執行恢復動作 {action.value} 時發生錯誤: {e}")
                    continue
            
            self.last_recovery_time = datetime.now()
            self.recovery_in_progress = False
            
        except Exception as e:
            print(f"執行恢復策略失敗: {e}")
            self.recovery_in_progress = False
    
    def should_skip_recovery(self, error_type: ErrorType) -> bool:
        """檢查是否應該跳過恢復"""
        try:
            # 檢查恢復嘗試次數
            attempts = self.recovery_attempts.get(error_type, 0)
            max_attempts = 3  # 最大嘗試次數
            
            if attempts >= max_attempts:
                return True
            
            # 檢查時間間隔
            if self.last_recovery_time:
                time_since_last = datetime.now() - self.last_recovery_time
                if time_since_last < timedelta(seconds=30):  # 30秒內不重複恢復
                    return True
            
            return False
            
        except Exception:
            return False
    
    def execute_recovery_action(self, action: RecoveryAction, error_event: ErrorEvent) -> bool:
        """執行具體的恢復動作"""
        try:
            if action == RecoveryAction.RECONNECT:
                return self.reconnect_ai_system()
            
            elif action == RecoveryAction.RESTART_COMPONENT:
                return self.restart_component(error_event.component)
            
            elif action == RecoveryAction.RESET_GUI:
                return self.reset_gui_components()
            
            elif action == RecoveryAction.FALLBACK_MODE:
                return self.activate_fallback_mode(error_event.message)
            
            elif action == RecoveryAction.NOTIFY_USER:
                return self.notify_user(error_event)
            
            elif action == RecoveryAction.LOG_ERROR:
                return self.log_error(error_event)
            
            elif action == RecoveryAction.IGNORE:
                return True
            
            return False
            
        except Exception as e:
            print(f"執行恢復動作失敗: {e}")
            return False
    
    def reconnect_ai_system(self) -> bool:
        """重新連接AI系統"""
        try:
            if not self.ai_connector:
                return False
            
            print("嘗試重新連接AI系統...")
            
            # 斷開現有連接
            self.ai_connector.disconnect_ai_system()
            time.sleep(2)
            
            # 重新連接
            success = self.ai_connector.connect_to_ai_system()
            
            if success:
                print("AI系統重新連接成功")
                # 重置恢復嘗試計數
                self.recovery_attempts[ErrorType.AI_CONNECTION_LOST] = 0
            else:
                # 增加恢復嘗試計數
                self.recovery_attempts[ErrorType.AI_CONNECTION_LOST] = \
                    self.recovery_attempts.get(ErrorType.AI_CONNECTION_LOST, 0) + 1
            
            return success
            
        except Exception as e:
            print(f"重新連接AI系統失敗: {e}")
            return False
    
    def restart_component(self, component: str) -> bool:
        """重啟組件"""
        try:
            print(f"嘗試重啟組件: {component}")
            
            if component == "status_sync_manager" and hasattr(self.main_window, 'status_sync_manager'):
                # 重啟狀態同步管理器
                self.main_window.status_sync_manager.stop_sync()
                time.sleep(1)
                self.main_window.status_sync_manager.start_sync()
                return True
            
            elif component == "ai_connector" and self.ai_connector:
                # 重啟AI連接器
                return self.reconnect_ai_system()
            
            # 其他組件的重啟邏輯可以在這裡添加
            
            return False
            
        except Exception as e:
            print(f"重啟組件失敗: {e}")
            return False
    
    def reset_gui_components(self) -> bool:
        """重置GUI組件"""
        try:
            print("嘗試重置GUI組件...")
            
            if not self.main_window:
                return False
            
            # 重置狀態面板
            if hasattr(self.main_window, 'status_panel'):
                self.main_window.status_panel.update_ai_status({
                    'status': '重置中...',
                    'active_count': 0,
                    'last_decision': '系統重置',
                    'confidence': 0.0
                })
            
            # 清理日誌面板
            if hasattr(self.main_window, 'log_panel'):
                self.main_window.log_panel.add_log("GUI組件已重置", "INFO")
            
            # 強制刷新GUI
            if QApplication.instance():
                QApplication.processEvents()
            
            return True
            
        except Exception as e:
            print(f"重置GUI組件失敗: {e}")
            return False
    
    def activate_fallback_mode(self, reason: str) -> bool:
        """激活降級模式"""
        try:
            if self.is_in_fallback_mode:
                return True
            
            print(f"激活降級模式: {reason}")
            self.is_in_fallback_mode = True
            
            # 發送降級模式信號
            self.fallback_mode_activated.emit(reason)
            
            # 更新GUI顯示
            if self.main_window and hasattr(self.main_window, 'status_panel'):
                self.main_window.status_panel.update_ai_status({
                    'status': '降級模式',
                    'active_count': 1,
                    'last_decision': '系統運行在降級模式',
                    'confidence': 50.0
                })
            
            # 記錄日誌
            if self.main_window and hasattr(self.main_window, 'log_panel'):
                self.main_window.log_panel.add_log(f"系統進入降級模式: {reason}", "WARNING")
            
            return True
            
        except Exception as e:
            print(f"激活降級模式失敗: {e}")
            return False
    
    def deactivate_fallback_mode(self) -> bool:
        """停用降級模式"""
        try:
            if not self.is_in_fallback_mode:
                return True
            
            print("停用降級模式")
            self.is_in_fallback_mode = False
            
            # 記錄日誌
            if self.main_window and hasattr(self.main_window, 'log_panel'):
                self.main_window.log_panel.add_log("系統退出降級模式", "SUCCESS")
            
            return True
            
        except Exception as e:
            print(f"停用降級模式失敗: {e}")
            return False
    
    def notify_user(self, error_event: ErrorEvent) -> bool:
        """通知用戶"""
        try:
            if error_event.severity in ["high", "critical"]:
                # 顯示對話框
                if QApplication.instance():
                    msg_box = QMessageBox()
                    msg_box.setIcon(QMessageBox.Icon.Warning)
                    msg_box.setWindowTitle("系統錯誤")
                    msg_box.setText(f"發生錯誤: {error_event.message}")
                    msg_box.setInformativeText("系統正在嘗試自動恢復...")
                    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                    msg_box.exec()
            
            # 記錄到日誌面板
            if self.main_window and hasattr(self.main_window, 'log_panel'):
                level = "ERROR" if error_event.severity in ["high", "critical"] else "WARNING"
                self.main_window.log_panel.add_log(
                    f"[{error_event.component}] {error_event.message}", 
                    level
                )
            
            return True
            
        except Exception as e:
            print(f"通知用戶失敗: {e}")
            return False
    
    def log_error(self, error_event: ErrorEvent) -> bool:
        """記錄錯誤"""
        try:
            # 記錄到控制台
            print(f"錯誤記錄: [{error_event.error_type.value}] {error_event.message}")
            
            # 記錄到日誌面板
            if self.main_window and hasattr(self.main_window, 'log_panel'):
                self.main_window.log_panel.add_log(
                    f"[{error_event.component}] {error_event.message}",
                    "ERROR"
                )
            
            return True
            
        except Exception as e:
            print(f"記錄錯誤失敗: {e}")
            return False
    
    def check_system_health(self):
        """檢查系統健康狀態"""
        try:
            # 檢查AI連接狀態
            if self.ai_connector and not self.ai_connector.is_system_connected():
                if not self.is_in_fallback_mode:
                    self.handle_error(
                        ErrorType.AI_CONNECTION_LOST,
                        "AI系統連接丟失",
                        "ai_connector",
                        "high"
                    )
            
            # 檢查記憶體使用
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 90:
                    self.handle_error(
                        ErrorType.MEMORY_ERROR,
                        f"記憶體使用率過高: {memory_percent:.1f}%",
                        "system",
                        "medium"
                    )
            except ImportError:
                pass  # psutil不可用時跳過記憶體檢查
            
        except Exception as e:
            print(f"系統健康檢查失敗: {e}")
    
    def handle_ai_disconnect(self, reason: str):
        """處理AI斷開連接"""
        self.handle_error(
            ErrorType.AI_CONNECTION_LOST,
            f"AI連接斷開: {reason}",
            "ai_connector",
            "high"
        )
    
    def handle_gui_freeze(self, duration: float):
        """處理GUI凍結"""
        self.handle_error(
            ErrorType.GUI_FREEZE,
            f"GUI凍結 {duration:.1f} 秒",
            "gui",
            "high"
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """獲取錯誤統計"""
        try:
            stats = {
                'total_errors': len(self.error_history),
                'error_types': {},
                'recent_errors': 0,
                'recovery_attempts': self.recovery_attempts.copy(),
                'is_in_fallback_mode': self.is_in_fallback_mode
            }
            
            # 統計錯誤類型
            for error in self.error_history:
                error_type = error.error_type.value
                stats['error_types'][error_type] = stats['error_types'].get(error_type, 0) + 1
            
            # 統計最近1小時的錯誤
            one_hour_ago = datetime.now() - timedelta(hours=1)
            stats['recent_errors'] = sum(
                1 for error in self.error_history 
                if error.timestamp >= one_hour_ago
            )
            
            return stats
            
        except Exception as e:
            print(f"獲取錯誤統計失敗: {e}")
            return {}
    
    def cleanup(self):
        """清理資源"""
        try:
            # 停止定時器
            if self.health_monitor_timer.isActive():
                self.health_monitor_timer.stop()
            
            # 清理監控器
            if hasattr(self, 'gui_freeze_detector'):
                self.gui_freeze_detector.cleanup()
            
            if hasattr(self, 'ai_connection_monitor'):
                self.ai_connection_monitor.cleanup()
            
            # 清理歷史記錄
            self.error_history.clear()
            
        except Exception as e:
            print(f"清理錯誤恢復系統失敗: {e}")


class GUIFreezeDetector(QObject):
    """GUI凍結檢測器"""
    
    freeze_detected = pyqtSignal(float)  # 凍結持續時間
    
    def __init__(self):
        super().__init__()
        self.last_response_time = time.time()
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_responsiveness)
        self.check_timer.start(1000)  # 每秒檢查
        
    def check_responsiveness(self):
        """檢查GUI響應性"""
        try:
            current_time = time.time()
            
            # 檢查是否有長時間無響應
            if current_time - self.last_response_time > 5.0:  # 5秒無響應
                freeze_duration = current_time - self.last_response_time
                self.freeze_detected.emit(freeze_duration)
            
            self.last_response_time = current_time
            
        except Exception as e:
            print(f"GUI響應性檢查失敗: {e}")
    
    def cleanup(self):
        """清理資源"""
        if self.check_timer.isActive():
            self.check_timer.stop()


class AIConnectionMonitor(QObject):
    """AI連接監控器"""
    
    connection_lost = pyqtSignal(str)  # 連接丟失原因
    
    def __init__(self, ai_connector):
        super().__init__()
        self.ai_connector = ai_connector
        self.last_connection_status = False
        
        # 監控定時器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_connection)
        self.monitor_timer.start(3000)  # 每3秒檢查
    
    def check_connection(self):
        """檢查AI連接狀態"""
        try:
            if not self.ai_connector:
                return
            
            current_status = self.ai_connector.is_system_connected()
            
            # 檢測連接狀態變化
            if self.last_connection_status and not current_status:
                self.connection_lost.emit("連接狀態檢查失敗")
            
            self.last_connection_status = current_status
            
        except Exception as e:
            if self.last_connection_status:
                self.connection_lost.emit(f"連接檢查異常: {str(e)}")
            self.last_connection_status = False
    
    def cleanup(self):
        """清理資源"""
        if self.monitor_timer.isActive():
            self.monitor_timer.stop()


if __name__ == "__main__":
    # 測試錯誤恢復系統
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建錯誤恢復系統
    error_recovery = ErrorRecovery()
    
    def on_error_detected(error_event):
        print(f"檢測到錯誤: {error_event.error_type.value} - {error_event.message}")
    
    def on_recovery_started(error_type, action):
        print(f"開始恢復: {error_type} -> {action}")
    
    def on_recovery_completed(success, message):
        print(f"恢復完成: {'成功' if success else '失敗'} - {message}")
    
    def on_fallback_mode_activated(reason):
        print(f"降級模式激活: {reason}")
    
    # 連接信號
    error_recovery.error_detected.connect(on_error_detected)
    error_recovery.recovery_started.connect(on_recovery_started)
    error_recovery.recovery_completed.connect(on_recovery_completed)
    error_recovery.fallback_mode_activated.connect(on_fallback_mode_activated)
    
    # 模擬錯誤
    error_recovery.handle_error(
        ErrorType.AI_CONNECTION_LOST,
        "測試AI連接丟失",
        "test_component",
        "high"
    )
    
    # 運行3秒後退出
    QTimer.singleShot(3000, app.quit)
    
    sys.exit(app.exec())