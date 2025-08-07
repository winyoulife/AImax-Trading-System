#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 結構化日誌系統 - 任務13實現
實現結構化日誌記錄、存儲和查詢功能
"""

import sys
import os
import json
import logging
import logging.handlers
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import queue
import traceback

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

class LogLevel(Enum):
    """日誌級別枚舉"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """日誌分類枚舉"""
    SYSTEM = "system"
    TRADING = "trading"
    STRATEGY = "strategy"
    NETWORK = "network"
    ERROR = "error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER = "user"

@dataclass
class LogEntry:
    """結構化日誌條目"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    module: str
    function: str
    line_number: int
    thread_id: str
    process_id: int
    extra_data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    correlation_id: Optional[str] = None

class StructuredLogger:
    """結構化日誌記錄器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # 日誌配置
        self.config = {
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'enable_console': True,
            'enable_file': True,
            'enable_json': True,
            'retention_days': 30
        }
        
        # 日誌隊列（用於異步寫入）
        self.log_queue = queue.Queue()
        self.log_worker_thread = None
        self.worker_active = False
        
        # 日誌統計
        self.log_stats = {
            'total_logs': 0,
            'logs_by_level': {level.value: 0 for level in LogLevel},
            'logs_by_category': {cat.value: 0 for cat in LogCategory},
            'errors_last_hour': 0,
            'last_reset_time': datetime.now()
        }
        
        self.setup_loggers()
        self.start_log_worker()
    
    def setup_loggers(self):
        """設置日誌記錄器"""
        # 創建主日誌記錄器
        self.logger = logging.getLogger('aimax')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除現有處理器
        self.logger.handlers.clear()
        
        # 控制台處理器
        if self.config['enable_console']:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                self.config['log_format'],
                datefmt=self.config['date_format']
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # 文件處理器
        if self.config['enable_file']:
            # 按級別分別記錄
            for level in [logging.INFO, logging.WARNING, logging.ERROR]:
                level_name = logging.getLevelName(level).lower()
                log_file = self.logs_dir / f"aimax_{level_name}.log"
                
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=self.config['max_file_size'],
                    backupCount=self.config['backup_count'],
                    encoding='utf-8'
                )
                file_handler.setLevel(level)
                
                file_formatter = logging.Formatter(
                    self.config['log_format'],
                    datefmt=self.config['date_format']
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
        
        # JSON結構化日誌處理器
        if self.config['enable_json']:
            json_log_file = self.logs_dir / "aimax_structured.jsonl"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=self.config['max_file_size'],
                backupCount=self.config['backup_count'],
                encoding='utf-8'
            )
            json_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(json_handler)
    
    def start_log_worker(self):
        """啟動日誌工作線程"""
        if self.worker_active:
            return
        
        self.worker_active = True
        self.log_worker_thread = threading.Thread(target=self._log_worker, daemon=True)
        self.log_worker_thread.start()
    
    def stop_log_worker(self):
        """停止日誌工作線程"""
        self.worker_active = False
        if self.log_worker_thread:
            self.log_worker_thread.join(timeout=5)
    
    def _log_worker(self):
        """日誌工作線程"""
        while self.worker_active:
            try:
                # 從隊列獲取日誌條目
                log_entry = self.log_queue.get(timeout=1)
                
                # 寫入結構化日誌
                self._write_structured_log(log_entry)
                
                # 更新統計
                self._update_log_stats(log_entry)
                
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                # 避免日誌系統本身的錯誤影響主程序
                print(f"日誌工作線程錯誤: {e}")
    
    def log(self, level: LogLevel, category: LogCategory, message: str,
            extra_data: Dict[str, Any] = None, correlation_id: str = None):
        """記錄結構化日誌"""
        # 獲取調用者信息
        frame = sys._getframe(1)
        module = frame.f_globals.get('__name__', 'unknown')
        function = frame.f_code.co_name
        line_number = frame.f_lineno
        
        # 創建日誌條目
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            module=module,
            function=function,
            line_number=line_number,
            thread_id=threading.current_thread().name,
            process_id=os.getpid(),
            extra_data=extra_data or {},
            correlation_id=correlation_id
        )
        
        # 如果是錯誤級別，添加堆棧跟蹤
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            log_entry.stack_trace = traceback.format_stack()
        
        # 添加到隊列
        try:
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            # 隊列滿時直接寫入
            self._write_structured_log(log_entry)
        
        # 同時使用標準日誌記錄器
        standard_level = getattr(logging, level.value)
        self.logger.log(standard_level, f"[{category.value}] {message}")
    
    def _write_structured_log(self, log_entry: LogEntry):
        """寫入結構化日誌"""
        try:
            # 轉換為JSON格式
            log_dict = asdict(log_entry)
            log_dict['timestamp'] = log_entry.timestamp.isoformat()
            log_dict['level'] = log_entry.level.value
            log_dict['category'] = log_entry.category.value
            
            # 寫入JSON日誌文件
            json_log_file = self.logs_dir / "aimax_structured.jsonl"
            with open(json_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_dict, ensure_ascii=False) + '\n')
                
        except Exception as e:
            print(f"寫入結構化日誌失敗: {e}")
    
    def _update_log_stats(self, log_entry: LogEntry):
        """更新日誌統計"""
        self.log_stats['total_logs'] += 1
        self.log_stats['logs_by_level'][log_entry.level.value] += 1
        self.log_stats['logs_by_category'][log_entry.category.value] += 1
        
        # 統計最近一小時的錯誤
        if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            now = datetime.now()
            if now - self.log_stats['last_reset_time'] > timedelta(hours=1):
                self.log_stats['errors_last_hour'] = 1
                self.log_stats['last_reset_time'] = now
            else:
                self.log_stats['errors_last_hour'] += 1
    
    def debug(self, category: LogCategory, message: str, **kwargs):
        """記錄DEBUG級別日誌"""
        self.log(LogLevel.DEBUG, category, message, kwargs)
    
    def info(self, category: LogCategory, message: str, **kwargs):
        """記錄INFO級別日誌"""
        self.log(LogLevel.INFO, category, message, kwargs)
    
    def warning(self, category: LogCategory, message: str, **kwargs):
        """記錄WARNING級別日誌"""
        self.log(LogLevel.WARNING, category, message, kwargs)
    
    def error(self, category: LogCategory, message: str, **kwargs):
        """記錄ERROR級別日誌"""
        self.log(LogLevel.ERROR, category, message, kwargs)
    
    def critical(self, category: LogCategory, message: str, **kwargs):
        """記錄CRITICAL級別日誌"""
        self.log(LogLevel.CRITICAL, category, message, kwargs)
    
    def query_logs(self, start_time: datetime = None, end_time: datetime = None,
                   level: LogLevel = None, category: LogCategory = None,
                   search_text: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """查詢日誌"""
        try:
            json_log_file = self.logs_dir / "aimax_structured.jsonl"
            
            if not json_log_file.exists():
                return []
            
            logs = []
            with open(json_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_dict = json.loads(line.strip())
                        
                        # 時間過濾
                        log_time = datetime.fromisoformat(log_dict['timestamp'])
                        if start_time and log_time < start_time:
                            continue
                        if end_time and log_time > end_time:
                            continue
                        
                        # 級別過濾
                        if level and log_dict['level'] != level.value:
                            continue
                        
                        # 分類過濾
                        if category and log_dict['category'] != category.value:
                            continue
                        
                        # 文本搜索
                        if search_text and search_text.lower() not in log_dict['message'].lower():
                            continue
                        
                        logs.append(log_dict)
                        
                        if len(logs) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            # 按時間倒序排列
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return logs
            
        except Exception as e:
            self.error(LogCategory.SYSTEM, f"查詢日誌失敗: {e}")
            return []
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """獲取日誌統計信息"""
        return {
            'total_logs': self.log_stats['total_logs'],
            'logs_by_level': self.log_stats['logs_by_level'].copy(),
            'logs_by_category': self.log_stats['logs_by_category'].copy(),
            'errors_last_hour': self.log_stats['errors_last_hour'],
            'last_reset_time': self.log_stats['last_reset_time'].isoformat(),
            'queue_size': self.log_queue.qsize(),
            'worker_active': self.worker_active
        }
    
    def cleanup_old_logs(self, days: int = None):
        """清理舊日誌文件"""
        days = days or self.config['retention_days']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cleaned_files = 0
        
        for log_file in self.logs_dir.glob("*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    cleaned_files += 1
            except Exception as e:
                self.warning(LogCategory.SYSTEM, f"清理日誌文件失敗: {log_file} - {e}")
        
        self.info(LogCategory.SYSTEM, f"清理了 {cleaned_files} 個舊日誌文件")
        return cleaned_files
    
    def export_logs(self, start_time: datetime, end_time: datetime,
                   export_format: str = 'json') -> Optional[Path]:
        """導出日誌"""
        try:
            logs = self.query_logs(start_time, end_time, limit=10000)
            
            if not logs:
                return None
            
            # 生成導出文件名
            start_str = start_time.strftime('%Y%m%d_%H%M%S')
            end_str = end_time.strftime('%Y%m%d_%H%M%S')
            export_file = self.logs_dir / f"export_{start_str}_to_{end_str}.{export_format}"
            
            if export_format == 'json':
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
            
            elif export_format == 'csv':
                import csv
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    if logs:
                        writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                        writer.writeheader()
                        writer.writerows(logs)
            
            self.info(LogCategory.SYSTEM, f"導出日誌成功: {export_file}")
            return export_file
            
        except Exception as e:
            self.error(LogCategory.SYSTEM, f"導出日誌失敗: {e}")
            return None

# 全局結構化日誌記錄器實例
structured_logger = StructuredLogger()

# 便捷函數
def log_info(category: LogCategory, message: str, **kwargs):
    """記錄信息日誌"""
    structured_logger.info(category, message, **kwargs)

def log_warning(category: LogCategory, message: str, **kwargs):
    """記錄警告日誌"""
    structured_logger.warning(category, message, **kwargs)

def log_error(category: LogCategory, message: str, **kwargs):
    """記錄錯誤日誌"""
    structured_logger.error(category, message, **kwargs)

def log_trading(message: str, **kwargs):
    """記錄交易日誌"""
    structured_logger.info(LogCategory.TRADING, message, **kwargs)

def log_strategy(message: str, **kwargs):
    """記錄策略日誌"""
    structured_logger.info(LogCategory.STRATEGY, message, **kwargs)

def log_system(message: str, **kwargs):
    """記錄系統日誌"""
    structured_logger.info(LogCategory.SYSTEM, message, **kwargs)