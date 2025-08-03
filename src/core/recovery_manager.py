#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢復管理器 - 提供自動重連和故障轉移功能
"""

import sys
import os
import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
import threading
from queue import Queue, Empty

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class ComponentStatus(Enum):
    """組件狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    OFFLINE = "offline"

class RecoveryStrategy(Enum):
    """恢復策略"""
    IMMEDIATE = "immediate"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    CIRCUIT_BREAKER = "circuit_breaker"

@dataclass
class ComponentInfo:
    """組件信息"""
    name: str
    status: ComponentStatus
    last_check: datetime
    failure_count: int
    recovery_attempts: int
    max_recovery_attempts: int
    health_check_callback: Callable
    recovery_callback: Callable
    fallback_callback: Optional[Callable] = None
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60

class RecoveryManager:
    """恢復管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.components: Dict[str, ComponentInfo] = {}
        self.monitoring_thread = None
        self.running = False
        self.check_interval = 10  # 健康檢查間隔（秒）
        self.recovery_queue = Queue()
        self.recovery_thread = None
        
        self.logger.info("🔄 恢復管理器初始化完成")
    
    def start(self):
        """啟動恢復管理器"""
        if not self.running:
            self.running = True
            
            # 啟動監控線程
            self.monitoring_thread = threading.Thread(
                target=self._monitor_components,
                daemon=True
            )
            self.monitoring_thread.start()
            
            # 啟動恢復線程
            self.recovery_thread = threading.Thread(
                target=self._process_recovery,
                daemon=True
            )
            self.recovery_thread.start()
            
            self.logger.info("🚀 恢復管理器已啟動")
    
    def stop(self):
        """停止恢復管理器"""
        self.running = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.recovery_thread:
            self.recovery_thread.join(timeout=5)
        
        self.logger.info("⏹️ 恢復管理器已停止")
    
    def register_component(
        self,
        name: str,
        health_check_callback: Callable,
        recovery_callback: Callable,
        fallback_callback: Optional[Callable] = None,
        max_recovery_attempts: int = 3,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60
    ):
        """註冊組件"""
        component = ComponentInfo(
            name=name,
            status=ComponentStatus.HEALTHY,
            last_check=datetime.now(),
            failure_count=0,
            recovery_attempts=0,
            max_recovery_attempts=max_recovery_attempts,
            health_check_callback=health_check_callback,
            recovery_callback=recovery_callback,
            fallback_callback=fallback_callback,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout
        )
        
        self.components[name] = component
        self.logger.info(f"📝 組件已註冊: {name}")
    
    def unregister_component(self, name: str):
        """取消註冊組件"""
        if name in self.components:
            del self.components[name]
            self.logger.info(f"🗑️ 組件已取消註冊: {name}")
    
    def get_component_status(self, name: str) -> Optional[ComponentStatus]:
        """獲取組件狀態"""
        if name in self.components:
            return self.components[name].status
        return None
    
    def get_all_components_status(self) -> Dict[str, ComponentStatus]:
        """獲取所有組件狀態"""
        return {name: comp.status for name, comp in self.components.items()}
    
    def force_recovery(self, name: str):
        """強制恢復組件"""
        if name in self.components:
            self.recovery_queue.put(name)
            self.logger.info(f"🔄 強制恢復組件: {name}")
    
    def _monitor_components(self):
        """監控組件健康狀態"""
        while self.running:
            try:
                for name, component in self.components.items():
                    self._check_component_health(name, component)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 監控組件時發生錯誤: {e}")
                time.sleep(5)
    
    def _check_component_health(self, name: str, component: ComponentInfo):
        """檢查組件健康狀態"""
        try:
            # 執行健康檢查
            is_healthy = component.health_check_callback()
            component.last_check = datetime.now()
            
            if is_healthy:
                if component.status != ComponentStatus.HEALTHY:
                    self.logger.info(f"✅ 組件恢復健康: {name}")
                    component.status = ComponentStatus.HEALTHY
                    component.failure_count = 0
                    component.recovery_attempts = 0
            else:
                self._handle_component_failure(name, component)
                
        except Exception as e:
            self.logger.error(f"❌ 檢查組件 {name} 健康狀態時發生錯誤: {e}")
            self._handle_component_failure(name, component)
    
    def _handle_component_failure(self, name: str, component: ComponentInfo):
        """處理組件故障"""
        component.failure_count += 1
        
        # 檢查是否觸發熔斷器
        if component.failure_count >= component.circuit_breaker_threshold:
            if component.status != ComponentStatus.OFFLINE:
                self.logger.warning(f"🔴 組件 {name} 觸發熔斷器，進入離線狀態")
                component.status = ComponentStatus.OFFLINE
                
                # 啟動熔斷器超時恢復
                self._schedule_circuit_breaker_recovery(name, component)
            return
        
        # 更新狀態
        if component.status == ComponentStatus.HEALTHY:
            component.status = ComponentStatus.DEGRADED
            self.logger.warning(f"🟡 組件 {name} 狀態降級")
        elif component.status == ComponentStatus.DEGRADED:
            component.status = ComponentStatus.FAILED
            self.logger.error(f"🔴 組件 {name} 故障")
            
            # 加入恢復隊列
            self.recovery_queue.put(name)
    
    def _schedule_circuit_breaker_recovery(self, name: str, component: ComponentInfo):
        """安排熔斷器恢復"""
        def recovery_timer():
            time.sleep(component.circuit_breaker_timeout)
            if component.status == ComponentStatus.OFFLINE:
                self.logger.info(f"🔄 熔斷器超時，嘗試恢復組件: {name}")
                component.failure_count = 0
                component.status = ComponentStatus.FAILED
                self.recovery_queue.put(name)
        
        timer_thread = threading.Thread(target=recovery_timer, daemon=True)
        timer_thread.start()
    
    def _process_recovery(self):
        """處理恢復隊列"""
        while self.running:
            try:
                name = self.recovery_queue.get(timeout=1)
                if name in self.components:
                    self._recover_component(name, self.components[name])
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ 處理恢復隊列時發生錯誤: {e}")
    
    def _recover_component(self, name: str, component: ComponentInfo):
        """恢復組件"""
        if component.recovery_attempts >= component.max_recovery_attempts:
            self.logger.error(f"❌ 組件 {name} 達到最大恢復嘗試次數，啟動備用方案")
            self._activate_fallback(name, component)
            return
        
        component.recovery_attempts += 1
        component.status = ComponentStatus.RECOVERING
        
        self.logger.info(f"🔄 嘗試恢復組件 {name} (第 {component.recovery_attempts} 次)")
        
        try:
            # 執行恢復操作
            success = component.recovery_callback()
            
            if success:
                self.logger.info(f"✅ 組件 {name} 恢復成功")
                component.status = ComponentStatus.HEALTHY
                component.failure_count = 0
                component.recovery_attempts = 0
            else:
                self.logger.warning(f"⚠️ 組件 {name} 恢復失敗，將重試")
                component.status = ComponentStatus.FAILED
                
                # 指數退避重試
                delay = min(2 ** component.recovery_attempts, 60)
                time.sleep(delay)
                self.recovery_queue.put(name)
                
        except Exception as e:
            self.logger.error(f"❌ 恢復組件 {name} 時發生錯誤: {e}")
            component.status = ComponentStatus.FAILED
            
            # 重新加入恢復隊列
            delay = min(2 ** component.recovery_attempts, 60)
            time.sleep(delay)
            self.recovery_queue.put(name)
    
    def _activate_fallback(self, name: str, component: ComponentInfo):
        """激活備用方案"""
        if component.fallback_callback:
            try:
                self.logger.info(f"🔄 激活組件 {name} 的備用方案")
                success = component.fallback_callback()
                
                if success:
                    self.logger.info(f"✅ 組件 {name} 備用方案激活成功")
                    component.status = ComponentStatus.DEGRADED
                else:
                    self.logger.error(f"❌ 組件 {name} 備用方案激活失敗")
                    component.status = ComponentStatus.OFFLINE
                    
            except Exception as e:
                self.logger.error(f"❌ 激活組件 {name} 備用方案時發生錯誤: {e}")
                component.status = ComponentStatus.OFFLINE
        else:
            self.logger.error(f"❌ 組件 {name} 沒有備用方案，進入離線狀態")
            component.status = ComponentStatus.OFFLINE
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """獲取恢復統計"""
        stats = {
            'total_components': len(self.components),
            'healthy_components': 0,
            'degraded_components': 0,
            'failed_components': 0,
            'recovering_components': 0,
            'offline_components': 0,
            'components': {}
        }
        
        for name, component in self.components.items():
            status = component.status.value
            stats[f'{status}_components'] += 1
            
            stats['components'][name] = {
                'status': status,
                'failure_count': component.failure_count,
                'recovery_attempts': component.recovery_attempts,
                'last_check': component.last_check.isoformat()
            }
        
        return stats

class AutoReconnector:
    """自動重連器"""
    
    def __init__(self, max_attempts: int = 5, base_delay: float = 1.0):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    async def reconnect_with_backoff(
        self,
        connect_func: Callable,
        disconnect_func: Optional[Callable] = None,
        health_check_func: Optional[Callable] = None
    ) -> bool:
        """使用指數退避進行重連"""
        for attempt in range(1, self.max_attempts + 1):
            try:
                self.logger.info(f"🔄 重連嘗試 {attempt}/{self.max_attempts}")
                
                # 先斷開連接（如果提供了斷開函數）
                if disconnect_func:
                    try:
                        await disconnect_func()
                    except Exception as e:
                        self.logger.warning(f"⚠️ 斷開連接時發生錯誤: {e}")
                
                # 嘗試重新連接
                await connect_func()
                
                # 健康檢查（如果提供了檢查函數）
                if health_check_func:
                    if not await health_check_func():
                        raise Exception("健康檢查失敗")
                
                self.logger.info(f"✅ 重連成功")
                return True
                
            except Exception as e:
                self.logger.warning(f"⚠️ 重連嘗試 {attempt} 失敗: {e}")
                
                if attempt < self.max_attempts:
                    delay = self.base_delay * (2 ** (attempt - 1))
                    self.logger.info(f"⏳ 等待 {delay:.1f} 秒後重試...")
                    await asyncio.sleep(delay)
        
        self.logger.error(f"❌ 重連失敗，已達到最大嘗試次數")
        return False

def create_recovery_manager() -> RecoveryManager:
    """創建恢復管理器實例"""
    return RecoveryManager()

def create_auto_reconnector(max_attempts: int = 5, base_delay: float = 1.0) -> AutoReconnector:
    """創建自動重連器實例"""
    return AutoReconnector(max_attempts, base_delay)

if __name__ == "__main__":
    # 測試恢復管理器
    logging.basicConfig(level=logging.INFO)
    
    recovery_manager = create_recovery_manager()
    
    # 模擬組件
    def mock_health_check():
        import random
        return random.random() > 0.3  # 70% 健康率
    
    def mock_recovery():
        import random
        return random.random() > 0.5  # 50% 恢復成功率
    
    def mock_fallback():
        return True
    
    # 註冊組件
    recovery_manager.register_component(
        "test_component",
        mock_health_check,
        mock_recovery,
        mock_fallback
    )
    
    recovery_manager.start()
    
    try:
        time.sleep(30)  # 運行30秒
        
        # 輸出統計
        stats = recovery_manager.get_recovery_statistics()
        print(f"恢復統計: {stats}")
        
    finally:
        recovery_manager.stop()