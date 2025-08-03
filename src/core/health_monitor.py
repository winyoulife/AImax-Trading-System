#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統健康監控器 - 提供系統健康檢查和自診斷功能
"""

import sys
import os
import logging
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import threading
from queue import Queue, Empty

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """健康狀態"""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MetricType(Enum):
    """指標類型"""
    SYSTEM = "system"
    APPLICATION = "application"
    NETWORK = "network"
    DATABASE = "database"
    AI_MODEL = "ai_model"
    TRADING = "trading"

@dataclass
class HealthMetric:
    """健康指標"""
    name: str
    type: MetricType
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime
    description: str

@dataclass
class SystemDiagnostic:
    """系統診斷結果"""
    component: str
    status: HealthStatus
    issues: List[str]
    recommendations: List[str]
    metrics: List[HealthMetric]
    timestamp: datetime

class HealthMonitor:
    """系統健康監控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metrics: Dict[str, HealthMetric] = {}
        self.diagnostics: List[SystemDiagnostic] = []
        self.monitoring_thread = None
        self.running = False
        self.check_interval = 30  # 檢查間隔（秒）
        self.max_history_size = 1000
        
        # 健康檢查回調
        self.health_checks: Dict[str, Callable] = {}
        
        # 初始化系統監控
        self._initialize_system_monitors()
        
        self.logger.info("🏥 系統健康監控器初始化完成")
    
    def _initialize_system_monitors(self):
        """初始化系統監控"""
        self.health_checks.update({
            'cpu_usage': self._check_cpu_usage,
            'memory_usage': self._check_memory_usage,
            'disk_usage': self._check_disk_usage,
            'network_connectivity': self._check_network_connectivity,
            'process_health': self._check_process_health,
            'database_health': self._check_database_health,
            'ai_model_health': self._check_ai_model_health,
            'trading_system_health': self._check_trading_system_health
        })
    
    def start(self):
        """啟動健康監控"""
        if not self.running:
            self.running = True
            self.monitoring_thread = threading.Thread(
                target=self._monitor_health,
                daemon=True
            )
            self.monitoring_thread.start()
            self.logger.info("🚀 系統健康監控已啟動")
    
    def stop(self):
        """停止健康監控"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("⏹️ 系統健康監控已停止")
    
    def _monitor_health(self):
        """監控系統健康"""
        while self.running:
            try:
                self._perform_health_checks()
                self._perform_system_diagnostics()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"❌ 健康監控時發生錯誤: {e}")
                time.sleep(5)
    
    def _perform_health_checks(self):
        """執行健康檢查"""
        for check_name, check_func in self.health_checks.items():
            try:
                metric = check_func()
                if metric:
                    self.metrics[check_name] = metric
            except Exception as e:
                self.logger.error(f"❌ 健康檢查 {check_name} 失敗: {e}")
    
    def _check_cpu_usage(self) -> HealthMetric:
        """檢查CPU使用率"""
        cpu_percent = psutil.cpu_percent(interval=1)
        
        if cpu_percent < 70:
            status = HealthStatus.EXCELLENT
        elif cpu_percent < 85:
            status = HealthStatus.GOOD
        elif cpu_percent < 95:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
        
        return HealthMetric(
            name="CPU使用率",
            type=MetricType.SYSTEM,
            value=cpu_percent,
            unit="%",
            status=status,
            threshold_warning=85.0,
            threshold_critical=95.0,
            timestamp=datetime.now(),
            description=f"當前CPU使用率為 {cpu_percent:.1f}%"
        )
    
    def _check_memory_usage(self) -> HealthMetric:
        """檢查內存使用率"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent < 70:
            status = HealthStatus.EXCELLENT
        elif memory_percent < 85:
            status = HealthStatus.GOOD
        elif memory_percent < 95:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
        
        return HealthMetric(
            name="內存使用率",
            type=MetricType.SYSTEM,
            value=memory_percent,
            unit="%",
            status=status,
            threshold_warning=85.0,
            threshold_critical=95.0,
            timestamp=datetime.now(),
            description=f"當前內存使用率為 {memory_percent:.1f}% ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)"
        )
    
    def _check_disk_usage(self) -> HealthMetric:
        """檢查磁盤使用率"""
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent < 70:
            status = HealthStatus.EXCELLENT
        elif disk_percent < 85:
            status = HealthStatus.GOOD
        elif disk_percent < 95:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL
        
        return HealthMetric(
            name="磁盤使用率",
            type=MetricType.SYSTEM,
            value=disk_percent,
            unit="%",
            status=status,
            threshold_warning=85.0,
            threshold_critical=95.0,
            timestamp=datetime.now(),
            description=f"當前磁盤使用率為 {disk_percent:.1f}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)"
        )
    
    def _check_network_connectivity(self) -> HealthMetric:
        """檢查網絡連接"""
        try:
            import requests
            response = requests.get("https://www.google.com", timeout=5)
            if response.status_code == 200:
                status = HealthStatus.EXCELLENT
                value = 100.0
                description = "網絡連接正常"
            else:
                status = HealthStatus.WARNING
                value = 50.0
                description = f"網絡連接異常，狀態碼: {response.status_code}"
        except Exception as e:
            status = HealthStatus.CRITICAL
            value = 0.0
            description = f"網絡連接失敗: {str(e)}"
        
        return HealthMetric(
            name="網絡連接",
            type=MetricType.NETWORK,
            value=value,
            unit="%",
            status=status,
            threshold_warning=50.0,
            threshold_critical=0.0,
            timestamp=datetime.now(),
            description=description
        )
    
    def _check_process_health(self) -> HealthMetric:
        """檢查進程健康"""
        try:
            current_process = psutil.Process()
            
            # 檢查進程狀態
            if current_process.status() == psutil.STATUS_RUNNING:
                status = HealthStatus.EXCELLENT
                value = 100.0
                description = "進程運行正常"
            else:
                status = HealthStatus.WARNING
                value = 50.0
                description = f"進程狀態異常: {current_process.status()}"
                
        except Exception as e:
            status = HealthStatus.CRITICAL
            value = 0.0
            description = f"進程檢查失敗: {str(e)}"
        
        return HealthMetric(
            name="進程健康",
            type=MetricType.APPLICATION,
            value=value,
            unit="%",
            status=status,
            threshold_warning=50.0,
            threshold_critical=0.0,
            timestamp=datetime.now(),
            description=description
        )
    
    def _check_database_health(self) -> HealthMetric:
        """檢查數據庫健康"""
        try:
            # 檢查數據庫文件是否存在
            db_files = [
                "data/kline_data.db",
                "data/market_history.db",
                "data/multi_pair_market.db"
            ]
            
            existing_files = 0
            for db_file in db_files:
                if Path(db_file).exists():
                    existing_files += 1
            
            health_percentage = (existing_files / len(db_files)) * 100
            
            if health_percentage == 100:
                status = HealthStatus.EXCELLENT
                description = "所有數據庫文件正常"
            elif health_percentage >= 66:
                status = HealthStatus.GOOD
                description = f"部分數據庫文件存在 ({existing_files}/{len(db_files)})"
            elif health_percentage >= 33:
                status = HealthStatus.WARNING
                description = f"多數數據庫文件缺失 ({existing_files}/{len(db_files)})"
            else:
                status = HealthStatus.CRITICAL
                description = f"數據庫文件嚴重缺失 ({existing_files}/{len(db_files)})"
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            health_percentage = 0.0
            description = f"數據庫檢查失敗: {str(e)}"
        
        return HealthMetric(
            name="數據庫健康",
            type=MetricType.DATABASE,
            value=health_percentage,
            unit="%",
            status=status,
            threshold_warning=66.0,
            threshold_critical=33.0,
            timestamp=datetime.now(),
            description=description
        )
    
    def _check_ai_model_health(self) -> HealthMetric:
        """檢查AI模型健康"""
        try:
            # 檢查Ollama服務
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_count = len(models)
                
                if model_count >= 5:
                    status = HealthStatus.EXCELLENT
                    description = f"AI模型服務正常，已加載 {model_count} 個模型"
                elif model_count >= 3:
                    status = HealthStatus.GOOD
                    description = f"AI模型服務正常，已加載 {model_count} 個模型"
                elif model_count >= 1:
                    status = HealthStatus.WARNING
                    description = f"AI模型服務正常，但模型數量較少 ({model_count} 個)"
                else:
                    status = HealthStatus.CRITICAL
                    description = "AI模型服務正常，但沒有可用模型"
                
                value = min(model_count * 20, 100)  # 每個模型20分
            else:
                status = HealthStatus.CRITICAL
                value = 0.0
                description = f"AI模型服務異常，狀態碼: {response.status_code}"
                
        except Exception as e:
            status = HealthStatus.CRITICAL
            value = 0.0
            description = f"AI模型服務檢查失敗: {str(e)}"
        
        return HealthMetric(
            name="AI模型健康",
            type=MetricType.AI_MODEL,
            value=value,
            unit="%",
            status=status,
            threshold_warning=60.0,
            threshold_critical=20.0,
            timestamp=datetime.now(),
            description=description
        )
    
    def _check_trading_system_health(self) -> HealthMetric:
        """檢查交易系統健康"""
        try:
            # 檢查關鍵組件文件
            critical_files = [
                "AImax/src/ai/enhanced_ai_manager.py",
                "AImax/src/trading/risk_manager.py",
                "AImax/src/data/max_client.py",
                "AImax/src/core/backtest_reporter.py"
            ]
            
            existing_files = 0
            for file_path in critical_files:
                if Path(file_path).exists():
                    existing_files += 1
            
            health_percentage = (existing_files / len(critical_files)) * 100
            
            if health_percentage == 100:
                status = HealthStatus.EXCELLENT
                description = "交易系統所有關鍵組件正常"
            elif health_percentage >= 75:
                status = HealthStatus.GOOD
                description = f"交易系統大部分組件正常 ({existing_files}/{len(critical_files)})"
            elif health_percentage >= 50:
                status = HealthStatus.WARNING
                description = f"交易系統部分組件缺失 ({existing_files}/{len(critical_files)})"
            else:
                status = HealthStatus.CRITICAL
                description = f"交易系統關鍵組件嚴重缺失 ({existing_files}/{len(critical_files)})"
            
        except Exception as e:
            status = HealthStatus.CRITICAL
            health_percentage = 0.0
            description = f"交易系統檢查失敗: {str(e)}"
        
        return HealthMetric(
            name="交易系統健康",
            type=MetricType.TRADING,
            value=health_percentage,
            unit="%",
            status=status,
            threshold_warning=75.0,
            threshold_critical=50.0,
            timestamp=datetime.now(),
            description=description
        )
    
    def _perform_system_diagnostics(self):
        """執行系統診斷"""
        try:
            # 收集所有指標
            all_metrics = list(self.metrics.values())
            
            # 按類型分組診斷
            system_metrics = [m for m in all_metrics if m.type == MetricType.SYSTEM]
            app_metrics = [m for m in all_metrics if m.type == MetricType.APPLICATION]
            network_metrics = [m for m in all_metrics if m.type == MetricType.NETWORK]
            db_metrics = [m for m in all_metrics if m.type == MetricType.DATABASE]
            ai_metrics = [m for m in all_metrics if m.type == MetricType.AI_MODEL]
            trading_metrics = [m for m in all_metrics if m.type == MetricType.TRADING]
            
            # 生成診斷報告
            diagnostics = [
                self._diagnose_component("系統資源", system_metrics),
                self._diagnose_component("應用程序", app_metrics),
                self._diagnose_component("網絡連接", network_metrics),
                self._diagnose_component("數據庫", db_metrics),
                self._diagnose_component("AI模型", ai_metrics),
                self._diagnose_component("交易系統", trading_metrics)
            ]
            
            # 更新診斷歷史
            self.diagnostics.extend(diagnostics)
            
            # 限制歷史大小
            if len(self.diagnostics) > self.max_history_size:
                self.diagnostics = self.diagnostics[-self.max_history_size:]
                
        except Exception as e:
            self.logger.error(f"❌ 系統診斷時發生錯誤: {e}")
    
    def _diagnose_component(self, component_name: str, metrics: List[HealthMetric]) -> SystemDiagnostic:
        """診斷組件"""
        if not metrics:
            return SystemDiagnostic(
                component=component_name,
                status=HealthStatus.UNKNOWN,
                issues=["沒有可用的監控指標"],
                recommendations=["檢查監控配置"],
                metrics=[],
                timestamp=datetime.now()
            )
        
        # 計算整體健康狀態
        critical_count = sum(1 for m in metrics if m.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for m in metrics if m.status == HealthStatus.WARNING)
        
        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_count > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.EXCELLENT
        
        # 收集問題和建議
        issues = []
        recommendations = []
        
        for metric in metrics:
            if metric.status == HealthStatus.CRITICAL:
                issues.append(f"{metric.name}: {metric.description}")
                recommendations.append(f"立即處理 {metric.name} 的關鍵問題")
            elif metric.status == HealthStatus.WARNING:
                issues.append(f"{metric.name}: {metric.description}")
                recommendations.append(f"關注 {metric.name} 的警告狀態")
        
        if not issues:
            issues.append("所有指標正常")
            recommendations.append("繼續保持良好狀態")
        
        return SystemDiagnostic(
            component=component_name,
            status=overall_status,
            issues=issues,
            recommendations=recommendations,
            metrics=metrics,
            timestamp=datetime.now()
        )
    
    def get_current_health_status(self) -> Dict[str, Any]:
        """獲取當前健康狀態"""
        if not self.metrics:
            return {
                'overall_status': HealthStatus.UNKNOWN.value,
                'score': 0,
                'metrics': {},
                'summary': "沒有可用的健康數據"
            }
        
        # 計算整體健康分數
        total_score = 0
        metric_count = 0
        
        status_scores = {
            HealthStatus.EXCELLENT: 100,
            HealthStatus.GOOD: 80,
            HealthStatus.WARNING: 60,
            HealthStatus.CRITICAL: 20,
            HealthStatus.UNKNOWN: 0
        }
        
        metrics_data = {}
        for name, metric in self.metrics.items():
            score = status_scores.get(metric.status, 0)
            total_score += score
            metric_count += 1
            
            metrics_data[name] = {
                'value': metric.value,
                'unit': metric.unit,
                'status': metric.status.value,
                'description': metric.description,
                'timestamp': metric.timestamp.isoformat()
            }
        
        overall_score = total_score / metric_count if metric_count > 0 else 0
        
        # 確定整體狀態
        if overall_score >= 90:
            overall_status = HealthStatus.EXCELLENT
            summary = "系統運行狀態優秀"
        elif overall_score >= 75:
            overall_status = HealthStatus.GOOD
            summary = "系統運行狀態良好"
        elif overall_score >= 50:
            overall_status = HealthStatus.WARNING
            summary = "系統存在一些警告，需要關注"
        else:
            overall_status = HealthStatus.CRITICAL
            summary = "系統存在嚴重問題，需要立即處理"
        
        return {
            'overall_status': overall_status.value,
            'score': round(overall_score, 1),
            'metrics': metrics_data,
            'summary': summary,
            'last_check': datetime.now().isoformat()
        }
    
    def get_diagnostics_report(self) -> Dict[str, Any]:
        """獲取診斷報告"""
        if not self.diagnostics:
            return {
                'components': {},
                'summary': "沒有可用的診斷數據",
                'timestamp': datetime.now().isoformat()
            }
        
        # 獲取最新診斷
        latest_diagnostics = {}
        for diagnostic in reversed(self.diagnostics):
            if diagnostic.component not in latest_diagnostics:
                latest_diagnostics[diagnostic.component] = diagnostic
        
        components_data = {}
        for component, diagnostic in latest_diagnostics.items():
            components_data[component] = {
                'status': diagnostic.status.value,
                'issues': diagnostic.issues,
                'recommendations': diagnostic.recommendations,
                'metrics_count': len(diagnostic.metrics),
                'timestamp': diagnostic.timestamp.isoformat()
            }
        
        # 生成摘要
        critical_components = [c for c, d in latest_diagnostics.items() if d.status == HealthStatus.CRITICAL]
        warning_components = [c for c, d in latest_diagnostics.items() if d.status == HealthStatus.WARNING]
        
        if critical_components:
            summary = f"發現 {len(critical_components)} 個關鍵問題組件: {', '.join(critical_components)}"
        elif warning_components:
            summary = f"發現 {len(warning_components)} 個警告組件: {', '.join(warning_components)}"
        else:
            summary = "所有組件運行正常"
        
        return {
            'components': components_data,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_health_report(self, filepath: str):
        """導出健康報告"""
        try:
            report_data = {
                'export_time': datetime.now().isoformat(),
                'health_status': self.get_current_health_status(),
                'diagnostics': self.get_diagnostics_report(),
                'metrics_history': []
            }
            
            # 添加指標歷史（最近100條）
            for metric in list(self.metrics.values())[-100:]:
                metric_data = asdict(metric)
                metric_data['timestamp'] = metric_data['timestamp'].isoformat()
                metric_data['type'] = metric_data['type'].value
                metric_data['status'] = metric_data['status'].value
                report_data['metrics_history'].append(metric_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 健康報告已導出到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ 導出健康報告失敗: {e}")
    
    def register_health_check(self, name: str, check_func: Callable):
        """註冊自定義健康檢查"""
        self.health_checks[name] = check_func
        self.logger.info(f"📝 已註冊健康檢查: {name}")
    
    def unregister_health_check(self, name: str):
        """取消註冊健康檢查"""
        if name in self.health_checks:
            del self.health_checks[name]
            self.logger.info(f"🗑️ 已取消註冊健康檢查: {name}")

def create_health_monitor() -> HealthMonitor:
    """創建健康監控器實例"""
    return HealthMonitor()

if __name__ == "__main__":
    # 測試健康監控器
    logging.basicConfig(level=logging.INFO)
    
    health_monitor = create_health_monitor()
    health_monitor.start()
    
    try:
        time.sleep(10)  # 運行10秒
        
        # 輸出健康狀態
        health_status = health_monitor.get_current_health_status()
        print(f"健康狀態: {health_status}")
        
        # 輸出診斷報告
        diagnostics = health_monitor.get_diagnostics_report()
        print(f"診斷報告: {diagnostics}")
        
    finally:
        health_monitor.stop()