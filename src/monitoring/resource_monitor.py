#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 資源使用監控和優化系統 - 任務10實現
監控GitHub Actions使用量、存儲空間、性能指標並提供優化建議
"""

import sys
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import threading
import psutil
import shutil

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class ResourceUsage:
    """資源使用數據結構"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_gb: float
    disk_free_gb: float
    network_io_mb: float
    process_count: int
    file_count: int
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GitHubActionsUsage:
    """GitHub Actions使用量數據結構"""
    total_minutes_used: int
    total_minutes_quota: int
    usage_percentage: float
    remaining_minutes: int
    billing_cycle_start: datetime
    billing_cycle_end: datetime
    workflow_runs_count: int
    storage_usage_mb: float

class ResourceMonitor:
    """資源監控器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.monitoring_data: List[ResourceUsage] = []
        self.github_usage_data: List[GitHubActionsUsage] = []
        
        # 監控配置
        self.config = {
            'monitoring_interval': 60,  # 60秒監控間隔
            'data_retention_days': 30,  # 保留30天數據
            'alert_thresholds': {
                'cpu_warning': 80.0,
                'cpu_critical': 95.0,
                'memory_warning': 85.0,
                'memory_critical': 95.0,
                'disk_warning': 85.0,
                'disk_critical': 95.0,
                'github_actions_warning': 80.0,
                'github_actions_critical': 95.0
            },
            'cleanup_thresholds': {
                'log_files_days': 7,
                'temp_files_days': 1,
                'cache_files_days': 3,
                'report_files_days': 30
            }
        }
        
        # GitHub API配置
        self.github_config = {
            'api_base': 'https://api.github.com',
            'owner': None,  # 將從環境變量或配置中獲取
            'repo': None,
            'token': None
        }
        
        # 監控狀態
        self.monitoring_active = False
        self.monitoring_thread = None
        
        self.setup_github_config()
    
    def setup_github_config(self):
        """設置GitHub配置"""
        # 嘗試從環境變量獲取配置
        self.github_config['token'] = os.environ.get('GITHUB_TOKEN')
        self.github_config['owner'] = os.environ.get('GITHUB_REPOSITORY_OWNER')
        
        # 嘗試從git配置獲取倉庫信息
        try:
            import subprocess
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                if 'github.com' in remote_url:
                    # 解析GitHub倉庫信息
                    if remote_url.endswith('.git'):
                        remote_url = remote_url[:-4]
                    
                    parts = remote_url.split('/')
                    if len(parts) >= 2:
                        self.github_config['owner'] = parts[-2]
                        self.github_config['repo'] = parts[-1]
        except Exception as e:
            logger.warning(f"無法獲取Git倉庫信息: {e}")
    
    def start_monitoring(self):
        """開始資源監控"""
        if self.monitoring_active:
            logger.warning("⚠️ 資源監控已在運行")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"📊 資源監控已啟動，監控間隔: {self.config['monitoring_interval']}秒")
    
    def stop_monitoring(self):
        """停止資源監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("🛑 資源監控已停止")
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.monitoring_active:
            try:
                # 收集系統資源使用情況
                resource_usage = self._collect_system_resources()
                self.monitoring_data.append(resource_usage)
                
                # 收集GitHub Actions使用情況
                if self._can_access_github_api():
                    github_usage = self._collect_github_actions_usage()
                    if github_usage:
                        self.github_usage_data.append(github_usage)
                
                # 檢查警告閾值
                self._check_alert_thresholds(resource_usage)
                
                # 清理舊數據
                self._cleanup_old_data()
                
                # 自動優化
                self._auto_optimize_resources()
                
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                time.sleep(self.config['monitoring_interval'])
    
    def _collect_system_resources(self) -> ResourceUsage:
        """收集系統資源使用情況"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁碟使用情況
            disk_usage = psutil.disk_usage(str(self.project_root))
            disk_usage_gb = (disk_usage.total - disk_usage.free) / (1024**3)
            disk_free_gb = disk_usage.free / (1024**3)
            
            # 網路IO
            network_io = psutil.net_io_counters()
            network_io_mb = (network_io.bytes_sent + network_io.bytes_recv) / (1024**2)
            
            # 進程數量
            process_count = len(psutil.pids())
            
            # 文件數量（項目目錄）
            file_count = sum(1 for _ in self.project_root.rglob('*') if _.is_file())
            
            # 詳細信息
            details = {
                'memory_total_gb': memory.total / (1024**3),
                'memory_available_gb': memory.available / (1024**3),
                'disk_total_gb': disk_usage.total / (1024**3),
                'cpu_count': psutil.cpu_count(),
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'project_size_mb': self._get_directory_size(self.project_root) / (1024**2)
            }
            
            return ResourceUsage(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_gb=disk_usage_gb,
                disk_free_gb=disk_free_gb,
                network_io_mb=network_io_mb,
                process_count=process_count,
                file_count=file_count,
                details=details
            )
            
        except Exception as e:
            logger.error(f"❌ 收集系統資源失敗: {e}")
            return ResourceUsage(
                timestamp=datetime.now(),
                cpu_percent=0, memory_percent=0, disk_usage_gb=0,
                disk_free_gb=0, network_io_mb=0, process_count=0, file_count=0
            )
    
    def _get_directory_size(self, directory: Path) -> int:
        """獲取目錄大小（字節）"""
        try:
            total_size = 0
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
            return total_size
        except Exception as e:
            logger.error(f"❌ 計算目錄大小失敗: {e}")
            return 0
    
    def _can_access_github_api(self) -> bool:
        """檢查是否可以訪問GitHub API"""
        return (self.github_config['token'] and 
                self.github_config['owner'] and 
                self.github_config['repo'])
    
    def _collect_github_actions_usage(self) -> Optional[GitHubActionsUsage]:
        """收集GitHub Actions使用情況"""
        try:
            headers = {
                'Authorization': f"token {self.github_config['token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 獲取Actions使用量
            billing_url = f"{self.github_config['api_base']}/repos/{self.github_config['owner']}/{self.github_config['repo']}/actions/billing"
            
            response = requests.get(billing_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                billing_data = response.json()
                
                # 獲取工作流運行統計
                runs_url = f"{self.github_config['api_base']}/repos/{self.github_config['owner']}/{self.github_config['repo']}/actions/runs"
                runs_response = requests.get(runs_url, headers=headers, timeout=30)
                
                workflow_runs_count = 0
                if runs_response.status_code == 200:
                    runs_data = runs_response.json()
                    workflow_runs_count = runs_data.get('total_count', 0)
                
                # 計算使用百分比
                total_minutes = billing_data.get('total_minutes_used', 0)
                included_minutes = billing_data.get('included_minutes', 2000)  # GitHub免費額度
                
                usage_percentage = (total_minutes / included_minutes * 100) if included_minutes > 0 else 0
                remaining_minutes = max(0, included_minutes - total_minutes)
                
                return GitHubActionsUsage(
                    total_minutes_used=total_minutes,
                    total_minutes_quota=included_minutes,
                    usage_percentage=usage_percentage,
                    remaining_minutes=remaining_minutes,
                    billing_cycle_start=datetime.now().replace(day=1),
                    billing_cycle_end=datetime.now().replace(day=1) + timedelta(days=32),
                    workflow_runs_count=workflow_runs_count,
                    storage_usage_mb=billing_data.get('total_paid_minutes_used', 0)
                )
            
            else:
                logger.warning(f"⚠️ GitHub API請求失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 收集GitHub Actions使用量失敗: {e}")
            return None
    
    def _check_alert_thresholds(self, resource_usage: ResourceUsage):
        """檢查警告閾值"""
        alerts = []
        thresholds = self.config['alert_thresholds']
        
        # CPU警告
        if resource_usage.cpu_percent >= thresholds['cpu_critical']:
            alerts.append(f"🚨 CPU使用率危險: {resource_usage.cpu_percent:.1f}%")
        elif resource_usage.cpu_percent >= thresholds['cpu_warning']:
            alerts.append(f"⚠️ CPU使用率警告: {resource_usage.cpu_percent:.1f}%")
        
        # 記憶體警告
        if resource_usage.memory_percent >= thresholds['memory_critical']:
            alerts.append(f"🚨 記憶體使用率危險: {resource_usage.memory_percent:.1f}%")
        elif resource_usage.memory_percent >= thresholds['memory_warning']:
            alerts.append(f"⚠️ 記憶體使用率警告: {resource_usage.memory_percent:.1f}%")
        
        # 磁碟空間警告
        total_disk = resource_usage.disk_usage_gb + resource_usage.disk_free_gb
        disk_usage_percent = (resource_usage.disk_usage_gb / total_disk * 100) if total_disk > 0 else 0
        
        if disk_usage_percent >= thresholds['disk_critical']:
            alerts.append(f"🚨 磁碟使用率危險: {disk_usage_percent:.1f}%")
        elif disk_usage_percent >= thresholds['disk_warning']:
            alerts.append(f"⚠️ 磁碟使用率警告: {disk_usage_percent:.1f}%")
        
        # GitHub Actions使用量警告
        if self.github_usage_data:
            latest_github_usage = self.github_usage_data[-1]
            if latest_github_usage.usage_percentage >= thresholds['github_actions_critical']:
                alerts.append(f"🚨 GitHub Actions使用量危險: {latest_github_usage.usage_percentage:.1f}%")
            elif latest_github_usage.usage_percentage >= thresholds['github_actions_warning']:
                alerts.append(f"⚠️ GitHub Actions使用量警告: {latest_github_usage.usage_percentage:.1f}%")
        
        # 記錄警告
        for alert in alerts:
            logger.warning(alert)
    
    def _cleanup_old_data(self):
        """清理舊數據"""
        cutoff_date = datetime.now() - timedelta(days=self.config['data_retention_days'])
        
        # 清理監控數據
        self.monitoring_data = [
            data for data in self.monitoring_data 
            if data.timestamp > cutoff_date
        ]
        
        # 清理GitHub使用數據
        self.github_usage_data = [
            data for data in self.github_usage_data 
            if data.billing_cycle_start > cutoff_date
        ]
    
    def _auto_optimize_resources(self):
        """自動資源優化"""
        try:
            if not self.monitoring_data:
                return
            
            latest_usage = self.monitoring_data[-1]
            
            # 如果記憶體使用率過高，觸發垃圾回收
            if latest_usage.memory_percent > 90:
                import gc
                collected = gc.collect()
                logger.info(f"🧹 自動垃圾回收: 清理了 {collected} 個對象")
            
            # 如果磁碟空間不足，清理臨時文件
            if latest_usage.disk_free_gb < 1.0:  # 少於1GB
                self.cleanup_temporary_files()
                logger.info("🧹 自動清理臨時文件")
            
        except Exception as e:
            logger.error(f"❌ 自動優化失敗: {e}")
    
    def cleanup_temporary_files(self) -> Dict[str, Any]:
        """清理臨時文件"""
        cleanup_result = {
            'cleaned_files': 0,
            'freed_space_mb': 0,
            'cleaned_directories': []
        }
        
        try:
            # 清理目標目錄
            cleanup_dirs = [
                self.project_root / "temp",
                self.project_root / "logs",
                self.project_root / "__pycache__",
                self.project_root / ".pytest_cache"
            ]
            
            for cleanup_dir in cleanup_dirs:
                if cleanup_dir.exists():
                    initial_size = self._get_directory_size(cleanup_dir)
                    
                    if cleanup_dir.name == "logs":
                        # 只清理舊日誌文件
                        self._cleanup_old_log_files(cleanup_dir)
                    elif cleanup_dir.name == "temp":
                        # 清理所有臨時文件
                        shutil.rmtree(cleanup_dir)
                        cleanup_dir.mkdir()
                    else:
                        # 清理緩存目錄
                        if cleanup_dir.exists():
                            shutil.rmtree(cleanup_dir)
                    
                    final_size = self._get_directory_size(cleanup_dir) if cleanup_dir.exists() else 0
                    freed_space = (initial_size - final_size) / (1024**2)
                    
                    if freed_space > 0:
                        cleanup_result['freed_space_mb'] += freed_space
                        cleanup_result['cleaned_directories'].append(str(cleanup_dir))
            
            logger.info(f"🧹 清理完成: 釋放 {cleanup_result['freed_space_mb']:.2f} MB 空間")
            
        except Exception as e:
            logger.error(f"❌ 清理臨時文件失敗: {e}")
        
        return cleanup_result
    
    def _cleanup_old_log_files(self, log_dir: Path):
        """清理舊日誌文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config['cleanup_thresholds']['log_files_days'])
            
            for log_file in log_dir.rglob("*.log"):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        log_file.unlink()
                        
        except Exception as e:
            logger.error(f"❌ 清理日誌文件失敗: {e}")
    
    def get_resource_statistics(self) -> Dict[str, Any]:
        """獲取資源統計"""
        if not self.monitoring_data:
            return {'error': 'No monitoring data available'}
        
        # 計算統計數據
        cpu_values = [data.cpu_percent for data in self.monitoring_data[-24:]]  # 最近24個數據點
        memory_values = [data.memory_percent for data in self.monitoring_data[-24:]]
        
        stats = {
            'current_usage': {
                'cpu_percent': self.monitoring_data[-1].cpu_percent,
                'memory_percent': self.monitoring_data[-1].memory_percent,
                'disk_usage_gb': self.monitoring_data[-1].disk_usage_gb,
                'disk_free_gb': self.monitoring_data[-1].disk_free_gb,
                'file_count': self.monitoring_data[-1].file_count
            },
            'averages_24h': {
                'cpu_percent': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'memory_percent': sum(memory_values) / len(memory_values) if memory_values else 0
            },
            'peaks_24h': {
                'cpu_percent': max(cpu_values) if cpu_values else 0,
                'memory_percent': max(memory_values) if memory_values else 0
            },
            'data_points': len(self.monitoring_data),
            'monitoring_duration_hours': (
                (self.monitoring_data[-1].timestamp - self.monitoring_data[0].timestamp).total_seconds() / 3600
                if len(self.monitoring_data) > 1 else 0
            )
        }
        
        # 添加GitHub Actions統計
        if self.github_usage_data:
            latest_github = self.github_usage_data[-1]
            stats['github_actions'] = {
                'usage_percentage': latest_github.usage_percentage,
                'minutes_used': latest_github.total_minutes_used,
                'minutes_remaining': latest_github.remaining_minutes,
                'workflow_runs': latest_github.workflow_runs_count
            }
        
        return stats
    
    def generate_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """生成優化建議"""
        recommendations = []
        
        if not self.monitoring_data:
            return recommendations
        
        latest_usage = self.monitoring_data[-1]
        stats = self.get_resource_statistics()
        
        # CPU優化建議
        if stats['averages_24h']['cpu_percent'] > 70:
            recommendations.append({
                'category': 'CPU',
                'priority': 'high',
                'issue': f"CPU平均使用率過高 ({stats['averages_24h']['cpu_percent']:.1f}%)",
                'recommendation': '考慮優化算法複雜度或減少並發處理',
                'actions': [
                    '檢查是否有死循環或低效算法',
                    '減少同時運行的GitHub Actions工作流',
                    '使用更高效的數據結構'
                ]
            })
        
        # 記憶體優化建議
        if stats['averages_24h']['memory_percent'] > 80:
            recommendations.append({
                'category': 'Memory',
                'priority': 'high',
                'issue': f"記憶體平均使用率過高 ({stats['averages_24h']['memory_percent']:.1f}%)",
                'recommendation': '優化記憶體使用，避免記憶體洩漏',
                'actions': [
                    '檢查是否有記憶體洩漏',
                    '優化數據緩存策略',
                    '及時釋放不需要的對象'
                ]
            })
        
        # 磁碟空間優化建議
        if latest_usage.disk_free_gb < 2.0:
            recommendations.append({
                'category': 'Disk',
                'priority': 'critical',
                'issue': f"磁碟空間不足 (剩餘 {latest_usage.disk_free_gb:.1f} GB)",
                'recommendation': '立即清理不必要的文件',
                'actions': [
                    '清理日誌文件',
                    '刪除臨時文件',
                    '壓縮或刪除舊的備份文件'
                ]
            })
        
        # GitHub Actions優化建議
        if self.github_usage_data:
            latest_github = self.github_usage_data[-1]
            if latest_github.usage_percentage > 80:
                recommendations.append({
                    'category': 'GitHub Actions',
                    'priority': 'high',
                    'issue': f"GitHub Actions使用量過高 ({latest_github.usage_percentage:.1f}%)",
                    'recommendation': '優化工作流執行頻率和效率',
                    'actions': [
                        '減少工作流觸發頻率',
                        '優化工作流執行時間',
                        '使用條件執行避免不必要的運行',
                        '考慮使用self-hosted runners'
                    ]
                })
        
        # 文件數量優化建議
        if latest_usage.file_count > 10000:
            recommendations.append({
                'category': 'Files',
                'priority': 'medium',
                'issue': f"項目文件數量過多 ({latest_usage.file_count} 個文件)",
                'recommendation': '清理不必要的文件，優化項目結構',
                'actions': [
                    '刪除未使用的文件',
                    '壓縮歷史數據',
                    '使用.gitignore排除不必要的文件'
                ]
            })
        
        return recommendations
    
    def generate_resource_report(self) -> str:
        """生成資源使用報告"""
        stats = self.get_resource_statistics()
        recommendations = self.generate_optimization_recommendations()
        
        report = f"""
📊 AImax 資源使用監控報告
{'='*60}

🖥️ 當前系統資源使用:
   CPU使用率: {stats['current_usage']['cpu_percent']:.1f}%
   記憶體使用率: {stats['current_usage']['memory_percent']:.1f}%
   磁碟使用: {stats['current_usage']['disk_usage_gb']:.2f} GB
   磁碟剩餘: {stats['current_usage']['disk_free_gb']:.2f} GB
   文件數量: {stats['current_usage']['file_count']:,}

📈 24小時平均使用率:
   CPU平均: {stats['averages_24h']['cpu_percent']:.1f}%
   記憶體平均: {stats['averages_24h']['memory_percent']:.1f}%

📊 24小時峰值使用率:
   CPU峰值: {stats['peaks_24h']['cpu_percent']:.1f}%
   記憶體峰值: {stats['peaks_24h']['memory_percent']:.1f}%

📋 監控統計:
   數據點數: {stats['data_points']}
   監控時長: {stats['monitoring_duration_hours']:.1f} 小時
"""
        
        # 添加GitHub Actions統計
        if 'github_actions' in stats:
            github_stats = stats['github_actions']
            report += f"""
🚀 GitHub Actions使用情況:
   使用率: {github_stats['usage_percentage']:.1f}%
   已用分鐘: {github_stats['minutes_used']}
   剩餘分鐘: {github_stats['minutes_remaining']}
   工作流運行次數: {github_stats['workflow_runs']}
"""
        
        # 添加優化建議
        if recommendations:
            report += f"\n💡 優化建議:\n"
            for i, rec in enumerate(recommendations, 1):
                priority_emoji = {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '💡',
                    'low': 'ℹ️'
                }.get(rec['priority'], '💡')
                
                report += f"\n{i}. {priority_emoji} {rec['category']} - {rec['priority'].upper()}\n"
                report += f"   問題: {rec['issue']}\n"
                report += f"   建議: {rec['recommendation']}\n"
                report += f"   行動:\n"
                for action in rec['actions']:
                    report += f"     • {action}\n"
        
        report += f"\n{'='*60}\n"
        report += f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def save_monitoring_data(self) -> Path:
        """保存監控數據到文件"""
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # 保存JSON格式的詳細數據
        data_file = reports_dir / f"resource_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        monitoring_data = {
            'timestamp': datetime.now().isoformat(),
            'system_resources': [
                {
                    'timestamp': data.timestamp.isoformat(),
                    'cpu_percent': data.cpu_percent,
                    'memory_percent': data.memory_percent,
                    'disk_usage_gb': data.disk_usage_gb,
                    'disk_free_gb': data.disk_free_gb,
                    'network_io_mb': data.network_io_mb,
                    'process_count': data.process_count,
                    'file_count': data.file_count,
                    'details': data.details
                }
                for data in self.monitoring_data
            ],
            'github_actions': [
                {
                    'total_minutes_used': data.total_minutes_used,
                    'usage_percentage': data.usage_percentage,
                    'remaining_minutes': data.remaining_minutes,
                    'workflow_runs_count': data.workflow_runs_count,
                    'billing_cycle_start': data.billing_cycle_start.isoformat(),
                    'billing_cycle_end': data.billing_cycle_end.isoformat()
                }
                for data in self.github_usage_data
            ],
            'statistics': self.get_resource_statistics(),
            'recommendations': self.generate_optimization_recommendations()
        }
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(monitoring_data, f, indent=2, ensure_ascii=False)
        
        # 保存文本格式的報告
        report_file = reports_dir / f"resource_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_resource_report())
        
        logger.info(f"📄 監控數據已保存: {data_file}")
        logger.info(f"📄 監控報告已保存: {report_file}")
        
        return data_file

# 全局資源監控器實例
resource_monitor = ResourceMonitor()

# 便捷函數
def start_resource_monitoring():
    """啟動資源監控"""
    resource_monitor.start_monitoring()

def stop_resource_monitoring():
    """停止資源監控"""
    resource_monitor.stop_monitoring()

def get_resource_stats() -> Dict[str, Any]:
    """獲取資源統計"""
    return resource_monitor.get_resource_statistics()

def cleanup_resources() -> Dict[str, Any]:
    """清理資源"""
    return resource_monitor.cleanup_temporary_files()

def get_optimization_recommendations() -> List[Dict[str, Any]]:
    """獲取優化建議"""
    return resource_monitor.generate_optimization_recommendations()