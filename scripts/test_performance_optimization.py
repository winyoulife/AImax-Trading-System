#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 性能優化測試腳本
測試三AI協作系統的性能優化效果
"""

import asyncio
import logging
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# 添加AImax路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.optimization.performance_optimizer import create_performance_optimizer
from src.ai.ai_manager import AICollaborationManager
from src.data.market_enhancer import MarketDataEnhancer

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTestSuite:
    """性能測試套件"""
    
    def __init__(self):
        """初始化測試套件"""
        self.optimizer = create_performance_optimizer()
        self.test_results = []
        
        # 測試數據
        self.test_market_data = {
            'current_price': 1500000,
            'price_change_1m': 0.5,
            'volume_ratio': 1.1,
            'ai_formatted_data': '市場呈現上漲趨勢，成交量放大'
        }
        
        logger.info("🧪 性能測試套件初始化完成")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有性能測試"""
        try:
            logger.info("🚀 開始AImax性能優化測試...")
            
            # 啟動性能監控
            self.optimizer.start_monitoring()
            
            # 測試結果收集
            test_results = {}
            
            # 1. AI推理性能測試
            logger.info("🤖 測試AI推理性能優化...")
            ai_result = await self.test_ai_inference_optimization()
            test_results['ai_inference'] = ai_result
            
            # 2. 數據處理性能測試
            logger.info("📊 測試數據處理性能優化...")
            data_result = await self.test_data_processing_optimization()
            test_results['data_processing'] = data_result
            
            # 3. 內存使用優化測試
            logger.info("💾 測試內存使用優化...")
            memory_result = await self.test_memory_optimization()
            test_results['memory_usage'] = memory_result
            
            # 4. 並行處理測試
            logger.info("⚡ 測試並行處理性能...")
            parallel_result = await self.test_parallel_processing()
            test_results['parallel_processing'] = parallel_result
            
            # 5. 緩存系統測試
            logger.info("🎯 測試緩存系統性能...")
            cache_result = await self.test_cache_performance()
            test_results['cache_performance'] = cache_result
            
            # 6. 整體系統性能測試
            logger.info("🏆 測試整體系統性能...")
            system_result = await self.test_overall_system_performance()
            test_results['overall_system'] = system_result
            
            # 停止監控
            self.optimizer.stop_monitoring()
            
            # 生成測試報告
            report = self.generate_test_report(test_results)
            
            logger.info("✅ 所有性能測試完成!")
            return report
            
        except Exception as e:
            logger.error(f"❌ 性能測試失敗: {e}")
            return {'error': str(e), 'timestamp': datetime.now()}
    
    async def test_ai_inference_optimization(self) -> Dict[str, Any]:
        """測試AI推理性能優化"""
        try:
            # 創建模擬AI管理器
            ai_manager = None  # 在實際測試中會使用真實的AI管理器
            
            # 執行AI推理優化測試
            result = await self.optimizer.optimize_ai_inference_parallel(
                ai_manager, self.test_market_data
            )
            
            return {
                'success': result.success,
                'original_time': result.original_time,
                'optimized_time': result.optimized_time,
                'improvement_ratio': result.improvement_ratio,
                'optimization_method': result.optimization_method,
                'meets_target': result.details.get('meets_target', False),
                'target_time': result.details.get('target_time', 30.0),
                'parallel_enabled': result.details.get('parallel_enabled', True)
            }
            
        except Exception as e:
            logger.error(f"❌ AI推理優化測試失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_data_processing_optimization(self) -> Dict[str, Any]:
        """測試數據處理性能優化"""
        try:
            # 創建模擬數據管理器
            data_manager = None  # 在實際測試中會使用真實的數據管理器
            
            # 執行數據處理優化測試
            result = await self.optimizer.optimize_data_processing(data_manager)
            
            return {
                'success': result.success,
                'original_time': result.original_time,
                'optimized_time': result.optimized_time,
                'improvement_ratio': result.improvement_ratio,
                'optimization_method': result.optimization_method,
                'meets_target': result.details.get('meets_target', False),
                'target_time': result.details.get('target_time', 5.0)
            }
            
        except Exception as e:
            logger.error(f"❌ 數據處理優化測試失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_memory_optimization(self) -> Dict[str, Any]:
        """測試內存使用優化"""
        try:
            # 先創建一些內存使用
            await self._create_memory_load()
            
            # 執行內存優化
            result = self.optimizer.optimize_memory_usage()
            
            return {
                'success': result.success,
                'original_memory_mb': result.original_time,  # 用時間字段存儲內存
                'optimized_memory_mb': result.optimized_time,
                'memory_saved_mb': result.details.get('memory_saved_mb', 0),
                'improvement_ratio': result.improvement_ratio,
                'meets_target': result.details.get('meets_target', False),
                'optimizations_applied': result.details.get('optimizations_applied', [])
            }
            
        except Exception as e:
            logger.error(f"❌ 內存優化測試失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _create_memory_load(self):
        """創建內存負載用於測試"""
        try:
            # 填充AI緩存
            for i in range(50):
                cache_key = f"test_cache_{i}"
                self.optimizer.ai_cache[cache_key] = {
                    'test_data': [j for j in range(100)],
                    'timestamp': datetime.now()
                }
            
            # 填充性能指標歷史
            for i in range(600):
                from src.optimization.performance_optimizer import PerformanceMetrics
                metrics = PerformanceMetrics(
                    component_name=f"test_component_{i}",
                    execution_time=i * 0.1,
                    memory_usage=100 + i,
                    cpu_usage=50 + (i % 50),
                    throughput=0.8,
                    success_rate=0.9,
                    timestamp=datetime.now()
                )
                self.optimizer.metrics_history.append(metrics)
            
            logger.info("📈 創建內存負載完成")
            
        except Exception as e:
            logger.error(f"❌ 創建內存負載失敗: {e}")
    
    async def test_parallel_processing(self) -> Dict[str, Any]:
        """測試並行處理性能"""
        try:
            # 測試順序執行
            start_time = time.time()
            sequential_results = []
            for i in range(3):
                result = await self._simulate_task(f"task_{i}", delay=0.5)
                sequential_results.append(result)
            sequential_time = time.time() - start_time
            
            # 測試並行執行
            start_time = time.time()
            tasks = [self._simulate_task(f"parallel_task_{i}", delay=0.5) for i in range(3)]
            parallel_results = await asyncio.gather(*tasks)
            parallel_time = time.time() - start_time
            
            # 計算改進
            improvement_ratio = (sequential_time - parallel_time) / sequential_time if sequential_time > 0 else 0
            
            return {
                'success': improvement_ratio > 0.5,  # 並行應該有顯著改進
                'sequential_time': sequential_time,
                'parallel_time': parallel_time,
                'improvement_ratio': improvement_ratio,
                'tasks_completed': len(parallel_results),
                'parallel_efficiency': improvement_ratio
            }
            
        except Exception as e:
            logger.error(f"❌ 並行處理測試失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _simulate_task(self, task_name: str, delay: float = 1.0) -> Dict[str, Any]:
        """模擬任務執行"""
        await asyncio.sleep(delay)
        return {
            'task_name': task_name,
            'execution_time': delay,
            'success': True
        }
    
    async def test_cache_performance(self) -> Dict[str, Any]:
        """測試緩存系統性能"""
        try:
            # 清空緩存統計
            original_hits = self.optimizer.cache_hits
            original_misses = self.optimizer.cache_misses
            
            # 測試緩存未命中（第一次訪問）
            start_time = time.time()
            result1 = await self.optimizer._execute_parallel_ai_analysis(None, self.test_market_data)
            first_access_time = time.time() - start_time
            
            # 測試緩存命中（第二次訪問相同數據）
            start_time = time.time()
            result2 = await self.optimizer._execute_parallel_ai_analysis(None, self.test_market_data)
            second_access_time = time.time() - start_time
            
            # 計算緩存效果
            cache_hits = self.optimizer.cache_hits - original_hits
            cache_misses = self.optimizer.cache_misses - original_misses
            total_requests = cache_hits + cache_misses
            hit_rate = cache_hits / max(1, total_requests)
            
            # 計算性能改進
            cache_improvement = (first_access_time - second_access_time) / first_access_time if first_access_time > 0 else 0
            
            return {
                'success': hit_rate > 0,
                'cache_hits': cache_hits,
                'cache_misses': cache_misses,
                'hit_rate': hit_rate,
                'first_access_time': first_access_time,
                'second_access_time': second_access_time,
                'cache_improvement': cache_improvement,
                'cache_size': len(self.optimizer.ai_cache)
            }
            
        except Exception as e:
            logger.error(f"❌ 緩存性能測試失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_overall_system_performance(self) -> Dict[str, Any]:
        """測試整體系統性能"""
        try:
            # 模擬完整的交易週期
            start_time = time.time()
            
            # 1. 數據獲取和處理
            data_start = time.time()
            await self.optimizer._simulate_data_processing(optimized=True)
            data_time = time.time() - data_start
            
            # 2. AI分析
            ai_start = time.time()
            ai_results = await self.optimizer._execute_parallel_ai_analysis(None, self.test_market_data)
            ai_time = time.time() - ai_start
            
            # 3. 決策整合
            decision_start = time.time()
            await asyncio.sleep(0.2)  # 模擬決策整合時間
            decision_time = time.time() - decision_start
            
            total_time = time.time() - start_time
            
            # 檢查是否達到性能目標
            target_total_time = self.optimizer.config['optimization_targets']['total_cycle_time']
            meets_target = total_time <= target_total_time
            
            return {
                'success': meets_target,
                'total_cycle_time': total_time,
                'data_processing_time': data_time,
                'ai_analysis_time': ai_time,
                'decision_integration_time': decision_time,
                'target_time': target_total_time,
                'meets_target': meets_target,
                'performance_breakdown': {
                    'data_processing_ratio': data_time / total_time,
                    'ai_analysis_ratio': ai_time / total_time,
                    'decision_integration_ratio': decision_time / total_time
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 整體系統性能測試失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_test_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成測試報告"""
        try:
            # 計算總體統計
            total_tests = len(test_results)
            successful_tests = sum(1 for result in test_results.values() 
                                 if isinstance(result, dict) and result.get('success', False))
            
            # 收集性能改進數據
            improvements = []
            for test_name, result in test_results.items():
                if isinstance(result, dict) and 'improvement_ratio' in result:
                    improvements.append({
                        'test': test_name,
                        'improvement': result['improvement_ratio']
                    })
            
            # 計算平均改進
            avg_improvement = np.mean([imp['improvement'] for imp in improvements]) if improvements else 0
            
            # 獲取性能優化器報告
            optimizer_report = self.optimizer.get_performance_report()
            
            # 生成最終報告
            report = {
                'test_summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'success_rate': successful_tests / max(1, total_tests),
                    'average_improvement': avg_improvement,
                    'test_timestamp': datetime.now()
                },
                'performance_improvements': improvements,
                'detailed_results': test_results,
                'optimizer_report': optimizer_report,
                'recommendations': self._generate_recommendations(test_results),
                'aimax_performance_status': self._assess_aimax_performance(test_results)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成測試報告失敗: {e}")
            return {'error': str(e), 'timestamp': datetime.now()}
    
    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """生成優化建議"""
        recommendations = []
        
        try:
            # AI推理優化建議
            ai_result = test_results.get('ai_inference', {})
            if not ai_result.get('meets_target', False):
                recommendations.append("建議啟用AI並行處理以提升推理速度")
            
            # 數據處理優化建議
            data_result = test_results.get('data_processing', {})
            if not data_result.get('meets_target', False):
                recommendations.append("建議實施數據並行獲取和緩存策略")
            
            # 內存使用建議
            memory_result = test_results.get('memory_usage', {})
            if not memory_result.get('meets_target', False):
                recommendations.append("建議定期清理緩存和優化內存使用")
            
            # 緩存性能建議
            cache_result = test_results.get('cache_performance', {})
            if cache_result.get('hit_rate', 0) < 0.7:
                recommendations.append("建議調整緩存策略以提高命中率")
            
            # 整體性能建議
            system_result = test_results.get('overall_system', {})
            if not system_result.get('meets_target', False):
                recommendations.append("建議進一步優化系統整體性能")
            
            if not recommendations:
                recommendations.append("系統性能表現良好，建議保持當前優化策略")
            
        except Exception as e:
            logger.error(f"❌ 生成建議失敗: {e}")
            recommendations.append("無法生成具體建議，請檢查測試結果")
        
        return recommendations
    
    def _assess_aimax_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """評估AImax系統性能狀態"""
        try:
            # 檢查關鍵性能指標
            ai_meets_target = test_results.get('ai_inference', {}).get('meets_target', False)
            data_meets_target = test_results.get('data_processing', {}).get('meets_target', False)
            system_meets_target = test_results.get('overall_system', {}).get('meets_target', False)
            
            # 計算整體性能等級
            targets_met = sum([ai_meets_target, data_meets_target, system_meets_target])
            
            if targets_met == 3:
                performance_level = "優秀"
                status = "所有性能目標均已達成"
            elif targets_met == 2:
                performance_level = "良好"
                status = "大部分性能目標已達成"
            elif targets_met == 1:
                performance_level = "一般"
                status = "部分性能目標需要改進"
            else:
                performance_level = "需要改進"
                status = "多項性能指標未達標"
            
            return {
                'performance_level': performance_level,
                'status': status,
                'targets_met': targets_met,
                'total_targets': 3,
                'ai_inference_status': "達標" if ai_meets_target else "未達標",
                'data_processing_status': "達標" if data_meets_target else "未達標",
                'overall_system_status': "達標" if system_meets_target else "未達標"
            }
            
        except Exception as e:
            logger.error(f"❌ 評估性能狀態失敗: {e}")
            return {
                'performance_level': "未知",
                'status': "評估失敗",
                'error': str(e)
            }


async def main():
    """主測試函數"""
    try:
        print("🚀 開始AImax性能優化測試...")
        print("=" * 60)
        
        # 創建測試套件
        test_suite = PerformanceTestSuite()
        
        # 運行所有測試
        report = await test_suite.run_all_tests()
        
        # 顯示測試結果
        print("\n" + "=" * 60)
        print("📊 AImax性能優化測試報告")
        print("=" * 60)
        
        if 'error' in report:
            print(f"❌ 測試失敗: {report['error']}")
            return
        
        # 測試摘要
        summary = report['test_summary']
        print(f"📋 測試摘要:")
        print(f"   總測試數: {summary['total_tests']}")
        print(f"   成功測試: {summary['successful_tests']}")
        print(f"   成功率: {summary['success_rate']:.1%}")
        print(f"   平均改進: {summary['average_improvement']:.1%}")
        
        # 性能狀態
        performance_status = report['aimax_performance_status']
        print(f"\n🏆 AImax性能狀態:")
        print(f"   性能等級: {performance_status['performance_level']}")
        print(f"   狀態: {performance_status['status']}")
        print(f"   達標項目: {performance_status['targets_met']}/{performance_status['total_targets']}")
        
        # 關鍵性能指標
        print(f"\n⚡ 關鍵性能指標:")
        detailed = report['detailed_results']
        
        if 'ai_inference' in detailed:
            ai_result = detailed['ai_inference']
            print(f"   AI推理時間: {ai_result.get('optimized_time', 0):.1f}s (目標: {ai_result.get('target_time', 30)}s)")
        
        if 'data_processing' in detailed:
            data_result = detailed['data_processing']
            print(f"   數據處理時間: {data_result.get('optimized_time', 0):.1f}s (目標: {data_result.get('target_time', 5)}s)")
        
        if 'overall_system' in detailed:
            system_result = detailed['overall_system']
            print(f"   總週期時間: {system_result.get('total_cycle_time', 0):.1f}s (目標: {system_result.get('target_time', 35)}s)")
        
        # 優化建議
        recommendations = report['recommendations']
        print(f"\n💡 優化建議:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "=" * 60)
        print("✅ AImax性能優化測試完成!")
        
        # 保存報告
        import json
        with open('AImax/performance_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        print("📄 測試報告已保存到: AImax/performance_test_results.json")
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 導入numpy用於計算
    import numpy as np
    
    # 運行測試
    asyncio.run(main())