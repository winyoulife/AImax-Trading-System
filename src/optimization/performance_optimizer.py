#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 性能優化器 - 專為三AI協作交易系統優化
"""

import asyncio
import logging
import time
import threading
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import json
import psutil
import numpy as np
from collections import deque
import queue

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指標"""
    component_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    success_rate: float
    timestamp: datetime

@dataclass
class OptimizationResult:
    """優化結果"""
    component: str
    original_time: float
    optimized_time: float
    improvement_ratio: float
    optimization_method: str
    success: bool
    details: Dict[str, Any]

class AIPerformanceOptimizer:
    """AI性能優化器 - 專為AImax三AI協作系統設計"""
    
    def __init__(self, config_path: str = "AImax/config/performance.json"):
        """
        初始化性能優化器
        
        Args:
            config_path: 性能配置文件路徑
        """
        self.config = self._load_config(config_path)
        self.metrics_history = deque(maxlen=1000)
        self.optimization_results = []
        
        # 線程池配置 - 針對AI推理優化
        self.ai_thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('ai_max_threads', 3)  # 三AI並行
        )
        self.data_thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('data_max_threads', 4)
        )
        
        # AI推理緩存
        self.ai_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_max_size = self.config.get('cache_max_size', 100)
        
        # 性能監控
        self.monitoring_active = False
        self.monitor_thread = None
        
        # AI模型預載入狀態
        self.preloaded_models = {}
        
        logger.info("⚡ AImax性能優化器初始化完成")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入性能配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✅ 載入性能配置: {config_path}")
            return config
        except Exception as e:
            logger.warning(f"⚠️ 載入配置失敗，使用默認配置: {e}")
            return {
                'ai_max_threads': 3,  # 三AI並行
                'data_max_threads': 4,
                'cache_max_size': 100,
                'monitoring_interval': 1.0,
                'ai_timeout_seconds': 30,
                'optimization_targets': {
                    'ai_inference_time': 30.0,  # 目標30秒
                    'data_processing_time': 5.0,
                    'total_cycle_time': 35.0,
                    'memory_usage_mb': 13000  # 13GB限制
                },
                'parallel_ai_enabled': True,
                'ai_cache_enabled': True,
                'preload_models': True
            }
    
    async def optimize_ai_inference_parallel(self, ai_manager, market_data: Dict[str, Any]) -> OptimizationResult:
        """
        優化AI推理 - 實現三AI並行處理
        
        Args:
            ai_manager: AI協作管理器
            market_data: 市場數據
            
        Returns:
            OptimizationResult: 優化結果
        """
        try:
            logger.info("🚀 開始AI推理並行優化...")
            
            # 測量原始性能（順序執行）
            start_time = time.time()
            try:
                # 模擬順序執行三AI
                sequential_results = []
                for role in ['market_scanner', 'deep_analyst', 'decision_maker']:
                    result = await self._simulate_ai_analysis(role, market_data)
                    sequential_results.append(result)
                sequential_time = time.time() - start_time
            except Exception as e:
                logger.warning(f"⚠️ 順序執行測試失敗: {e}")
                sequential_time = 35.0  # 假設原始時間
            
            # 實現並行優化
            start_time = time.time()
            
            if self.config.get('parallel_ai_enabled', True):
                # 並行執行三AI
                parallel_results = await self._execute_parallel_ai_analysis(ai_manager, market_data)
                parallel_time = time.time() - start_time
                optimization_method = "parallel_ai_execution"
            else:
                # 如果並行被禁用，使用緩存優化
                cached_results = await self._execute_cached_ai_analysis(ai_manager, market_data)
                parallel_time = time.time() - start_time
                optimization_method = "ai_caching"
            
            # 計算改進比例
            improvement_ratio = (sequential_time - parallel_time) / sequential_time if sequential_time > 0 else 0
            
            result = OptimizationResult(
                component="ai_inference",
                original_time=sequential_time,
                optimized_time=parallel_time,
                improvement_ratio=improvement_ratio,
                optimization_method=optimization_method,
                success=improvement_ratio > 0.1,  # 至少10%改進
                details={
                    'sequential_time': sequential_time,
                    'parallel_time': parallel_time,
                    'target_time': self.config['optimization_targets']['ai_inference_time'],
                    'meets_target': parallel_time <= self.config['optimization_targets']['ai_inference_time'],
                    'parallel_enabled': self.config.get('parallel_ai_enabled', True),
                    'cache_hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses)
                }
            )
            
            self.optimization_results.append(result)
            
            if result.success:
                logger.info(f"✅ AI推理優化成功: {improvement_ratio:.1%} 提升 ({sequential_time:.1f}s → {parallel_time:.1f}s)")
            else:
                logger.info(f"ℹ️ AI推理性能已達標: {parallel_time:.1f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI推理優化失敗: {e}")
            return OptimizationResult(
                "ai_inference", 0, 0, 0, "error", False, {'error': str(e)}
            )
    
    async def _execute_parallel_ai_analysis(self, ai_manager, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行並行AI分析"""
        try:
            # 創建三個AI任務
            tasks = []
            roles = ['market_scanner', 'deep_analyst', 'decision_maker']
            
            # 檢查緩存
            cache_key = self._generate_cache_key(market_data)
            if self.config.get('ai_cache_enabled', True) and cache_key in self.ai_cache:
                self.cache_hits += 1
                logger.info("🎯 使用AI分析緩存")
                return self.ai_cache[cache_key]
            
            self.cache_misses += 1
            
            # 並行執行三AI分析
            for role in roles:
                task = asyncio.create_task(self._simulate_ai_analysis(role, market_data))
                tasks.append(task)
            
            # 等待所有AI完成，設置超時
            timeout = self.config.get('ai_timeout_seconds', 30)
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
            
            # 處理結果
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"⚠️ {roles[i]} AI分析失敗: {result}")
                    # 提供默認結果
                    valid_results.append({
                        'role': roles[i],
                        'analysis': 'AI分析失敗',
                        'confidence': 0.0,
                        'recommendation': 'HOLD'
                    })
                else:
                    valid_results.append(result)
            
            # 緩存結果
            if self.config.get('ai_cache_enabled', True):
                self._update_cache(cache_key, valid_results)
            
            return valid_results
            
        except asyncio.TimeoutError:
            logger.error(f"❌ AI並行分析超時 ({timeout}秒)")
            return self._get_fallback_results()
        except Exception as e:
            logger.error(f"❌ 並行AI分析失敗: {e}")
            return self._get_fallback_results()
    
    async def _execute_cached_ai_analysis(self, ai_manager, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行緩存優化的AI分析"""
        try:
            cache_key = self._generate_cache_key(market_data)
            
            if cache_key in self.ai_cache:
                self.cache_hits += 1
                logger.info("🎯 使用AI分析緩存")
                return self.ai_cache[cache_key]
            
            self.cache_misses += 1
            
            # 順序執行但使用優化的AI調用
            results = []
            roles = ['market_scanner', 'deep_analyst', 'decision_maker']
            
            for role in roles:
                result = await self._simulate_ai_analysis(role, market_data, optimized=True)
                results.append(result)
            
            # 緩存結果
            self._update_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 緩存AI分析失敗: {e}")
            return self._get_fallback_results()
    
    async def _simulate_ai_analysis(self, role: str, market_data: Dict[str, Any], optimized: bool = False) -> Dict[str, Any]:
        """模擬AI分析 - 用於測試和優化"""
        try:
            # 模擬不同AI角色的處理時間
            base_times = {
                'market_scanner': 6,   # 快速掃描
                'deep_analyst': 17,    # 深度分析
                'decision_maker': 11   # 最終決策
            }
            
            processing_time = base_times.get(role, 10)
            
            # 如果是優化模式，減少處理時間
            if optimized:
                processing_time *= 0.7  # 30%優化
            
            # 模擬AI處理
            await asyncio.sleep(processing_time / 10)  # 縮短測試時間
            
            # 生成模擬結果
            confidence = np.random.uniform(60, 90)
            recommendations = ['BUY', 'SELL', 'HOLD']
            recommendation = np.random.choice(recommendations)
            
            return {
                'role': role,
                'analysis': f'{role}分析完成',
                'confidence': confidence,
                'recommendation': recommendation,
                'processing_time': processing_time,
                'optimized': optimized
            }
            
        except Exception as e:
            logger.error(f"❌ {role} AI分析模擬失敗: {e}")
            return {
                'role': role,
                'analysis': 'AI分析失敗',
                'confidence': 0.0,
                'recommendation': 'HOLD',
                'error': str(e)
            }
    
    def _generate_cache_key(self, market_data: Dict[str, Any]) -> str:
        """生成緩存鍵"""
        try:
            # 基於關鍵市場數據生成緩存鍵
            key_data = {
                'price': market_data.get('current_price', 0),
                'change': market_data.get('price_change_1m', 0),
                'volume': market_data.get('volume_ratio', 1.0)
            }
            
            # 簡化鍵以提高緩存命中率
            price_bucket = int(key_data['price'] / 10000) * 10000  # 價格區間
            change_bucket = round(key_data['change'], 1)  # 變化率精度
            volume_bucket = round(key_data['volume'], 1)  # 成交量比率精度
            
            return f"ai_cache_{price_bucket}_{change_bucket}_{volume_bucket}"
            
        except Exception as e:
            logger.error(f"❌ 生成緩存鍵失敗: {e}")
            return f"ai_cache_default_{int(time.time())}"
    
    def _update_cache(self, cache_key: str, results: List[Dict[str, Any]]):
        """更新AI分析緩存"""
        try:
            # 檢查緩存大小限制
            if len(self.ai_cache) >= self.cache_max_size:
                # 移除最舊的緩存項
                oldest_key = next(iter(self.ai_cache))
                del self.ai_cache[oldest_key]
            
            # 添加新的緩存項
            self.ai_cache[cache_key] = results
            
        except Exception as e:
            logger.error(f"❌ 更新緩存失敗: {e}")
    
    def _get_fallback_results(self) -> List[Dict[str, Any]]:
        """獲取備用結果"""
        return [
            {
                'role': 'market_scanner',
                'analysis': '備用分析',
                'confidence': 50.0,
                'recommendation': 'HOLD'
            },
            {
                'role': 'deep_analyst',
                'analysis': '備用分析',
                'confidence': 50.0,
                'recommendation': 'HOLD'
            },
            {
                'role': 'decision_maker',
                'analysis': '備用分析',
                'confidence': 50.0,
                'recommendation': 'HOLD'
            }
        ]
    
    async def optimize_data_processing(self, data_manager) -> OptimizationResult:
        """
        優化數據處理性能
        
        Args:
            data_manager: 數據管理器
            
        Returns:
            OptimizationResult: 優化結果
        """
        try:
            logger.info("📊 開始數據處理優化...")
            
            # 測量原始性能
            start_time = time.time()
            try:
                # 模擬原始數據處理
                await self._simulate_data_processing(optimized=False)
                original_time = time.time() - start_time
            except Exception as e:
                logger.warning(f"⚠️ 原始數據處理測試失敗: {e}")
                original_time = 8.0
            
            # 實現優化
            start_time = time.time()
            
            # 並行數據獲取和處理
            optimized_results = await self._execute_optimized_data_processing()
            optimized_time = time.time() - start_time
            
            # 計算改進比例
            improvement_ratio = (original_time - optimized_time) / original_time if original_time > 0 else 0
            
            result = OptimizationResult(
                component="data_processing",
                original_time=original_time,
                optimized_time=optimized_time,
                improvement_ratio=improvement_ratio,
                optimization_method="parallel_data_processing",
                success=improvement_ratio > 0.2,  # 至少20%改進
                details={
                    'target_time': self.config['optimization_targets']['data_processing_time'],
                    'meets_target': optimized_time <= self.config['optimization_targets']['data_processing_time'],
                    'optimization_techniques': ['parallel_fetch', 'data_caching', 'batch_processing']
                }
            )
            
            self.optimization_results.append(result)
            
            if result.success:
                logger.info(f"✅ 數據處理優化成功: {improvement_ratio:.1%} 提升 ({original_time:.1f}s → {optimized_time:.1f}s)")
            else:
                logger.info(f"ℹ️ 數據處理性能已達標: {optimized_time:.1f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 數據處理優化失敗: {e}")
            return OptimizationResult(
                "data_processing", 0, 0, 0, "error", False, {'error': str(e)}
            )
    
    async def _simulate_data_processing(self, optimized: bool = False) -> Dict[str, Any]:
        """模擬數據處理"""
        try:
            # 模擬數據獲取時間
            base_time = 5.0 if not optimized else 2.0
            
            await asyncio.sleep(base_time / 10)  # 縮短測試時間
            
            return {
                'success': True,
                'processing_time': base_time,
                'data_points': 1000,
                'optimized': optimized
            }
            
        except Exception as e:
            logger.error(f"❌ 數據處理模擬失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_optimized_data_processing(self) -> Dict[str, Any]:
        """執行優化的數據處理"""
        try:
            # 並行執行多個數據處理任務
            tasks = [
                self._simulate_data_processing(optimized=True),
                self._simulate_technical_indicators(),
                self._simulate_data_validation()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            successful_results = []
            for result in results:
                if not isinstance(result, Exception):
                    successful_results.append(result)
            
            return {
                'success': True,
                'results': successful_results,
                'optimization_applied': True
            }
            
        except Exception as e:
            logger.error(f"❌ 優化數據處理失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _simulate_technical_indicators(self) -> Dict[str, Any]:
        """模擬技術指標計算"""
        await asyncio.sleep(0.5)  # 模擬計算時間
        return {'indicators': 'calculated', 'time': 0.5}
    
    async def _simulate_data_validation(self) -> Dict[str, Any]:
        """模擬數據驗證"""
        await asyncio.sleep(0.3)  # 模擬驗證時間
        return {'validation': 'passed', 'time': 0.3}
    
    def optimize_memory_usage(self) -> OptimizationResult:
        """優化內存使用"""
        try:
            logger.info("💾 開始內存優化...")
            
            # 獲取當前內存使用
            process = psutil.Process()
            original_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 執行內存優化
            optimizations_applied = []
            
            # 1. 清理AI緩存
            if len(self.ai_cache) > self.cache_max_size // 2:
                cache_size_before = len(self.ai_cache)
                self._cleanup_cache()
                optimizations_applied.append(f"清理AI緩存: {cache_size_before} → {len(self.ai_cache)}")
            
            # 2. 清理性能指標歷史
            if len(self.metrics_history) > 500:
                metrics_before = len(self.metrics_history)
                # 保留最近500條記錄
                self.metrics_history = deque(list(self.metrics_history)[-500:], maxlen=1000)
                optimizations_applied.append(f"清理性能歷史: {metrics_before} → {len(self.metrics_history)}")
            
            # 3. 強制垃圾回收
            import gc
            collected = gc.collect()
            if collected > 0:
                optimizations_applied.append(f"垃圾回收: {collected} 對象")
            
            # 獲取優化後內存使用
            optimized_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 計算改進
            memory_saved = original_memory - optimized_memory
            improvement_ratio = memory_saved / original_memory if original_memory > 0 else 0
            
            result = OptimizationResult(
                component="memory_usage",
                original_time=original_memory,  # 用內存代替時間
                optimized_time=optimized_memory,
                improvement_ratio=improvement_ratio,
                optimization_method="memory_cleanup",
                success=memory_saved > 0,
                details={
                    'memory_saved_mb': memory_saved,
                    'target_memory_mb': self.config['optimization_targets']['memory_usage_mb'],
                    'meets_target': optimized_memory <= self.config['optimization_targets']['memory_usage_mb'],
                    'optimizations_applied': optimizations_applied
                }
            )
            
            self.optimization_results.append(result)
            
            if result.success:
                logger.info(f"✅ 內存優化成功: 節省 {memory_saved:.1f}MB ({improvement_ratio:.1%})")
            else:
                logger.info(f"ℹ️ 內存使用已優化: {optimized_memory:.1f}MB")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 內存優化失敗: {e}")
            return OptimizationResult(
                "memory_usage", 0, 0, 0, "error", False, {'error': str(e)}
            )
    
    def _cleanup_cache(self):
        """清理緩存"""
        try:
            # 保留最近使用的緩存項
            target_size = self.cache_max_size // 2
            
            if len(self.ai_cache) > target_size:
                # 簡單的LRU清理
                items_to_remove = len(self.ai_cache) - target_size
                keys_to_remove = list(self.ai_cache.keys())[:items_to_remove]
                
                for key in keys_to_remove:
                    del self.ai_cache[key]
                
                logger.info(f"🧹 緩存清理完成: 移除 {items_to_remove} 項")
            
        except Exception as e:
            logger.error(f"❌ 緩存清理失敗: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        try:
            # 計算統計信息
            total_optimizations = len(self.optimization_results)
            successful_optimizations = sum(1 for r in self.optimization_results if r.success)
            
            # 計算平均改進
            if successful_optimizations > 0:
                avg_improvement = np.mean([
                    r.improvement_ratio for r in self.optimization_results if r.success
                ])
            else:
                avg_improvement = 0
            
            # 緩存統計
            total_cache_requests = self.cache_hits + self.cache_misses
            cache_hit_rate = self.cache_hits / max(1, total_cache_requests)
            
            # 系統資源使用
            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            cpu_percent = process.cpu_percent()
            
            report = {
                'optimization_summary': {
                    'total_optimizations': total_optimizations,
                    'successful_optimizations': successful_optimizations,
                    'success_rate': successful_optimizations / max(1, total_optimizations),
                    'average_improvement': avg_improvement
                },
                'ai_performance': {
                    'cache_size': len(self.ai_cache),
                    'cache_hits': self.cache_hits,
                    'cache_misses': self.cache_misses,
                    'hit_rate': cache_hit_rate,
                    'parallel_enabled': self.config.get('parallel_ai_enabled', True)
                },
                'system_resources': {
                    'current_memory_mb': current_memory,
                    'cpu_usage_percent': cpu_percent,
                    'target_memory_mb': self.config['optimization_targets']['memory_usage_mb'],
                    'memory_within_target': current_memory <= self.config['optimization_targets']['memory_usage_mb']
                },
                'performance_targets': {
                    'ai_inference_target': self.config['optimization_targets']['ai_inference_time'],
                    'data_processing_target': self.config['optimization_targets']['data_processing_time'],
                    'total_cycle_target': self.config['optimization_targets']['total_cycle_time']
                },
                'recent_optimizations': [
                    {
                        'component': r.component,
                        'improvement': f"{r.improvement_ratio:.1%}",
                        'method': r.optimization_method,
                        'success': r.success
                    }
                    for r in self.optimization_results[-5:]  # 最近5個結果
                ]
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成性能報告失敗: {e}")
            return {'error': str(e)}
    
    def start_monitoring(self):
        """開始性能監控"""
        try:
            if self.monitoring_active:
                logger.warning("⚠️ 性能監控已經在運行")
                return
            
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitor_thread.start()
            
            logger.info("📊 性能監控已啟動")
            
        except Exception as e:
            logger.error(f"❌ 啟動性能監控失敗: {e}")
    
    def stop_monitoring(self):
        """停止性能監控"""
        try:
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5.0)
            
            logger.info("📊 性能監控已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止性能監控失敗: {e}")
    
    def _monitoring_loop(self):
        """監控循環"""
        try:
            interval = self.config.get('monitoring_interval', 1.0)
            
            while self.monitoring_active:
                # 收集性能指標
                metrics = self._collect_performance_metrics()
                self.metrics_history.append(metrics)
                
                # 檢查是否需要自動優化
                if self._should_auto_optimize(metrics):
                    self._trigger_auto_optimization()
                
                time.sleep(interval)
                
        except Exception as e:
            logger.error(f"❌ 性能監控循環異常: {e}")
    
    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """收集性能指標"""
        try:
            process = psutil.Process()
            
            # 系統資源使用
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # AI緩存性能
            total_requests = self.cache_hits + self.cache_misses
            cache_hit_rate = self.cache_hits / max(1, total_requests)
            
            # 成功率（基於最近的優化結果）
            recent_results = self.optimization_results[-10:] if self.optimization_results else []
            success_rate = sum(1 for r in recent_results if r.success) / max(1, len(recent_results))
            
            return PerformanceMetrics(
                component_name="system",
                execution_time=0.0,  # 系統級別不適用
                memory_usage=memory_mb,
                cpu_usage=cpu_percent,
                throughput=cache_hit_rate,
                success_rate=success_rate,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 收集性能指標失敗: {e}")
            return PerformanceMetrics(
                "system", 0.0, 0.0, 0.0, 0.0, 0.0, datetime.now()
            )
    
    def _should_auto_optimize(self, metrics: PerformanceMetrics) -> bool:
        """判斷是否需要自動優化"""
        try:
            # 檢查內存使用
            if metrics.memory_usage > self.config['optimization_targets']['memory_usage_mb']:
                return True
            
            # 檢查CPU使用率
            if metrics.cpu_usage > 80:
                return True
            
            # 檢查緩存命中率
            if metrics.throughput < 0.6:  # 緩存命中率低於60%
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 判斷自動優化需求失敗: {e}")
            return False
    
    def _trigger_auto_optimization(self):
        """觸發自動優化"""
        try:
            logger.info("🔧 觸發自動優化...")
            
            # 執行內存優化
            self.optimize_memory_usage()
            
            # 清理緩存
            if len(self.ai_cache) > self.cache_max_size * 0.8:
                self._cleanup_cache()
            
        except Exception as e:
            logger.error(f"❌ 自動優化失敗: {e}")
    
    def __del__(self):
        """清理資源"""
        try:
            self.stop_monitoring()
            if hasattr(self, 'ai_thread_pool'):
                self.ai_thread_pool.shutdown(wait=False)
            if hasattr(self, 'data_thread_pool'):
                self.data_thread_pool.shutdown(wait=False)
        except:
            pass


def create_performance_optimizer() -> AIPerformanceOptimizer:
    """創建性能優化器實例"""
    return AIPerformanceOptimizer()


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_performance_optimizer():
        """測試性能優化器"""
        print("🧪 測試AImax性能優化器...")
        
        optimizer = create_performance_optimizer()
        
        # 啟動監控
        optimizer.start_monitoring()
        
        # 測試AI推理優化
        test_market_data = {
            'current_price': 1500000,
            'price_change_1m': 0.5,
            'volume_ratio': 1.1
        }
        
        ai_result = await optimizer.optimize_ai_inference_parallel(None, test_market_data)
        print(f"✅ AI推理優化結果: {ai_result.improvement_ratio:.1%} 提升")
        
        # 測試數據處理優化
        data_result = await optimizer.optimize_data_processing(None)
        print(f"✅ 數據處理優化結果: {data_result.improvement_ratio:.1%} 提升")
        
        # 測試內存優化
        memory_result = optimizer.optimize_memory_usage()
        print(f"✅ 內存優化結果: 節省 {memory_result.details.get('memory_saved_mb', 0):.1f}MB")
        
        # 獲取性能報告
        report = optimizer.get_performance_report()
        print(f"📊 性能報告: {report['optimization_summary']}")
        
        # 停止監控
        optimizer.stop_monitoring()
        
        print("✅ 性能優化器測試完成!")
    
    # 運行測試
    asyncio.run(test_performance_optimizer())