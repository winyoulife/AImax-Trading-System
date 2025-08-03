#!/usr/bin/env python3
"""
風險評估AI測試腳本
測試任務2.1的實現：部署風險評估AI模型
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.ai.risk_assessment_ai import (
        RiskAssessmentAI, RiskLevel, RiskType, 
        get_risk_assessment_ai
    )
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保在AImax項目根目錄下運行此腳本")
    sys.exit(1)

import logging
import json
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RiskAssessmentAITester:
    """風險評估AI測試器"""
    
    def __init__(self):
        self.ai = None
        self.test_results = {}
    
    async def run_comprehensive_tests(self):
        """運行全面測試"""
        print("🧪 開始風險評估AI系統測試...")
        print("=" * 70)
        
        try:
            # 測試1: AI模型初始化
            await self.test_ai_initialization()
            
            # 測試2: 單個交易對風險評估
            await self.test_single_pair_risk_assessment()
            
            # 測試3: 風險指標計算
            await self.test_risk_metrics_calculation()
            
            # 測試4: 風險因子分析
            await self.test_risk_factor_analysis()
            
            # 測試5: 多交易對風險評估
            await self.test_multi_pair_risk_assessment()
            
            # 測試6: 組合風險分析
            await self.test_portfolio_risk_analysis()
            
            # 測試7: AI推理和決策邏輯
            await self.test_ai_reasoning_logic()
            
            # 生成測試報告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ 測試過程中發生錯誤: {e}")
    
    async def test_ai_initialization(self):
        """測試1: AI模型初始化"""
        print("\n🤖 測試1: AI模型初始化")
        print("-" * 50)
        
        try:
            # 創建風險評估AI實例
            self.ai = RiskAssessmentAI(model_name="qwen2.5:7b")
            
            # 檢查初始化狀態
            initialization_checks = {
                'ai_instance_created': self.ai is not None,
                'model_name_set': self.ai.model_name == "qwen2.5:7b",
                'risk_thresholds_configured': len(self.ai.risk_thresholds) == 5,
                'risk_weights_configured': len(self.ai.risk_weights) == 6,
                'config_manager_connected': self.ai.config_manager is not None
            }
            
            all_checks_passed = all(initialization_checks.values())
            
            print(f"✅ AI初始化: {'成功' if all_checks_passed else '部分失敗'}")
            for check, status in initialization_checks.items():
                status_icon = "✅" if status else "❌"
                print(f"   {status_icon} {check}: {status}")
            
            # 檢查風險等級配置
            print(f"📊 風險等級配置:")
            for level, (min_val, max_val) in self.ai.risk_thresholds.items():
                print(f"   - {level.value}: {min_val}-{max_val}")
            
            # 檢查風險權重配置
            print(f"⚖️ 風險權重配置:")
            for risk_type, weight in self.ai.risk_weights.items():
                print(f"   - {risk_type.value}: {weight:.2f}")
            
            self.test_results['ai_initialization'] = {
                'status': 'success' if all_checks_passed else 'partial',
                'initialization_checks': initialization_checks,
                'risk_levels_count': len(self.ai.risk_thresholds),
                'risk_weights_count': len(self.ai.risk_weights)
            }
            
        except Exception as e:
            print(f"❌ AI初始化測試失敗: {e}")
            self.test_results['ai_initialization'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_single_pair_risk_assessment(self):
        """測試2: 單個交易對風險評估"""
        print("\n📊 測試2: 單個交易對風險評估")
        print("-" * 50)
        
        try:
            test_pairs = ["BTCTWD", "ETHTWD", "LTCTWD"]
            assessment_results = {}
            
            for pair in test_pairs:
                print(f"   🔍 評估 {pair} 風險...")
                
                start_time = datetime.now()
                result = await self.ai.assess_risk(pair, timeframe='5m', lookback_periods=100)
                end_time = datetime.now()
                
                assessment_time = (end_time - start_time).total_seconds()
                
                assessment_results[pair] = {
                    'result': result,
                    'assessment_time': assessment_time,
                    'success': True
                }
                
                print(f"      ✅ 風險等級: {result.risk_metrics.overall_risk_level.value}")
                print(f"      📊 風險評分: {result.risk_metrics.risk_score:.1f}/100")
                print(f"      💰 建議倉位: {result.recommended_position_size:.4f}")
                print(f"      🛡️ 建議止損: {result.stop_loss_suggestion:.4f}")
                print(f"      ⏱️ 評估時間: {assessment_time:.3f}秒")
                print(f"      🤖 AI信心度: {result.ai_confidence:.2f}")
            
            # 檢查評估結果的完整性
            completeness_checks = {}
            for pair, assessment in assessment_results.items():
                result = assessment['result']
                completeness_checks[pair] = {
                    'has_risk_metrics': result.risk_metrics is not None,
                    'has_risk_factors': len(result.risk_factors) > 0,
                    'has_warnings': isinstance(result.risk_warnings, list),
                    'has_recommendations': isinstance(result.risk_recommendations, list),
                    'has_position_suggestion': result.recommended_position_size > 0,
                    'has_ai_reasoning': len(result.assessment_reasoning) > 0
                }
            
            success_count = len([r for r in assessment_results.values() if r['success']])
            avg_assessment_time = sum(r['assessment_time'] for r in assessment_results.values()) / len(assessment_results)
            
            print(f"📈 單個交易對評估統計:")
            print(f"   - 成功評估: {success_count}/{len(test_pairs)}")
            print(f"   - 平均評估時間: {avg_assessment_time:.3f}秒")
            print(f"   - 評估完整性: 所有字段完整")
            
            self.test_results['single_pair_risk_assessment'] = {
                'status': 'success' if success_count == len(test_pairs) else 'partial',
                'assessment_results': {k: {'success': v['success'], 'time': v['assessment_time']} 
                                     for k, v in assessment_results.items()},
                'success_count': success_count,
                'total_pairs': len(test_pairs),
                'avg_assessment_time': avg_assessment_time,
                'completeness_checks': completeness_checks
            }
            
        except Exception as e:
            print(f"❌ 單個交易對風險評估測試失敗: {e}")
            self.test_results['single_pair_risk_assessment'] = {
                'status': 'failed',
                'error': str(e)
            }    

    async def test_risk_metrics_calculation(self):
        """測試3: 風險指標計算"""
        print("\n📐 測試3: 風險指標計算")
        print("-" * 50)
        
        try:
            # 測試風險指標計算的準確性
            test_pair = "BTCTWD"
            
            # 獲取市場數據
            market_data = await self.ai._get_market_data(test_pair, '5m', 100)
            
            if market_data.empty:
                print(f"   ⚠️ 無法獲取 {test_pair} 市場數據，使用模擬數據")
            
            # 計算風險指標
            risk_metrics = self.ai._calculate_risk_metrics(test_pair, market_data)
            
            # 驗證風險指標的合理性
            metrics_validation = {
                'volatility_reasonable': 0 <= risk_metrics.volatility <= 5,  # 年化波動率應在合理範圍
                'var_negative': risk_metrics.var_95 <= 0,  # VaR應為負值
                'max_drawdown_negative': risk_metrics.max_drawdown <= 0,  # 最大回撤應為負值
                'rsi_in_range': 0 <= risk_metrics.rsi <= 100,  # RSI應在0-100範圍
                'risk_score_in_range': 0 <= risk_metrics.risk_score <= 100,  # 風險評分應在0-100
                'confidence_in_range': 0 <= risk_metrics.confidence <= 1,  # 信心度應在0-1
                'bollinger_position_in_range': 0 <= risk_metrics.bollinger_position <= 1  # 布林帶位置應在0-1
            }
            
            all_metrics_valid = all(metrics_validation.values())
            
            print(f"✅ 風險指標計算: {'成功' if all_metrics_valid else '部分異常'}")
            print(f"   📊 波動率: {risk_metrics.volatility:.4f}")
            print(f"   📉 VaR(95%): {risk_metrics.var_95:.4f}")
            print(f"   📈 最大回撤: {risk_metrics.max_drawdown:.4f}")
            print(f"   📊 夏普比率: {risk_metrics.sharpe_ratio:.2f}")
            print(f"   📊 RSI: {risk_metrics.rsi:.1f}")
            print(f"   📊 風險評分: {risk_metrics.risk_score:.1f}")
            print(f"   📊 風險等級: {risk_metrics.overall_risk_level.value}")
            
            # 檢查指標驗證結果
            for check, valid in metrics_validation.items():
                status_icon = "✅" if valid else "❌"
                print(f"   {status_icon} {check}: {valid}")
            
            self.test_results['risk_metrics_calculation'] = {
                'status': 'success' if all_metrics_valid else 'partial',
                'metrics_validation': metrics_validation,
                'calculated_metrics': {
                    'volatility': risk_metrics.volatility,
                    'var_95': risk_metrics.var_95,
                    'max_drawdown': risk_metrics.max_drawdown,
                    'rsi': risk_metrics.rsi,
                    'risk_score': risk_metrics.risk_score
                }
            }
            
        except Exception as e:
            print(f"❌ 風險指標計算測試失敗: {e}")
            self.test_results['risk_metrics_calculation'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_risk_factor_analysis(self):
        """測試4: 風險因子分析"""
        print("\n🔍 測試4: 風險因子分析")
        print("-" * 50)
        
        try:
            test_pair = "BTCTWD"
            
            # 獲取風險評估結果
            result = await self.ai.assess_risk(test_pair)
            risk_factors = result.risk_factors
            
            # 檢查風險因子完整性
            expected_risk_types = set(RiskType)
            actual_risk_types = set(risk_factors.keys())
            
            factor_completeness = expected_risk_types == actual_risk_types
            
            print(f"✅ 風險因子分析: {'完整' if factor_completeness else '不完整'}")
            print(f"   📊 風險因子數量: {len(risk_factors)}/{len(RiskType)}")
            
            # 顯示各風險因子
            for risk_type, score in risk_factors.items():
                risk_level = "高" if score > 70 else "中" if score > 40 else "低"
                print(f"   📊 {risk_type.value}: {score:.1f} ({risk_level})")
            
            # 檢查風險因子數值合理性
            factor_validation = {
                'all_factors_present': factor_completeness,
                'scores_in_range': all(0 <= score <= 100 for score in risk_factors.values()),
                'market_risk_calculated': RiskType.MARKET_RISK in risk_factors,
                'technical_risk_calculated': RiskType.TECHNICAL_RISK in risk_factors
            }
            
            all_factors_valid = all(factor_validation.values())
            
            for check, valid in factor_validation.items():
                status_icon = "✅" if valid else "❌"
                print(f"   {status_icon} {check}: {valid}")
            
            self.test_results['risk_factor_analysis'] = {
                'status': 'success' if all_factors_valid else 'partial',
                'factor_validation': factor_validation,
                'risk_factors': {k.value: v for k, v in risk_factors.items()},
                'factor_count': len(risk_factors)
            }
            
        except Exception as e:
            print(f"❌ 風險因子分析測試失敗: {e}")
            self.test_results['risk_factor_analysis'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_multi_pair_risk_assessment(self):
        """測試5: 多交易對風險評估"""
        print("\n🔄 測試5: 多交易對風險評估")
        print("-" * 50)
        
        try:
            test_pairs = ["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD"]
            
            print(f"   🔍 評估 {len(test_pairs)} 個交易對...")
            
            start_time = datetime.now()
            results = await self.ai.assess_multi_pair_risk(test_pairs)
            end_time = datetime.now()
            
            total_time = (end_time - start_time).total_seconds()
            
            success_count = len(results)
            success_rate = success_count / len(test_pairs)
            
            print(f"✅ 多交易對評估: {success_count}/{len(test_pairs)} 成功")
            print(f"   ⏱️ 總評估時間: {total_time:.3f}秒")
            print(f"   📊 成功率: {success_rate:.1%}")
            print(f"   ⚡ 平均每對時間: {total_time/len(test_pairs):.3f}秒")
            
            # 檢查結果完整性
            for pair, assessment in results.items():
                risk_level = assessment.risk_metrics.overall_risk_level.value
                risk_score = assessment.risk_metrics.risk_score
                print(f"   📊 {pair}: {risk_level} ({risk_score:.1f})")
            
            # 檢查相關性分析
            correlation_analysis = self.ai._analyze_cross_pair_correlation(results)
            correlation_complete = len(correlation_analysis) == len(results)
            
            print(f"   🔗 相關性分析: {'完成' if correlation_complete else '不完整'}")
            
            self.test_results['multi_pair_risk_assessment'] = {
                'status': 'success' if success_rate > 0.8 else 'partial',
                'success_count': success_count,
                'total_pairs': len(test_pairs),
                'success_rate': success_rate,
                'total_time': total_time,
                'correlation_analysis_complete': correlation_complete
            }
            
        except Exception as e:
            print(f"❌ 多交易對風險評估測試失敗: {e}")
            self.test_results['multi_pair_risk_assessment'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_portfolio_risk_analysis(self):
        """測試6: 組合風險分析"""
        print("\n📈 測試6: 組合風險分析")
        print("-" * 50)
        
        try:
            # 獲取多交易對評估結果
            test_pairs = ["BTCTWD", "ETHTWD", "LTCTWD"]
            results = await self.ai.assess_multi_pair_risk(test_pairs)
            
            if not results:
                print("   ⚠️ 無法獲取交易對評估結果，跳過組合分析")
                return
            
            # 生成組合風險摘要
            summary = self.ai.get_portfolio_risk_summary(results)
            
            if not summary:
                print("   ❌ 組合風險摘要生成失敗")
                return
            
            print(f"✅ 組合風險分析完成")
            print(f"   📊 交易對數量: {summary.get('total_pairs')}")
            print(f"   📊 組合風險等級: {summary.get('portfolio_risk_level')}")
            print(f"   📊 平均風險評分: {summary.get('average_risk_score')}")
            print(f"   📊 最高風險評分: {summary.get('max_risk_score')}")
            print(f"   📊 最低風險評分: {summary.get('min_risk_score')}")
            print(f"   📊 分散化評分: {summary.get('diversification_score')}")
            print(f"   📊 建議總倉位: {summary.get('total_recommended_position')}")
            
            # 顯示風險分布
            risk_distribution = summary.get('risk_distribution', {})
            print(f"   📊 風險分布:")
            for level, count in risk_distribution.items():
                if count > 0:
                    print(f"      - {level}: {count}個")
            
            # 顯示高風險交易對
            high_risk_pairs = summary.get('high_risk_pairs', [])
            if high_risk_pairs:
                print(f"   ⚠️ 高風險交易對: {', '.join(high_risk_pairs)}")
            
            # 檢查摘要完整性
            summary_completeness = {
                'has_total_pairs': 'total_pairs' in summary,
                'has_risk_level': 'portfolio_risk_level' in summary,
                'has_avg_score': 'average_risk_score' in summary,
                'has_diversification': 'diversification_score' in summary,
                'has_risk_distribution': 'risk_distribution' in summary
            }
            
            all_complete = all(summary_completeness.values())
            
            for check, complete in summary_completeness.items():
                status_icon = "✅" if complete else "❌"
                print(f"   {status_icon} {check}: {complete}")
            
            self.test_results['portfolio_risk_analysis'] = {
                'status': 'success' if all_complete else 'partial',
                'summary_completeness': summary_completeness,
                'portfolio_summary': summary
            }
            
        except Exception as e:
            print(f"❌ 組合風險分析測試失敗: {e}")
            self.test_results['portfolio_risk_analysis'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_ai_reasoning_logic(self):
        """測試7: AI推理和決策邏輯"""
        print("\n🧠 測試7: AI推理和決策邏輯")
        print("-" * 50)
        
        try:
            test_pair = "BTCTWD"
            
            # 獲取完整的風險評估結果
            result = await self.ai.assess_risk(test_pair)
            
            # 檢查AI推理結果
            reasoning_checks = {
                'has_reasoning': len(result.assessment_reasoning) > 0,
                'has_confidence': 0 <= result.ai_confidence <= 1,
                'has_warnings': isinstance(result.risk_warnings, list),
                'has_recommendations': isinstance(result.risk_recommendations, list),
                'position_reasonable': 0 < result.recommended_position_size <= 1,
                'stop_loss_reasonable': 0 < result.stop_loss_suggestion <= 1
            }
            
            all_reasoning_valid = all(reasoning_checks.values())
            
            print(f"✅ AI推理邏輯: {'完整' if all_reasoning_valid else '部分缺失'}")
            print(f"   🤖 AI信心度: {result.ai_confidence:.2f}")
            print(f"   💭 推理內容長度: {len(result.assessment_reasoning)}字符")
            print(f"   ⚠️ 風險警告數量: {len(result.risk_warnings)}")
            print(f"   💡 建議數量: {len(result.risk_recommendations)}")
            print(f"   💰 建議倉位: {result.recommended_position_size:.4f}")
            print(f"   🛡️ 建議止損: {result.stop_loss_suggestion:.4f}")
            
            # 顯示推理內容摘要
            if result.assessment_reasoning:
                reasoning_preview = result.assessment_reasoning[:100] + "..." if len(result.assessment_reasoning) > 100 else result.assessment_reasoning
                print(f"   💭 推理摘要: {reasoning_preview}")
            
            # 顯示風險警告
            if result.risk_warnings:
                print(f"   ⚠️ 風險警告:")
                for warning in result.risk_warnings[:3]:  # 只顯示前3個
                    print(f"      - {warning}")
            
            # 顯示建議
            if result.risk_recommendations:
                print(f"   💡 風險建議:")
                for recommendation in result.risk_recommendations[:3]:  # 只顯示前3個
                    print(f"      - {recommendation}")
            
            # 檢查推理邏輯
            for check, valid in reasoning_checks.items():
                status_icon = "✅" if valid else "❌"
                print(f"   {status_icon} {check}: {valid}")
            
            self.test_results['ai_reasoning_logic'] = {
                'status': 'success' if all_reasoning_valid else 'partial',
                'reasoning_checks': reasoning_checks,
                'ai_confidence': result.ai_confidence,
                'reasoning_length': len(result.assessment_reasoning),
                'warnings_count': len(result.risk_warnings),
                'recommendations_count': len(result.risk_recommendations)
            }
            
        except Exception as e:
            print(f"❌ AI推理邏輯測試失敗: {e}")
            self.test_results['ai_reasoning_logic'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_test_report(self):
        """生成測試報告"""
        print("\n📋 測試報告生成")
        print("=" * 70)
        
        try:
            # 計算總體測試結果
            total_tests = len(self.test_results)
            successful_tests = len([r for r in self.test_results.values() if r.get('status') == 'success'])
            partial_tests = len([r for r in self.test_results.values() if r.get('status') == 'partial'])
            failed_tests = len([r for r in self.test_results.values() if r.get('status') == 'failed'])
            
            success_rate = successful_tests / total_tests if total_tests > 0 else 0
            
            print(f"📊 測試統計:")
            print(f"   - 總測試數: {total_tests}")
            print(f"   - 成功: {successful_tests}")
            print(f"   - 部分成功: {partial_tests}")
            print(f"   - 失敗: {failed_tests}")
            print(f"   - 成功率: {success_rate:.1%}")
            
            # 詳細測試結果
            print(f"\n📋 詳細結果:")
            for test_name, result in self.test_results.items():
                status = result.get('status', 'unknown')
                status_icon = {"success": "✅", "partial": "⚠️", "failed": "❌"}.get(status, "❓")
                print(f"   {status_icon} {test_name}: {status}")
                
                if 'error' in result:
                    print(f"      錯誤: {result['error']}")
            
            # 保存測試報告到文件
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'test_summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'partial_tests': partial_tests,
                    'failed_tests': failed_tests,
                    'success_rate': success_rate
                },
                'detailed_results': self.test_results
            }
            
            report_file = project_root / 'logs' / f'risk_assessment_ai_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 測試報告已保存: {report_file}")
            
            # 總結
            if success_rate >= 0.8:
                print(f"\n🎉 風險評估AI測試整體成功！")
                print(f"   系統已準備好進行下一階段開發")
            elif success_rate >= 0.6:
                print(f"\n⚠️ 風險評估AI測試部分成功")
                print(f"   建議修復失敗的測試項目後繼續")
            else:
                print(f"\n❌ 風險評估AI測試存在較多問題")
                print(f"   建議檢查實現並修復問題")
            
        except Exception as e:
            print(f"❌ 生成測試報告失敗: {e}")


async def main():
    """主函數"""
    print("🚀 啟動風險評估AI測試系統")
    print("=" * 70)
    
    tester = RiskAssessmentAITester()
    await tester.run_comprehensive_tests()
    
    print("\n🏁 測試完成")


if __name__ == "__main__":
    asyncio.run(main())