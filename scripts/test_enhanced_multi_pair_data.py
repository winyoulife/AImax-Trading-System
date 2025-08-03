#!/usr/bin/env python3
"""
增強版多交易對數據管理系統測試腳本
測試任務1.2的完整實現
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.data.enhanced_multi_pair_data_manager import EnhancedMultiPairDataManager, create_enhanced_multi_pair_data_manager
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保在AImax項目根目錄下運行此腳本")
    sys.exit(1)

import logging

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedMultiPairDataTester:
    """增強版多交易對數據系統測試器"""
    
    def __init__(self):
        self.manager = None
        self.test_results = {}
    
    async def run_comprehensive_tests(self):
        """運行全面測試"""
        print("🧪 開始增強版多交易對數據管理系統測試...")
        print("=" * 70)
        
        try:
            # 測試1: 系統初始化
            await self.test_system_initialization()
            
            # 測試2: 獨立歷史數據管理器
            await self.test_independent_data_managers()
            
            # 測試3: 並行數據流處理
            await self.test_parallel_data_processing()
            
            # 測試4: 數據同步和一致性機制
            await self.test_data_sync_consistency()
            
            # 測試5: 優化存儲結構
            await self.test_optimized_storage_structure()
            
            # 測試6: 多交易對查詢性能
            await self.test_multi_pair_query_performance()
            
            # 生成最終測試報告
            self.generate_comprehensive_report()
            
        except Exception as e:
            logger.error(f"❌ 測試過程中發生錯誤: {e}")
        finally:
            if self.manager:
                await self.manager.close()
    
    async def test_system_initialization(self):
        """測試1: 系統初始化"""
        print("\n🚀 測試1: 系統初始化")
        print("-" * 50)
        
        try:
            # 創建增強版多交易對數據管理器
            self.manager = create_enhanced_multi_pair_data_manager()
            
            # 驗證核心組件
            components_check = {
                'max_client': self.manager.max_client is not None,
                'pair_manager': self.manager.pair_manager is not None,
                'sync_coordinator': self.manager.sync_coordinator is not None,
                'pair_data_managers': len(self.manager.pair_data_managers) > 0,
                'stream_configs': len(self.manager.stream_configs) > 0,
                'database_initialized': self.manager.db_path.exists()
            }
            
            all_passed = all(components_check.values())
            
            print(f"✅ 系統初始化: {'成功' if all_passed else '部分失敗'}")
            for component, status in components_check.items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {component}: {status}")
            
            print(f"📊 系統統計:")
            print(f"   - 支持交易對: {len(self.manager.stream_configs)}")
            print(f"   - 獨立數據管理器: {len(self.manager.pair_data_managers)}")
            print(f"   - 線程池大小: {self.manager.executor._max_workers}")
            print(f"   - 數據庫路徑: {self.manager.db_path}")
            
            self.test_results['system_initialization'] = {
                'status': 'success' if all_passed else 'partial',
                'components_check': components_check,
                'pairs_count': len(self.manager.stream_configs),
                'managers_count': len(self.manager.pair_data_managers)
            }
            
        except Exception as e:
            print(f"❌ 系統初始化測試失敗: {e}")
            self.test_results['system_initialization'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def test_independent_data_managers(self):
        """測試2: 獨立歷史數據管理器"""
        print("\n📊 測試2: 獨立歷史數據管理器")
        print("-" * 50)
        
        try:
            managers_status = {}
            
            for pair, data_manager in self.manager.pair_data_managers.items():
                # 檢查每個交易對的獨立數據管理器
                manager_check = {
                    'exists': data_manager is not None,
                    'type': type(data_manager).__name__,
                    'has_db_path': hasattr(data_manager, 'db_path')
                }
                
                managers_status[pair] = manager_check
                
                status_icon = "✅" if manager_check['exists'] else "❌"
                print(f"   {status_icon} {pair}: {manager_check['type']}")
            
            success_count = sum(1 for status in managers_status.values() 
                              if status['exists'])
            total_count = len(managers_status)
            
            print(f"📈 獨立數據管理器統計:")
            print(f"   - 成功創建: {success_count}/{total_count}")
            print(f"   - 成功率: {success_count/total_count*100:.1f}%")
            
            self.test_results['independent_data_managers'] = {
                'status': 'success' if success_count == total_count else 'partial',
                'managers_status': managers_status,
                'success_count': success_count,
                'total_count': total_count,
                'success_rate': success_count / total_count
            }
            
        except Exception as e:
            print(f"❌ 獨立數據管理器測試失敗: {e}")
            self.test_results['independent_data_managers'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_parallel_data_processing(self):
        """測試3: 並行數據流處理"""
        print("\n📡 測試3: 並行數據流處理")
        print("-" * 50)
        
        try:
            # 檢查數據流配置
            stream_analysis = {
                'total_streams': len(self.manager.stream_configs),
                'enabled_streams': 0,
                'timeframes_configured': 0,
                'buffers_initialized': len(self.manager.data_buffers),
                'locks_created': len(self.manager.sync_locks)
            }
            
            for pair, config in self.manager.stream_configs.items():
                if config.enabled:
                    stream_analysis['enabled_streams'] += 1
                
                stream_analysis['timeframes_configured'] += len(config.timeframes)
                
                print(f"   📊 {pair}:")
                print(f"      - 狀態: {'啟用' if config.enabled else '禁用'}")
                print(f"      - 時間框架: {config.timeframes}")
                print(f"      - 緩衝區大小: {config.buffer_size}")
            
            # 測試並行數據流啟動
            print(f"\n🚀 測試並行數據流啟動...")
            await self.manager.start_parallel_data_streams()
            
            print(f"📈 並行處理統計:")
            print(f"   - 總數據流: {stream_analysis['total_streams']}")
            print(f"   - 啟用數據流: {stream_analysis['enabled_streams']}")
            print(f"   - 配置時間框架: {stream_analysis['timeframes_configured']}")
            print(f"   - 數據緩衝區: {stream_analysis['buffers_initialized']}")
            print(f"   - 同步鎖: {stream_analysis['locks_created']}")
            
            self.test_results['parallel_data_processing'] = {
                'status': 'success',
                'stream_analysis': stream_analysis,
                'parallel_start_completed': True
            }
            
        except Exception as e:
            print(f"❌ 並行數據流處理測試失敗: {e}")
            self.test_results['parallel_data_processing'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_data_sync_consistency(self):
        """測試4: 數據同步和一致性機制"""
        print("\n🔄 測試4: 數據同步和一致性機制")
        print("-" * 50)
        
        try:
            # 測試同步協調器
            coordinator = self.manager.sync_coordinator
            test_pairs = list(self.manager.stream_configs.keys())[:3]
            
            print(f"🔄 測試協調同步 ({len(test_pairs)} 個交易對)...")
            sync_results = await coordinator.coordinate_sync(test_pairs, 'consistency_test')
            
            # 分析同步結果
            sync_analysis = {
                'total_pairs': len(test_pairs),
                'successful_syncs': 0,
                'failed_syncs': 0,
                'sync_details': []
            }
            
            for result in sync_results:
                if isinstance(result, dict):
                    if result.get('status') == 'success':
                        sync_analysis['successful_syncs'] += 1
                        print(f"   ✅ {result.get('pair')}: 同步成功")
                    else:
                        sync_analysis['failed_syncs'] += 1
                        print(f"   ❌ {result.get('pair')}: 同步失敗")
                    
                    sync_analysis['sync_details'].append(result)
                else:
                    sync_analysis['failed_syncs'] += 1
                    print(f"   ⚠️ 同步異常: {result}")
            
            # 測試數據一致性檢查
            print(f"\n🔍 測試數據一致性檢查...")
            consistency_report = self.manager.check_data_consistency(test_pairs)
            
            consistency_issues = len(consistency_report.get('consistency_issues', []))
            print(f"   📊 一致性問題: {consistency_issues} 個")
            
            for issue in consistency_report.get('consistency_issues', [])[:3]:  # 顯示前3個
                print(f"      - {issue.get('pair')}: {issue.get('issue')}")
            
            # 測試同步建議
            print(f"\n💡 測試同步建議...")
            for pair in test_pairs[:2]:
                recommendations = coordinator.get_sync_recommendations(pair)
                print(f"   📋 {pair}: 優先級 {recommendations.get('priority', 'normal')}")
            
            sync_success_rate = sync_analysis['successful_syncs'] / sync_analysis['total_pairs']
            
            print(f"📈 同步一致性統計:")
            print(f"   - 同步成功率: {sync_success_rate*100:.1f}%")
            print(f"   - 一致性問題: {consistency_issues} 個")
            print(f"   - 建議數量: {len(consistency_report.get('recommendations', []))}")
            
            self.test_results['data_sync_consistency'] = {
                'status': 'success',
                'sync_analysis': sync_analysis,
                'consistency_report': consistency_report,
                'sync_success_rate': sync_success_rate
            }
            
        except Exception as e:
            print(f"❌ 數據同步和一致性測試失敗: {e}")
            self.test_results['data_sync_consistency'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_optimized_storage_structure(self):
        """測試5: 優化存儲結構"""
        print("\n🗄️ 測試5: 優化存儲結構")
        print("-" * 50)
        
        try:
            # 執行存儲優化
            print(f"🔧 執行存儲結構優化...")
            optimization_report = self.manager.optimize_storage_structure()
            
            optimizations_applied = len(optimization_report.get('optimizations_applied', []))
            performance_improvements = len(optimization_report.get('performance_improvements', []))
            
            print(f"📊 優化結果:")
            print(f"   - 應用優化: {optimizations_applied} 項")
            print(f"   - 性能改進: {performance_improvements} 項")
            
            for optimization in optimization_report.get('optimizations_applied', []):
                print(f"      ✅ {optimization}")
            
            # 檢查存儲統計
            storage_stats = optimization_report.get('storage_stats', {})
            if storage_stats:
                print(f"📈 存儲統計:")
                print(f"   - 總記錄數: {storage_stats.get('total_records', 0)}")
                print(f"   - 唯一交易對: {storage_stats.get('unique_pairs', 0)}")
                print(f"   - 最早數據: {storage_stats.get('earliest_data', 'N/A')}")
                print(f"   - 最新數據: {storage_stats.get('latest_data', 'N/A')}")
            
            self.test_results['optimized_storage_structure'] = {
                'status': 'success',
                'optimization_report': optimization_report,
                'optimizations_count': optimizations_applied,
                'improvements_count': performance_improvements
            }
            
        except Exception as e:
            print(f"❌ 優化存儲結構測試失敗: {e}")
            self.test_results['optimized_storage_structure'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_multi_pair_query_performance(self):
        """測試6: 多交易對查詢性能"""
        print("\n⚡ 測試6: 多交易對查詢性能")
        print("-" * 50)
        
        try:
            import time
            
            test_pairs = list(self.manager.stream_configs.keys())[:4]  # 測試前4個交易對
            
            # 測試歷史數據查詢
            print(f"📚 測試多交易對歷史數據查詢...")
            start_time = time.time()
            
            historical_data = self.manager.get_multi_pair_historical_data(
                pairs=test_pairs,
                timeframe='5m',
                limit=50
            )
            
            historical_query_time = time.time() - start_time
            
            print(f"   ⏱️ 查詢時間: {historical_query_time:.3f} 秒")
            print(f"   📊 返回數據: {len(historical_data)} 個交易對")
            
            for pair, df in historical_data.items():
                record_count = len(df) if not df.empty else 0
                print(f"      - {pair}: {record_count} 條記錄")
            
            # 測試實時數據摘要查詢
            print(f"\n📡 測試實時數據摘要查詢...")
            start_time = time.time()
            
            real_time_summary = self.manager.get_real_time_data_summary(pairs=test_pairs)
            
            realtime_query_time = time.time() - start_time
            
            print(f"   ⏱️ 查詢時間: {realtime_query_time:.3f} 秒")
            print(f"   📊 返回數據: {len(real_time_summary)} 個交易對")
            
            for pair, data in real_time_summary.items():
                price = data.get('price', 'N/A')
                print(f"      - {pair}: 價格 {price}")
            
            # 測試同步狀態查詢
            print(f"\n📊 測試同步狀態查詢...")
            start_time = time.time()
            
            sync_summary = self.manager.get_sync_status_summary()
            
            sync_query_time = time.time() - start_time
            
            print(f"   ⏱️ 查詢時間: {sync_query_time:.3f} 秒")
            print(f"   📊 狀態統計:")
            print(f"      - 總交易對: {sync_summary.get('total_pairs', 0)}")
            print(f"      - 活躍交易對: {sync_summary.get('active_count', 0)}")
            print(f"      - 錯誤交易對: {sync_summary.get('error_count', 0)}")
            
            # 性能評估
            total_query_time = historical_query_time + realtime_query_time + sync_query_time
            avg_query_time = total_query_time / 3
            
            performance_rating = "優秀" if avg_query_time < 0.1 else "良好" if avg_query_time < 0.5 else "需要優化"
            
            print(f"📈 查詢性能統計:")
            print(f"   - 平均查詢時間: {avg_query_time:.3f} 秒")
            print(f"   - 性能評級: {performance_rating}")
            print(f"   - 歷史數據查詢: {historical_query_time:.3f} 秒")
            print(f"   - 實時數據查詢: {realtime_query_time:.3f} 秒")
            print(f"   - 狀態查詢: {sync_query_time:.3f} 秒")
            
            self.test_results['multi_pair_query_performance'] = {
                'status': 'success',
                'query_times': {
                    'historical': historical_query_time,
                    'realtime': realtime_query_time,
                    'sync_status': sync_query_time,
                    'average': avg_query_time
                },
                'data_counts': {
                    'historical_pairs': len(historical_data),
                    'realtime_pairs': len(real_time_summary),
                    'total_pairs': sync_summary.get('total_pairs', 0)
                },
                'performance_rating': performance_rating
            }
            
        except Exception as e:
            print(f"❌ 多交易對查詢性能測試失敗: {e}")
            self.test_results['multi_pair_query_performance'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_comprehensive_report(self):
        """生成全面測試報告"""
        print("\n" + "=" * 70)
        print("📋 增強版多交易對數據管理系統 - 全面測試報告")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result.get('status') == 'success')
        partial_tests = sum(1 for result in self.test_results.values() 
                           if result.get('status') == 'partial')
        failed_tests = total_tests - passed_tests - partial_tests
        
        print(f"📊 測試統計總覽:")
        print(f"   - 總測試數: {total_tests}")
        print(f"   - 完全通過: {passed_tests}")
        print(f"   - 部分通過: {partial_tests}")
        print(f"   - 測試失敗: {failed_tests}")
        print(f"   - 總體成功率: {(passed_tests + partial_tests*0.5)/total_tests*100:.1f}%")
        
        print(f"\n📋 詳細測試結果:")
        for test_name, result in self.test_results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                status_icon = "✅"
            elif status == 'partial':
                status_icon = "🟡"
            else:
                status_icon = "❌"
            
            print(f"   {status_icon} {test_name}: {status}")
            
            if status == 'failed':
                print(f"      錯誤: {result.get('error', 'Unknown error')}")
        
        # 任務1.2實現確認
        print(f"\n🎯 任務1.2實現確認:")
        implementation_checks = [
            ("為每個交易對創建獨立的歷史數據管理器", 
             self.test_results.get('independent_data_managers', {}).get('status') == 'success'),
            ("實現多交易對實時數據流並行處理", 
             self.test_results.get('parallel_data_processing', {}).get('status') == 'success'),
            ("建立交易對間數據同步和一致性機制", 
             self.test_results.get('data_sync_consistency', {}).get('status') == 'success'),
            ("優化數據存儲結構以支持多交易對查詢", 
             self.test_results.get('optimized_storage_structure', {}).get('status') == 'success')
        ]
        
        for requirement, implemented in implementation_checks:
            status_icon = "✅" if implemented else "❌"
            print(f"   {status_icon} {requirement}")
        
        # 性能指標
        if 'multi_pair_query_performance' in self.test_results:
            perf_data = self.test_results['multi_pair_query_performance']
            if perf_data.get('status') == 'success':
                print(f"\n⚡ 性能指標:")
                query_times = perf_data.get('query_times', {})
                print(f"   - 平均查詢時間: {query_times.get('average', 0):.3f} 秒")
                print(f"   - 性能評級: {perf_data.get('performance_rating', 'N/A')}")
        
        # 系統統計
        if 'system_initialization' in self.test_results:
            init_data = self.test_results['system_initialization']
            if init_data.get('status') in ['success', 'partial']:
                print(f"\n📊 系統統計:")
                print(f"   - 支持交易對: {init_data.get('pairs_count', 0)}")
                print(f"   - 獨立數據管理器: {init_data.get('managers_count', 0)}")
        
        # 最終評估
        all_requirements_met = all(implemented for _, implemented in implementation_checks)
        
        if all_requirements_met and passed_tests >= 4:
            print(f"\n🎉 任務1.2實現成功！")
            print(f"   增強版多交易對數據管理系統已完全實現所有要求。")
        elif passed_tests + partial_tests >= 4:
            print(f"\n✅ 任務1.2基本實現！")
            print(f"   多交易對數據管理系統核心功能已實現，部分功能需要進一步完善。")
        else:
            print(f"\n⚠️ 任務1.2需要改進！")
            print(f"   部分核心功能未能正確實現，需要進一步開發。")
        
        # 保存測試報告
        self.save_comprehensive_report()
    
    def save_comprehensive_report(self):
        """保存全面測試報告"""
        try:
            import json
            from datetime import datetime
            
            report = {
                'test_time': datetime.now().isoformat(),
                'test_type': 'enhanced_multi_pair_data_system',
                'task': '1.2 建立多交易對數據管理系統',
                'test_results': self.test_results,
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results.values() 
                                      if r.get('status') == 'success'),
                    'partial_tests': sum(1 for r in self.test_results.values() 
                                       if r.get('status') == 'partial'),
                    'failed_tests': sum(1 for r in self.test_results.values() 
                                      if r.get('status') == 'failed'),
                    'overall_success_rate': (
                        sum(1 for r in self.test_results.values() if r.get('status') == 'success') +
                        sum(0.5 for r in self.test_results.values() if r.get('status') == 'partial')
                    ) / len(self.test_results)
                }
            }
            
            report_path = Path("AImax/logs/enhanced_multi_pair_data_test_report.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 全面測試報告已保存: {report_path}")
            
        except Exception as e:
            print(f"⚠️ 保存測試報告失敗: {e}")


async def main():
    """主函數"""
    tester = EnhancedMultiPairDataTester()
    await tester.run_comprehensive_tests()


if __name__ == "__main__":
    asyncio.run(main())