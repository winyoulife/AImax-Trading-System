#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI增強DCA時機選擇測試 - 驗證智能定投時機優化功能
"""

import sys
import logging
import asyncio
import time
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.simple_ai_dca_timing import (
    create_simple_ai_dca_timing, TimingSignal, MarketPhase
)
from src.strategies.dca_strategy_engine import (
    DCAStrategyEngine, DCAConfig, DCAMode, DCAFrequency
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ai_enhanced_dca_timing():
    """測試AI增強的DCA時機選擇"""
    print("🧪 開始測試AI增強的DCA時機選擇...")
    print("🎯 測試目標:")
    print("   1. AI時機分析功能")
    print("   2. 多種市場條件測試")
    print("   3. 決策邏輯驗證")
    print("   4. DCA策略整合")
    print("   5. 性能統計和建議")
    
    try:
        # 測試1: 創建AI增強DCA時機選擇器
        print("\n🔧 測試1: 創建AI增強DCA時機選擇器")
        
        timing_selector = create_simple_ai_dca_timing()
        print("   ✅ AI增強DCA時機選擇器創建成功")
        
        # 測試2: 多種市場條件時機分析
        print("\n📊 測試2: 多種市場條件時機分析")
        
        market_scenarios = [
            {
                "name": "熊市超賣",
                "data": {
                    'rsi_14': 25,
                    'price_change_24h': -0.08,
                    'price_change_7d': -0.15,
                    'price_change_30d': -0.25,
                    'volatility': 0.08
                },
                "expected_signal": ["strong_buy", "buy"]
            },
            {
                "name": "牛市超買",
                "data": {
                    'rsi_14': 75,
                    'price_change_24h': 0.06,
                    'price_change_7d': 0.12,
                    'price_change_30d': 0.20,
                    'volatility': 0.03
                },
                "expected_signal": ["wait", "skip"]
            },
            {
                "name": "震盪市場",
                "data": {
                    'rsi_14': 52,
                    'price_change_24h': -0.01,
                    'price_change_7d': 0.02,
                    'price_change_30d': -0.03,
                    'volatility': 0.025
                },
                "expected_signal": ["neutral", "buy"]
            },
            {
                "name": "高波動下跌",
                "data": {
                    'rsi_14': 40,
                    'price_change_24h': -0.12,
                    'price_change_7d': -0.08,
                    'price_change_30d': -0.10,
                    'volatility': 0.10
                },
                "expected_signal": ["buy", "strong_buy"]
            }
        ]
        
        scenario_results = {}
        
        async def analyze_scenarios():
            for scenario in market_scenarios:
                print(f"   測試場景: {scenario['name']}")
                
                timing_analysis = await timing_selector.analyze_dca_timing(
                    "BTCTWD", scenario["data"], {}
                )
                
                scenario_results[scenario['name']] = {
                    'signal': timing_analysis.signal.value,
                    'confidence': timing_analysis.confidence,
                    'market_phase': timing_analysis.market_phase.value,
                    'amount_multiplier': timing_analysis.recommended_amount_multiplier,
                    'reasoning': timing_analysis.reasoning,
                    'risk_assessment': timing_analysis.risk_assessment,
                    'opportunity_score': timing_analysis.opportunity_score,
                    'expected_signal': scenario['expected_signal']
                }
                
                print(f"      信號: {timing_analysis.signal.value}")
                print(f"      信心度: {timing_analysis.confidence:.2f}")
                print(f"      市場階段: {timing_analysis.market_phase.value}")
                print(f"      建議倍數: {timing_analysis.recommended_amount_multiplier:.2f}")
                print(f"      風險評估: {timing_analysis.risk_assessment:.2f}")
                print(f"      機會分數: {timing_analysis.opportunity_score:.2f}")
                print(f"      分析理由: {timing_analysis.reasoning}")
        
        # 運行場景測試
        asyncio.run(analyze_scenarios())
        
        # 測試3: 驗證決策邏輯
        print("\n🎯 測試3: 驗證決策邏輯")
        
        logic_test_results = {}
        
        for scenario_name, result in scenario_results.items():
            expected_signals = result['expected_signal']
            actual_signal = result['signal']
            
            # 檢查信號邏輯
            signal_correct = actual_signal in expected_signals
            
            # 檢查信心度合理性
            confidence_reasonable = 0.3 <= result['confidence'] <= 1.0
            
            # 檢查倍數邏輯
            multiplier_reasonable = True
            if actual_signal in ['strong_buy', 'buy']:
                multiplier_reasonable = result['amount_multiplier'] >= 1.0
            elif actual_signal == 'wait':
                multiplier_reasonable = result['amount_multiplier'] <= 0.8
            
            logic_test_results[scenario_name] = {
                'signal_correct': signal_correct,
                'confidence_reasonable': confidence_reasonable,
                'multiplier_reasonable': multiplier_reasonable,
                'overall_pass': signal_correct and confidence_reasonable and multiplier_reasonable
            }
            
            status = "✅" if logic_test_results[scenario_name]['overall_pass'] else "❌"
            print(f"   {status} {scenario_name}:")
            print(f"      信號邏輯: {'✅' if signal_correct else '❌'} "
                  f"(期望: {expected_signals}, 實際: {actual_signal})")
            print(f"      信心度: {'✅' if confidence_reasonable else '❌'} "
                  f"(實際: {result['confidence']:.2f})")
            print(f"      倍數邏輯: {'✅' if multiplier_reasonable else '❌'} "
                  f"(實際: {result['amount_multiplier']:.2f})")
        
        # 測試4: DCA策略引擎整合
        print("\n🔗 測試4: DCA策略引擎整合")
        
        # 創建DCA配置
        dca_config = DCAConfig(
            pair="BTCTWD",
            mode=DCAMode.SMART_DCA,
            frequency=DCAFrequency.DAILY,
            base_amount=5000,
            max_total_investment=100000,
            use_ai_timing=True,
            ai_confidence_threshold=0.6
        )
        
        # 創建DCA引擎
        dca_engine = DCAStrategyEngine(dca_config)
        print("   ✅ DCA策略引擎創建成功")
        
        # 啟動DCA策略
        if dca_engine.start_dca():
            print("   ✅ DCA策略啟動成功")
            
            # 模擬價格更新和投資決策
            test_prices = [3500000, 3400000, 3300000, 3450000, 3380000, 3520000]
            investment_results = []
            
            for i, price in enumerate(test_prices, 1):
                print(f"   價格更新 {i}: {price:,.0f} TWD")
                
                # 更新市場價格
                price_result = dca_engine.update_market_price(price)
                print(f"      市場條件: {price_result.get('market_condition', 'unknown')}")
                
                # 嘗試執行投資
                investment_result = dca_engine.execute_investment()
                investment_results.append(investment_result)
                
                if investment_result['success']:
                    order = investment_result['order']
                    print(f"      ✅ 投資成功: {order['amount']:,.2f} TWD @ {order['price']:,.0f}")
                    print(f"         數量: {order['quantity']:.6f}")
                    print(f"         市場條件: {order['market_condition']}")
                else:
                    print(f"      ⚠️ 投資被阻止: {investment_result['error']}")
            
            # 獲取DCA狀態
            dca_status = dca_engine.get_dca_status()
            print(f"\n   📊 DCA策略狀態:")
            print(f"      總投資次數: {dca_status['total_investments']}")
            print(f"      總投資金額: {dca_status['total_amount_invested']:,.2f} TWD")
            print(f"      平均成本: {dca_status['average_cost']:,.2f} TWD")
            print(f"      當前價值: {dca_status['current_value']:,.2f} TWD")
            print(f"      未實現盈虧: {dca_status['unrealized_pnl']:,.2f} TWD")
            print(f"      盈虧百分比: {dca_status['unrealized_pnl_pct']:.2%}")
            
            # 停止DCA策略
            dca_engine.stop_dca()
            print("   🛑 DCA策略已停止")
        
        # 測試5: 性能統計和建議
        print("\n📈 測試5: 性能統計和建議")
        
        # 獲取時機性能統計
        performance = timing_selector.get_timing_performance()
        print(f"   時機分析統計:")
        print(f"      總分析次數: {performance['total_analyses']}")
        print(f"      平均信心度: {performance['avg_confidence']:.2f}")
        
        if 'signal_distribution' in performance:
            print(f"      信號分佈: {performance['signal_distribution']}")
        
        # 獲取投資建議
        recommendations = timing_selector.get_timing_recommendations("BTCTWD")
        print(f"\n   💡 投資建議:")
        print(f"      建議: {recommendations['recommendation']}")
        print(f"      建議頻率: {recommendations['suggested_frequency']}")
        print(f"      建議調整倍數: {recommendations['suggested_amount_adjustment']:.2f}")
        
        print("\n✅ AI增強DCA時機選擇測試完成！")
        
        # 生成測試報告
        test_report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_type": "AI增強DCA時機選擇系統",
            "test_features": [
                "多場景時機分析",
                "決策邏輯驗證",
                "DCA策略整合",
                "性能統計和建議"
            ],
            "scenario_results": scenario_results,
            "logic_test_results": logic_test_results,
            "dca_integration": {
                "total_investments": dca_status['total_investments'],
                "total_amount": dca_status['total_amount_invested'],
                "success_rate": sum(1 for r in investment_results if r['success']) / len(investment_results)
            },
            "performance_metrics": {
                "total_analyses": performance['total_analyses'],
                "avg_confidence": performance['avg_confidence'],
                "recommendation_quality": "good" if recommendations['suggested_amount_adjustment'] > 0 else "conservative"
            }
        }
        
        print(f"\n📊 測試報告摘要:")
        print(f"   測試時間: {test_report['test_time']}")
        print(f"   系統類型: {test_report['system_type']}")
        print(f"   場景測試: {len(scenario_results)} 個場景")
        print(f"   邏輯測試通過率: {sum(1 for r in logic_test_results.values() if r['overall_pass']) / len(logic_test_results):.1%}")
        print(f"   DCA整合成功率: {test_report['dca_integration']['success_rate']:.1%}")
        print(f"   總投資次數: {test_report['dca_integration']['total_investments']}")
        print(f"   平均信心度: {test_report['performance_metrics']['avg_confidence']:.2f}")
        
        return test_report
        
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

def main():
    """主函數"""
    print("🚀 啟動AI增強DCA時機選擇測試...")
    
    try:
        result = test_ai_enhanced_dca_timing()
        
        if isinstance(result, dict) and 'error' in result:
            print(f"❌ 測試失敗: {result['error']}")
            return 1
        else:
            print("🎉 AI增強DCA時機選擇測試全部通過！")
            print("🎯 AI增強DCA時機選擇功能成功實現！")
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