#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
動態倉位管理系統測試腳本
測試基於AI信心度和市場條件的智能倉位調整功能
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.trading.dynamic_position_manager import (
    DynamicPositionManager, 
    DynamicPositionConfig,
    PositionAdjustmentReason,
    PositionSizeMode
)

class DynamicPositionManagerTester:
    """動態倉位管理器測試器"""
    
    def __init__(self):
        self.test_results = []
        self.manager = None
        
    async def run_all_tests(self):
        """運行所有測試"""
        print("🧪 開始動態倉位管理系統測試")
        print("=" * 60)
        
        # 測試列表
        tests = [
            ("基礎配置測試", self.test_basic_configuration),
            ("倉位計算測試", self.test_position_calculation),
            ("AI信心度調整測試", self.test_ai_confidence_adjustment),
            ("市場波動率調整測試", self.test_volatility_adjustment),
            ("風險評估調整測試", self.test_risk_adjustment),
            ("相關性風險測試", self.test_correlation_risk),
            ("倉位調整執行測試", self.test_position_adjustment),
            ("緊急風險控制測試", self.test_emergency_risk_control),
            ("多交易對管理測試", self.test_multi_pair_management),
            ("統計和報告測試", self.test_statistics_and_reporting)
        ]
        
        # 執行測試
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 {test_name}")
                print("-" * 40)
                result = await test_func()
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'PASSED' if result else 'FAILED',
                    'timestamp': datetime.now()
                })
                print(f"✅ {test_name}: {'通過' if result else '失敗'}")
            except Exception as e:
                print(f"❌ {test_name}: 錯誤 - {e}")
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        # 生成測試報告
        await self.generate_test_report()
    
    async def test_basic_configuration(self):
        """測試基礎配置"""
        try:
            # 測試默認配置
            config = DynamicPositionConfig()
            self.manager = DynamicPositionManager(config)
            
            print(f"   基礎倉位大小: {config.base_position_size:.1%}")
            print(f"   最大倉位大小: {config.max_position_size:.1%}")
            print(f"   最大總敞口: {config.max_total_exposure:.1%}")
            print(f"   最低信心度閾值: {config.min_confidence_threshold:.1%}")
            
            # 驗證配置合理性
            assert 0 < config.base_position_size <= config.max_position_size
            assert config.max_position_size <= config.max_total_exposure
            assert 0 < config.min_confidence_threshold < 1
            
            print("   ✅ 基礎配置驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 基礎配置測試失敗: {e}")
            return False
    
    async def test_position_calculation(self):
        """測試倉位計算"""
        try:
            # 準備測試數據
            ai_analysis = {
                'confidence': 0.75,
                'risk_score': 0.3,
                'signal_strength': 0.8
            }
            
            market_data = {
                'volatility_level': 'medium',
                'trend_strength': 0.6,
                'volume_profile': 'normal'
            }
            
            # 計算倉位
            target_size, details = await self.manager.calculate_optimal_position_size(
                'BTCTWD', ai_analysis, market_data
            )
            
            print(f"   目標倉位大小: {target_size:.3%}")
            print(f"   基礎大小: {details.get('base_size', 0):.3%}")
            print(f"   信心度調整: {details.get('confidence_adjustment', 1):.2f}")
            print(f"   波動率調整: {details.get('volatility_adjustment', 1):.2f}")
            print(f"   風險調整: {details.get('risk_adjustment', 1):.2f}")
            
            # 驗證結果
            assert 0 <= target_size <= self.manager.config.max_position_size
            assert 'base_size' in details
            assert 'confidence_adjustment' in details
            
            print("   ✅ 倉位計算驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 倉位計算測試失敗: {e}")
            return False
    
    async def test_ai_confidence_adjustment(self):
        """測試AI信心度調整"""
        try:
            test_cases = [
                {'confidence': 0.3, 'expected_range': (0.2, 0.4)},  # 低信心度
                {'confidence': 0.6, 'expected_range': (0.4, 0.8)},  # 中等信心度
                {'confidence': 0.9, 'expected_range': (0.8, 1.5)}   # 高信心度
            ]
            
            for case in test_cases:
                confidence = case['confidence']
                adjustment = await self.manager._calculate_confidence_adjustment(confidence)
                
                print(f"   信心度 {confidence:.1%} → 調整係數 {adjustment:.2f}")
                
                # 驗證調整係數在合理範圍內
                min_expected, max_expected = case['expected_range']
                assert min_expected <= adjustment <= max_expected, \
                    f"調整係數 {adjustment:.2f} 不在預期範圍 [{min_expected}, {max_expected}]"
            
            print("   ✅ AI信心度調整驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ AI信心度調整測試失敗: {e}")
            return False
    
    async def test_volatility_adjustment(self):
        """測試市場波動率調整"""
        try:
            volatility_levels = ['low', 'medium', 'high', 'extreme']
            
            for level in volatility_levels:
                adjustment = self.manager._calculate_volatility_adjustment(level)
                print(f"   波動率 {level} → 調整係數 {adjustment:.2f}")
                
                # 驗證調整邏輯
                if level == 'low':
                    assert adjustment > 1.0, "低波動率應該增加倉位"
                elif level == 'high':
                    assert adjustment < 1.0, "高波動率應該減少倉位"
                elif level == 'extreme':
                    assert adjustment < 0.5, "極端波動率應該大幅減少倉位"
            
            print("   ✅ 波動率調整驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 波動率調整測試失敗: {e}")
            return False
    
    async def test_risk_adjustment(self):
        """測試風險評估調整"""
        try:
            risk_scores = [0.1, 0.3, 0.5, 0.7, 0.9]
            
            for risk_score in risk_scores:
                adjustment = self.manager._calculate_risk_adjustment(risk_score)
                print(f"   風險分數 {risk_score:.1f} → 調整係數 {adjustment:.2f}")
                
                # 驗證風險調整邏輯
                if risk_score <= 0.2:
                    assert adjustment > 1.0, "極低風險應該增加倉位"
                elif risk_score >= 0.8:
                    assert adjustment < 1.0, "高風險應該減少倉位"
            
            print("   ✅ 風險調整驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 風險調整測試失敗: {e}")
            return False
    
    async def test_correlation_risk(self):
        """測試相關性風險"""
        try:
            # 模擬相關性矩陣
            self.manager.correlation_matrix = {
                'BTCTWD': {'ETHTWD': 0.8, 'LTCTWD': 0.6},
                'ETHTWD': {'BTCTWD': 0.8, 'LTCTWD': 0.7},
                'LTCTWD': {'BTCTWD': 0.6, 'ETHTWD': 0.7}
            }
            
            # 添加現有倉位
            from src.trading.dynamic_position_manager import PositionMetrics
            self.manager.active_positions['BTCTWD'] = PositionMetrics(
                pair='BTCTWD',
                current_size=0.03,
                target_size=0.03,
                ai_confidence=0.7,
                risk_score=0.4,
                market_volatility='medium',
                correlation_risk=0.0,
                holding_duration=timedelta(hours=2),
                unrealized_pnl=0.0,
                unrealized_return=0.0,
                last_adjustment=datetime.now()
            )
            
            # 測試新交易對的相關性調整
            correlation_adj = await self.manager._calculate_correlation_adjustment('ETHTWD')
            print(f"   ETHTWD 相關性調整係數: {correlation_adj:.2f}")
            
            # 高相關性應該減少倉位
            assert correlation_adj < 1.0, "高相關性應該減少倉位"
            
            print("   ✅ 相關性風險驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 相關性風險測試失敗: {e}")
            return False
    
    async def test_position_adjustment(self):
        """測試倉位調整執行"""
        try:
            # 準備測試數據
            ai_analysis = {
                'confidence': 0.8,
                'risk_score': 0.2,
                'signal_strength': 0.9
            }
            
            market_data = {
                'volatility_level': 'low',
                'trend_strength': 0.8,
                'volume_profile': 'high'
            }
            
            # 執行倉位調整
            result = await self.manager.adjust_position('BTCTWD', ai_analysis, market_data)
            
            print(f"   調整動作: {result.get('action')}")
            print(f"   新倉位大小: {result.get('new_size', 0):.3%}")
            print(f"   調整原因: {result.get('reason')}")
            print(f"   調整成功: {result.get('success')}")
            
            # 驗證調整結果
            assert 'action' in result
            assert result.get('success') is not None
            
            print("   ✅ 倉位調整執行驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 倉位調整執行測試失敗: {e}")
            return False
    
    async def test_emergency_risk_control(self):
        """測試緊急風險控制"""
        try:
            # 添加多個倉位
            pairs = ['BTCTWD', 'ETHTWD', 'LTCTWD']
            for pair in pairs:
                from src.trading.dynamic_position_manager import PositionMetrics
                self.manager.active_positions[pair] = PositionMetrics(
                    pair=pair,
                    current_size=0.04,
                    target_size=0.04,
                    ai_confidence=0.6,
                    risk_score=0.5,
                    market_volatility='medium',
                    correlation_risk=0.0,
                    holding_duration=timedelta(hours=1),
                    unrealized_pnl=0.0,
                    unrealized_return=0.0,
                    last_adjustment=datetime.now()
                )
            
            print(f"   調整前總倉位: {len(self.manager.active_positions)}")
            
            # 觸發緊急減倉（不等待完整執行）
            emergency_task = asyncio.create_task(
                self.manager.emergency_risk_reduction(0.6)
            )
            
            # 等待短時間讓緊急減倉開始
            await asyncio.sleep(0.1)
            
            # 檢查緊急模式狀態
            assert self.manager.emergency_mode, "應該進入緊急模式"
            
            # 取消任務以避免長時間等待
            emergency_task.cancel()
            
            print(f"   緊急模式狀態: {self.manager.emergency_mode}")
            print(f"   緊急減倉統計: {self.manager.adjustment_stats['emergency_reductions']}")
            
            print("   ✅ 緊急風險控制驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 緊急風險控制測試失敗: {e}")
            return False
    
    async def test_multi_pair_management(self):
        """測試多交易對管理"""
        try:
            pairs = ['BTCTWD', 'ETHTWD', 'LTCTWD', 'BCHTWD']
            
            # 為每個交易對執行倉位調整
            for pair in pairs:
                ai_analysis = {
                    'confidence': 0.6 + (hash(pair) % 30) / 100,  # 0.6-0.9
                    'risk_score': 0.2 + (hash(pair) % 40) / 100,  # 0.2-0.6
                    'signal_strength': 0.5 + (hash(pair) % 40) / 100
                }
                
                market_data = {
                    'volatility_level': ['low', 'medium', 'high'][hash(pair) % 3],
                    'trend_strength': 0.4 + (hash(pair) % 50) / 100,
                    'volume_profile': 'normal'
                }
                
                result = await self.manager.adjust_position(pair, ai_analysis, market_data)
                print(f"   {pair}: {result.get('new_size', 0):.3%} (信心度: {ai_analysis['confidence']:.1%})")
            
            # 檢查總敞口
            summary = self.manager.get_position_summary()
            total_exposure = summary['summary']['total_exposure']
            
            print(f"   總敞口: {total_exposure:.3%}")
            print(f"   敞口利用率: {summary['summary']['exposure_utilization']:.1%}")
            print(f"   活躍倉位數: {summary['summary']['active_positions']}")
            
            # 驗證總敞口不超過限制
            assert total_exposure <= self.manager.config.max_total_exposure
            
            print("   ✅ 多交易對管理驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 多交易對管理測試失敗: {e}")
            return False
    
    async def test_statistics_and_reporting(self):
        """測試統計和報告"""
        try:
            # 獲取倉位摘要
            summary = self.manager.get_position_summary()
            
            print(f"   活躍倉位: {summary['summary']['active_positions']}")
            print(f"   總調整次數: {summary['adjustment_stats']['total_adjustments']}")
            print(f"   成功調整: {summary['adjustment_stats']['successful_adjustments']}")
            print(f"   增倉次數: {summary['adjustment_stats']['size_increases']}")
            print(f"   減倉次數: {summary['adjustment_stats']['size_decreases']}")
            
            # 獲取倉位建議
            recommendations = self.manager.get_position_recommendations()
            print(f"   倉位建議數量: {len(recommendations)}")
            
            for rec in recommendations[:3]:  # 顯示前3個建議
                print(f"     - {rec['pair']}: {rec['action']} ({rec['reason']})")
            
            # 驗證報告結構
            assert 'summary' in summary
            assert 'positions' in summary
            assert 'adjustment_stats' in summary
            assert isinstance(recommendations, list)
            
            print("   ✅ 統計和報告驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 統計和報告測試失敗: {e}")
            return False
    
    async def generate_test_report(self):
        """生成測試報告"""
        try:
            print("\n" + "=" * 60)
            print("📊 動態倉位管理系統測試報告")
            print("=" * 60)
            
            # 統計測試結果
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
            failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
            error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
            
            print(f"總測試數量: {total_tests}")
            print(f"通過測試: {passed_tests} ✅")
            print(f"失敗測試: {failed_tests} ❌")
            print(f"錯誤測試: {error_tests} 💥")
            print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
            
            # 詳細結果
            print(f"\n詳細測試結果:")
            for result in self.test_results:
                status_icon = "✅" if result['status'] == 'PASSED' else "❌" if result['status'] == 'FAILED' else "💥"
                print(f"  {status_icon} {result['test_name']}: {result['status']}")
                if 'error' in result:
                    print(f"     錯誤: {result['error']}")
            
            # 系統狀態
            if self.manager:
                summary = self.manager.get_position_summary()
                print(f"\n系統狀態:")
                print(f"  活躍倉位: {summary['summary']['active_positions']}")
                print(f"  總敞口: {summary['summary']['total_exposure']:.3%}")
                print(f"  平均信心度: {summary['summary']['avg_ai_confidence']:.1%}")
                print(f"  平均風險分數: {summary['summary']['avg_risk_score']:.1%}")
                print(f"  緊急模式: {summary['summary']['emergency_mode']}")
            
            # 保存報告到文件
            report_data = {
                'test_summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'error_tests': error_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'test_results': self.test_results,
                'system_status': summary if self.manager else {},
                'timestamp': datetime.now().isoformat()
            }
            
            report_file = f"AImax/logs/dynamic_position_manager_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n📄 測試報告已保存: {report_file}")
            
            # 總結
            if passed_tests == total_tests:
                print(f"\n🎉 所有測試通過！動態倉位管理系統運行正常")
            else:
                print(f"\n⚠️ 有 {failed_tests + error_tests} 個測試未通過，需要檢查")
            
        except Exception as e:
            print(f"❌ 生成測試報告失敗: {e}")


async def main():
    """主函數"""
    tester = DynamicPositionManagerTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())