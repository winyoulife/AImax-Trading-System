#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 存儲空間監控和優化 - 任務10實現
監控存儲空間使用，自動清理不必要文件，優化存儲效率
"""

import sys
import os
import json
import time
import logging
import shutil
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
import threading

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class DirectoryInfo:
    """目錄信息"""
    path: Path
    size_mb: float
    file_count: int
    subdirectory_count: int
    last_modified: datetime
    file_types: Dict[str, int] = field(default_factory=dict)

@dataclass
class CleanupResult:
    """清理結果"""
    cleaned_files: int
    freed_space_mb: float
    cleaned_directories: List[str]
    errors: List[str] = field(default_factory=list)

class StorageOptimizer:
    """存儲空間優化器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.storage_stats: List[Dict[str, Any]] = []
        
        # 清理配置
        self.cleanup_config = {
            'log_files': {
                'extensions': ['.log', '.out', '.err'],
                'max_age_days': 7,
                'compress_after_days': 1,
                'max_size_mb': 100
            },
            'temp_files': {
                'directories': ['temp', 'tmp', '__pycache__', '.pytest_cache'],
                'extensions': ['.tmp', '.temp', '.cache'],
                'max_age_hours': 24
            },
            'backup_files': {
                'extensions': ['.bak', '.backup', '.old'],
                'max_age_days': 30,
                'max_count': 5
            },
            'report_files': {
                'extensions': ['.json', '.txt', '.html'],
                'directories': ['reports'],
                'max_age_days': 30,
                'max_count': 100
            },
            'data_files': {
                'extensions': ['.csv', '.db'],
                'directories': ['data'],
                'max_age_days': 90,
                'compress_after_days': 30
            }
        }
        
        # 存儲監控配置
        self.monitoring_config = {
            'scan_interval_hours': 6,
            'alert_thresholds': {
                'total_size_gb': 1.0,      # 項目總大小超過1GB警告
                'single_dir_mb': 100,      # 單個目錄超過100MB警告
                'file_count': 10000,       # 文件數量超過10000警告
                'log_size_mb': 50          # 日誌文件超過50MB警告
            },
            'exclude_patterns': [
                '.git',
                'node_modules',
                '.venv',
                'venv',
                '__pycache__',
                '.pytest_cache'
            ]
        }
        
        # 監控狀態
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def start_monitoring(self):
        """開始存儲監控"""
        if self.monitoring_active:
            logger.warning("⚠️ 存儲監控已在運行")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info(f"💾 存儲監控已啟動，掃描間隔: {self.monitoring_config['scan_interval_hours']}小時")
    
    def stop_monitoring(self):
        """停止存儲監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("🛑 存儲監控已停止")
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.monitoring_active:
            try:
                # 掃描存儲使用情況
                storage_info = self.scan_storage_usage()
                self.storage_stats.append(storage_info)
                
                # 檢查警告閾值
                self._check_storage_alerts(storage_info)
                
                # 自動清理
                self._auto_cleanup()
                
                # 清理舊統計數據
                self._cleanup_old_stats()
                
                # 等待下次掃描
                time.sleep(self.monitoring_config['scan_interval_hours'] * 3600)
                
            except Exception as e:
                logger.error(f"❌ 存儲監控循環錯誤: {e}")
                time.sleep(3600)  # 出錯時等待1小時
    
    def scan_storage_usage(self) -> Dict[str, Any]:
        """掃描存儲使用情況"""
        logger.info("🔍 掃描存儲使用情況...")
        
        scan_start = time.time()
        directory_info = {}
        total_size = 0
        total_files = 0
        
        try:
            # 掃描主要目錄
            main_directories = [
                'src', 'scripts', 'tests', 'data', 'logs', 'reports', 
                'static', 'templates', '.github', 'docs'
            ]
            
            for dir_name in main_directories:
                dir_path = self.project_root / dir_name
                if dir_path.exists():
                    dir_info = self._analyze_directory(dir_path)
                    directory_info[dir_name] = dir_info
                    total_size += dir_info.size_mb
                    total_files += dir_info.file_count
            
            # 掃描根目錄文件
            root_files = self._analyze_directory(self.project_root, recursive=False)
            directory_info['root_files'] = root_files
            total_size += root_files.size_mb
            total_files += root_files.file_count
            
            scan_time = time.time() - scan_start
            
            storage_info = {
                'timestamp': datetime.now(),
                'total_size_mb': total_size,
                'total_size_gb': total_size / 1024,
                'total_files': total_files,
                'directory_info': directory_info,
                'scan_time_seconds': scan_time,
                'largest_directories': self._get_largest_directories(directory_info),
                'file_type_distribution': self._get_file_type_distribution(directory_info)
            }
            
            logger.info(f"✅ 存儲掃描完成: {total_size:.2f} MB, {total_files} 個文件")
            
            return storage_info
            
        except Exception as e:
            logger.error(f"❌ 存儲掃描失敗: {e}")
            return {
                'timestamp': datetime.now(),
                'error': str(e),
                'total_size_mb': 0,
                'total_files': 0
            }
    
    def _analyze_directory(self, directory: Path, recursive: bool = True) -> DirectoryInfo:
        """分析目錄信息"""
        try:
            total_size = 0
            file_count = 0
            subdirectory_count = 0
            file_types = {}
            last_modified = datetime.fromtimestamp(0)
            
            if recursive:
                # 遞歸掃描
                for item in directory.rglob('*'):
                    if item.is_file():
                        try:
                            file_size = item.stat().st_size
                            total_size += file_size
                            file_count += 1
                            
                            # 統計文件類型
                            extension = item.suffix.lower()
                            file_types[extension] = file_types.get(extension, 0) + 1
                            
                            # 更新最後修改時間
                            file_mtime = datetime.fromtimestamp(item.stat().st_mtime)
                            if file_mtime > last_modified:
                                last_modified = file_mtime
                                
                        except (OSError, FileNotFoundError):
                            continue
                    elif item.is_dir():
                        subdirectory_count += 1
            else:
                # 只掃描當前目錄
                for item in directory.iterdir():
                    if item.is_file():
                        try:
                            file_size = item.stat().st_size
                            total_size += file_size
                            file_count += 1
                            
                            extension = item.suffix.lower()
                            file_types[extension] = file_types.get(extension, 0) + 1
                            
                            file_mtime = datetime.fromtimestamp(item.stat().st_mtime)
                            if file_mtime > last_modified:
                                last_modified = file_mtime
                                
                        except (OSError, FileNotFoundError):
                            continue
                    elif item.is_dir():
                        subdirectory_count += 1
            
            return DirectoryInfo(
                path=directory,
                size_mb=total_size / (1024 * 1024),
                file_count=file_count,
                subdirectory_count=subdirectory_count,
                last_modified=last_modified,
                file_types=file_types
            )
            
        except Exception as e:
            logger.error(f"❌ 分析目錄失敗 {directory}: {e}")
            return DirectoryInfo(
                path=directory,
                size_mb=0,
                file_count=0,
                subdirectory_count=0,
                last_modified=datetime.fromtimestamp(0)
            )
    
    def _get_largest_directories(self, directory_info: Dict[str, DirectoryInfo]) -> List[Tuple[str, float]]:
        """獲取最大的目錄"""
        dir_sizes = [
            (name, info.size_mb) 
            for name, info in directory_info.items()
            if isinstance(info, DirectoryInfo)
        ]
        
        return sorted(dir_sizes, key=lambda x: x[1], reverse=True)[:10]
    
    def _get_file_type_distribution(self, directory_info: Dict[str, DirectoryInfo]) -> Dict[str, int]:
        """獲取文件類型分布"""
        file_types = {}
        
        for info in directory_info.values():
            if isinstance(info, DirectoryInfo):
                for ext, count in info.file_types.items():
                    file_types[ext] = file_types.get(ext, 0) + count
        
        return dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True))
    
    def _check_storage_alerts(self, storage_info: Dict[str, Any]):
        """檢查存儲警告"""
        alerts = []
        thresholds = self.monitoring_config['alert_thresholds']
        
        # 檢查總大小
        if storage_info['total_size_gb'] > thresholds['total_size_gb']:
            alerts.append(f"🚨 項目總大小過大: {storage_info['total_size_gb']:.2f} GB")
        
        # 檢查文件數量
        if storage_info['total_files'] > thresholds['file_count']:
            alerts.append(f"⚠️ 文件數量過多: {storage_info['total_files']:,} 個文件")
        
        # 檢查單個目錄大小
        for dir_name, size_mb in storage_info.get('largest_directories', []):
            if size_mb > thresholds['single_dir_mb']:
                alerts.append(f"⚠️ 目錄 '{dir_name}' 過大: {size_mb:.2f} MB")
        
        # 檢查日誌文件大小
        if 'logs' in storage_info.get('directory_info', {}):
            logs_info = storage_info['directory_info']['logs']
            if isinstance(logs_info, DirectoryInfo) and logs_info.size_mb > thresholds['log_size_mb']:
                alerts.append(f"⚠️ 日誌文件過大: {logs_info.size_mb:.2f} MB")
        
        # 記錄警告
        for alert in alerts:
            logger.warning(alert)
    
    def _auto_cleanup(self):
        """自動清理"""
        try:
            logger.info("🧹 開始自動清理...")
            
            # 清理日誌文件
            log_result = self.cleanup_log_files()
            if log_result.freed_space_mb > 0:
                logger.info(f"📄 清理日誌文件: 釋放 {log_result.freed_space_mb:.2f} MB")
            
            # 清理臨時文件
            temp_result = self.cleanup_temporary_files()
            if temp_result.freed_space_mb > 0:
                logger.info(f"🗂️ 清理臨時文件: 釋放 {temp_result.freed_space_mb:.2f} MB")
            
            # 清理舊報告
            report_result = self.cleanup_old_reports()
            if report_result.freed_space_mb > 0:
                logger.info(f"📊 清理舊報告: 釋放 {report_result.freed_space_mb:.2f} MB")
            
        except Exception as e:
            logger.error(f"❌ 自動清理失敗: {e}")
    
    def cleanup_log_files(self) -> CleanupResult:
        """清理日誌文件"""
        result = CleanupResult(0, 0.0, [])
        
        try:
            logs_dir = self.project_root / "logs"
            if not logs_dir.exists():
                return result
            
            config = self.cleanup_config['log_files']
            cutoff_date = datetime.now() - timedelta(days=config['max_age_days'])
            compress_date = datetime.now() - timedelta(days=config['compress_after_days'])
            
            for log_file in logs_dir.rglob("*"):
                if not log_file.is_file():
                    continue
                
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    file_size = log_file.stat().st_size
                    
                    # 刪除過舊的文件
                    if file_mtime < cutoff_date:
                        freed_mb = file_size / (1024 * 1024)
                        log_file.unlink()
                        result.cleaned_files += 1
                        result.freed_space_mb += freed_mb
                        
                    # 壓縮較舊的文件
                    elif (file_mtime < compress_date and 
                          log_file.suffix in config['extensions'] and
                          not log_file.name.endswith('.gz')):
                        
                        compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                        
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # 刪除原文件
                        original_size = file_size / (1024 * 1024)
                        compressed_size = compressed_file.stat().st_size / (1024 * 1024)
                        
                        log_file.unlink()
                        result.cleaned_files += 1
                        result.freed_space_mb += (original_size - compressed_size)
                        
                except (OSError, FileNotFoundError) as e:
                    result.errors.append(f"處理日誌文件失敗 {log_file}: {e}")
            
            if result.cleaned_files > 0:
                result.cleaned_directories.append(str(logs_dir))
            
        except Exception as e:
            result.errors.append(f"清理日誌文件失敗: {e}")
        
        return result
    
    def cleanup_temporary_files(self) -> CleanupResult:
        """清理臨時文件"""
        result = CleanupResult(0, 0.0, [])
        
        try:
            config = self.cleanup_config['temp_files']
            cutoff_time = datetime.now() - timedelta(hours=config['max_age_hours'])
            
            # 清理指定的臨時目錄
            for dir_name in config['directories']:
                temp_dir = self.project_root / dir_name
                if temp_dir.exists():
                    initial_size = self._get_directory_size_mb(temp_dir)
                    
                    if dir_name in ['__pycache__', '.pytest_cache']:
                        # 完全刪除緩存目錄
                        shutil.rmtree(temp_dir)
                        result.cleaned_files += 1
                        result.freed_space_mb += initial_size
                        result.cleaned_directories.append(str(temp_dir))
                    else:
                        # 清理舊文件
                        for temp_file in temp_dir.rglob("*"):
                            if temp_file.is_file():
                                try:
                                    file_mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                                    if file_mtime < cutoff_time:
                                        file_size = temp_file.stat().st_size / (1024 * 1024)
                                        temp_file.unlink()
                                        result.cleaned_files += 1
                                        result.freed_space_mb += file_size
                                except (OSError, FileNotFoundError):
                                    continue
                        
                        if result.cleaned_files > 0:
                            result.cleaned_directories.append(str(temp_dir))
            
            # 清理指定擴展名的臨時文件
            for temp_file in self.project_root.rglob("*"):
                if (temp_file.is_file() and 
                    temp_file.suffix in config['extensions']):
                    try:
                        file_mtime = datetime.fromtimestamp(temp_file.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            file_size = temp_file.stat().st_size / (1024 * 1024)
                            temp_file.unlink()
                            result.cleaned_files += 1
                            result.freed_space_mb += file_size
                    except (OSError, FileNotFoundError):
                        continue
            
        except Exception as e:
            result.errors.append(f"清理臨時文件失敗: {e}")
        
        return result
    
    def cleanup_old_reports(self) -> CleanupResult:
        """清理舊報告文件"""
        result = CleanupResult(0, 0.0, [])
        
        try:
            reports_dir = self.project_root / "reports"
            if not reports_dir.exists():
                return result
            
            config = self.cleanup_config['report_files']
            cutoff_date = datetime.now() - timedelta(days=config['max_age_days'])
            
            # 獲取所有報告文件並按時間排序
            report_files = []
            for report_file in reports_dir.rglob("*"):
                if (report_file.is_file() and 
                    report_file.suffix in config['extensions']):
                    try:
                        file_mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                        file_size = report_file.stat().st_size
                        report_files.append((report_file, file_mtime, file_size))
                    except (OSError, FileNotFoundError):
                        continue
            
            # 按時間排序（最新的在前）
            report_files.sort(key=lambda x: x[1], reverse=True)
            
            # 保留最新的文件，刪除過舊或過多的文件
            for i, (report_file, file_mtime, file_size) in enumerate(report_files):
                should_delete = False
                
                # 超過最大數量限制
                if i >= config['max_count']:
                    should_delete = True
                
                # 超過時間限制
                elif file_mtime < cutoff_date:
                    should_delete = True
                
                if should_delete:
                    try:
                        freed_mb = file_size / (1024 * 1024)
                        report_file.unlink()
                        result.cleaned_files += 1
                        result.freed_space_mb += freed_mb
                    except (OSError, FileNotFoundError):
                        continue
            
            if result.cleaned_files > 0:
                result.cleaned_directories.append(str(reports_dir))
            
        except Exception as e:
            result.errors.append(f"清理報告文件失敗: {e}")
        
        return result
    
    def _get_directory_size_mb(self, directory: Path) -> float:
        """獲取目錄大小（MB）"""
        try:
            total_size = 0
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _cleanup_old_stats(self):
        """清理舊統計數據"""
        cutoff_date = datetime.now() - timedelta(days=30)
        self.storage_stats = [
            stat for stat in self.storage_stats
            if stat.get('timestamp', datetime.now()) > cutoff_date
        ]
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """獲取存儲統計"""
        if not self.storage_stats:
            # 如果沒有統計數據，立即掃描一次
            current_stats = self.scan_storage_usage()
            return current_stats
        
        latest_stats = self.storage_stats[-1]
        
        # 計算趨勢
        if len(self.storage_stats) > 1:
            previous_stats = self.storage_stats[-2]
            size_trend = latest_stats['total_size_mb'] - previous_stats['total_size_mb']
            files_trend = latest_stats['total_files'] - previous_stats['total_files']
        else:
            size_trend = 0
            files_trend = 0
        
        return {
            'current': latest_stats,
            'trends': {
                'size_change_mb': size_trend,
                'files_change': files_trend
            },
            'history_points': len(self.storage_stats)
        }
    
    def generate_storage_report(self) -> str:
        """生成存儲報告"""
        stats = self.get_storage_statistics()
        current = stats['current']
        
        report = f"""
💾 AImax 存儲空間監控報告
{'='*60}

📊 當前存儲使用:
   總大小: {current['total_size_mb']:.2f} MB ({current['total_size_gb']:.2f} GB)
   總文件數: {current['total_files']:,}
   掃描時間: {current.get('scan_time_seconds', 0):.2f} 秒
"""
        
        # 添加趨勢信息
        if 'trends' in stats:
            trends = stats['trends']
            size_trend_str = f"+{trends['size_change_mb']:.2f}" if trends['size_change_mb'] >= 0 else f"{trends['size_change_mb']:.2f}"
            files_trend_str = f"+{trends['files_change']}" if trends['files_change'] >= 0 else f"{trends['files_change']}"
            
            report += f"""
📈 變化趨勢:
   大小變化: {size_trend_str} MB
   文件數變化: {files_trend_str}
"""
        
        # 添加最大目錄信息
        if 'largest_directories' in current:
            report += f"\n📁 最大目錄 (前5名):\n"
            for dir_name, size_mb in current['largest_directories'][:5]:
                report += f"   {dir_name}: {size_mb:.2f} MB\n"
        
        # 添加文件類型分布
        if 'file_type_distribution' in current:
            report += f"\n📄 文件類型分布 (前10名):\n"
            for ext, count in list(current['file_type_distribution'].items())[:10]:
                ext_display = ext if ext else '(無擴展名)'
                report += f"   {ext_display}: {count} 個文件\n"
        
        report += f"\n{'='*60}\n"
        report += f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def save_storage_data(self) -> Path:
        """保存存儲數據"""
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # 保存詳細數據
        data_file = reports_dir / f"storage_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        storage_data = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.get_storage_statistics(),
            'cleanup_config': self.cleanup_config,
            'monitoring_config': self.monitoring_config
        }
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(storage_data, f, indent=2, ensure_ascii=False, default=str)
        
        # 保存報告
        report_file = reports_dir / f"storage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_storage_report())
        
        logger.info(f"📄 存儲數據已保存: {data_file}")
        logger.info(f"📄 存儲報告已保存: {report_file}")
        
        return data_file

# 全局存儲優化器實例
storage_optimizer = StorageOptimizer()

# 便捷函數
def start_storage_monitoring():
    """啟動存儲監控"""
    storage_optimizer.start_monitoring()

def stop_storage_monitoring():
    """停止存儲監控"""
    storage_optimizer.stop_monitoring()

def get_storage_stats() -> Dict[str, Any]:
    """獲取存儲統計"""
    return storage_optimizer.get_storage_statistics()

def cleanup_storage() -> Dict[str, Any]:
    """清理存儲空間"""
    log_result = storage_optimizer.cleanup_log_files()
    temp_result = storage_optimizer.cleanup_temporary_files()
    report_result = storage_optimizer.cleanup_old_reports()
    
    return {
        'log_cleanup': log_result,
        'temp_cleanup': temp_result,
        'report_cleanup': report_result,
        'total_freed_mb': (log_result.freed_space_mb + 
                          temp_result.freed_space_mb + 
                          report_result.freed_space_mb)
    }