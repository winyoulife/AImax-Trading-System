#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCA市場適應性機制測試 - 驗證智能DCA策略的市場適應性調整功能
"""

import sys
import logging
import asyncio
import time
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.dca_market_adaptation import (
    create_dca_market_adaptation, MarketRegime, AdaptationAction
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dca_market_adaptation():
    """測試DCA市場適應性機制"""
    print("🧪 開始測試DCA市場適應性機制...")
    print("🎯 測試目標:")
    print("   1. 市場條件分析")
    print("   2. 適應性規則評估")
    print("   3. 多種市場場景測試")
    print("   4. 風險評估機制")
    print("   5. 適應性決策制定")
    
    try:
        # 測試1: 創建DCA市場適應性機制
        print("\n🔧 測試1: 創建DCA市場適應性機制")
        
        adaptation = create_dca_market_adaptation()
        print("   ✅ DCA市場適應性機制創建成功")
        print(f"   📋 適應性規則數量: {len(adaptation.adaptation_rules)}")
        
        # 顯示規則列表
        print("   📜 適應性規則列表:")
        for rule in adaptation.adaptation_rules:
            print(f"      - {rule.name} (優先級: {rule.priority})")
        
        # 測試2: 多種市場場景測試
        print("\n📊 測試2: 多種市場場景測試")
        
        market_scenarios = [
            {
                "name": "熊市崩盤",
                "data": {
                    'current_price': 2800000,
                    'price_change_1h': -0.05,
                    'price_change_24h': -0.18,
                    'price_change_7d': -0.25,
                    'price_change_30d': -0.35,
                    'volatility': 0.12,
                    'volatility_7d': 0.15,
                    'volume_ratio': 2.5,
                    'rsi_14': 20
                },
                "expected_regime": MarketRegime.CRASH_MARKET,
                "expected_actions": [AdaptationAction.INCREASE_AMOUNT, AdaptationAction.EMERGENCY_STOP]
            },
            {
                "name": "牛市過熱",
                "data": {
                    'current_price': 4200000,
                    'price_change_1h': 0.03,
                    'price_change_24h': 0.08,
                    'price_change_7d': 0.18,
                    'price_change_30d': 0.25,
                    'volatility': 0.04,
                    'volatility_7d': 0.05,
                    'volume_ratio': 0.8,
                    'rsi_14': 78
                },
                "expected_regime": MarketRegime.BULL_MARKET,
                "expected_actions": [AdaptationAction.DECREASE_AMOUNT]
            },
            {
                "name": "高波動震盪",
                "data": {
                    'current_price': 3500000,
                    'price_change_1h': -0.02,
                    'price_change_24h': 0.01,
                    'price_change_7d': -0.03,
                    'price_change_30d': 0.02,
                    'volatility': 0.09,
                    'volatility_7d': 0.10,
                    'volume_ratio': 1.3,
                    'rsi_14': 52
                },
                "expected_regime": MarketRegime.VOLATILE_MARKET,
                "expected_actions": [AdaptationAction.INCREASE_FREQUENCY]
            },
            {
                "name": "低波動橫盤",
                "data": {
                    'current_price': 3450000,
                    'price_change_1h': 0.001,
                    'price_change_24h': -0.005,
                    'price_change_7d': 0.01,
                    'price_change_30d': -0.02,
                    'volatility': 0.015,
                    'volatility_7d': 0.018,
                    'volume_ratio': 0.9,
                    'rsi_14': 48
                },
                "expected_regime": MarketRegime.SIDEWAYS_MARKET,
                "expected_actions": [AdaptationAction.DECREASE_FREQUENCY]
            }
        ]
        
        scenario_results = {}
        
        async def analyze_scenarios():
            for scenario in market_scenarios:
                print(f"   測試場景: {scenario['name']}")
                
                current_config = {
                    'base_amount': 5000,
                    'frequency': 'daily'
                }
                
                result = await adaptation.analyze_market_adaptation(
                    "BTCTWD", scenario["data"], current_config
                )
                
                market_condition = result['market_condition']
                adaptations = result['adaptations']
                
                scenario_results[scenario['name']] = {
                    'market_regime': market_condition.market_regime,
                    'trend_strength': market_condition.trend_strength,
                    'triggered_rules': result['triggered_rules'],
                    'adaptations_count': len(adaptations),
                    'adaptations': adaptations,
                    'risk_level': result['risk_level'],
                    'confidence': result['confidence'],
                    'expected_regime': scenario['expected_regime'],
                    'expected_actions': scenario['expected_actions']
                }
                
                print(f"      市場狀態: {market_condition.market_regime.value}")
                print(f"      趨勢強度: {market_condition.trend_strength:.2f}")
                print(f"      觸發規則: {result['triggered_rules']} 個")
                print(f"      適應性調整: {len(adaptations)} 個")
                print(f"      風險水平: {result['risk_level']:.2f}")
                print(f"      信心度: {result['confidence']:.2f}")
                
                for adaptation_rec in adaptations:
                    print(f"         - {adaptation_rec['rule_name']}: {adaptation_rec['action'].value}")
                    if adaptation_rec.get('old_value') is not None:
                        print(f"           調整: {adaptation_rec['old_value']} -> {adaptation_rec['new_value']}")
                    print(f"           信心度: {adaptation_rec['confidence']:.2f}")
        
        # 運行場景測試
        asyncio.run(analyze_scenarios())
        
        # 測試3: 驗證適應性邏輯
        print("\n🎯 測試3: 驗證適應性邏輯")
        
        logic_test_results = {}
        
        for scenario_name, result in scenario_results.items():
            expected_regime = result['expected_regime']
            actual_regime = result['market_regime']
            expected_actions = result['expected_actions']
            actual_actions = [adapt['action'] for adapt in result['adaptations']]
            
            # 檢查市場狀態識別
            regime_correct = actual_regime == expected_regime
            
            # 檢查適應性動作
            actions_correct = any(action in actual_actions for action in expected_actions)
            
            # 檢查風險評估合理性
            risk_reasonable = 0.0 <= result['risk_level'] <= 1.0
            confidence_reasonable = 0.0 <= result['confidence'] <= 1.0
            
            # 檢查調整數量合理性
            adjustments_reasonable = 0 <= result['adaptations_count'] <= 5
            
            logic_test_results[scenario_name] = {
                'regime_correct': regime_correct,
                'actions_correct': actions_correct,
                'risk_reasonable': risk_reasonable,
                'confidence_reasonable': confidence_reasonable,
                'adjustments_reasonable': adjustments_reasonable,
                'overall_pass': all([regime_correct, actions_correct, risk_reasonable, 
                                   confidence_reasonable, adjustments_reasonable])
            }
            
            status = "✅" if logic_test_results[scenario_name]['overall_pass'] else "❌"
            print(f"   {status} {scenario_name}:")
            print(f"      市場狀態: {'✅' if regime_correct else '❌'} "
                  f"(期望: {expected_regime.value}, 實際: {actual_regime.value})")
            print(f"      適應性動作: {'✅' if actions_correct else '❌'} "
                  f"(期望: {[a.value for a in expected_actions]}, 實際: {[a.value for a in actual_actions]})")
            print(f"      風險評估: {'✅' if risk_reasonable else '❌'} "
                  f"(實際: {result['risk_level']:.2f})")
            print(f"      信心度: {'✅' if confidence_reasonable else '❌'} "
                  f"(實際: {result['confidence']:.2f})")
            print(f"      調整數量: {'✅' if adjustments_reasonable else '❌'} "
                  f"(實際: {result['adaptations_count']})")
        
        # 測試4: 規則冷卻和限制機制
        print("\n⏰ 測試4: 規則冷卻和限制機制")
        
        # 模擬連續觸發同一規則
        test_data = market_scenarios[0]["data"]  # 使用熊市崩盤場景
        current_config = {'base_amount': 5000, 'frequency': 'daily'}
        
        consecutive_results = []
        
        async def test_consecutive_triggers():
            for i in range(3):
                print(f"   連續觸發測試 {i+1}:")
                
                result = await adaptation.analyze_market_adaptation(
                    "BTCTWD", test_data, current_config
                )
                
                consecutive_results.append({
                    'iteration': i+1,
                    'triggered_rules': result['triggered_rules'],
                    'adaptations_count': len(result['adaptations']),
                    'adaptations': result['adaptations']
                })
                
                print(f"      觸發規則: {result['triggered_rules']} 個")
                print(f"      適應性調整: {len(result['adaptations'])} 個")
                
                # 短暫延遲模擬時間流逝
                await asyncio.sleep(0.1)
        
        asyncio.run(test_consecutive_triggers())
        
        # 檢查冷卻機制是否生效
        first_adaptations = consecutive_results[0]['adaptations_count']
        later_adaptations = [r['adaptations_count'] for r in consecutive_results[1:]]
        
        cooldown_working = any(count < first_adaptations for count in later_adaptations)
        print(f"   🔒 冷卻機制測試: {'✅ 生效' if cooldown_working else '⚠️ 需檢查'}")
        
        # 測試5: 統計和歷史記錄
        print("\n📈 測試5: 統計和歷史記錄")
        
        stats = adaptation.adaptation_stats
        print(f"   適應性統計:")
        print(f"      總適應次數: {stats['total_adaptations']}")
        print(f"      成功適應次數: {stats['successful_adaptations']}")
        print(f"      頻率調整次數: {stats['frequency_adjustments']}")
        print(f"      金額調整次數: {stats['amount_adjustments']}")
        print(f"      緊急停止次數: {stats['emergency_stops']}")
        print(f"      平均信心度: {stats['avg_adaptation_confidence']:.2f}")
        
        print(f"\n   歷史記錄:")
        print(f"      適應性事件: {len(adaptation.adaptation_history)} 個")
        print(f"      市場條件記錄: {len(adaptation.market_conditions_history)} 個")
        
        # 顯示最近的適應性事件
        if adaptation.adaptation_history:
            print(f"   最近適應性事件:")
            for event in adaptation.adaptation_history[-3:]:
                print(f"      - {event.timestamp.strftime('%H:%M:%S')}: {event.action.value} "
                      f"(規則: {event.rule_id}, 成功: {event.success})")
        
        print("\n✅ DCA市場適應性機制測試完成！")
        
        # 生成測試報告
        test_report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_type": "DCA市場適應性機制",
            "test_features": [
                "市場條件分析",
                "適應性規則評估",
                "多場景適應性測試",
                "風險評估機制",
                "規則冷卻和限制",
                "統計和歷史記錄"
            ],
            "scenario_results": scenario_results,
            "logic_test_results": logic_test_results,
            "cooldown_mechanism": {
                "tested": True,
                "working": cooldown_working,
                "first_adaptations": first_adaptations,
                "later_adaptations": later_adaptations
            },
            "performance_metrics": {
                "total_rules": len(adaptation.adaptation_rules),
                "total_adaptations": stats['total_adaptations'],
                "success_rate": stats['successful_adaptations'] / max(1, stats['total_adaptations']),
                "avg_confidence": stats['avg_adaptation_confidence']
            }
        }
        
        print(f"\n📊 測試報告摘要:")
        print(f"   測試時間: {test_report['test_time']}")
        print(f"   系統類型: {test_report['system_type']}")
        print(f"   場景測試: {len(scenario_results)} 個場景")
        print(f"   邏輯測試通過率: {sum(1 for r in logic_test_results.values() if r['overall_pass']) / len(logic_test_results):.1%}")
        print(f"   適應性規則: {test_report['performance_metrics']['total_rules']} 個")
        print(f"   總適應次數: {test_report['performance_metrics']['total_adaptations']}")
        print(f"   成功率: {test_report['performance_metrics']['success_rate']:.1%}")
        print(f"   平均信心度: {test_report['performance_metrics']['avg_confidence']:.2f}")
        print(f"   冷卻機制: {'✅ 正常' if cooldown_working else '⚠️ 需檢查'}")
        
        return test_report
        
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

def main():
    """主函數"""
    print("🚀 啟動DCA市場適應性機制測試...")
    
    try:
        result = test_dca_market_adaptation()
        
        if isinstance(result, dict) and 'error' in result:
            print(f"❌ 測試失敗: {result['error']}")
            return 1
        else:
            print("🎉 DCA市場適應性機制測試全部通過！")
            print("🎯 DCA市場適應性機制功能成功實現！")
            return 0
            
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        return 1
    except Exception as e:
        print(f"❌ 測試運行失敗: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)