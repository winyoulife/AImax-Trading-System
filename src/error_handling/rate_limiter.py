#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax API頻率限制處理模塊 - 任務9實現
處理API限制、頻率控制和智能請求調度
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import threading
from collections import deque, defaultdict
from functools import wraps
import hashlib

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class RateLimiter:
    """API頻率限制器"""
    
    def __init__(self):
        self.request_history = defaultdict(deque)  # 每個API的請求歷史
        self.rate_limits = {}  # API頻率限制配置
        self.lock = threading.Lock()
        
        # 默認頻率限制配置
        self.default_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'requests_per_day': 10000,
            'burst_limit': 10  # 突發請求限制
        }
        
        # 動態調整參數
        self.adaptive_config = {
            'enabled': True,
            'success_rate_threshold': 0.95,
            'adjustment_factor': 0.8,
            'recovery_factor': 1.1
        }
        
        self.setup_default_limits()
    
    def setup_default_limits(self):
        """設置默認API限制"""
        # GitHub API限制
        self.set_rate_limit('github_api', {
            'requests_per_minute': 60,
            'requests_per_hour': 5000,
            'requests_per_day': 50000
        })
        
        # MAX交易所API限制
        self.set_rate_limit('max_api', {
            'requests_per_minute': 100,
            'requests_per_hour': 6000,
            'requests_per_day': 100000
        })
        
        # Telegram API限制
        self.set_rate_limit('telegram_api', {
            'requests_per_minute': 30,
            'requests_per_hour': 1800,
            'requests_per_day': 43200
        })
    
    def set_rate_limit(self, api_name: str, limits: Dict[str, int]):
        """設置API頻率限制"""
        self.rate_limits[api_name] = {
            **self.default_limits,
            **limits,
            'current_usage': {
                'minute': 0,
                'hour': 0,
                'day': 0
            },
            'last_reset': {
                'minute': datetime.now(),
                'hour': datetime.now(),
                'day': datetime.now()
            },
            'success_count': 0,
            'total_count': 0
        }
        logger.info(f"📊 設置 {api_name} 頻率限制: {limits}")
    
    def check_rate_limit(self, api_name: str) -> Dict[str, Any]:
        """檢查API頻率限制狀態"""
        with self.lock:
            if api_name not in self.rate_limits:
                self.set_rate_limit(api_name, {})
            
            limits = self.rate_limits[api_name]
            now = datetime.now()
            
            # 重置計數器
            self._reset_counters_if_needed(api_name, now)
            
            # 檢查各時間窗口的限制
            checks = {
                'minute': limits['current_usage']['minute'] < limits['requests_per_minute'],
                'hour': limits['current_usage']['hour'] < limits['requests_per_hour'],
                'day': limits['current_usage']['day'] < limits['requests_per_day']
            }
            
            allowed = all(checks.values())
            
            # 計算等待時間
            wait_time = 0
            if not allowed:
                wait_times = []
                
                if not checks['minute']:
                    next_minute = limits['last_reset']['minute'] + timedelta(minutes=1)
                    wait_times.append((next_minute - now).total_seconds())
                
                if not checks['hour']:
                    next_hour = limits['last_reset']['hour'] + timedelta(hours=1)
                    wait_times.append((next_hour - now).total_seconds())
                
                if not checks['day']:
                    next_day = limits['last_reset']['day'] + timedelta(days=1)
                    wait_times.append((next_day - now).total_seconds())
                
                wait_time = min(wait_times) if wait_times else 0
            
            return {
                'allowed': allowed,
                'wait_time': max(0, wait_time),
                'current_usage': limits['current_usage'].copy(),
                'limits': {
                    'minute': limits['requests_per_minute'],
                    'hour': limits['requests_per_hour'],
                    'day': limits['requests_per_day']
                },
                'success_rate': self._calculate_success_rate(api_name)
            }
    
    def _reset_counters_if_needed(self, api_name: str, now: datetime):
        """重置計數器（如果需要）"""
        limits = self.rate_limits[api_name]
        
        # 重置分鐘計數器
        if now - limits['last_reset']['minute'] >= timedelta(minutes=1):
            limits['current_usage']['minute'] = 0
            limits['last_reset']['minute'] = now
        
        # 重置小時計數器
        if now - limits['last_reset']['hour'] >= timedelta(hours=1):
            limits['current_usage']['hour'] = 0
            limits['last_reset']['hour'] = now
        
        # 重置日計數器
        if now - limits['last_reset']['day'] >= timedelta(days=1):
            limits['current_usage']['day'] = 0
            limits['last_reset']['day'] = now
    
    def record_request(self, api_name: str, success: bool = True):
        """記錄API請求"""
        with self.lock:
            if api_name not in self.rate_limits:
                self.set_rate_limit(api_name, {})
            
            limits = self.rate_limits[api_name]
            
            # 增加使用計數
            limits['current_usage']['minute'] += 1
            limits['current_usage']['hour'] += 1
            limits['current_usage']['day'] += 1
            
            # 記錄成功率
            limits['total_count'] += 1
            if success:
                limits['success_count'] += 1
            
            # 記錄請求歷史
            self.request_history[api_name].append({
                'timestamp': datetime.now(),
                'success': success
            })
            
            # 保持歷史記錄在合理範圍內
            if len(self.request_history[api_name]) > 1000:
                self.request_history[api_name].popleft()
            
            # 動態調整頻率限制
            if self.adaptive_config['enabled']:
                self._adjust_rate_limits(api_name)
    
    def _calculate_success_rate(self, api_name: str) -> float:
        """計算API成功率"""
        if api_name not in self.rate_limits:
            return 1.0
        
        limits = self.rate_limits[api_name]
        if limits['total_count'] == 0:
            return 1.0
        
        return limits['success_count'] / limits['total_count']
    
    def _adjust_rate_limits(self, api_name: str):
        """動態調整頻率限制"""
        success_rate = self._calculate_success_rate(api_name)
        limits = self.rate_limits[api_name]
        
        # 如果成功率低於閾值，降低頻率限制
        if success_rate < self.adaptive_config['success_rate_threshold']:
            adjustment = self.adaptive_config['adjustment_factor']
            
            limits['requests_per_minute'] = int(limits['requests_per_minute'] * adjustment)
            limits['requests_per_hour'] = int(limits['requests_per_hour'] * adjustment)
            
            logger.warning(f"⚠️ {api_name} 成功率低 ({success_rate:.2%})，降低頻率限制")
        
        # 如果成功率高，逐漸恢復頻率限制
        elif success_rate > 0.98 and limits['total_count'] > 100:
            recovery = self.adaptive_config['recovery_factor']
            original_limits = self.default_limits
            
            current_minute = limits['requests_per_minute']
            target_minute = original_limits.get('requests_per_minute', 60)
            
            if current_minute < target_minute:
                new_limit = min(int(current_minute * recovery), target_minute)
                limits['requests_per_minute'] = new_limit
                
                logger.info(f"✅ {api_name} 成功率高 ({success_rate:.2%})，恢復頻率限制")
    
    def wait_if_needed(self, api_name: str) -> float:
        """如果需要，等待直到可以發送請求"""
        check_result = self.check_rate_limit(api_name)
        
        if not check_result['allowed']:
            wait_time = check_result['wait_time']
            
            if wait_time > 0:
                logger.info(f"⏰ {api_name} 頻率限制，等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)
                return wait_time
        
        return 0.0
    
    def get_api_stats(self, api_name: str) -> Dict[str, Any]:
        """獲取API統計信息"""
        if api_name not in self.rate_limits:
            return {'error': 'API not found'}
        
        limits = self.rate_limits[api_name]
        
        return {
            'api_name': api_name,
            'current_usage': limits['current_usage'].copy(),
            'limits': {
                'minute': limits['requests_per_minute'],
                'hour': limits['requests_per_hour'],
                'day': limits['requests_per_day']
            },
            'success_rate': self._calculate_success_rate(api_name),
            'total_requests': limits['total_count'],
            'successful_requests': limits['success_count'],
            'usage_percentage': {
                'minute': (limits['current_usage']['minute'] / limits['requests_per_minute'] * 100),
                'hour': (limits['current_usage']['hour'] / limits['requests_per_hour'] * 100),
                'day': (limits['current_usage']['day'] / limits['requests_per_day'] * 100)
            }
        }

class SmartRequestScheduler:
    """智能請求調度器"""
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.request_queue = defaultdict(deque)
        self.processing = defaultdict(bool)
        self.scheduler_threads = {}
        
    def schedule_request(self, api_name: str, request_func: Callable, 
                        priority: int = 1, **kwargs) -> str:
        """調度API請求"""
        request_id = self._generate_request_id(api_name, request_func.__name__)
        
        request_item = {
            'id': request_id,
            'api_name': api_name,
            'function': request_func,
            'kwargs': kwargs,
            'priority': priority,
            'created_at': datetime.now(),
            'attempts': 0,
            'max_attempts': 3
        }
        
        # 按優先級插入隊列
        self._insert_by_priority(api_name, request_item)
        
        # 啟動處理線程（如果尚未啟動）
        if not self.processing[api_name]:
            self._start_processor(api_name)
        
        logger.info(f"📋 調度請求: {request_id} (優先級: {priority})")
        return request_id
    
    def _generate_request_id(self, api_name: str, func_name: str) -> str:
        """生成請求ID"""
        timestamp = datetime.now().isoformat()
        content = f"{api_name}_{func_name}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _insert_by_priority(self, api_name: str, request_item: Dict):
        """按優先級插入請求到隊列"""
        queue = self.request_queue[api_name]
        
        # 找到合適的插入位置
        insert_index = len(queue)
        for i, item in enumerate(queue):
            if request_item['priority'] > item['priority']:
                insert_index = i
                break
        
        # 插入到指定位置
        queue.insert(insert_index, request_item)
    
    def _start_processor(self, api_name: str):
        """啟動請求處理器"""
        if self.processing[api_name]:
            return
        
        self.processing[api_name] = True
        thread = threading.Thread(
            target=self._process_requests,
            args=(api_name,),
            daemon=True
        )
        thread.start()
        self.scheduler_threads[api_name] = thread
        
        logger.info(f"🚀 啟動 {api_name} 請求處理器")
    
    def _process_requests(self, api_name: str):
        """處理請求隊列"""
        while self.processing[api_name] or self.request_queue[api_name]:
            try:
                if not self.request_queue[api_name]:
                    time.sleep(0.1)
                    continue
                
                request_item = self.request_queue[api_name].popleft()
                
                # 檢查頻率限制
                wait_time = self.rate_limiter.wait_if_needed(api_name)
                
                # 執行請求
                success = self._execute_request(request_item)
                
                # 記錄請求結果
                self.rate_limiter.record_request(api_name, success)
                
                if not success and request_item['attempts'] < request_item['max_attempts']:
                    # 重新調度失敗的請求
                    request_item['attempts'] += 1
                    self._insert_by_priority(api_name, request_item)
                    logger.warning(f"🔄 重新調度失敗請求: {request_item['id']} (嘗試 {request_item['attempts']})")
                
            except Exception as e:
                logger.error(f"❌ 請求處理錯誤: {e}")
                time.sleep(1)
        
        self.processing[api_name] = False
        logger.info(f"🛑 {api_name} 請求處理器已停止")
    
    def _execute_request(self, request_item: Dict) -> bool:
        """執行單個請求"""
        try:
            logger.info(f"⚡ 執行請求: {request_item['id']}")
            
            result = request_item['function'](**request_item['kwargs'])
            
            logger.info(f"✅ 請求成功: {request_item['id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 請求失敗: {request_item['id']} - {str(e)}")
            return False
    
    def get_queue_status(self, api_name: str) -> Dict[str, Any]:
        """獲取隊列狀態"""
        queue = self.request_queue[api_name]
        
        return {
            'api_name': api_name,
            'queue_length': len(queue),
            'processing': self.processing[api_name],
            'pending_requests': [
                {
                    'id': item['id'],
                    'priority': item['priority'],
                    'attempts': item['attempts'],
                    'created_at': item['created_at'].isoformat()
                }
                for item in list(queue)[:10]  # 只顯示前10個
            ]
        }

# 頻率限制裝飾器
def rate_limited(api_name: str, priority: int = 1):
    """頻率限制裝飾器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 檢查並等待頻率限制
            wait_time = rate_limiter.wait_if_needed(api_name)
            
            try:
                result = func(*args, **kwargs)
                rate_limiter.record_request(api_name, success=True)
                return result
            except Exception as e:
                rate_limiter.record_request(api_name, success=False)
                raise e
        
        return wrapper
    return decorator

# 全局實例
rate_limiter = RateLimiter()
request_scheduler = SmartRequestScheduler(rate_limiter)

# 便捷函數
def check_api_limit(api_name: str) -> bool:
    """檢查API是否可用"""
    result = rate_limiter.check_rate_limit(api_name)
    return result['allowed']

def get_api_usage(api_name: str) -> Dict[str, Any]:
    """獲取API使用情況"""
    return rate_limiter.get_api_stats(api_name)