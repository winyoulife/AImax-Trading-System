"""
組件管理器 - 管理GUI組件的初始化順序和依賴關係
"""
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import threading
import traceback

class ComponentStatus(Enum):
    """組件狀態枚舉"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"
    RETRYING = "retrying"

@dataclass
class ComponentInfo:
    """組件信息"""
    name: str
    component_class: type
    dependencies: List[str]
    instance: Optional[Any] = None
    status: ComponentStatus = ComponentStatus.NOT_INITIALIZED
    error_count: int = 0
    last_error: Optional[str] = None
    initialization_time: Optional[datetime] = None
    retry_count: int = 0

class ComponentManager:
    """
    組件管理器 - 負責管理GUI組件的生命週期
    
    功能:
    - 管理組件初始化順序
    - 處理組件依賴關係
    - 提供錯誤恢復和重試機制
    - 監控組件健康狀態
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.logger = logging.getLogger(__name__)
        self.components: Dict[str, ComponentInfo] = {}
        self.initialization_order: List[str] = []
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.initialization_lock = threading.Lock()
        self.status_callbacks: Dict[str, List[Callable]] = {}
        
        # 初始化進度追蹤
        self.total_components = 0
        self.initialized_components = 0
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None
        
    def register_component(self, name: str, component_class: type, 
                         dependencies: List[str] = None, **kwargs) -> bool:
        """
        註冊組件
        
        Args:
            name: 組件名稱
            component_class: 組件類
            dependencies: 依賴的組件列表
            **kwargs: 組件初始化參數
            
        Returns:
            bool: 註冊是否成功
        """
        try:
            if dependencies is None:
                dependencies = []
                
            # 檢查依賴是否存在
            for dep in dependencies:
                if dep not in self.components:
                    self.logger.warning(f"組件 {name} 的依賴 {dep} 尚未註冊")
            
            component_info = ComponentInfo(
                name=name,
                component_class=component_class,
                dependencies=dependencies
            )
            
            self.components[name] = component_info
            self.logger.info(f"✅ 組件 {name} 註冊成功，依賴: {dependencies}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 組件 {name} 註冊失敗: {e}")
            return False
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """設置初始化進度回調"""
        self.progress_callback = callback
    
    def _update_progress(self, message: str):
        """更新初始化進度"""
        if self.progress_callback:
            self.progress_callback(self.initialized_components, self.total_components, message)
    
    def _resolve_initialization_order(self) -> List[str]:
        """
        解析組件初始化順序（拓撲排序）
        
        Returns:
            List[str]: 按依賴順序排列的組件名稱列表
        """
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component_name: str):
            if component_name in temp_visited:
                raise ValueError(f"檢測到循環依賴: {component_name}")
            if component_name in visited:
                return
                
            temp_visited.add(component_name)
            
            if component_name in self.components:
                for dep in self.components[component_name].dependencies:
                    visit(dep)
            
            temp_visited.remove(component_name)
            visited.add(component_name)
            order.append(component_name)
        
        for component_name in self.components:
            if component_name not in visited:
                visit(component_name)
        
        return order
    
    def _initialize_single_component(self, name: str, **kwargs) -> bool:
        """
        初始化單個組件
        
        Args:
            name: 組件名稱
            **kwargs: 初始化參數
            
        Returns:
            bool: 初始化是否成功
        """
        component_info = self.components[name]
        
        try:
            # 更新狀態為初始化中
            component_info.status = ComponentStatus.INITIALIZING
            self._notify_status_change(name, ComponentStatus.INITIALIZING)
            
            self.logger.info(f"🔄 開始初始化組件: {name}")
            start_time = time.time()
            
            # 檢查依賴是否已初始化
            for dep in component_info.dependencies:
                if dep not in self.components:
                    raise ValueError(f"依賴組件 {dep} 不存在")
                if self.components[dep].status != ComponentStatus.READY:
                    raise ValueError(f"依賴組件 {dep} 未就緒，狀態: {self.components[dep].status}")
            
            # 準備初始化參數
            init_kwargs = kwargs.copy()
            
            # 將依賴組件實例作為參數傳入
            for dep in component_info.dependencies:
                init_kwargs[f"{dep}_instance"] = self.components[dep].instance
            
            # 創建組件實例
            component_info.instance = component_info.component_class(**init_kwargs)
            
            # 如果組件有初始化方法，調用它
            if hasattr(component_info.instance, 'initialize'):
                component_info.instance.initialize()
            
            # 更新狀態
            component_info.status = ComponentStatus.READY
            component_info.initialization_time = datetime.now()
            component_info.error_count = 0
            component_info.retry_count = 0
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"✅ 組件 {name} 初始化成功，耗時: {elapsed_time:.2f}s")
            
            self._notify_status_change(name, ComponentStatus.READY)
            return True
            
        except Exception as e:
            error_msg = f"組件 {name} 初始化失敗: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())
            
            component_info.status = ComponentStatus.ERROR
            component_info.last_error = error_msg
            component_info.error_count += 1
            
            self._notify_status_change(name, ComponentStatus.ERROR)
            return False
    
    def _retry_component_initialization(self, name: str, **kwargs) -> bool:
        """
        重試組件初始化
        
        Args:
            name: 組件名稱
            **kwargs: 初始化參數
            
        Returns:
            bool: 重試是否成功
        """
        component_info = self.components[name]
        
        if component_info.retry_count >= self.max_retries:
            self.logger.error(f"❌ 組件 {name} 重試次數已達上限 ({self.max_retries})")
            return False
        
        component_info.retry_count += 1
        component_info.status = ComponentStatus.RETRYING
        
        self.logger.info(f"🔄 重試初始化組件 {name} (第 {component_info.retry_count} 次)")
        self._notify_status_change(name, ComponentStatus.RETRYING)
        
        # 等待重試延遲
        time.sleep(self.retry_delay)
        
        return self._initialize_single_component(name, **kwargs)
    
    def initialize_components(self, **kwargs) -> bool:
        """
        初始化所有組件
        
        Args:
            **kwargs: 全局初始化參數
            
        Returns:
            bool: 是否所有組件都初始化成功
        """
        with self.initialization_lock:
            try:
                # 解析初始化順序
                self.initialization_order = self._resolve_initialization_order()
                self.total_components = len(self.initialization_order)
                self.initialized_components = 0
                
                self.logger.info(f"🚀 開始初始化 {self.total_components} 個組件")
                self.logger.info(f"初始化順序: {' -> '.join(self.initialization_order)}")
                
                self._update_progress("開始組件初始化...")
                
                success_count = 0
                failed_components = []
                
                # 按順序初始化組件
                for name in self.initialization_order:
                    self._update_progress(f"正在初始化: {name}")
                    
                    success = self._initialize_single_component(name, **kwargs)
                    
                    if not success:
                        # 嘗試重試
                        self.logger.warning(f"⚠️ 組件 {name} 初始化失敗，嘗試重試...")
                        success = self._retry_component_initialization(name, **kwargs)
                    
                    if success:
                        success_count += 1
                        self.initialized_components += 1
                        self._update_progress(f"✅ {name} 初始化完成")
                    else:
                        failed_components.append(name)
                        self._update_progress(f"❌ {name} 初始化失敗")
                
                # 總結初始化結果
                if failed_components:
                    self.logger.warning(f"⚠️ 組件初始化完成，成功: {success_count}/{self.total_components}")
                    self.logger.warning(f"失敗的組件: {', '.join(failed_components)}")
                    
                    # 嘗試優雅降級
                    self._handle_initialization_failures(failed_components)
                    return False
                else:
                    self.logger.info(f"🎉 所有組件初始化成功! ({success_count}/{self.total_components})")
                    self._update_progress("所有組件初始化完成!")
                    return True
                    
            except Exception as e:
                self.logger.error(f"❌ 組件初始化過程發生錯誤: {e}")
                self.logger.debug(traceback.format_exc())
                return False
    
    def _handle_initialization_failures(self, failed_components: List[str]):
        """
        處理初始化失敗的組件（優雅降級）
        
        Args:
            failed_components: 失敗的組件列表
        """
        self.logger.info("🔧 開始處理初始化失敗的組件...")
        
        for name in failed_components:
            component_info = self.components[name]
            
            # 嘗試創建降級版本
            if hasattr(component_info.component_class, 'create_fallback'):
                try:
                    self.logger.info(f"🔄 為組件 {name} 創建降級版本...")
                    component_info.instance = component_info.component_class.create_fallback()
                    component_info.status = ComponentStatus.READY
                    self.logger.info(f"✅ 組件 {name} 降級版本創建成功")
                except Exception as e:
                    self.logger.error(f"❌ 組件 {name} 降級版本創建失敗: {e}")
                    component_info.status = ComponentStatus.DISABLED
            else:
                # 禁用組件
                component_info.status = ComponentStatus.DISABLED
                self.logger.warning(f"⚠️ 組件 {name} 已被禁用")
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        獲取組件實例
        
        Args:
            name: 組件名稱
            
        Returns:
            組件實例或None
        """
        if name not in self.components:
            self.logger.warning(f"組件 {name} 不存在")
            return None
            
        component_info = self.components[name]
        if component_info.status != ComponentStatus.READY:
            self.logger.warning(f"組件 {name} 未就緒，狀態: {component_info.status}")
            return None
            
        return component_info.instance
    
    def restart_component(self, name: str, **kwargs) -> bool:
        """
        重啟組件
        
        Args:
            name: 組件名稱
            **kwargs: 初始化參數
            
        Returns:
            bool: 重啟是否成功
        """
        if name not in self.components:
            self.logger.error(f"組件 {name} 不存在")
            return False
        
        self.logger.info(f"🔄 重啟組件: {name}")
        
        # 重置組件狀態
        component_info = self.components[name]
        component_info.instance = None
        component_info.status = ComponentStatus.NOT_INITIALIZED
        component_info.retry_count = 0
        
        # 重新初始化
        return self._initialize_single_component(name, **kwargs)
    
    def get_component_status(self, name: str) -> Optional[ComponentStatus]:
        """獲取組件狀態"""
        if name not in self.components:
            return None
        return self.components[name].status
    
    def get_all_components_status(self) -> Dict[str, ComponentStatus]:
        """獲取所有組件狀態"""
        return {name: info.status for name, info in self.components.items()}
    
    def subscribe_to_status_changes(self, component_name: str, callback: Callable[[str, ComponentStatus], None]):
        """訂閱組件狀態變化"""
        if component_name not in self.status_callbacks:
            self.status_callbacks[component_name] = []
        self.status_callbacks[component_name].append(callback)
    
    def _notify_status_change(self, component_name: str, new_status: ComponentStatus):
        """通知組件狀態變化"""
        if component_name in self.status_callbacks:
            for callback in self.status_callbacks[component_name]:
                try:
                    callback(component_name, new_status)
                except Exception as e:
                    self.logger.error(f"狀態變化回調執行失敗: {e}")
    
    def get_initialization_report(self) -> Dict[str, Any]:
        """
        獲取初始化報告
        
        Returns:
            包含初始化詳情的字典
        """
        report = {
            "total_components": len(self.components),
            "ready_components": sum(1 for info in self.components.values() 
                                  if info.status == ComponentStatus.READY),
            "failed_components": sum(1 for info in self.components.values() 
                                   if info.status == ComponentStatus.ERROR),
            "disabled_components": sum(1 for info in self.components.values() 
                                     if info.status == ComponentStatus.DISABLED),
            "initialization_order": self.initialization_order,
            "component_details": {}
        }
        
        for name, info in self.components.items():
            report["component_details"][name] = {
                "status": info.status.value,
                "error_count": info.error_count,
                "last_error": info.last_error,
                "retry_count": info.retry_count,
                "initialization_time": info.initialization_time.isoformat() if info.initialization_time else None,
                "dependencies": info.dependencies
            }
        
        return report
    
    def shutdown_all_components(self):
        """關閉所有組件"""
        self.logger.info("🔄 開始關閉所有組件...")
        
        # 按初始化順序的逆序關閉組件
        shutdown_order = list(reversed(self.initialization_order))
        
        for name in shutdown_order:
            try:
                component_info = self.components[name]
                if component_info.instance and hasattr(component_info.instance, 'shutdown'):
                    self.logger.info(f"🔄 關閉組件: {name}")
                    component_info.instance.shutdown()
                    component_info.status = ComponentStatus.NOT_INITIALIZED
                    component_info.instance = None
            except Exception as e:
                self.logger.error(f"❌ 關閉組件 {name} 時發生錯誤: {e}")
        
        self.logger.info("✅ 所有組件關閉完成")