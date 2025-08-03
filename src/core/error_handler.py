#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
錯誤處理和恢復系統 - 提供全系統的異常處理和自動恢復機制
"""

import sys
import os
import logging
import traceback
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from functools import wraps
import threading
from queue import Queue, Empty

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """錯誤類別"""
    NETWORK = "network"
    DATA = "data"
    AI_MODEL = "ai_model"
    TRADING = "trading"
    SYSTEM = "system"
    GUI = "gui"
    DATABASE = "database"
    API = "api"

class RecoveryAction(Enum):
    """恢復動作"""
    RETRY = "retry"
    RECONNECT = "reconnect"
    RESTART_COMPONENT = "restart_component"
    FALLBACK = "fallback"
    EMERGENCY_STOP = "emergency_stop"
    IGNORE = "ignore"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorInfo:
    """錯誤信息數據類"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    component: str
    error_type: str
    message: str
    traceback: str
    context: Dict[str, Any]
    recovery_action: Optional[RecoveryAction] = None
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_history: List[ErrorInfo] = []
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.max_history_size = 1000
        self.error_queue = Queue()
        self.processing_thread = None
        self.running = False
        
        # 初始化默認恢復策略
        self._initialize_default_strategies()
        
        self.logger.info("🛡️ 錯誤處理器初始化完成")
    
    def _initialize_default_strategies(self):
        """初始化默認恢復策略"""
        self.recovery_strategies.update({
            'network_retry': self._network_retry_strategy,
            'component_restart': self._component_restart_strategy,
            'fallback_mode': self._fallback_mode_strategy,
            'emergency_stop': self._emergency_stop_strategy
        })
    
    def start(self):
        """啟動錯誤處理器"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(
                target=self._process_errors,
                daemon=True
            )
            self.processing_thread.start()
            self.logger.info("🚀 錯誤處理器已啟動")
    
    def stop(self):
        """停止錯誤處理器"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        self.logger.info("⏹️ 錯誤處理器已停止")
    
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        component: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """處理錯誤"""
        try:
            # 創建錯誤信息
            error_info = ErrorInfo(
                error_id=self._generate_error_id(),
                timestamp=datetime.now(),
                category=category,
                severity=severity,
                component=component,
                error_type=type(error).__name__,
                message=str(error),
                traceback=traceback.format_exc(),
                context=context or {}
            )
            
            # 確定恢復動作
            error_info.recovery_action = self._determine_recovery_action(error_info)
            
            # 記錄錯誤
            self._log_error(error_info)
            
            # 添加到歷史記錄
            self._add_to_history(error_info)
            
            # 異步處理恢復
            self.error_queue.put(error_info)
            
            return error_info
            
        except Exception as e:
            self.logger.error(f"❌ 錯誤處理器自身發生錯誤: {e}")
            return None
    
    def _generate_error_id(self) -> str:
        """生成錯誤ID"""
        return f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.error_history):04d}"
    
    def _determine_recovery_action(self, error_info: ErrorInfo) -> RecoveryAction:
        """確定恢復動作"""
        # 基於錯誤類別和嚴重程度確定恢復策略
        if error_info.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction.EMERGENCY_STOP
        
        if error_info.category == ErrorCategory.NETWORK:
            return RecoveryAction.RECONNECT
        elif error_info.category == ErrorCategory.AI_MODEL:
            return RecoveryAction.RESTART_COMPONENT
        elif error_info.category == ErrorCategory.TRADING:
            if error_info.severity == ErrorSeverity.HIGH:
                return RecoveryAction.EMERGENCY_STOP
            else:
                return RecoveryAction.FALLBACK
        elif error_info.category == ErrorCategory.DATA:
            return RecoveryAction.RETRY
        else:
            return RecoveryAction.RETRY
    
    def _log_error(self, error_info: ErrorInfo):
        """記錄錯誤"""
        severity_emoji = {
            ErrorSeverity.LOW: "⚠️",
            ErrorSeverity.MEDIUM: "🟡",
            ErrorSeverity.HIGH: "🔴",
            ErrorSeverity.CRITICAL: "💥"
        }
        
        emoji = severity_emoji.get(error_info.severity, "❌")
        
        self.logger.error(
            f"{emoji} [{error_info.error_id}] {error_info.component}: "
            f"{error_info.error_type} - {error_info.message}"
        )
        
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"   Traceback: {error_info.traceback}")
    
    def _add_to_history(self, error_info: ErrorInfo):
        """添加到歷史記錄"""
        self.error_history.append(error_info)
        
        # 限制歷史記錄大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def _process_errors(self):
        """處理錯誤隊列"""
        while self.running:
            try:
                error_info = self.error_queue.get(timeout=1)
                self._execute_recovery(error_info)
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ 處理錯誤隊列時發生異常: {e}")
    
    def _execute_recovery(self, error_info: ErrorInfo):
        """執行恢復動作"""
        if error_info.recovery_attempts >= error_info.max_recovery_attempts:
            self.logger.warning(f"⚠️ [{error_info.error_id}] 達到最大恢復嘗試次數")
            error_info.recovery_action = RecoveryAction.MANUAL_INTERVENTION
            return
        
        error_info.recovery_attempts += 1
        
        try:
            if error_info.recovery_action == RecoveryAction.RETRY:
                success = self._retry_operation(error_info)
            elif error_info.recovery_action == RecoveryAction.RECONNECT:
                success = self._reconnect_component(error_info)
            elif error_info.recovery_action == RecoveryAction.RESTART_COMPONENT:
                success = self._restart_component(error_info)
            elif error_info.recovery_action == RecoveryAction.FALLBACK:
                success = self._activate_fallback(error_info)
            elif error_info.recovery_action == RecoveryAction.EMERGENCY_STOP:
                success = self._emergency_stop(error_info)
            else:
                success = False
            
            if success:
                error_info.resolved = True
                error_info.resolution_time = datetime.now()
                self.logger.info(f"✅ [{error_info.error_id}] 恢復成功")
            else:
                # 重新加入隊列進行下次嘗試
                time.sleep(2 ** error_info.recovery_attempts)  # 指數退避
                self.error_queue.put(error_info)
                
        except Exception as e:
            self.logger.error(f"❌ [{error_info.error_id}] 恢復執行失敗: {e}")
            self.error_queue.put(error_info)
    
    def _retry_operation(self, error_info: ErrorInfo) -> bool:
        """重試操作"""
        self.logger.info(f"🔄 [{error_info.error_id}] 重試操作...")
        
        # 調用重試策略
        if 'retry_callback' in error_info.context:
            try:
                callback = error_info.context['retry_callback']
                return callback()
            except Exception as e:
                self.logger.error(f"❌ 重試回調失敗: {e}")
                return False
        
        return True  # 默認認為重試成功
    
    def _reconnect_component(self, error_info: ErrorInfo) -> bool:
        """重新連接組件"""
        self.logger.info(f"🔗 [{error_info.error_id}] 重新連接組件...")
        
        # 調用重連策略
        if 'reconnect_callback' in error_info.context:
            try:
                callback = error_info.context['reconnect_callback']
                return callback()
            except Exception as e:
                self.logger.error(f"❌ 重連回調失敗: {e}")
                return False
        
        return True  # 默認認為重連成功
    
    def _restart_component(self, error_info: ErrorInfo) -> bool:
        """重啟組件"""
        self.logger.info(f"🔄 [{error_info.error_id}] 重啟組件...")
        
        # 調用重啟策略
        if 'restart_callback' in error_info.context:
            try:
                callback = error_info.context['restart_callback']
                return callback()
            except Exception as e:
                self.logger.error(f"❌ 重啟回調失敗: {e}")
                return False
        
        return True  # 默認認為重啟成功
    
    def _activate_fallback(self, error_info: ErrorInfo) -> bool:
        """激活備用方案"""
        self.logger.info(f"🔄 [{error_info.error_id}] 激活備用方案...")
        
        # 調用備用策略
        if 'fallback_callback' in error_info.context:
            try:
                callback = error_info.context['fallback_callback']
                return callback()
            except Exception as e:
                self.logger.error(f"❌ 備用方案回調失敗: {e}")
                return False
        
        return True  # 默認認為備用方案成功
    
    def _emergency_stop(self, error_info: ErrorInfo) -> bool:
        """緊急停止"""
        self.logger.critical(f"🚨 [{error_info.error_id}] 執行緊急停止...")
        
        # 調用緊急停止策略
        if 'emergency_callback' in error_info.context:
            try:
                callback = error_info.context['emergency_callback']
                return callback()
            except Exception as e:
                self.logger.error(f"❌ 緊急停止回調失敗: {e}")
                return False
        
        return True  # 默認認為緊急停止成功
    
    def _network_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """網絡重試策略"""
        self.logger.info(f"🌐 執行網絡重試策略...")
        time.sleep(1)  # 等待網絡恢復
        return True
    
    def _component_restart_strategy(self, error_info: ErrorInfo) -> bool:
        """組件重啟策略"""
        self.logger.info(f"🔄 執行組件重啟策略...")
        time.sleep(2)  # 等待組件重啟
        return True
    
    def _fallback_mode_strategy(self, error_info: ErrorInfo) -> bool:
        """備用模式策略"""
        self.logger.info(f"🔄 執行備用模式策略...")
        return True
    
    def _emergency_stop_strategy(self, error_info: ErrorInfo) -> bool:
        """緊急停止策略"""
        self.logger.critical(f"🚨 執行緊急停止策略...")
        return True
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """註冊錯誤回調"""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def register_recovery_strategy(self, name: str, strategy: Callable):
        """註冊恢復策略"""
        self.recovery_strategies[name] = strategy
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """獲取錯誤統計"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'resolved_errors': 0,
                'unresolved_errors': 0,
                'resolution_rate': 0.0,
                'categories': {},
                'severities': {}
            }
        
        total_errors = len(self.error_history)
        resolved_errors = sum(1 for e in self.error_history if e.resolved)
        unresolved_errors = total_errors - resolved_errors
        
        # 按類別統計
        categories = {}
        for error in self.error_history:
            cat = error.category.value
            if cat not in categories:
                categories[cat] = {'total': 0, 'resolved': 0}
            categories[cat]['total'] += 1
            if error.resolved:
                categories[cat]['resolved'] += 1
        
        # 按嚴重程度統計
        severities = {}
        for error in self.error_history:
            sev = error.severity.value
            if sev not in severities:
                severities[sev] = {'total': 0, 'resolved': 0}
            severities[sev]['total'] += 1
            if error.resolved:
                severities[sev]['resolved'] += 1
        
        return {
            'total_errors': total_errors,
            'resolved_errors': resolved_errors,
            'unresolved_errors': unresolved_errors,
            'resolution_rate': resolved_errors / total_errors if total_errors > 0 else 0.0,
            'categories': categories,
            'severities': severities
        }
    
    def export_error_log(self, filepath: str):
        """導出錯誤日誌"""
        try:
            log_data = {
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_error_statistics(),
                'errors': [asdict(error) for error in self.error_history]
            }
            
            # 處理datetime序列化
            for error in log_data['errors']:
                error['timestamp'] = error['timestamp'].isoformat()
                if error['resolution_time']:
                    error['resolution_time'] = error['resolution_time'].isoformat()
                error['category'] = error['category'].value
                error['severity'] = error['severity'].value
                if error['recovery_action']:
                    error['recovery_action'] = error['recovery_action'].value
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 錯誤日誌已導出到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ 導出錯誤日誌失敗: {e}")

def error_handler_decorator(
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    component: str = "unknown",
    retry_callback: Optional[Callable] = None,
    reconnect_callback: Optional[Callable] = None,
    restart_callback: Optional[Callable] = None,
    fallback_callback: Optional[Callable] = None,
    emergency_callback: Optional[Callable] = None
):
    """錯誤處理裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 獲取全局錯誤處理器
                error_handler = get_global_error_handler()
                
                # 構建上下文
                context = {}
                if retry_callback:
                    context['retry_callback'] = retry_callback
                if reconnect_callback:
                    context['reconnect_callback'] = reconnect_callback
                if restart_callback:
                    context['restart_callback'] = restart_callback
                if fallback_callback:
                    context['fallback_callback'] = fallback_callback
                if emergency_callback:
                    context['emergency_callback'] = emergency_callback
                
                # 處理錯誤
                error_handler.handle_error(e, category, severity, component, context)
                
                # 重新拋出異常（可選）
                raise
        return wrapper
    return decorator

# 全局錯誤處理器實例
_global_error_handler = None

def get_global_error_handler() -> ErrorHandler:
    """獲取全局錯誤處理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
        _global_error_handler.start()
    return _global_error_handler

def create_error_handler() -> ErrorHandler:
    """創建錯誤處理器實例"""
    return ErrorHandler()

if __name__ == "__main__":
    # 測試錯誤處理器
    logging.basicConfig(level=logging.INFO)
    
    error_handler = create_error_handler()
    error_handler.start()
    
    try:
        # 模擬一些錯誤
        raise ValueError("測試錯誤")
    except Exception as e:
        error_handler.handle_error(
            e, 
            ErrorCategory.SYSTEM, 
            ErrorSeverity.MEDIUM, 
            "test_component"
        )
    
    time.sleep(3)  # 等待處理完成
    
    # 輸出統計
    stats = error_handler.get_error_statistics()
    print(f"錯誤統計: {stats}")
    
    error_handler.stop()