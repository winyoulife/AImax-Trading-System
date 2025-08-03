#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 數據緩存優化器 - 實現數據緩存和並行處理
"""

import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
from collections import OrderedDict
import sqlite3
import pickle

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """緩存條目"""
    key: str
    data: Any
    timestamp: datetime
    access_count: int
    size_bytes: int

class DataCacheOptimizer:
    """數據緩存優化器 - 專為AImax系統設計"""
    
    def __init__(self, config_path: str = "AImax/config/cache.json"):
        """
        初始化數據緩存優化器
        
        Args:
            config_path: 緩存配置文件路徑
        """
        self.config = self._load_config(config_path)
        
        # 內存緩存
        self.memory_cache = OrderedDict()
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size': 0
        }
        
        # 持久化緩存
        self.db_path = self.config.get('db_path', 'AImax/data/cache/data_cache.db')
        self._init_persistent_cache()
        
        # 並行處理配置
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('max_workers', 4)
        )
        
        # 緩存清理線程
        self.cleanup_thread = None
        self.cleanup_active = False
        
        logger.info("🎯 數據緩存優化器初始化完成")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入緩存配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✅ 載入緩存配置: {config_path}")
            return config
        except Exception as e:
            logger.warning(f"⚠️ 載入配置失敗，使用默認配置: {e}")
            return {
                'max_memory_cache_size': 100,  # 最大緩存條目數
                'max_memory_size_mb': 500,     # 最大內存使用MB
                'cache_ttl_seconds': 3600,     # 緩存過期時間1小時
                'cleanup_interval_seconds': 300,  # 清理間隔5分鐘
                'max_workers': 4,              # 並行工作線程數
                'enable_persistent_cache': True,
                'db_path': 'AImax/data/cache/data_cache.db'
            }
    
    def _init_persistent_cache(self):
        """初始化持久化緩存"""
        try:
            if not self.config.get('enable_persistent_cache', True):
                return
            
            # 確保目錄存在
            import os
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # 創建數據庫表
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key TEXT PRIMARY KEY,
                        data BLOB,
                        timestamp TEXT,
                        access_count INTEGER,
                        size_bytes INTEGER
                    )
                ''')
                conn.commit()
            
            logger.info(f"✅ 持久化緩存初始化完成: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ 持久化緩存初始化失敗: {e}")
    
    def start_cleanup_service(self):
        """啟動緩存清理服務"""
        try:
            if self.cleanup_active:
                logger.warning("⚠️ 緩存清理服務已在運行")
                return
            
            self.cleanup_active = True
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True
            )
            self.cleanup_thread.start()
            
            logger.info("🧹 緩存清理服務已啟動")
            
        except Exception as e:
            logger.error(f"❌ 啟動緩存清理服務失敗: {e}")
    
    def stop_cleanup_service(self):
        """停止緩存清理服務"""
        try:
            self.cleanup_active = False
            if self.cleanup_thread:
                self.cleanup_thread.join(timeout=5.0)
            
            logger.info("🧹 緩存清理服務已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止緩存清理服務失敗: {e}")
    
    def _cleanup_loop(self):
        """緩存清理循環"""
        try:
            interval = self.config.get('cleanup_interval_seconds', 300)
            
            while self.cleanup_active:
                self._cleanup_expired_cache()
                self._cleanup_oversized_cache()
                time.sleep(interval)
                
        except Exception as e:
            logger.error(f"❌ 緩存清理循環異常: {e}")
    
    def _cleanup_expired_cache(self):
        """清理過期緩存"""
        try:
            ttl_seconds = self.config.get('cache_ttl_seconds', 3600)
            cutoff_time = datetime.now() - timedelta(seconds=ttl_seconds)
            
            # 清理內存緩存
            expired_keys = []
            for key, entry in self.memory_cache.items():
                if entry.timestamp < cutoff_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_cache[key]
                self.cache_stats['evictions'] += 1
            
            if expired_keys:
                logger.info(f"🧹 清理過期內存緩存: {len(expired_keys)} 項")
            
            # 清理持久化緩存
            if self.config.get('enable_persistent_cache', True):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        'DELETE FROM cache_entries WHERE timestamp < ?',
                        (cutoff_time.isoformat(),)
                    )
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"🧹 清理過期持久化緩存: {deleted_count} 項")
            
        except Exception as e:
            logger.error(f"❌ 清理過期緩存失敗: {e}")
    
    def _cleanup_oversized_cache(self):
        """清理超大緩存"""
        try:
            max_size = self.config.get('max_memory_cache_size', 100)
            
            # 如果緩存超過限制，移除最少使用的項目
            while len(self.memory_cache) > max_size:
                # OrderedDict的第一個項目是最舊的
                oldest_key = next(iter(self.memory_cache))
                del self.memory_cache[oldest_key]
                self.cache_stats['evictions'] += 1
            
            # 檢查內存使用
            total_size_mb = sum(entry.size_bytes for entry in self.memory_cache.values()) / 1024 / 1024
            max_memory_mb = self.config.get('max_memory_size_mb', 500)
            
            if total_size_mb > max_memory_mb:
                # 移除大型緩存項
                sorted_entries = sorted(
                    self.memory_cache.items(),
                    key=lambda x: x[1].size_bytes,
                    reverse=True
                )
                
                removed_count = 0
                for key, entry in sorted_entries:
                    if total_size_mb <= max_memory_mb:
                        break
                    
                    total_size_mb -= entry.size_bytes / 1024 / 1024
                    del self.memory_cache[key]
                    self.cache_stats['evictions'] += 1
                    removed_count += 1
                
                if removed_count > 0:
                    logger.info(f"🧹 清理大型緩存項: {removed_count} 項")
            
        except Exception as e:
            logger.error(f"❌ 清理超大緩存失敗: {e}")
    
    def get_cache_key(self, data_type: str, params: Dict[str, Any]) -> str:
        """生成緩存鍵"""
        try:
            # 創建穩定的參數字符串
            param_str = json.dumps(params, sort_keys=True)
            
            # 生成哈希
            hash_obj = hashlib.md5(f"{data_type}:{param_str}".encode())
            return f"cache_{data_type}_{hash_obj.hexdigest()[:16]}"
            
        except Exception as e:
            logger.error(f"❌ 生成緩存鍵失敗: {e}")
            return f"cache_{data_type}_{int(time.time())}"
    
    async def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """獲取緩存數據"""
        try:
            # 首先檢查內存緩存
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                # 檢查是否過期
                ttl_seconds = self.config.get('cache_ttl_seconds', 3600)
                if datetime.now() - entry.timestamp < timedelta(seconds=ttl_seconds):
                    # 更新訪問統計
                    entry.access_count += 1
                    # 移動到末尾（LRU）
                    self.memory_cache.move_to_end(cache_key)
                    self.cache_stats['hits'] += 1
                    
                    logger.debug(f"🎯 內存緩存命中: {cache_key}")
                    return entry.data
                else:
                    # 過期，移除
                    del self.memory_cache[cache_key]
            
            # 檢查持久化緩存
            if self.config.get('enable_persistent_cache', True):
                persistent_data = await self._get_persistent_cache(cache_key)
                if persistent_data is not None:
                    # 加載到內存緩存
                    await self.set_cached_data(cache_key, persistent_data)
                    self.cache_stats['hits'] += 1
                    
                    logger.debug(f"🎯 持久化緩存命中: {cache_key}")
                    return persistent_data
            
            # 緩存未命中
            self.cache_stats['misses'] += 1
            logger.debug(f"❌ 緩存未命中: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"❌ 獲取緩存數據失敗: {e}")
            self.cache_stats['misses'] += 1
            return None
    
    async def set_cached_data(self, cache_key: str, data: Any):
        """設置緩存數據"""
        try:
            # 計算數據大小
            data_bytes = pickle.dumps(data)
            size_bytes = len(data_bytes)
            
            # 創建緩存條目
            entry = CacheEntry(
                key=cache_key,
                data=data,
                timestamp=datetime.now(),
                access_count=1,
                size_bytes=size_bytes
            )
            
            # 存儲到內存緩存
            self.memory_cache[cache_key] = entry
            self.memory_cache.move_to_end(cache_key)  # 移動到末尾
            
            # 更新統計
            self.cache_stats['total_size'] += size_bytes
            
            # 存儲到持久化緩存
            if self.config.get('enable_persistent_cache', True):
                await self._set_persistent_cache(cache_key, data, entry)
            
            logger.debug(f"💾 緩存數據已存儲: {cache_key} ({size_bytes} bytes)")
            
        except Exception as e:
            logger.error(f"❌ 設置緩存數據失敗: {e}")
    
    async def _get_persistent_cache(self, cache_key: str) -> Optional[Any]:
        """從持久化緩存獲取數據"""
        try:
            def get_from_db():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        'SELECT data, timestamp FROM cache_entries WHERE key = ?',
                        (cache_key,)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        data_blob, timestamp_str = row
                        timestamp = datetime.fromisoformat(timestamp_str)
                        
                        # 檢查是否過期
                        ttl_seconds = self.config.get('cache_ttl_seconds', 3600)
                        if datetime.now() - timestamp < timedelta(seconds=ttl_seconds):
                            return pickle.loads(data_blob)
                        else:
                            # 過期，刪除
                            conn.execute('DELETE FROM cache_entries WHERE key = ?', (cache_key,))
                            conn.commit()
                    
                    return None
            
            # 在線程池中執行數據庫操作
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.thread_pool, get_from_db)
            
        except Exception as e:
            logger.error(f"❌ 從持久化緩存獲取數據失敗: {e}")
            return None
    
    async def _set_persistent_cache(self, cache_key: str, data: Any, entry: CacheEntry):
        """設置持久化緩存"""
        try:
            def set_to_db():
                data_blob = pickle.dumps(data)
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO cache_entries 
                        (key, data, timestamp, access_count, size_bytes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        cache_key,
                        data_blob,
                        entry.timestamp.isoformat(),
                        entry.access_count,
                        entry.size_bytes
                    ))
                    conn.commit()
            
            # 在線程池中執行數據庫操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.thread_pool, set_to_db)
            
        except Exception as e:
            logger.error(f"❌ 設置持久化緩存失敗: {e}")
    
    async def parallel_data_fetch(self, fetch_tasks: List[Callable]) -> List[Any]:
        """並行數據獲取"""
        try:
            logger.info(f"⚡ 開始並行數據獲取: {len(fetch_tasks)} 個任務")
            
            # 創建異步任務
            tasks = []
            for i, fetch_func in enumerate(fetch_tasks):
                task = asyncio.create_task(self._execute_fetch_task(fetch_func, i))
                tasks.append(task)
            
            # 並行執行所有任務
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            successful_results = []
            failed_count = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ 任務 {i} 失敗: {result}")
                    failed_count += 1
                    successful_results.append(None)
                else:
                    successful_results.append(result)
            
            success_rate = (len(results) - failed_count) / len(results) if results else 0
            logger.info(f"✅ 並行數據獲取完成: 成功率 {success_rate:.1%}")
            
            return successful_results
            
        except Exception as e:
            logger.error(f"❌ 並行數據獲取失敗: {e}")
            return []
    
    async def _execute_fetch_task(self, fetch_func: Callable, task_id: int) -> Any:
        """執行單個獲取任務"""
        try:
            # 如果是協程函數
            if asyncio.iscoroutinefunction(fetch_func):
                return await fetch_func()
            else:
                # 在線程池中執行同步函數
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(self.thread_pool, fetch_func)
                
        except Exception as e:
            logger.error(f"❌ 執行獲取任務 {task_id} 失敗: {e}")
            raise
    
    async def cached_data_fetch(self, data_type: str, params: Dict[str, Any], 
                               fetch_func: Callable) -> Any:
        """帶緩存的數據獲取"""
        try:
            # 生成緩存鍵
            cache_key = self.get_cache_key(data_type, params)
            
            # 嘗試從緩存獲取
            cached_data = await self.get_cached_data(cache_key)
            if cached_data is not None:
                logger.debug(f"🎯 使用緩存數據: {data_type}")
                return cached_data
            
            # 緩存未命中，獲取新數據
            logger.debug(f"📡 獲取新數據: {data_type}")
            
            if asyncio.iscoroutinefunction(fetch_func):
                new_data = await fetch_func()
            else:
                loop = asyncio.get_event_loop()
                new_data = await loop.run_in_executor(self.thread_pool, fetch_func)
            
            # 存儲到緩存
            await self.set_cached_data(cache_key, new_data)
            
            return new_data
            
        except Exception as e:
            logger.error(f"❌ 帶緩存的數據獲取失敗: {e}")
            raise
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計信息"""
        try:
            total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = self.cache_stats['hits'] / max(1, total_requests)
            
            # 計算內存使用
            memory_usage_mb = sum(entry.size_bytes for entry in self.memory_cache.values()) / 1024 / 1024
            
            return {
                'cache_hits': self.cache_stats['hits'],
                'cache_misses': self.cache_stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self.cache_stats['evictions'],
                'memory_cache_size': len(self.memory_cache),
                'memory_usage_mb': memory_usage_mb,
                'max_memory_cache_size': self.config.get('max_memory_cache_size', 100),
                'max_memory_size_mb': self.config.get('max_memory_size_mb', 500),
                'cleanup_active': self.cleanup_active,
                'persistent_cache_enabled': self.config.get('enable_persistent_cache', True)
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取緩存統計失敗: {e}")
            return {'error': str(e)}
    
    def clear_cache(self, cache_type: str = 'all'):
        """清空緩存"""
        try:
            if cache_type in ['all', 'memory']:
                cleared_count = len(self.memory_cache)
                self.memory_cache.clear()
                self.cache_stats['evictions'] += cleared_count
                logger.info(f"🧹 清空內存緩存: {cleared_count} 項")
            
            if cache_type in ['all', 'persistent'] and self.config.get('enable_persistent_cache', True):
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute('DELETE FROM cache_entries')
                    deleted_count = cursor.rowcount
                    conn.commit()
                    logger.info(f"🧹 清空持久化緩存: {deleted_count} 項")
            
        except Exception as e:
            logger.error(f"❌ 清空緩存失敗: {e}")
    
    def __del__(self):
        """清理資源"""
        try:
            self.stop_cleanup_service()
            if hasattr(self, 'thread_pool'):
                self.thread_pool.shutdown(wait=False)
        except:
            pass


def create_data_cache_optimizer() -> DataCacheOptimizer:
    """創建數據緩存優化器實例"""
    return DataCacheOptimizer()


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_data_cache_optimizer():
        """測試數據緩存優化器"""
        print("🧪 測試數據緩存優化器...")
        
        optimizer = create_data_cache_optimizer()
        optimizer.start_cleanup_service()
        
        # 測試緩存功能
        async def mock_data_fetch():
            await asyncio.sleep(0.1)  # 模擬網絡延遲
            return {'data': 'test_data', 'timestamp': datetime.now()}
        
        # 第一次獲取（緩存未命中）
        start_time = time.time()
        data1 = await optimizer.cached_data_fetch(
            'test_data', {'param': 'value'}, mock_data_fetch
        )
        first_time = time.time() - start_time
        
        # 第二次獲取（緩存命中）
        start_time = time.time()
        data2 = await optimizer.cached_data_fetch(
            'test_data', {'param': 'value'}, mock_data_fetch
        )
        second_time = time.time() - start_time
        
        # 測試並行獲取
        fetch_tasks = [mock_data_fetch for _ in range(3)]
        start_time = time.time()
        parallel_results = await optimizer.parallel_data_fetch(fetch_tasks)
        parallel_time = time.time() - start_time
        
        # 獲取統計信息
        stats = optimizer.get_cache_stats()
        
        print(f"✅ 緩存測試結果:")
        print(f"   第一次獲取時間: {first_time:.3f}s")
        print(f"   第二次獲取時間: {second_time:.3f}s")
        print(f"   緩存加速比: {first_time/second_time:.1f}x")
        print(f"   並行獲取時間: {parallel_time:.3f}s")
        print(f"   緩存命中率: {stats['hit_rate']:.1%}")
        print(f"   內存緩存大小: {stats['memory_cache_size']}")
        
        optimizer.stop_cleanup_service()
        print("✅ 數據緩存優化器測試完成!")
    
    # 運行測試
    asyncio.run(test_data_cache_optimizer())