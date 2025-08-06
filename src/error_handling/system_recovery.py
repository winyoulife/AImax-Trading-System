#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 系統自動恢復模塊 - 任務9實現
實現系統異常的自動檢測、診斷和恢復功能
"""

import sys
import os
import time
import json
import logging
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import shutil

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.error_handling.error_handler import error_handler
from src.error_handling.network_handler import network_handler

logger = logging.getLogger(__name__)

class SystemHealth(Enum):
    """系統健康狀態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    RECOVERING = "recovering"
    FAILED = "failed"

class RecoveryAction(Enum):
    """恢復動作類型"""
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RESET_CONNECTION = "reset_connection"
    CLEANUP_FILES = "cleanup_files"
    RESTORE_BACKUP = "restore_backup"
    EMERGENCY_STOP = "emergency_stop"

@dataclass
class HealthCheck:
    """健康檢查項目"""
    name: str
    description: str
    check_function: Callable
    threshold_warning: float
    threshold_critical: float
    recovery_actions: List[RecoveryAction] = field(default_factory=list)
    enabled: bool = True
    last_check: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None

@dataclass
class RecoveryPlan:
    """恢復計劃"""
    plan_id: str
    trigger_condition: str
    actions: List[Dict[str, Any]]
    priority: int = 1
    max_attempts: int = 3
    cooldown_minutes: int = 5
    enabled: bool = True

class SystemRecoveryManager:
    """系統恢復管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.health_checks: Dict[str, HealthCheck] = {}
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        
        # 監控配置
        self.monitoring_config = {
            'check_interval': 30,  # 30秒檢查一次
            'auto_recovery': True,
            'max_recovery_attempts': 3,
            'recovery_cooldown': 300,  # 5分鐘冷卻期
            'alert_threshold': 2  # 連續2次異常才觸發恢復
        }
        
        # 系統狀態
        self.system_status = {
            'overall_health': SystemHealth.HEALTHY,
            'last_check_time': datetime.now(),
            'consecutive_failures': 0,
            'recovery_in_progress': False,
            'last_recovery_time': None
        }
        
        # 監控線程
        self.monitoring_thread = None
        self.monitoring_active = False
        
        self.setup_default_health_checks()
        self.setup_default_recovery_plans()
    
    def setup_default_health_checks(self):
        """設置默認健康檢查"""
        # CPU使用率檢查
        self.register_health_check(
            name="cpu_usage",
            description="CPU使用率檢查",
            check_function=self._check_cpu_usage,
            threshold_warning=80.0,
            threshold_critical=95.0,
            recovery_actions=[RecoveryAction.CLEANUP_FILES]
        )
        
        # 記憶體使用率檢查
        self.register_health_check(
            name="memory_usage",
            description="記憶體使用率檢查",
            check_function=self._check_memory_usage,
            threshold_warning=85.0,
            threshold_critical=95.0,
            recovery_actions=[RecoveryAction.CLEAR_CACHE, RecoveryAction.CLEANUP_FILES]
        )
        
        # 磁碟空間檢查
        self.register_health_check(
            name="disk_space",
            description="磁碟空間檢查",
            check_function=self._check_disk_space,
            threshold_warning=85.0,
            threshold_critical=95.0,
            recovery_actions=[RecoveryAction.CLEANUP_FILES]
        )
        
        # 網路連接檢查
        self.register_health_check(
            name="network_connectivity",
            description="網路連接檢查",
            check_function=self._check_network_connectivity,
            threshold_warning=70.0,
            threshold_critical=50.0,
            recovery_actions=[RecoveryAction.RESET_CONNECTION]
        )
        
        # 進程健康檢查
        self.register_health_check(
            name="process_health",
            description="關鍵進程健康檢查",
            check_function=self._check_process_health,
            threshold_warning=80.0,
            threshold_critical=60.0,
            recovery_actions=[RecoveryAction.RESTART_SERVICE]
        )
        
        # 文件系統檢查
        self.register_health_check(
            name="filesystem_health",
            description="文件系統健康檢查",
            check_function=self._check_filesystem_health,
            threshold_warning=90.0,
            threshold_critical=95.0,
            recovery_actions=[RecoveryAction.CLEANUP_FILES]
        )
    
    def setup_default_recovery_plans(self):
        """設置默認恢復計劃"""
        # 高CPU使用率恢復計劃
        self.register_recovery_plan(
            plan_id="high_cpu_recovery",
            trigger_condition="cpu_usage > 90",
            actions=[
                {"action": "cleanup_temp_files", "priority": 1},
                {"action": "restart_non_critical_services", "priority": 2},
                {"action": "alert_administrators", "priority": 3}
            ],
            priority=1
        )
        
        # 記憶體不足恢復計劃
        self.register_recovery_plan(
            plan_id="memory_shortage_recovery",
            trigger_condition="memory_usage > 90",
            actions=[
                {"action": "clear_application_cache", "priority": 1},
                {"action": "garbage_collection", "priority": 2},
                {"action": "restart_memory_intensive_services", "priority": 3}
            ],
            priority=1
        )
        
        # 網路連接問題恢復計劃
        self.register_recovery_plan(
            plan_id="network_issue_recovery",
            trigger_condition="network_connectivity < 60",
            actions=[
                {"action": "reset_network_connections", "priority": 1},
                {"action": "restart_network_services", "priority": 2},
                {"action": "switch_to_backup_endpoints", "priority": 3}
            ],
            priority=2
        )
        
        # 磁碟空間不足恢復計劃
        self.register_recovery_plan(
            plan_id="disk_space_recovery",
            trigger_condition="disk_space > 90",
            actions=[
                {"action": "cleanup_log_files", "priority": 1},
                {"action": "cleanup_temp_files", "priority": 2},
                {"action": "compress_old_data", "priority": 3}
            ],
            priority=2
        )
    
    def register_health_check(self, name: str, description: str, check_function: Callable,
                            threshold_warning: float, threshold_critical: float,
                            recovery_actions: List[RecoveryAction] = None):
        """註冊健康檢查"""
        health_check = HealthCheck(
            name=name,
            description=description,
            check_function=check_function,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            recovery_actions=recovery_actions or []
        )
        
        self.health_checks[name] = health_check
        logger.info(f"📋 註冊健康檢查: {name}")
    
    def register_recovery_plan(self, plan_id: str, trigger_condition: str,
                             actions: List[Dict[str, Any]], priority: int = 1):
        """註冊恢復計劃"""
        recovery_plan = RecoveryPlan(
            plan_id=plan_id,
            trigger_condition=trigger_condition,
            actions=actions,
            priority=priority
        )
        
        self.recovery_plans[plan_id] = recovery_plan
        logger.info(f"🔧 註冊恢復計劃: {plan_id}")
    
    def start_monitoring(self):
        """開始系統監控"""
        if self.monitoring_active:
            logger.warning("⚠️ 系統監控已在運行")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"🔍 系統監控已啟動，檢查間隔: {self.monitoring_config['check_interval']}秒")
    
    def stop_monitoring(self):
        """停止系統監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("🛑 系統監控已停止")
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.monitoring_active:
            try:
                # 執行所有健康檢查
                health_results = self.run_health_checks()
                
                # 評估系統整體健康狀態
                overall_health = self._evaluate_overall_health(health_results)
                self.system_status['overall_health'] = overall_health
                self.system_status['last_check_time'] = datetime.now()
                
                # 檢查是否需要恢復
                if overall_health in [SystemHealth.WARNING, SystemHealth.CRITICAL]:
                    self.system_status['consecutive_failures'] += 1
                    
                    if (self.system_status['consecutive_failures'] >= self.monitoring_config['alert_threshold'] and
                        self.monitoring_config['auto_recovery'] and
                        not self.system_status['recovery_in_progress']):
                        
                        # 觸發自動恢復
                        self._trigger_auto_recovery(health_results)
                else:
                    self.system_status['consecutive_failures'] = 0
                
                time.sleep(self.monitoring_config['check_interval'])
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                time.sleep(self.monitoring_config['check_interval'])
    
    def run_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """運行所有健康檢查"""
        results = {}
        
        for name, health_check in self.health_checks.items():
            if not health_check.enabled:
                continue
            
            try:
                start_time = time.time()
                result = health_check.check_function()
                check_time = time.time() - start_time
                
                # 評估健康狀態
                value = result.get('value', 0)
                if value >= health_check.threshold_critical:
                    status = SystemHealth.CRITICAL
                elif value >= health_check.threshold_warning:
                    status = SystemHealth.WARNING
                else:
                    status = SystemHealth.HEALTHY
                
                health_check.last_check = datetime.now()
                health_check.last_result = {
                    'status': status,
                    'value': value,
                    'details': result,
                    'check_time': check_time
                }
                
                results[name] = health_check.last_result
                
            except Exception as e:
                logger.error(f"❌ 健康檢查失敗: {name} - {str(e)}")
                results[name] = {
                    'status': SystemHealth.FAILED,
                    'error': str(e),
                    'check_time': 0
                }
        
        return results
    
    def _evaluate_overall_health(self, health_results: Dict[str, Dict[str, Any]]) -> SystemHealth:
        """評估系統整體健康狀態"""
        if not health_results:
            return SystemHealth.HEALTHY
        
        critical_count = sum(1 for result in health_results.values() 
                           if result.get('status') == SystemHealth.CRITICAL)
        warning_count = sum(1 for result in health_results.values() 
                          if result.get('status') == SystemHealth.WARNING)
        failed_count = sum(1 for result in health_results.values() 
                         if result.get('status') == SystemHealth.FAILED)
        
        total_checks = len(health_results)
        
        # 如果有任何檢查失敗或超過50%的檢查處於危險狀態
        if failed_count > 0 or critical_count > total_checks * 0.5:
            return SystemHealth.CRITICAL
        
        # 如果有危險狀態或超過30%的檢查處於警告狀態
        if critical_count > 0 or warning_count > total_checks * 0.3:
            return SystemHealth.WARNING
        
        return SystemHealth.HEALTHY
    
    def _trigger_auto_recovery(self, health_results: Dict[str, Dict[str, Any]]):
        """觸發自動恢復"""
        logger.warning("🚨 觸發系統自動恢復")
        
        self.system_status['recovery_in_progress'] = True
        self.system_status['last_recovery_time'] = datetime.now()
        
        try:
            # 找到適用的恢復計劃
            applicable_plans = self._find_applicable_recovery_plans(health_results)
            
            if not applicable_plans:
                logger.warning("⚠️ 沒有找到適用的恢復計劃")
                return
            
            # 按優先級排序執行恢復計劃
            applicable_plans.sort(key=lambda x: x.priority)
            
            for plan in applicable_plans:
                logger.info(f"🔧 執行恢復計劃: {plan.plan_id}")
                self._execute_recovery_plan(plan)
            
            # 等待一段時間後重新檢查
            time.sleep(30)
            
            # 重新檢查系統健康狀態
            new_health_results = self.run_health_checks()
            new_overall_health = self._evaluate_overall_health(new_health_results)
            
            if new_overall_health == SystemHealth.HEALTHY:
                logger.info("✅ 系統恢復成功")
                self.system_status['consecutive_failures'] = 0
            else:
                logger.warning("⚠️ 系統恢復後仍有問題")
        
        except Exception as e:
            logger.error(f"❌ 自動恢復過程中發生錯誤: {e}")
        
        finally:
            self.system_status['recovery_in_progress'] = False
    
    def _find_applicable_recovery_plans(self, health_results: Dict[str, Dict[str, Any]]) -> List[RecoveryPlan]:
        """找到適用的恢復計劃"""
        applicable_plans = []
        
        for plan_id, plan in self.recovery_plans.items():
            if not plan.enabled:
                continue
            
            # 簡單的條件匹配（實際應用中可以更複雜）
            if self._evaluate_trigger_condition(plan.trigger_condition, health_results):
                applicable_plans.append(plan)
        
        return applicable_plans
    
    def _evaluate_trigger_condition(self, condition: str, health_results: Dict[str, Dict[str, Any]]) -> bool:
        """評估觸發條件"""
        # 簡化的條件評估邏輯
        try:
            for check_name, result in health_results.items():
                if check_name in condition:
                    value = result.get('value', 0)
                    
                    # 解析條件（例如: "cpu_usage > 90"）
                    if '>' in condition:
                        threshold = float(condition.split('>')[-1].strip())
                        return value > threshold
                    elif '<' in condition:
                        threshold = float(condition.split('<')[-1].strip())
                        return value < threshold
            
            return False
        
        except Exception as e:
            logger.error(f"❌ 條件評估錯誤: {condition} - {e}")
            return False
    
    def _execute_recovery_plan(self, plan: RecoveryPlan):
        """執行恢復計劃"""
        recovery_record = {
            'plan_id': plan.plan_id,
            'start_time': datetime.now(),
            'actions_executed': [],
            'success': False
        }
        
        try:
            # 按優先級排序執行動作
            sorted_actions = sorted(plan.actions, key=lambda x: x.get('priority', 999))
            
            for action_config in sorted_actions:
                action_name = action_config.get('action')
                
                logger.info(f"⚡ 執行恢復動作: {action_name}")
                
                action_result = self._execute_recovery_action(action_name, action_config)
                
                recovery_record['actions_executed'].append({
                    'action': action_name,
                    'result': action_result,
                    'timestamp': datetime.now()
                })
                
                if not action_result.get('success', False):
                    logger.warning(f"⚠️ 恢復動作失敗: {action_name}")
            
            recovery_record['success'] = True
            recovery_record['end_time'] = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 恢復計劃執行失敗: {plan.plan_id} - {e}")
            recovery_record['error'] = str(e)
            recovery_record['end_time'] = datetime.now()
        
        self.recovery_history.append(recovery_record)
    
    def _execute_recovery_action(self, action_name: str, action_config: Dict[str, Any]) -> Dict[str, Any]:
        """執行單個恢復動作"""
        try:
            if action_name == "cleanup_temp_files":
                return self._cleanup_temp_files()
            elif action_name == "clear_application_cache":
                return self._clear_application_cache()
            elif action_name == "restart_network_services":
                return self._restart_network_services()
            elif action_name == "cleanup_log_files":
                return self._cleanup_log_files()
            elif action_name == "garbage_collection":
                return self._force_garbage_collection()
            else:
                logger.warning(f"⚠️ 未知的恢復動作: {action_name}")
                return {'success': False, 'reason': 'Unknown action'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # 健康檢查函數
    def _check_cpu_usage(self) -> Dict[str, Any]:
        """檢查CPU使用率"""
        cpu_percent = psutil.cpu_percent(interval=1)
        return {
            'value': cpu_percent,
            'unit': '%',
            'details': {
                'per_cpu': psutil.cpu_percent(percpu=True),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        }
    
    def _check_memory_usage(self) -> Dict[str, Any]:
        """檢查記憶體使用率"""
        memory = psutil.virtual_memory()
        return {
            'value': memory.percent,
            'unit': '%',
            'details': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'free': memory.free
            }
        }
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """檢查磁碟空間"""
        disk_usage = psutil.disk_usage('/')
        usage_percent = (disk_usage.used / disk_usage.total) * 100
        
        return {
            'value': usage_percent,
            'unit': '%',
            'details': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free
            }
        }
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """檢查網路連接"""
        connectivity_result = network_handler.check_internet_connectivity()
        
        success_rate = 0
        if connectivity_result['successful_checks'] + connectivity_result['failed_checks'] > 0:
            success_rate = (connectivity_result['successful_checks'] / 
                          (connectivity_result['successful_checks'] + connectivity_result['failed_checks'])) * 100
        
        return {
            'value': success_rate,
            'unit': '%',
            'details': connectivity_result
        }
    
    def _check_process_health(self) -> Dict[str, Any]:
        """檢查進程健康狀態"""
        # 檢查Python進程的健康狀態
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower():
                    python_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 計算健康分數（簡化邏輯）
        health_score = 100
        if len(python_processes) == 0:
            health_score = 0
        elif len(python_processes) > 10:  # 太多進程可能有問題
            health_score = 70
        
        return {
            'value': health_score,
            'unit': 'score',
            'details': {
                'python_processes_count': len(python_processes),
                'processes': python_processes[:5]  # 只返回前5個
            }
        }
    
    def _check_filesystem_health(self) -> Dict[str, Any]:
        """檢查文件系統健康狀態"""
        try:
            # 檢查項目目錄的可寫性
            test_file = self.project_root / "temp" / "health_check.tmp"
            test_file.parent.mkdir(exist_ok=True)
            
            # 寫入測試
            test_file.write_text("health check")
            content = test_file.read_text()
            test_file.unlink()
            
            health_score = 100 if content == "health check" else 50
            
            return {
                'value': health_score,
                'unit': 'score',
                'details': {
                    'writable': True,
                    'readable': True
                }
            }
        
        except Exception as e:
            return {
                'value': 0,
                'unit': 'score',
                'details': {
                    'error': str(e),
                    'writable': False,
                    'readable': False
                }
            }
    
    # 恢復動作函數
    def _cleanup_temp_files(self) -> Dict[str, Any]:
        """清理臨時文件"""
        try:
            temp_dir = self.project_root / "temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                temp_dir.mkdir()
            
            return {'success': True, 'action': 'temp_files_cleaned'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _clear_application_cache(self) -> Dict[str, Any]:
        """清理應用程式緩存"""
        try:
            cache_dirs = [
                self.project_root / "data" / "cache",
                self.project_root / "__pycache__"
            ]
            
            cleaned_dirs = 0
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    cleaned_dirs += 1
            
            return {'success': True, 'cleaned_directories': cleaned_dirs}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _restart_network_services(self) -> Dict[str, Any]:
        """重啟網路服務"""
        # 這裡只是模擬，實際應用中可能需要重啟特定服務
        logger.info("🔄 模擬重啟網路服務")
        return {'success': True, 'action': 'network_services_restarted'}
    
    def _cleanup_log_files(self) -> Dict[str, Any]:
        """清理日誌文件"""
        try:
            logs_dir = self.project_root / "logs"
            if not logs_dir.exists():
                return {'success': True, 'message': 'No logs directory found'}
            
            # 刪除7天前的日誌文件
            cutoff_date = datetime.now() - timedelta(days=7)
            cleaned_files = 0
            
            for log_file in logs_dir.rglob("*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    cleaned_files += 1
            
            return {'success': True, 'cleaned_files': cleaned_files}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _force_garbage_collection(self) -> Dict[str, Any]:
        """強制垃圾回收"""
        try:
            import gc
            collected = gc.collect()
            return {'success': True, 'objects_collected': collected}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'overall_health': self.system_status['overall_health'].value,
            'last_check_time': self.system_status['last_check_time'].isoformat(),
            'consecutive_failures': self.system_status['consecutive_failures'],
            'recovery_in_progress': self.system_status['recovery_in_progress'],
            'last_recovery_time': (self.system_status['last_recovery_time'].isoformat() 
                                 if self.system_status['last_recovery_time'] else None),
            'monitoring_active': self.monitoring_active,
            'health_checks_count': len(self.health_checks),
            'recovery_plans_count': len(self.recovery_plans)
        }
    
    def get_recovery_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取恢復歷史"""
        return self.recovery_history[-limit:]

# 全局系統恢復管理器實例
system_recovery_manager = SystemRecoveryManager()

# 便捷函數
def start_system_monitoring():
    """啟動系統監控"""
    system_recovery_manager.start_monitoring()

def stop_system_monitoring():
    """停止系統監控"""
    system_recovery_manager.stop_monitoring()

def get_system_health() -> Dict[str, Any]:
    """獲取系統健康狀態"""
    return system_recovery_manager.get_system_status()