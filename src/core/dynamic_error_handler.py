#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 錯誤處理系統
提供全面的異常處理、錯誤恢復和系統診斷功能
"""
import logging
import traceback
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os
from pathlib import Path

# 錯誤類型枚舉
class ErrorType(Enum):
    """錯誤類型分類"""
    DATA_ERROR = "data_error"
    CALCULATION_ERROR = "calculation_error"
    NETWORK_ERROR = "network_error"
    MEMORY_ERROR = "memory_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    TRADING_ERROR = "trading_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"

class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    """恢復動作類型"""
    RETRY = "retry"
    SKIP = "skip"
    RESET = "reset"
    FALLBACK = "fallback"
    SHUTDOWN = "shutdown"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorRecord:
    """錯誤記錄數據結構"""
    error_id: str
    timestamp: datetime
    error_type: ErrorType
    severity: ErrorSeverity
    component: str
    function_name: str
    error_message: str
    stack_trace: str
    context_data: Dict[str, Any]
    recovery_action: Optional[RecoveryAction] = None
    recovery_success: Optional[bool] = None
    recovery_attempts: int = 0
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        data = asdict(self)
        # 處理枚舉類型
        data['error_type'] = self.error_type.value
        data['severity'] = self.severity.value
        if self.recovery_action:
            data['recovery_action'] = self.recovery_action.value
        # 處理時間格式
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolution_time:
            data['resolution_time'] = self.resolution_time.isoformat()
        return data

class DynamicErrorHandler:
    """動態交易系統錯誤處理器"""
    
    def __init__(self, log_dir: str = "logs", max_error_records: int = 1000):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_error_records = max_error_records
        
        # 錯誤記錄存儲
        self.error_records: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self.component_errors: Dict[str, List[ErrorRecord]] = {}
        
        # 恢復策略配置
        self.recovery_strategies: Dict[ErrorType, RecoveryAction] = {
            ErrorType.DATA_ERROR: RecoveryAction.RETRY,
            ErrorType.CALCULATION_ERROR: RecoveryAction.FALLBACK,
            ErrorType.NETWORK_ERROR: RecoveryAction.RETRY,
            ErrorType.MEMORY_ERROR: RecoveryAction.RESET,
            ErrorType.TIMEOUT_ERROR: RecoveryAction.RETRY,
            ErrorType.CONFIGURATION_ERROR: RecoveryAction.MANUAL_INTERVENTION,
            ErrorType.TRADING_ERROR: RecoveryAction.FALLBACK,
            ErrorType.SYSTEM_ERROR: RecoveryAction.RESET,
            ErrorType.UNKNOWN_ERROR: RecoveryAction.MANUAL_INTERVENTION
        }
        
        # 重試配置
        self.max_retry_attempts = 3
        self.retry_delays = [1, 2, 5]  # 秒
        
        # 回調函數
        self.error_callbacks: List[Callable] = []
        self.recovery_callbacks: List[Callable] = []
        
        # 線程安全鎖
        self.lock = threading.RLock()
        
        # 設置日誌
        self.setup_logging()
        
        self.logger.info("動態錯誤處理系統初始化完成")
    
    def setup_logging(self):
        """設置日誌系統"""
        self.logger = logging.getLogger(f"{__name__}.DynamicErrorHandler")
        
        # 創建錯誤日誌文件處理器
        error_log_file = self.log_dir / f"dynamic_errors_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        file_handler.setLevel(logging.ERROR)
        
        # 創建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # 添加處理器
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.DEBUG)
    
    def handle_error(self, 
                    error: Exception,
                    component: str,
                    function_name: str,
                    context_data: Optional[Dict[str, Any]] = None,
                    error_type: Optional[ErrorType] = None,
                    severity: Optional[ErrorSeverity] = None) -> ErrorRecord:
        """
        處理錯誤的主要方法
        
        Args:
            error: 異常對象
            component: 發生錯誤的組件名稱
            function_name: 發生錯誤的函數名稱
            context_data: 錯誤上下文數據
            error_type: 錯誤類型（可選，會自動推斷）
            severity: 錯誤嚴重程度（可選，會自動推斷）
        
        Returns:
            ErrorRecord: 錯誤記錄
        """
        with self.lock:
            try:
                # 生成錯誤ID
                error_id = f"{component}_{function_name}_{int(time.time())}"
                
                # 自動推斷錯誤類型和嚴重程度
                if error_type is None:
                    error_type = self._infer_error_type(error)
                if severity is None:
                    severity = self._infer_severity(error, error_type)
                
                # 創建錯誤記錄
                error_record = ErrorRecord(
                    error_id=error_id,
                    timestamp=datetime.now(),
                    error_type=error_type,
                    severity=severity,
                    component=component,
                    function_name=function_name,
                    error_message=str(error),
                    stack_trace=traceback.format_exc(),
                    context_data=context_data or {}
                )
                
                # 記錄錯誤
                self._record_error(error_record)
                
                # 記錄日誌
                self.logger.error(
                    f"錯誤處理 - ID: {error_id}, 組件: {component}, "
                    f"函數: {function_name}, 類型: {error_type.value}, "
                    f"嚴重程度: {severity.value}, 訊息: {str(error)}"
                )
                
                # 執行恢復策略
                self._execute_recovery_strategy(error_record)
                
                # 觸發錯誤回調
                self._trigger_error_callbacks(error_record)
                
                return error_record
                
            except Exception as handler_error:
                # 錯誤處理器本身出錯的情況
                self.logger.critical(f"錯誤處理器內部錯誤: {handler_error}")
                # 創建基本錯誤記錄
                return ErrorRecord(
                    error_id=f"handler_error_{int(time.time())}",
                    timestamp=datetime.now(),
                    error_type=ErrorType.SYSTEM_ERROR,
                    severity=ErrorSeverity.CRITICAL,
                    component="error_handler",
                    function_name="handle_error",
                    error_message=str(handler_error),
                    stack_trace=traceback.format_exc(),
                    context_data={"original_error": str(error)}
                )
    
    def _infer_error_type(self, error: Exception) -> ErrorType:
        """推斷錯誤類型"""
        error_name = type(error).__name__.lower()
        error_message = str(error).lower()
        
        if any(keyword in error_name for keyword in ['value', 'type', 'key', 'index', 'attribute']):
            return ErrorType.DATA_ERROR
        elif any(keyword in error_name for keyword in ['calculation', 'math', 'overflow', 'division']):
            return ErrorType.CALCULATION_ERROR
        elif any(keyword in error_name for keyword in ['connection', 'network', 'http', 'url']):
            return ErrorType.NETWORK_ERROR
        elif any(keyword in error_name for keyword in ['memory', 'allocation']):
            return ErrorType.MEMORY_ERROR
        elif any(keyword in error_name for keyword in ['timeout', 'time']):
            return ErrorType.TIMEOUT_ERROR
        elif any(keyword in error_message for keyword in ['config', 'setting', 'parameter']):
            return ErrorType.CONFIGURATION_ERROR
        elif any(keyword in error_message for keyword in ['trade', 'order', 'position']):
            return ErrorType.TRADING_ERROR
        elif any(keyword in error_name for keyword in ['system', 'os', 'io']):
            return ErrorType.SYSTEM_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    def _infer_severity(self, error: Exception, error_type: ErrorType) -> ErrorSeverity:
        """推斷錯誤嚴重程度"""
        error_name = type(error).__name__.lower()
        
        # 關鍵錯誤
        if any(keyword in error_name for keyword in ['critical', 'fatal', 'system']):
            return ErrorSeverity.CRITICAL
        
        # 根據錯誤類型判斷
        if error_type in [ErrorType.SYSTEM_ERROR, ErrorType.MEMORY_ERROR]:
            return ErrorSeverity.HIGH
        elif error_type in [ErrorType.TRADING_ERROR, ErrorType.CONFIGURATION_ERROR]:
            return ErrorSeverity.HIGH
        elif error_type in [ErrorType.NETWORK_ERROR, ErrorType.TIMEOUT_ERROR]:
            return ErrorSeverity.MEDIUM
        elif error_type in [ErrorType.DATA_ERROR, ErrorType.CALCULATION_ERROR]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _record_error(self, error_record: ErrorRecord):
        """記錄錯誤"""
        # 添加到錯誤記錄列表
        self.error_records.append(error_record)
        
        # 更新錯誤計數
        error_key = f"{error_record.component}_{error_record.error_type.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # 按組件分類錯誤
        if error_record.component not in self.component_errors:
            self.component_errors[error_record.component] = []
        self.component_errors[error_record.component].append(error_record)
        
        # 限制記錄數量
        if len(self.error_records) > self.max_error_records:
            self.error_records = self.error_records[-self.max_error_records:]
        
        # 保存到文件
        self._save_error_record(error_record)
    
    def _save_error_record(self, error_record: ErrorRecord):
        """保存錯誤記錄到文件"""
        try:
            error_file = self.log_dir / f"error_records_{datetime.now().strftime('%Y%m%d')}.json"
            
            # 讀取現有記錄
            records = []
            if error_file.exists():
                try:
                    with open(error_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except:
                    records = []
            
            # 添加新記錄
            records.append(error_record.to_dict())
            
            # 保存回文件
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存錯誤記錄失敗: {e}")
    
    def _execute_recovery_strategy(self, error_record: ErrorRecord):
        """執行恢復策略"""
        try:
            recovery_action = self.recovery_strategies.get(
                error_record.error_type, 
                RecoveryAction.MANUAL_INTERVENTION
            )
            
            error_record.recovery_action = recovery_action
            
            self.logger.info(f"執行恢復策略: {recovery_action.value} for 錯誤 {error_record.error_id}")
            
            if recovery_action == RecoveryAction.RETRY:
                self._execute_retry_strategy(error_record)
            elif recovery_action == RecoveryAction.FALLBACK:
                self._execute_fallback_strategy(error_record)
            elif recovery_action == RecoveryAction.RESET:
                self._execute_reset_strategy(error_record)
            elif recovery_action == RecoveryAction.SKIP:
                self._execute_skip_strategy(error_record)
            elif recovery_action == RecoveryAction.SHUTDOWN:
                self._execute_shutdown_strategy(error_record)
            else:
                self.logger.warning(f"需要手動干預處理錯誤: {error_record.error_id}")
                
        except Exception as e:
            self.logger.error(f"執行恢復策略失敗: {e}")
            error_record.recovery_success = False
    
    def _execute_retry_strategy(self, error_record: ErrorRecord):
        """執行重試策略"""
        # 這裡只是記錄重試意圖，實際重試由調用方執行
        error_record.recovery_attempts += 1
        self.logger.info(f"標記重試策略 - 錯誤 {error_record.error_id}, 嘗試次數: {error_record.recovery_attempts}")
        
        if error_record.recovery_attempts <= self.max_retry_attempts:
            error_record.recovery_success = None  # 待定
        else:
            error_record.recovery_success = False
            self.logger.warning(f"重試次數超限 - 錯誤 {error_record.error_id}")
    
    def _execute_fallback_strategy(self, error_record: ErrorRecord):
        """執行回退策略"""
        self.logger.info(f"執行回退策略 - 錯誤 {error_record.error_id}")
        # 回退策略的具體實現由各組件自行處理
        error_record.recovery_success = True
    
    def _execute_reset_strategy(self, error_record: ErrorRecord):
        """執行重置策略"""
        self.logger.info(f"執行重置策略 - 錯誤 {error_record.error_id}")
        # 重置策略的具體實現由各組件自行處理
        error_record.recovery_success = True
    
    def _execute_skip_strategy(self, error_record: ErrorRecord):
        """執行跳過策略"""
        self.logger.info(f"執行跳過策略 - 錯誤 {error_record.error_id}")
        error_record.recovery_success = True
        error_record.resolved = True
        error_record.resolution_time = datetime.now()
    
    def _execute_shutdown_strategy(self, error_record: ErrorRecord):
        """執行關閉策略"""
        self.logger.critical(f"執行關閉策略 - 錯誤 {error_record.error_id}")
        # 關閉策略需要由系統級別處理
        error_record.recovery_success = False
    
    def _trigger_error_callbacks(self, error_record: ErrorRecord):
        """觸發錯誤回調函數"""
        for callback in self.error_callbacks:
            try:
                callback(error_record)
            except Exception as e:
                self.logger.error(f"錯誤回調執行失敗: {e}")
    
    def add_error_callback(self, callback: Callable[[ErrorRecord], None]):
        """添加錯誤回調函數"""
        self.error_callbacks.append(callback)
    
    def add_recovery_callback(self, callback: Callable[[ErrorRecord], None]):
        """添加恢復回調函數"""
        self.recovery_callbacks.append(callback)
    
    def should_retry(self, error_record: ErrorRecord) -> bool:
        """判斷是否應該重試"""
        return (error_record.recovery_action == RecoveryAction.RETRY and 
                error_record.recovery_attempts < self.max_retry_attempts)
    
    def get_retry_delay(self, attempt: int) -> float:
        """獲取重試延遲時間"""
        if attempt <= len(self.retry_delays):
            return self.retry_delays[attempt - 1]
        else:
            return self.retry_delays[-1] * (attempt - len(self.retry_delays) + 1)
    
    def mark_resolved(self, error_id: str, resolution_note: str = ""):
        """標記錯誤已解決"""
        with self.lock:
            for error_record in self.error_records:
                if error_record.error_id == error_id:
                    error_record.resolved = True
                    error_record.resolution_time = datetime.now()
                    if resolution_note:
                        error_record.context_data['resolution_note'] = resolution_note
                    self.logger.info(f"錯誤已解決: {error_id}")
                    break
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """獲取錯誤統計信息"""
        with self.lock:
            total_errors = len(self.error_records)
            resolved_errors = sum(1 for record in self.error_records if record.resolved)
            
            # 按類型統計
            type_stats = {}
            for error_type in ErrorType:
                count = sum(1 for record in self.error_records if record.error_type == error_type)
                type_stats[error_type.value] = count
            
            # 按嚴重程度統計
            severity_stats = {}
            for severity in ErrorSeverity:
                count = sum(1 for record in self.error_records if record.severity == severity)
                severity_stats[severity.value] = count
            
            # 按組件統計
            component_stats = {}
            for component, records in self.component_errors.items():
                component_stats[component] = len(records)
            
            return {
                'total_errors': total_errors,
                'resolved_errors': resolved_errors,
                'unresolved_errors': total_errors - resolved_errors,
                'resolution_rate': (resolved_errors / total_errors * 100) if total_errors > 0 else 0,
                'error_by_type': type_stats,
                'error_by_severity': severity_stats,
                'error_by_component': component_stats,
                'recent_errors': [record.to_dict() for record in self.error_records[-10:]]
            }
    
    def get_component_health(self, component: str) -> Dict[str, Any]:
        """獲取組件健康狀態"""
        with self.lock:
            component_records = self.component_errors.get(component, [])
            
            if not component_records:
                return {
                    'component': component,
                    'status': 'healthy',
                    'total_errors': 0,
                    'recent_errors': 0,
                    'last_error': None
                }
            
            # 最近24小時的錯誤
            recent_cutoff = datetime.now() - timedelta(hours=24)
            recent_errors = [r for r in component_records if r.timestamp > recent_cutoff]
            
            # 未解決的錯誤
            unresolved_errors = [r for r in component_records if not r.resolved]
            
            # 確定健康狀態
            if len(unresolved_errors) > 5:
                status = 'critical'
            elif len(recent_errors) > 10:
                status = 'warning'
            elif len(recent_errors) > 0:
                status = 'caution'
            else:
                status = 'healthy'
            
            return {
                'component': component,
                'status': status,
                'total_errors': len(component_records),
                'recent_errors': len(recent_errors),
                'unresolved_errors': len(unresolved_errors),
                'last_error': component_records[-1].to_dict() if component_records else None
            }
    
    def export_error_report(self, output_path: str) -> bool:
        """導出錯誤報告"""
        try:
            report_data = {
                'report_timestamp': datetime.now().isoformat(),
                'statistics': self.get_error_statistics(),
                'component_health': {
                    component: self.get_component_health(component)
                    for component in self.component_errors.keys()
                },
                'all_errors': [record.to_dict() for record in self.error_records]
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"錯誤報告已導出到: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"導出錯誤報告失敗: {e}")
            return False
    
    def cleanup_old_records(self, days: int = 30):
        """清理舊的錯誤記錄"""
        with self.lock:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 清理內存中的記錄
            original_count = len(self.error_records)
            self.error_records = [
                record for record in self.error_records 
                if record.timestamp > cutoff_date
            ]
            
            # 重建組件錯誤映射
            self.component_errors.clear()
            for record in self.error_records:
                if record.component not in self.component_errors:
                    self.component_errors[record.component] = []
                self.component_errors[record.component].append(record)
            
            cleaned_count = original_count - len(self.error_records)
            self.logger.info(f"清理了 {cleaned_count} 條舊錯誤記錄")
            
            return cleaned_count

# 裝飾器函數
def handle_errors(component: str, error_handler: Optional[DynamicErrorHandler] = None):
    """錯誤處理裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    
                    if error_handler:
                        error_record = error_handler.handle_error(
                            error=e,
                            component=component,
                            function_name=func.__name__,
                            context_data={
                                'args': str(args)[:200],  # 限制長度
                                'kwargs': str(kwargs)[:200],
                                'attempt': attempt
                            }
                        )
                        
                        # 如果可以重試且未達到最大嘗試次數，則重試
                        if attempt < max_attempts and error_handler.should_retry(error_record):
                            retry_delay = error_handler.get_retry_delay(attempt)
                            time.sleep(retry_delay)
                            continue
                    
                    # 重新拋出異常
                    raise
            
            # 如果所有嘗試都失敗，拋出最後的異常
            raise RuntimeError(f"函數 {func.__name__} 在 {max_attempts} 次嘗試後仍然失敗")
        return wrapper
    return decorator

# 全局錯誤處理器實例
_global_error_handler: Optional[DynamicErrorHandler] = None

def get_global_error_handler() -> DynamicErrorHandler:
    """獲取全局錯誤處理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = DynamicErrorHandler()
    return _global_error_handler

def set_global_error_handler(handler: DynamicErrorHandler):
    """設置全局錯誤處理器"""
    global _global_error_handler
    _global_error_handler = handler