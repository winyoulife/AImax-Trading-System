"""
錯誤處理器 - 統一處理GUI系統的異常和錯誤恢復
"""
import logging
import traceback
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import threading
import json

class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """錯誤分類"""
    INITIALIZATION = "initialization"
    RUNTIME = "runtime"
    NETWORK = "network"
    RESOURCE = "resource"
    USER_INPUT = "user_input"
    AI_MODEL = "ai_model"
    DATA_PROCESSING = "data_processing"

@dataclass
class ErrorRecord:
    """錯誤記錄"""
    timestamp: datetime
    component: str
    error_type: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: str
    stack_trace: str
    context: Dict[str, Any]
    resolved: bool = False
    resolution_method: Optional[str] = None
    resolution_time: Optional[datetime] = None

class RecoveryStrategy:
    """錯誤恢復策略"""
    
    def __init__(self, name: str, max_retries: int = 3, retry_delay: float = 1.0):
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0
        
    def attempt_recovery(self, component: Any, error: Exception, context: Dict[str, Any]) -> bool:
        """
        嘗試錯誤恢復
        
        Args:
            component: 出錯的組件
            error: 異常對象
            context: 錯誤上下文
            
        Returns:
            bool: 恢復是否成功
        """
        raise NotImplementedError("子類必須實現此方法")
    
    def reset_retry_count(self):
        """重置重試計數"""
        self.retry_count = 0
    
    def is_recoverable(self, error: Exception) -> bool:
        """
        判斷錯誤是否可恢復
        
        Args:
            error: 異常對象
            
        Returns:
            bool: 是否可恢復
        """
        return True

class ComponentRestartStrategy(RecoveryStrategy):
    """組件重啟恢復策略"""
    
    def attempt_recovery(self, component: Any, error: Exception, context: Dict[str, Any]) -> bool:
        """嘗試重啟組件"""
        try:
            if hasattr(component, 'restart'):
                component.restart()
                return True
            elif hasattr(component, 'initialize'):
                component.initialize()
                return True
            return False
        except Exception:
            return False

class FallbackModeStrategy(RecoveryStrategy):
    """降級模式恢復策略"""
    
    def attempt_recovery(self, component: Any, error: Exception, context: Dict[str, Any]) -> bool:
        """嘗試切換到降級模式"""
        try:
            if hasattr(component, 'enable_fallback_mode'):
                component.enable_fallback_mode()
                return True
            return False
        except Exception:
            return False

class NetworkRetryStrategy(RecoveryStrategy):
    """網絡重試恢復策略"""
    
    def __init__(self, name: str, max_retries: int = 5, retry_delay: float = 2.0):
        super().__init__(name, max_retries, retry_delay)
    
    def attempt_recovery(self, component: Any, error: Exception, context: Dict[str, Any]) -> bool:
        """嘗試網絡重連"""
        import time
        
        if self.retry_count >= self.max_retries:
            return False
            
        self.retry_count += 1
        time.sleep(self.retry_delay * self.retry_count)  # 指數退避
        
        try:
            if hasattr(component, 'reconnect'):
                component.reconnect()
                return True
            elif hasattr(component, 'refresh_connection'):
                component.refresh_connection()
                return True
            return False
        except Exception:
            return False

class ErrorHandler:
    """
    錯誤處理器 - 統一處理系統異常和錯誤恢復
    
    功能:
    - 統一異常捕獲和記錄
    - 用戶友好的錯誤消息顯示
    - 自動錯誤恢復策略
    - 錯誤統計和分析
    """
    
    def __init__(self, gui_instance=None):
        self.logger = logging.getLogger(__name__)
        self.gui = gui_instance
        self.error_log: List[ErrorRecord] = []
        self.recovery_strategies: Dict[type, RecoveryStrategy] = {}
        self.error_callbacks: List[Callable[[ErrorRecord], None]] = []
        self.lock = threading.Lock()
        
        # 錯誤統計
        self.error_stats = {
            "total_errors": 0,
            "resolved_errors": 0,
            "by_category": {category.value: 0 for category in ErrorCategory},
            "by_severity": {severity.value: 0 for severity in ErrorSeverity},
            "by_component": {}
        }
        
        # 註冊默認恢復策略
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """註冊默認的錯誤恢復策略"""
        self.register_recovery_strategy(ConnectionError, NetworkRetryStrategy("network_retry"))
        self.register_recovery_strategy(TimeoutError, NetworkRetryStrategy("timeout_retry"))
        self.register_recovery_strategy(RuntimeError, ComponentRestartStrategy("component_restart"))
        self.register_recovery_strategy(AttributeError, FallbackModeStrategy("fallback_mode"))
    
    def register_recovery_strategy(self, error_type: type, strategy: RecoveryStrategy):
        """
        註冊錯誤恢復策略
        
        Args:
            error_type: 錯誤類型
            strategy: 恢復策略
        """
        self.recovery_strategies[error_type] = strategy
        self.logger.info(f"✅ 註冊錯誤恢復策略: {error_type.__name__} -> {strategy.name}")
    
    def subscribe_to_errors(self, callback: Callable[[ErrorRecord], None]):
        """
        訂閱錯誤事件
        
        Args:
            callback: 錯誤回調函數
        """
        self.error_callbacks.append(callback)
    
    def handle_exception(self, exception: Exception, component: str, 
                        category: ErrorCategory = ErrorCategory.RUNTIME,
                        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                        context: Dict[str, Any] = None) -> bool:
        """
        處理異常
        
        Args:
            exception: 異常對象
            component: 出錯的組件名稱
            category: 錯誤分類
            severity: 錯誤嚴重程度
            context: 錯誤上下文
            
        Returns:
            bool: 是否成功處理（恢復）
        """
        with self.lock:
            if context is None:
                context = {}
            
            # 創建錯誤記錄
            error_record = ErrorRecord(
                timestamp=datetime.now(),
                component=component,
                error_type=type(exception).__name__,
                category=category,
                severity=severity,
                message=str(exception),
                details=self._extract_error_details(exception),
                stack_trace=traceback.format_exc(),
                context=context
            )
            
            # 記錄錯誤
            self.error_log.append(error_record)
            self._update_error_stats(error_record)
            
            # 記錄日誌
            log_level = self._get_log_level(severity)
            self.logger.log(log_level, f"❌ {component} 發生 {category.value} 錯誤: {exception}")
            
            # 嘗試自動恢復
            recovery_success = self._attempt_auto_recovery(error_record, exception, context)
            
            if recovery_success:
                error_record.resolved = True
                error_record.resolution_time = datetime.now()
                self.error_stats["resolved_errors"] += 1
                self.logger.info(f"✅ {component} 錯誤已自動恢復")
            else:
                # 顯示用戶友好的錯誤消息
                self.show_user_friendly_error(error_record)
            
            # 通知錯誤訂閱者
            self._notify_error_subscribers(error_record)
            
            return recovery_success
    
    def _extract_error_details(self, exception: Exception) -> str:
        """提取錯誤詳細信息"""
        details = []
        
        # 基本信息
        details.append(f"錯誤類型: {type(exception).__name__}")
        details.append(f"錯誤消息: {str(exception)}")
        
        # 如果有額外屬性
        if hasattr(exception, 'errno'):
            details.append(f"錯誤代碼: {exception.errno}")
        if hasattr(exception, 'filename'):
            details.append(f"相關文件: {exception.filename}")
        
        return "\n".join(details)
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """根據嚴重程度獲取日誌級別"""
        level_map = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return level_map.get(severity, logging.WARNING)
    
    def _attempt_auto_recovery(self, error_record: ErrorRecord, 
                              exception: Exception, context: Dict[str, Any]) -> bool:
        """
        嘗試自動錯誤恢復
        
        Args:
            error_record: 錯誤記錄
            exception: 異常對象
            context: 錯誤上下文
            
        Returns:
            bool: 恢復是否成功
        """
        error_type = type(exception)
        
        # 查找匹配的恢復策略
        strategy = None
        for registered_type, registered_strategy in self.recovery_strategies.items():
            if issubclass(error_type, registered_type):
                strategy = registered_strategy
                break
        
        if not strategy:
            self.logger.warning(f"⚠️ 沒有找到 {error_type.__name__} 的恢復策略")
            return False
        
        if not strategy.is_recoverable(exception):
            self.logger.warning(f"⚠️ 錯誤 {error_type.__name__} 不可恢復")
            return False
        
        # 嘗試恢復
        try:
            self.logger.info(f"🔄 嘗試使用策略 {strategy.name} 恢復錯誤...")
            
            # 獲取組件實例（如果可能）
            component_instance = context.get('component_instance')
            
            success = strategy.attempt_recovery(component_instance, exception, context)
            
            if success:
                error_record.resolution_method = strategy.name
                self.logger.info(f"✅ 錯誤恢復成功，使用策略: {strategy.name}")
                strategy.reset_retry_count()
            else:
                self.logger.warning(f"❌ 錯誤恢復失敗，策略: {strategy.name}")
            
            return success
            
        except Exception as recovery_error:
            self.logger.error(f"❌ 錯誤恢復過程中發生異常: {recovery_error}")
            return False
    
    def show_user_friendly_error(self, error_record: ErrorRecord):
        """
        顯示用戶友好的錯誤消息
        
        Args:
            error_record: 錯誤記錄
        """
        # 生成用戶友好的錯誤消息
        user_message = self._generate_user_friendly_message(error_record)
        
        # 如果有GUI實例，顯示錯誤對話框
        if self.gui and hasattr(self.gui, 'show_error_dialog'):
            self.gui.show_error_dialog(user_message, error_record.details)
        else:
            # 否則記錄到日誌
            self.logger.error(f"用戶錯誤消息: {user_message}")
    
    def _generate_user_friendly_message(self, error_record: ErrorRecord) -> str:
        """
        生成用戶友好的錯誤消息
        
        Args:
            error_record: 錯誤記錄
            
        Returns:
            str: 用戶友好的錯誤消息
        """
        category_messages = {
            ErrorCategory.INITIALIZATION: "系統初始化時發生問題",
            ErrorCategory.NETWORK: "網絡連接出現問題",
            ErrorCategory.RESOURCE: "系統資源不足",
            ErrorCategory.AI_MODEL: "AI模型處理出現問題",
            ErrorCategory.DATA_PROCESSING: "數據處理出現問題",
            ErrorCategory.USER_INPUT: "輸入數據有誤",
            ErrorCategory.RUNTIME: "程序運行時出現問題"
        }
        
        base_message = category_messages.get(error_record.category, "系統出現未知問題")
        
        # 根據錯誤類型提供具體建議
        suggestions = self._get_error_suggestions(error_record)
        
        if suggestions:
            return f"{base_message}。\n\n建議解決方案:\n{suggestions}"
        else:
            return f"{base_message}。請檢查系統狀態或聯繫技術支持。"
    
    def _get_error_suggestions(self, error_record: ErrorRecord) -> str:
        """
        根據錯誤類型獲取解決建議
        
        Args:
            error_record: 錯誤記錄
            
        Returns:
            str: 解決建議
        """
        suggestions_map = {
            "ConnectionError": "• 檢查網絡連接\n• 確認服務器狀態\n• 稍後重試",
            "TimeoutError": "• 檢查網絡速度\n• 增加超時時間\n• 重新嘗試操作",
            "MemoryError": "• 關閉不必要的程序\n• 重啟應用程序\n• 檢查系統內存",
            "FileNotFoundError": "• 檢查文件路徑\n• 確認文件存在\n• 檢查文件權限",
            "AttributeError": "• 重啟相關組件\n• 檢查配置設置\n• 更新程序版本"
        }
        
        return suggestions_map.get(error_record.error_type, "")
    
    def _update_error_stats(self, error_record: ErrorRecord):
        """更新錯誤統計"""
        self.error_stats["total_errors"] += 1
        self.error_stats["by_category"][error_record.category.value] += 1
        self.error_stats["by_severity"][error_record.severity.value] += 1
        
        if error_record.component not in self.error_stats["by_component"]:
            self.error_stats["by_component"][error_record.component] = 0
        self.error_stats["by_component"][error_record.component] += 1
    
    def _notify_error_subscribers(self, error_record: ErrorRecord):
        """通知錯誤訂閱者"""
        for callback in self.error_callbacks:
            try:
                callback(error_record)
            except Exception as e:
                self.logger.error(f"錯誤回調執行失敗: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        獲取錯誤統計信息
        
        Returns:
            Dict: 錯誤統計信息
        """
        return self.error_stats.copy()
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorRecord]:
        """
        獲取最近的錯誤記錄
        
        Args:
            limit: 返回記錄數量限制
            
        Returns:
            List[ErrorRecord]: 最近的錯誤記錄
        """
        return sorted(self.error_log, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def generate_error_report(self) -> str:
        """
        生成錯誤報告
        
        Returns:
            str: 錯誤報告
        """
        report = {
            "report_time": datetime.now().isoformat(),
            "statistics": self.get_error_statistics(),
            "recent_errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "component": error.component,
                    "error_type": error.error_type,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "message": error.message,
                    "resolved": error.resolved,
                    "resolution_method": error.resolution_method
                }
                for error in self.get_recent_errors(20)
            ]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def clear_error_log(self):
        """清空錯誤日誌"""
        with self.lock:
            self.error_log.clear()
            self.error_stats = {
                "total_errors": 0,
                "resolved_errors": 0,
                "by_category": {category.value: 0 for category in ErrorCategory},
                "by_severity": {severity.value: 0 for severity in ErrorSeverity},
                "by_component": {}
            }
            self.logger.info("✅ 錯誤日誌已清空")