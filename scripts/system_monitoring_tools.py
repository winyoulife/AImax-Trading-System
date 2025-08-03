#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統監控和維護工具 - 任務8.3實現
建立系統監控和維護工具
"""

import sys
import os
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging
from pathlib import Path
import sqlite3
from collections import deque, defaultdict

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    thread_count: int
    uptime: float

@dataclass
class Alert:
    """警報"""
    id: str
    type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None

class MetricsCollector:
    """指標收集器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "AImax/logs/system_metrics.db"
        self.setup_database()
        self.collecting = False
        self.collection_thread = None
        
    def setup_database(self):
        """設置數據庫"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        network_sent INTEGER,
                        network_recv INTEGER,
                        process_count INTEGER,
                        thread_count INTEGER,
                        uptime REAL
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        resolved INTEGER DEFAULT 0,
                        resolution_time TEXT
                    )
                """)
                
                conn.commit()
                
            logger.info(f"✅ 指標數據庫初始化完成: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ 數據庫設置失敗: {e}")
            raise
    
    def collect_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # CPU使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 內存使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁盤使用率
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # 網絡IO
            net_io = psutil.net_io_counters()
            network_io = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            }
            
            # 進程和線程數
            process_count = len(psutil.pids())
            
            # 當前進程的線程數
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            
            # 系統運行時間
            uptime = time.time() - psutil.boot_time()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                thread_count=thread_count,
                uptime=uptime
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ 指標收集失敗: {e}")
            raise
    
    def save_metrics(self, metrics: SystemMetrics):
        """保存指標到數據庫"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_metrics 
                    (timestamp, cpu_usage, memory_usage, disk_usage, 
                     network_sent, network_recv, process_count, thread_count, uptime)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.cpu_usage,
                    metrics.memory_usage,
                    metrics.disk_usage,
                    metrics.network_io['bytes_sent'],
                    metrics.network_io['bytes_recv'],
                    metrics.process_count,
                    metrics.thread_count,
                    metrics.uptime
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ 指標保存失敗: {e}")
    
    def start_collection(self, interval: int = 60):
        """開始指標收集"""
        if self.collecting:
            return
        
        self.collecting = True
        self.collection_thread = threading.Thread(
            target=self._collection_loop,
            args=(interval,),
            daemon=True
        )
        self.collection_thread.start()
        
        logger.info(f"📊 開始指標收集 (間隔: {interval}秒)")
    
    def stop_collection(self):
        """停止指標收集"""
        self.collecting = False
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        logger.info("⏹️ 停止指標收集")
    
    def _collection_loop(self, interval: int):
        """指標收集循環"""
        while self.collecting:
            try:
                metrics = self.collect_metrics()
                self.save_metrics(metrics)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 指標收集循環錯誤: {e}")
                time.sleep(interval)
    
    def get_recent_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """獲取最近的指標"""
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM system_metrics 
                    WHERE timestamp > ? 
                    ORDER BY timestamp DESC
                """, (since.isoformat(),))
                
                metrics = []
                for row in cursor.fetchall():
                    metrics.append(dict(row))
                
                return metrics
                
        except Exception as e:
            logger.error(f"❌ 獲取指標失敗: {e}")
            return []
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """獲取指標摘要"""
        try:
            metrics = self.get_recent_metrics(hours)
            
            if not metrics:
                return {}
            
            # 計算統計信息
            cpu_values = [m['cpu_usage'] for m in metrics if m['cpu_usage'] is not None]
            memory_values = [m['memory_usage'] for m in metrics if m['memory_usage'] is not None]
            disk_values = [m['disk_usage'] for m in metrics if m['disk_usage'] is not None]
            
            summary = {
                "time_range_hours": hours,
                "total_records": len(metrics),
                "cpu_stats": {
                    "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    "max": max(cpu_values) if cpu_values else 0,
                    "min": min(cpu_values) if cpu_values else 0
                },
                "memory_stats": {
                    "avg": sum(memory_values) / len(memory_values) if memory_values else 0,
                    "max": max(memory_values) if memory_values else 0,
                    "min": min(memory_values) if memory_values else 0
                },
                "disk_stats": {
                    "avg": sum(disk_values) / len(disk_values) if disk_values else 0,
                    "max": max(disk_values) if disk_values else 0,
                    "min": min(disk_values) if disk_values else 0
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ 指標摘要生成失敗: {e}")
            return {}

class AlertManager:
    """警報管理器"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "AImax/logs/system_metrics.db"
        self.alert_rules = []
        self.setup_alert_rules()
        
    def setup_alert_rules(self):
        """設置警報規則"""
        self.alert_rules = [
            {
                "name": "高CPU使用率",
                "condition": lambda metrics: metrics.cpu_usage > 80,
                "severity": "HIGH",
                "message": lambda metrics: f"CPU使用率過高: {metrics.cpu_usage:.1f}%"
            },
            {
                "name": "高內存使用率",
                "condition": lambda metrics: metrics.memory_usage > 85,
                "severity": "HIGH", 
                "message": lambda metrics: f"內存使用率過高: {metrics.memory_usage:.1f}%"
            },
            {
                "name": "磁盤空間不足",
                "condition": lambda metrics: metrics.disk_usage > 90,
                "severity": "CRITICAL",
                "message": lambda metrics: f"磁盤使用率過高: {metrics.disk_usage:.1f}%"
            },
            {
                "name": "進程數過多",
                "condition": lambda metrics: metrics.process_count > 500,
                "severity": "MEDIUM",
                "message": lambda metrics: f"進程數過多: {metrics.process_count}"
            }
        ]
    
    def check_alerts(self, metrics: SystemMetrics) -> List[Alert]:
        """檢查警報"""
        alerts = []
        
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    alert_id = f"{rule['name']}_{metrics.timestamp.strftime('%Y%m%d_%H%M%S')}"
                    
                    alert = Alert(
                        id=alert_id,
                        type=rule["name"],
                        severity=rule["severity"],
                        message=rule["message"](metrics),
                        timestamp=metrics.timestamp
                    )
                    
                    alerts.append(alert)
                    
            except Exception as e:
                logger.error(f"❌ 警報規則檢查失敗: {rule['name']}, {e}")
        
        return alerts
    
    def save_alert(self, alert: Alert):
        """保存警報"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alerts 
                    (id, type, severity, message, timestamp, resolved, resolution_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id,
                    alert.type,
                    alert.severity,
                    alert.message,
                    alert.timestamp.isoformat(),
                    1 if alert.resolved else 0,
                    alert.resolution_time.isoformat() if alert.resolution_time else None
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ 警報保存失敗: {e}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """獲取活躍警報"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM alerts 
                    WHERE resolved = 0 
                    ORDER BY timestamp DESC
                """)
                
                alerts = []
                for row in cursor.fetchall():
                    alerts.append(dict(row))
                
                return alerts
                
        except Exception as e:
            logger.error(f"❌ 獲取活躍警報失敗: {e}")
            return []
    
    def resolve_alert(self, alert_id: str):
        """解決警報"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET resolved = 1, resolution_time = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), alert_id))
                conn.commit()
                
            logger.info(f"✅ 警報已解決: {alert_id}")
            
        except Exception as e:
            logger.error(f"❌ 解決警報失敗: {e}")

class SystemMaintenance:
    """系統維護工具"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        
    def cleanup_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """清理舊日誌"""
        try:
            logger.info(f"🧹 清理 {days_to_keep} 天前的日誌")
            
            logs_dir = self.project_root / "AImax" / "logs"
            if not logs_dir.exists():
                return {"success": True, "message": "日誌目錄不存在", "cleaned_files": 0}
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleaned_files = 0
            total_size_cleaned = 0
            
            for log_file in logs_dir.rglob("*.log"):
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        cleaned_files += 1
                        total_size_cleaned += file_size
                        
                except Exception as e:
                    logger.warning(f"⚠️ 清理日誌文件失敗: {log_file}, {e}")
            
            return {
                "success": True,
                "message": f"清理完成: {cleaned_files} 個文件, {total_size_cleaned / 1024 / 1024:.1f} MB",
                "cleaned_files": cleaned_files,
                "size_cleaned_mb": total_size_cleaned / 1024 / 1024
            }
            
        except Exception as e:
            logger.error(f"❌ 日誌清理失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def optimize_database(self) -> Dict[str, Any]:
        """優化數據庫"""
        try:
            logger.info("🔧 優化系統數據庫")
            
            db_files = [
                "AImax/logs/system_metrics.db",
                "data/kline_data.db",
                "data/market_history.db",
                "data/multi_pair_market.db"
            ]
            
            optimized_dbs = []
            
            for db_file in db_files:
                db_path = self.project_root / db_file
                if db_path.exists():
                    try:
                        with sqlite3.connect(str(db_path)) as conn:
                            # 執行VACUUM優化
                            conn.execute("VACUUM")
                            # 重建索引
                            conn.execute("REINDEX")
                            conn.commit()
                        
                        optimized_dbs.append(db_file)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ 數據庫優化失敗: {db_file}, {e}")
            
            return {
                "success": True,
                "message": f"優化了 {len(optimized_dbs)} 個數據庫",
                "optimized_databases": optimized_dbs
            }
            
        except Exception as e:
            logger.error(f"❌ 數據庫優化失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def check_disk_space(self) -> Dict[str, Any]:
        """檢查磁盤空間"""
        try:
            disk_usage = psutil.disk_usage(str(self.project_root))
            
            total_gb = disk_usage.total / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            usage_percent = (used_gb / total_gb) * 100
            
            status = "OK"
            if usage_percent > 90:
                status = "CRITICAL"
            elif usage_percent > 80:
                status = "WARNING"
            
            return {
                "success": True,
                "status": status,
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "usage_percent": round(usage_percent, 1)
            }
            
        except Exception as e:
            logger.error(f"❌ 磁盤空間檢查失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def system_health_report(self) -> Dict[str, Any]:
        """生成系統健康報告"""
        try:
            logger.info("📋 生成系統健康報告")
            
            # 收集各種系統信息
            metrics_collector = MetricsCollector()
            current_metrics = metrics_collector.collect_metrics()
            metrics_summary = metrics_collector.get_metrics_summary(24)
            
            alert_manager = AlertManager()
            active_alerts = alert_manager.get_active_alerts()
            
            disk_info = self.check_disk_space()
            
            # 進程信息
            current_process = psutil.Process()
            process_info = {
                "pid": current_process.pid,
                "memory_mb": current_process.memory_info().rss / 1024 / 1024,
                "cpu_percent": current_process.cpu_percent(),
                "num_threads": current_process.num_threads(),
                "create_time": datetime.fromtimestamp(current_process.create_time()).isoformat()
            }
            
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "current_metrics": {
                    "cpu_usage": current_metrics.cpu_usage,
                    "memory_usage": current_metrics.memory_usage,
                    "disk_usage": current_metrics.disk_usage,
                    "process_count": current_metrics.process_count,
                    "thread_count": current_metrics.thread_count,
                    "uptime_hours": current_metrics.uptime / 3600
                },
                "metrics_summary_24h": metrics_summary,
                "active_alerts": len(active_alerts),
                "alert_details": active_alerts,
                "disk_info": disk_info,
                "process_info": process_info,
                "system_status": self._determine_system_status(current_metrics, active_alerts, disk_info)
            }
            
            return health_report
            
        except Exception as e:
            logger.error(f"❌ 健康報告生成失敗: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _determine_system_status(self, metrics: SystemMetrics, alerts: List, disk_info: Dict) -> str:
        """確定系統狀態"""
        try:
            # 檢查關鍵指標
            critical_issues = []
            
            if metrics.cpu_usage > 90:
                critical_issues.append("CPU使用率過高")
            
            if metrics.memory_usage > 90:
                critical_issues.append("內存使用率過高")
            
            if disk_info.get("usage_percent", 0) > 95:
                critical_issues.append("磁盤空間不足")
            
            # 檢查關鍵警報
            critical_alerts = [a for a in alerts if a.get("severity") == "CRITICAL"]
            
            if critical_issues or critical_alerts:
                return "CRITICAL"
            elif metrics.cpu_usage > 80 or metrics.memory_usage > 80 or len(alerts) > 0:
                return "WARNING"
            else:
                return "HEALTHY"
                
        except Exception as e:
            logger.error(f"❌ 系統狀態判斷失敗: {e}")
            return "UNKNOWN"

class SystemMonitor:
    """系統監控主類"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.maintenance = SystemMaintenance(project_root)
        self.monitoring = False
        
    def start_monitoring(self, interval: int = 60):
        """開始系統監控"""
        try:
            logger.info("🔍 啟動系統監控")
            
            # 啟動指標收集
            self.metrics_collector.start_collection(interval)
            
            # 啟動警報監控
            self.monitoring = True
            monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(interval,),
                daemon=True
            )
            monitor_thread.start()
            
            logger.info(f"✅ 系統監控已啟動 (間隔: {interval}秒)")
            
        except Exception as e:
            logger.error(f"❌ 系統監控啟動失敗: {e}")
    
    def stop_monitoring(self):
        """停止系統監控"""
        try:
            logger.info("⏹️ 停止系統監控")
            
            self.monitoring = False
            self.metrics_collector.stop_collection()
            
            logger.info("✅ 系統監控已停止")
            
        except Exception as e:
            logger.error(f"❌ 系統監控停止失敗: {e}")
    
    def _monitoring_loop(self, interval: int):
        """監控循環"""
        while self.monitoring:
            try:
                # 收集當前指標
                metrics = self.metrics_collector.collect_metrics()
                
                # 檢查警報
                alerts = self.alert_manager.check_alerts(metrics)
                
                # 保存新警報
                for alert in alerts:
                    self.alert_manager.save_alert(alert)
                    logger.warning(f"⚠️ 新警報: {alert.message}")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                time.sleep(interval)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """獲取監控儀表板數據"""
        try:
            health_report = self.maintenance.system_health_report()
            active_alerts = self.alert_manager.get_active_alerts()
            
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "system_status": health_report.get("system_status", "UNKNOWN"),
                "current_metrics": health_report.get("current_metrics", {}),
                "active_alerts_count": len(active_alerts),
                "recent_alerts": active_alerts[:5],  # 最近5個警報
                "disk_info": health_report.get("disk_info", {}),
                "process_info": health_report.get("process_info", {})
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"❌ 儀表板數據獲取失敗: {e}")
            return {"error": str(e)}

def main():
    """主函數"""
    print("🔍 AImax 系統監控工具")
    print("=" * 40)
    
    try:
        # 創建系統監控
        monitor = SystemMonitor()
        
        # 啟動監控
        monitor.start_monitoring(interval=30)  # 30秒間隔
        
        # 運行一段時間收集數據
        print("📊 收集系統指標中...")
        time.sleep(60)  # 運行1分鐘
        
        # 獲取儀表板數據
        dashboard_data = monitor.get_dashboard_data()
        
        print(f"\n📋 系統狀態: {dashboard_data.get('system_status', 'UNKNOWN')}")
        
        current_metrics = dashboard_data.get('current_metrics', {})
        print(f"CPU使用率: {current_metrics.get('cpu_usage', 0):.1f}%")
        print(f"內存使用率: {current_metrics.get('memory_usage', 0):.1f}%")
        print(f"磁盤使用率: {current_metrics.get('disk_usage', 0):.1f}%")
        print(f"活躍警報: {dashboard_data.get('active_alerts_count', 0)} 個")
        
        # 執行維護任務
        print(f"\n🧹 執行系統維護...")
        cleanup_result = monitor.maintenance.cleanup_logs(days_to_keep=7)
        print(f"日誌清理: {cleanup_result.get('message', '失敗')}")
        
        optimize_result = monitor.maintenance.optimize_database()
        print(f"數據庫優化: {optimize_result.get('message', '失敗')}")
        
        # 停止監控
        monitor.stop_monitoring()
        
        # 保存監控報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path("AImax/logs/monitoring_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"monitoring_report_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "dashboard_data": dashboard_data,
                "maintenance_results": {
                    "cleanup": cleanup_result,
                    "optimize": optimize_result
                }
            }, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 監控報告已保存: {report_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 系統監控執行失敗: {e}")
        return 1

if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    exit_code = main()
    sys.exit(exit_code)