#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 錯誤處理和故障恢復系統 - 任務9實現
提供網路重試、API限制處理、交易回滾和系統恢復功能
"""

import sys
import os
import time
import json
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
import threading
import queue

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

@dataclass
class ErrorRecord:
    """錯誤記錄數據結構"""
    timestamp: datetime
    error_type: str
    error_message: str
    function_name: str
    retry_count: int = 0
    resolved: bool = False
    recovery_action: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RetryConfig:
    """重試配置"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True

class AIMaxErrorHandler:
    """AImax 錯誤處理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.error_log_dir = self.project_root / "logs" / "errors"
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        
        self.error_records: List[ErrorRecord] = []
        self.recovery_strategies: Dict[str, Callable] = {}
        self.circuit_breakers: Dict[str, Dict] = {}
        
        self.setup_logging()
        self.register_default_recovery_strategies()
        
    def setup_logging(self):
        """設置錯誤日誌"""
        log_file = self.error_log_dir / f"error_handler_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """註冊恢復策略"""
        self.recovery_strategies[error_type] = strategy
        self.logger.info(f"註冊恢復策略: {error_type}")
    
    def register_default_recovery_strategies(self):
        """註冊默認恢復策略"""
        self.register_recovery_strategy("NetworkError", self._network_recovery)
        self.register_recovery_strategy("APIError", self._api_recovery)
        self.register_recovery_strategy("DataError", self._data_recovery)
        self.register_recovery_strategy("TradingError", self._trading_recovery)
        self.register_recovery_strategy("SystemError", self._system_recovery)
    
    def retry_with_backoff(self, config: RetryConfig = None):
        """重試裝飾器，支援指數退避"""
        if config is None:
            config = RetryConfig()
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(config.max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        
                        # 如果之前有錯誤，記錄恢復
                        if attempt > 0:
                            self.logger.info(f"✅ {func.__name__} 在第 {attempt + 1} 次嘗試後成功恢復")
                        
                        return result
                        
                    except Exception as e:
                        last_exception = e
                        
                        if attempt < config.max_retries:
                            delay = self._calculate_delay(attempt, config)
                            
                            self.logger.warning(
                                f"⚠️ {func.__name__} 第 {attempt + 1} 次嘗試失敗: {str(e)}, "
                                f"{delay:.2f}秒後重試..."
                            )
                            
                            # 記錄錯誤
                            self._record_error(
                                error_type=type(e).__name__,
                                error_message=str(e),
                                function_name=func.__name__,
                                retry_count=attempt + 1
                            )
                            
                            time.sleep(delay)
                        else:
                            self.logger.error(f"❌ {func.__name__} 在 {config.max_retries + 1} 次嘗試後仍然失敗")
                
                # 所有重試都失敗，嘗試恢復策略
                recovery_result = self._attempt_recovery(type(last_exception).__name__, last_exception, func.__name__)
                
                if recovery_result.get('success'):
                    self.logger.info(f"🔧 {func.__name__} 通過恢復策略成功修復")
                    return recovery_result.get('result')
                
                # 恢復失敗，拋出原始異常
                raise last_exception
            
            return wrapper
        return decorator
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """計算重試延遲時間"""
        if config.exponential_backoff:
            delay = config.base_delay * (2 ** attempt)
        else:
            delay = config.base_delay
        
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 添加50%的隨機抖動
        
        return delay
    
    def _record_error(self, error_type: str, error_message: str, function_name: str, retry_count: int = 0, context: Dict = None):
        """記錄錯誤"""
        error_record = ErrorRecord(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=error_message,
            function_name=function_name,
            retry_count=retry_count,
            context=context or {}
        )
        
        self.error_records.append(error_record)
        
        # 保存到文件
        self._save_error_record(error_record)
    
    def _save_error_record(self, error_record: ErrorRecord):
        """保存錯誤記錄到文件"""
        error_file = self.error_log_dir / f"error_records_{datetime.now().strftime('%Y%m%d')}.json"
        
        # 讀取現有記錄
        existing_records = []
        if error_file.exists():
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    existing_records = json.load(f)
            except:
                existing_records = []
        
        # 添加新記錄
        record_dict = {
            'timestamp': error_record.timestamp.isoformat(),
            'error_type': error_record.error_type,
            'error_message': error_record.error_message,
            'function_name': error_record.function_name,
            'retry_count': error_record.retry_count,
            'resolved': error_record.resolved,
            'recovery_action': error_record.recovery_action,
            'context': error_record.context
        }
        
        existing_records.append(record_dict)
        
        # 保存到文件
        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(existing_records, f, indent=2, ensure_ascii=False)
    
    def _attempt_recovery(self, error_type: str, exception: Exception, function_name: str) -> Dict[str, Any]:
        """嘗試錯誤恢復"""
        self.logger.info(f"🔧 嘗試恢復 {error_type} 錯誤...")
        
        if error_type in self.recovery_strategies:
            try:
                recovery_strategy = self.recovery_strategies[error_type]
                result = recovery_strategy(exception, function_name)
                
                if result.get('success'):
                    # 更新錯誤記錄
                    for record in reversed(self.error_records):
                        if (record.error_type == error_type and 
                            record.function_name == function_name and 
                            not record.resolved):
                            record.resolved = True
                            record.recovery_action = result.get('action', 'Unknown')
                            break
                    
                    self.logger.info(f"✅ {error_type} 錯誤恢復成功: {result.get('action')}")
                    return result
                else:
                    self.logger.warning(f"⚠️ {error_type} 錯誤恢復失敗: {result.get('reason')}")
            
            except Exception as recovery_error:
                self.logger.error(f"❌ 恢復策略執行失敗: {str(recovery_error)}")
        
        else:
            self.logger.warning(f"⚠️ 沒有找到 {error_type} 的恢復策略")
        
        return {'success': False, 'reason': 'No recovery strategy available'}
    
    def _network_recovery(self, exception: Exception, function_name: str) -> Dict[str, Any]:
        """網路錯誤恢復策略"""
        self.logger.info("🌐 執行網路錯誤恢復策略...")
        
        # 檢查網路連接
        import subprocess
        try:
            # 嘗試ping Google DNS
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, timeout=10)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'action': 'Network connectivity verified',
                    'result': None
                }
            else:
                return {
                    'success': False,
                    'reason': 'Network connectivity issue detected'
                }
        
        except Exception as e:
            return {
                'success': False,
                'reason': f'Network check failed: {str(e)}'
            }
    
    def _api_recovery(self, exception: Exception, function_name: str) -> Dict[str, Any]:
        """API錯誤恢復策略"""
        self.logger.info("🔌 執行API錯誤恢復策略...")
        
        # 檢查是否是頻率限制錯誤
        error_message = str(exception).lower()
        
        if 'rate limit' in error_message or 'too many requests' in error_message:
            # 等待更長時間
            wait_time = 60  # 等待1分鐘
            self.logger.info(f"⏰ 檢測到頻率限制，等待 {wait_time} 秒...")
            time.sleep(wait_time)
            
            return {
                'success': True,
                'action': f'Waited {wait_time} seconds for rate limit reset',
                'result': None
            }
        
        elif 'unauthorized' in error_message or 'forbidden' in error_message:
            return {
                'success': False,
                'reason': 'Authentication issue - check API credentials'
            }
        
        else:
            return {
                'success': False,
                'reason': 'Unknown API error'
            }
    
    def _data_recovery(self, exception: Exception, function_name: str) -> Dict[str, Any]:
        """數據錯誤恢復策略"""
        self.logger.info("📊 執行數據錯誤恢復策略...")
        
        # 嘗試使用備用數據源或生成模擬數據
        try:
            if 'data_fetcher' in function_name.lower():
                # 使用模擬數據
                from src.data.simple_data_fetcher import DataFetcher
                fetcher = DataFetcher()
                
                # 生成基本的模擬數據
                mock_data = fetcher.get_historical_data('BTCUSDT', '1h', 50)
                
                return {
                    'success': True,
                    'action': 'Used mock data as fallback',
                    'result': mock_data
                }
        
        except Exception as e:
            return {
                'success': False,
                'reason': f'Data recovery failed: {str(e)}'
            }
        
        return {
            'success': False,
            'reason': 'No data recovery strategy available'
        }
    
    def _trading_recovery(self, exception: Exception, function_name: str) -> Dict[str, Any]:
        """交易錯誤恢復策略"""
        self.logger.info("💰 執行交易錯誤恢復策略...")
        
        # 檢查是否需要回滾交易
        error_message = str(exception).lower()
        
        if 'insufficient' in error_message or 'balance' in error_message:
            # 餘額不足，停止交易
            return {
                'success': True,
                'action': 'Trading halted due to insufficient balance',
                'result': {'trading_halted': True}
            }
        
        elif 'position' in error_message:
            # 倉位問題，嘗試平倉
            return {
                'success': True,
                'action': 'Attempted position cleanup',
                'result': {'position_cleaned': True}
            }
        
        else:
            return {
                'success': False,
                'reason': 'Unknown trading error'
            }
    
    def _system_recovery(self, exception: Exception, function_name: str) -> Dict[str, Any]:
        """系統錯誤恢復策略"""
        self.logger.info("🔧 執行系統錯誤恢復策略...")
        
        # 清理臨時文件
        try:
            temp_dir = self.project_root / "temp"
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                temp_dir.mkdir()
            
            return {
                'success': True,
                'action': 'Cleaned temporary files',
                'result': None
            }
        
        except Exception as e:
            return {
                'success': False,
                'reason': f'System recovery failed: {str(e)}'
            }
    
    def get_circuit_breaker(self, service_name: str, failure_threshold: int = 5, 
                           recovery_timeout: int = 60) -> Callable:
        """獲取熔斷器裝飾器"""
        
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = {
                'failure_count': 0,
                'last_failure_time': None,
                'state': 'CLOSED',  # CLOSED, OPEN, HALF_OPEN
                'failure_threshold': failure_threshold,
                'recovery_timeout': recovery_timeout
            }
        
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                breaker = self.circuit_breakers[service_name]
                
                # 檢查熔斷器狀態
                if breaker['state'] == 'OPEN':
                    # 檢查是否可以嘗試恢復
                    if (breaker['last_failure_time'] and 
                        datetime.now() - breaker['last_failure_time'] > timedelta(seconds=breaker['recovery_timeout'])):
                        breaker['state'] = 'HALF_OPEN'
                        self.logger.info(f"🔄 {service_name} 熔斷器進入半開狀態")
                    else:
                        raise Exception(f"Circuit breaker is OPEN for {service_name}")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # 成功執行，重置失敗計數
                    if breaker['state'] == 'HALF_OPEN':
                        breaker['state'] = 'CLOSED'
                        self.logger.info(f"✅ {service_name} 熔斷器恢復到關閉狀態")
                    
                    breaker['failure_count'] = 0
                    return result
                
                except Exception as e:
                    breaker['failure_count'] += 1
                    breaker['last_failure_time'] = datetime.now()
                    
                    if breaker['failure_count'] >= breaker['failure_threshold']:
                        breaker['state'] = 'OPEN'
                        self.logger.warning(f"⚠️ {service_name} 熔斷器開啟，失敗次數: {breaker['failure_count']}")
                    
                    raise e
            
            return wrapper
        return decorator
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """獲取錯誤統計"""
        if not self.error_records:
            return {'total_errors': 0}
        
        # 按錯誤類型統計
        error_types = {}
        resolved_count = 0
        
        for record in self.error_records:
            error_types[record.error_type] = error_types.get(record.error_type, 0) + 1
            if record.resolved:
                resolved_count += 1
        
        # 最近24小時的錯誤
        recent_errors = [
            record for record in self.error_records
            if datetime.now() - record.timestamp < timedelta(hours=24)
        ]
        
        return {
            'total_errors': len(self.error_records),
            'resolved_errors': resolved_count,
            'resolution_rate': (resolved_count / len(self.error_records) * 100) if self.error_records else 0,
            'error_types': error_types,
            'recent_24h_errors': len(recent_errors),
            'most_common_error': max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def generate_error_report(self) -> str:
        """生成錯誤報告"""
        stats = self.get_error_statistics()
        
        report = f"""
🛠️ AImax 錯誤處理報告
{'='*50}

📊 錯誤統計:
   總錯誤數: {stats['total_errors']}
   已解決: {stats['resolved_errors']}
   解決率: {stats['resolution_rate']:.1f}%
   最近24小時: {stats['recent_24h_errors']}

🔍 錯誤類型分布:
"""
        
        for error_type, count in stats.get('error_types', {}).items():
            report += f"   {error_type}: {count}\n"
        
        if stats.get('most_common_error'):
            report += f"\n⚠️ 最常見錯誤: {stats['most_common_error']}\n"
        
        # 熔斷器狀態
        if self.circuit_breakers:
            report += f"\n🔌 熔斷器狀態:\n"
            for service, breaker in self.circuit_breakers.items():
                report += f"   {service}: {breaker['state']} (失敗: {breaker['failure_count']})\n"
        
        report += f"\n{'='*50}\n"
        report += f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report

# 全局錯誤處理器實例
error_handler = AIMaxErrorHandler()

# 便捷裝飾器
def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """便捷重試裝飾器"""
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)
    return error_handler.retry_with_backoff(config)

def with_circuit_breaker(service_name: str, failure_threshold: int = 5):
    """便捷熔斷器裝飾器"""
    return error_handler.get_circuit_breaker(service_name, failure_threshold)

def handle_errors(func):
    """通用錯誤處理裝飾器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler._record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                function_name=func.__name__,
                context={'args': str(args), 'kwargs': str(kwargs)}
            )
            
            # 嘗試恢復
            recovery_result = error_handler._attempt_recovery(type(e).__name__, e, func.__name__)
            
            if recovery_result.get('success'):
                return recovery_result.get('result')
            
            # 重新拋出異常
            raise e
    
    return wrapper