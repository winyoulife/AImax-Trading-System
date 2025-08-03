#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統性能優化器 - 任務8.2實現
優化多線程並發處理性能和系統資源管理
"""

import sys
import os
import asyncio
import threading
import multiprocessing
import psutil
import gc
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, PriorityQueue
import weakref
import json
from collections import defaultdict, deque
try:
    import resource
    RESOURCE_AVAILABLE = True
except ImportError:
    RESOURCE_AVAILABLE = False

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_available: float = 0.0
    thread_count: int = 0
    process_count: int = 0
    io_read_bytes: int = 0
    io_write_bytes: int = 0
    network_sent: int = 0
    network_recv: int = 0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    response_times: List[float] = field(default_factory=list)
    throughput: float = 0.0
    error_rate: float = 0.0

@dataclass
class ResourceLimits:
    """資源限制配置"""
    max_cpu_usage: float = 80.0  # 最大CPU使用率 (%)
    max_memory_usage: float = 70.0  # 最大內存使用率 (%)
    max_threads: int = 50  # 最大線程數
    max_processes: int = 8  # 最大進程數
    max_queue_size: int = 1000  # 最大隊列大小
    gc_threshold: float = 60.0  # 垃圾回收觸發閾值 (%)
    api_rate_limit: int = 100  # API調用頻率限制 (次/分鐘)

class ThreadPoolManager:
    """線程池管理器"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.pools: Dict[str, ThreadPoolExecutor] = {}
        self.pool_stats: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
    def get_pool(self, pool_name: str, max_workers: int = None) -> ThreadPoolExecutor:
        """獲取或創建線程池"""
        with self.lock:
            if pool_name not in self.pools:
                workers = max_workers or self.max_workers
                self.pools[pool_name] = ThreadPoolExecutor(
                    max_workers=workers,
                    thread_name_prefix=f"{pool_name}_"
                )
                self.pool_stats[pool_name] = {
                    'created_at': datetime.now(),
                    'max_workers': workers,
                    'submitted_tasks': 0,
                    'completed_tasks': 0,
                    'failed_tasks': 0,
                    'avg_execution_time': 0.0
                }
                logger.info(f"✅ 創建線程池 {pool_name}: {workers} workers")
            
            return self.pools[pool_name]
    
    def submit_task(self, pool_name: str, func: Callable, *args, **kwargs):
        """提交任務到指定線程池"""
        pool = self.get_pool(pool_name)
        
        def wrapped_func(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # 更新統計
                with self.lock:
                    stats = self.pool_stats[pool_name]
                    stats['completed_tasks'] += 1
                    stats['avg_execution_time'] = (
                        (stats['avg_execution_time'] * (stats['completed_tasks'] - 1) + execution_time) /
                        stats['completed_tasks']
                    )
                
                return result
                
            except Exception as e:
                with self.lock:
                    self.pool_stats[pool_name]['failed_tasks'] += 1
                logger.error(f"❌ 線程池 {pool_name} 任務執行失敗: {e}")
                raise
        
        with self.lock:
            self.pool_stats[pool_name]['submitted_tasks'] += 1
        
        return pool.submit(wrapped_func, *args, **kwargs)
    
    def get_pool_stats(self) -> Dict[str, Dict[str, Any]]:
        """獲取線程池統計信息"""
        with self.lock:
            return dict(self.pool_stats)
    
    def shutdown_all(self, wait: bool = True):
        """關閉所有線程池"""
        with self.lock:
            for pool_name, pool in self.pools.items():
                logger.info(f"🔄 關閉線程池 {pool_name}")
                pool.shutdown(wait=wait)
            self.pools.clear()
            self.pool_stats.clear()

class MemoryManager:
    """內存管理器"""
    
    def __init__(self, gc_threshold: float = 60.0):
        self.gc_threshold = gc_threshold
        self.memory_stats = deque(maxlen=100)  # 保留最近100次記錄
        self.weak_refs: List[weakref.ref] = []
        self.cache_registry: Dict[str, Any] = {}
        
    def monitor_memory(self) -> Dict[str, Any]:
        """監控內存使用情況"""
        try:
            # 獲取系統內存信息
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            memory_info = {
                'timestamp': datetime.now(),
                'system_total': memory.total,
                'system_available': memory.available,
                'system_used': memory.used,
                'system_percent': memory.percent,
                'process_rss': process_memory.rss,
                'process_vms': process_memory.vms,
                'process_percent': process.memory_percent(),
                'gc_stats': {
                    gen: gc.get_count()[gen] for gen in range(3)
                }
            }
            
            self.memory_stats.append(memory_info)
            
            # 檢查是否需要垃圾回收
            if memory.percent > self.gc_threshold:
                self.force_garbage_collection()
            
            return memory_info
            
        except Exception as e:
            logger.error(f"❌ 內存監控失敗: {e}")
            return {}
    
    def force_garbage_collection(self) -> Dict[str, int]:
        """強制垃圾回收"""
        try:
            logger.info("🗑️ 執行強制垃圾回收")
            
            # 清理弱引用
            self.cleanup_weak_refs()
            
            # 執行垃圾回收
            collected = {}
            for generation in range(3):
                collected[f'gen_{generation}'] = gc.collect(generation)
            
            # 清理緩存
            self.cleanup_caches()
            
            logger.info(f"✅ 垃圾回收完成: {collected}")
            return collected
            
        except Exception as e:
            logger.error(f"❌ 垃圾回收失敗: {e}")
            return {}
    
    def cleanup_weak_refs(self):
        """清理弱引用"""
        try:
            alive_refs = []
            for ref in self.weak_refs:
                if ref() is not None:
                    alive_refs.append(ref)
            
            cleaned = len(self.weak_refs) - len(alive_refs)
            self.weak_refs = alive_refs
            
            if cleaned > 0:
                logger.info(f"🧹 清理了 {cleaned} 個弱引用")
                
        except Exception as e:
            logger.error(f"❌ 弱引用清理失敗: {e}")
    
    def cleanup_caches(self):
        """清理緩存"""
        try:
            cleaned_count = 0
            for cache_name in list(self.cache_registry.keys()):
                cache = self.cache_registry[cache_name]
                if hasattr(cache, 'clear'):
                    cache.clear()
                    cleaned_count += 1
                elif isinstance(cache, dict):
                    cache.clear()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 清理了 {cleaned_count} 個緩存")
                
        except Exception as e:
            logger.error(f"❌ 緩存清理失敗: {e}")
    
    def register_cache(self, name: str, cache_obj: Any):
        """註冊緩存對象"""
        self.cache_registry[name] = cache_obj
        logger.info(f"📝 註冊緩存: {name}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """獲取內存統計信息"""
        if not self.memory_stats:
            return {}
        
        recent_stats = list(self.memory_stats)[-10:]  # 最近10次記錄
        
        return {
            'current': recent_stats[-1] if recent_stats else {},
            'avg_system_percent': sum(s['system_percent'] for s in recent_stats) / len(recent_stats),
            'avg_process_percent': sum(s['process_percent'] for s in recent_stats) / len(recent_stats),
            'peak_system_percent': max(s['system_percent'] for s in recent_stats),
            'peak_process_percent': max(s['process_percent'] for s in recent_stats),
            'total_records': len(self.memory_stats)
        }

class APIRateLimiter:
    """API頻率限制器"""
    
    def __init__(self, rate_limit: int = 100, time_window: int = 60):
        self.rate_limit = rate_limit  # 每分鐘最大請求數
        self.time_window = time_window  # 時間窗口（秒）
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.lock = threading.Lock()
        
    def can_make_request(self, api_key: str = "default") -> bool:
        """檢查是否可以發起請求"""
        with self.lock:
            now = time.time()
            requests = self.requests[api_key]
            
            # 清理過期請求
            while requests and requests[0] < now - self.time_window:
                requests.popleft()
            
            # 檢查是否超過限制
            return len(requests) < self.rate_limit
    
    def make_request(self, api_key: str = "default") -> bool:
        """記錄請求"""
        with self.lock:
            if self.can_make_request(api_key):
                self.requests[api_key].append(time.time())
                return True
            return False
    
    def wait_for_slot(self, api_key: str = "default", timeout: float = 30.0) -> bool:
        """等待可用的請求槽位"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.can_make_request(api_key):
                return self.make_request(api_key)
            
            # 計算等待時間
            with self.lock:
                requests = self.requests[api_key]
                if requests:
                    oldest_request = requests[0]
                    wait_time = max(0, oldest_request + self.time_window - time.time())
                    time.sleep(min(wait_time, 1.0))
                else:
                    time.sleep(0.1)
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取限流統計"""
        with self.lock:
            stats = {}
            for api_key, requests in self.requests.items():
                now = time.time()
                recent_requests = [r for r in requests if r > now - self.time_window]
                
                stats[api_key] = {
                    'current_requests': len(recent_requests),
                    'rate_limit': self.rate_limit,
                    'utilization': len(recent_requests) / self.rate_limit,
                    'time_to_reset': max(0, recent_requests[0] + self.time_window - now) if recent_requests else 0
                }
            
            return stats

class ResourceMonitor:
    """資源監控器"""
    
    def __init__(self, limits: ResourceLimits = None):
        self.limits = limits or ResourceLimits()
        self.metrics_history = deque(maxlen=1000)
        self.alerts: List[Dict[str, Any]] = []
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: float = 5.0):
        """開始資源監控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"🔍 開始資源監控 (間隔: {interval}秒)")
    
    def stop_monitoring(self):
        """停止資源監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("⏹️ 停止資源監控")
    
    def _monitor_loop(self, interval: float):
        """監控循環"""
        while self.monitoring:
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                self.check_resource_limits(metrics)
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 資源監控錯誤: {e}")
                time.sleep(interval)
    
    def collect_metrics(self) -> PerformanceMetrics:
        """收集性能指標"""
        try:
            # 系統資源
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # 進程信息
            process = psutil.Process()
            process_info = process.as_dict([
                'num_threads', 'memory_info', 'io_counters', 'connections'
            ])
            
            # 網絡信息
            net_io = psutil.net_io_counters()
            
            # 垃圾回收統計
            gc_stats = {i: gc.get_count()[i] for i in range(3)}
            
            metrics = PerformanceMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                memory_available=memory.available,
                thread_count=process_info.get('num_threads', 0),
                process_count=len(psutil.pids()),
                io_read_bytes=process_info.get('io_counters', {}).get('read_bytes', 0),
                io_write_bytes=process_info.get('io_counters', {}).get('write_bytes', 0),
                network_sent=net_io.bytes_sent if net_io else 0,
                network_recv=net_io.bytes_recv if net_io else 0,
                gc_collections=gc_stats
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ 指標收集失敗: {e}")
            return PerformanceMetrics()
    
    def check_resource_limits(self, metrics: PerformanceMetrics):
        """檢查資源限制"""
        alerts = []
        
        # CPU使用率檢查
        if metrics.cpu_usage > self.limits.max_cpu_usage:
            alerts.append({
                'type': 'cpu_high',
                'message': f'CPU使用率過高: {metrics.cpu_usage:.1f}% > {self.limits.max_cpu_usage}%',
                'severity': 'warning',
                'timestamp': metrics.timestamp
            })
        
        # 內存使用率檢查
        if metrics.memory_usage > self.limits.max_memory_usage:
            alerts.append({
                'type': 'memory_high',
                'message': f'內存使用率過高: {metrics.memory_usage:.1f}% > {self.limits.max_memory_usage}%',
                'severity': 'warning',
                'timestamp': metrics.timestamp
            })
        
        # 線程數檢查
        if metrics.thread_count > self.limits.max_threads:
            alerts.append({
                'type': 'thread_high',
                'message': f'線程數過多: {metrics.thread_count} > {self.limits.max_threads}',
                'severity': 'error',
                'timestamp': metrics.timestamp
            })
        
        # 記錄警報
        for alert in alerts:
            self.alerts.append(alert)
            logger.warning(f"⚠️ 資源警報: {alert['message']}")
        
        # 保持警報列表大小
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-50:]
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """獲取當前指標"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = list(self.metrics_history)[-60:]  # 最近60次記錄
        
        return {
            'avg_cpu_usage': sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
            'avg_memory_usage': sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
            'avg_thread_count': sum(m.thread_count for m in recent_metrics) / len(recent_metrics),
            'peak_cpu_usage': max(m.cpu_usage for m in recent_metrics),
            'peak_memory_usage': max(m.memory_usage for m in recent_metrics),
            'peak_thread_count': max(m.thread_count for m in recent_metrics),
            'total_alerts': len(self.alerts),
            'recent_alerts': len([a for a in self.alerts if a['timestamp'] > datetime.now() - timedelta(minutes=10)])
        }

class SystemPerformanceOptimizer:
    """系統性能優化器主類"""
    
    def __init__(self, limits: ResourceLimits = None):
        self.limits = limits or ResourceLimits()
        self.thread_pool_manager = ThreadPoolManager()
        self.memory_manager = MemoryManager(self.limits.gc_threshold)
        self.api_rate_limiter = APIRateLimiter(self.limits.api_rate_limit)
        self.resource_monitor = ResourceMonitor(self.limits)
        
        self.optimization_stats = {
            'start_time': datetime.now(),
            'optimizations_applied': 0,
            'performance_improvements': [],
            'resource_savings': {}
        }
        
        logger.info("🚀 系統性能優化器初始化完成")
    
    def start_optimization(self):
        """開始性能優化"""
        try:
            logger.info("🔧 開始系統性能優化")
            
            # 啟動資源監控
            self.resource_monitor.start_monitoring(interval=5.0)
            
            # 應用初始優化
            self.apply_initial_optimizations()
            
            # 註冊緩存
            self.register_system_caches()
            
            logger.info("✅ 系統性能優化啟動完成")
            
        except Exception as e:
            logger.error(f"❌ 性能優化啟動失敗: {e}")
    
    def stop_optimization(self):
        """停止性能優化"""
        try:
            logger.info("⏹️ 停止系統性能優化")
            
            # 停止資源監控
            self.resource_monitor.stop_monitoring()
            
            # 關閉線程池
            self.thread_pool_manager.shutdown_all()
            
            # 最終垃圾回收
            self.memory_manager.force_garbage_collection()
            
            logger.info("✅ 系統性能優化停止完成")
            
        except Exception as e:
            logger.error(f"❌ 性能優化停止失敗: {e}")
    
    def apply_initial_optimizations(self):
        """應用初始優化"""
        try:
            optimizations = []
            
            # 1. 設置垃圾回收閾值
            original_thresholds = gc.get_threshold()
            new_thresholds = (700, 10, 10)  # 更積極的垃圾回收
            gc.set_threshold(*new_thresholds)
            optimizations.append(f"垃圾回收閾值: {original_thresholds} → {new_thresholds}")
            
            # 2. 設置資源限制 (僅在支持的平台上)
            if RESOURCE_AVAILABLE:
                try:
                    # 設置最大文件描述符數
                    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                    new_soft = min(hard, 4096)
                    resource.setrlimit(resource.RLIMIT_NOFILE, (new_soft, hard))
                    optimizations.append(f"文件描述符限制: {soft} → {new_soft}")
                except:
                    optimizations.append("資源限制設置跳過 (平台不支持)")
            else:
                optimizations.append("資源限制設置跳過 (Windows平台)")
            
            # 3. 優化線程池配置
            cpu_count = os.cpu_count() or 1
            optimal_threads = min(32, cpu_count * 2)
            self.thread_pool_manager.max_workers = optimal_threads
            optimizations.append(f"線程池大小: {optimal_threads}")
            
            # 4. 啟用內存監控
            self.memory_manager.monitor_memory()
            optimizations.append("內存監控已啟用")
            
            self.optimization_stats['optimizations_applied'] = len(optimizations)
            self.optimization_stats['performance_improvements'] = optimizations
            
            logger.info(f"✅ 應用了 {len(optimizations)} 項初始優化")
            for opt in optimizations:
                logger.info(f"   • {opt}")
                
        except Exception as e:
            logger.error(f"❌ 初始優化應用失敗: {e}")
    
    def register_system_caches(self):
        """註冊系統緩存"""
        try:
            # 這裡可以註冊各種系統緩存
            # 例如：數據緩存、AI模型緩存、API響應緩存等
            
            caches = [
                "market_data_cache",
                "ai_prediction_cache", 
                "technical_indicator_cache",
                "api_response_cache"
            ]
            
            for cache_name in caches:
                # 創建模擬緩存對象
                cache_obj = {}
                self.memory_manager.register_cache(cache_name, cache_obj)
            
            logger.info(f"✅ 註冊了 {len(caches)} 個系統緩存")
            
        except Exception as e:
            logger.error(f"❌ 系統緩存註冊失敗: {e}")
    
    def optimize_for_trading_pairs(self, pair_count: int) -> Dict[str, Any]:
        """針對交易對數量優化系統"""
        try:
            logger.info(f"🎯 針對 {pair_count} 個交易對優化系統")
            
            optimizations = {}
            
            # 1. 動態調整線程池大小
            optimal_threads = min(50, max(8, pair_count * 2))
            self.thread_pool_manager.max_workers = optimal_threads
            optimizations['thread_pool_size'] = optimal_threads
            
            # 2. 調整API限流
            optimal_rate_limit = min(200, max(50, pair_count * 20))
            self.api_rate_limiter.rate_limit = optimal_rate_limit
            optimizations['api_rate_limit'] = optimal_rate_limit
            
            # 3. 調整內存管理
            if pair_count > 10:
                # 更頻繁的垃圾回收
                gc.set_threshold(500, 8, 8)
                optimizations['gc_threshold'] = 'aggressive'
            else:
                # 標準垃圾回收
                gc.set_threshold(700, 10, 10)
                optimizations['gc_threshold'] = 'standard'
            
            # 4. 調整資源限制
            self.limits.max_threads = optimal_threads + 10
            self.limits.max_memory_usage = min(80.0, 50.0 + pair_count * 2)
            optimizations['memory_limit'] = self.limits.max_memory_usage
            
            logger.info(f"✅ 交易對優化完成: {optimizations}")
            return optimizations
            
        except Exception as e:
            logger.error(f"❌ 交易對優化失敗: {e}")
            return {}
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """獲取優化報告"""
        try:
            current_metrics = self.resource_monitor.get_current_metrics()
            metrics_summary = self.resource_monitor.get_metrics_summary()
            memory_stats = self.memory_manager.get_memory_stats()
            thread_pool_stats = self.thread_pool_manager.get_pool_stats()
            api_stats = self.api_rate_limiter.get_stats()
            
            report = {
                'optimization_info': {
                    'start_time': self.optimization_stats['start_time'].isoformat(),
                    'running_time': (datetime.now() - self.optimization_stats['start_time']).total_seconds(),
                    'optimizations_applied': self.optimization_stats['optimizations_applied'],
                    'improvements': self.optimization_stats['performance_improvements']
                },
                'current_performance': {
                    'cpu_usage': current_metrics.cpu_usage if current_metrics else 0,
                    'memory_usage': current_metrics.memory_usage if current_metrics else 0,
                    'thread_count': current_metrics.thread_count if current_metrics else 0,
                    'timestamp': current_metrics.timestamp.isoformat() if current_metrics else None
                },
                'performance_summary': metrics_summary,
                'memory_management': memory_stats,
                'thread_pools': thread_pool_stats,
                'api_rate_limiting': api_stats,
                'resource_limits': {
                    'max_cpu_usage': self.limits.max_cpu_usage,
                    'max_memory_usage': self.limits.max_memory_usage,
                    'max_threads': self.limits.max_threads,
                    'api_rate_limit': self.limits.api_rate_limit
                },
                'alerts': self.resource_monitor.alerts[-10:] if self.resource_monitor.alerts else []
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 優化報告生成失敗: {e}")
            return {'error': str(e)}

# 全局優化器實例
_global_optimizer: Optional[SystemPerformanceOptimizer] = None

def get_performance_optimizer() -> SystemPerformanceOptimizer:
    """獲取全局性能優化器實例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = SystemPerformanceOptimizer()
    return _global_optimizer

def start_system_optimization():
    """啟動系統優化"""
    optimizer = get_performance_optimizer()
    optimizer.start_optimization()
    return optimizer

def stop_system_optimization():
    """停止系統優化"""
    global _global_optimizer
    if _global_optimizer:
        _global_optimizer.stop_optimization()
        _global_optimizer = None

# 測試代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 測試性能優化器
    print("🧪 測試系統性能優化器...")
    
    optimizer = SystemPerformanceOptimizer()
    
    try:
        # 啟動優化
        optimizer.start_optimization()
        
        # 針對5個交易對優化
        pair_optimizations = optimizer.optimize_for_trading_pairs(5)
        print(f"交易對優化: {pair_optimizations}")
        
        # 等待一段時間收集指標
        time.sleep(10)
        
        # 獲取優化報告
        report = optimizer.get_optimization_report()
        print(f"優化報告: {json.dumps(report, indent=2, default=str)}")
        
    finally:
        # 停止優化
        optimizer.stop_optimization()
    
    print("✅ 性能優化器測試完成")