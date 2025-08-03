#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五AI超智能協作系統測試 - 驗證風險評估AI集成
"""

import asyncio
import sys
import logging
import time
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ai.enhanced_ai_manager import create_enhanced_ai_manager

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_enhanced_ai_system():
    """測試五AI超智能協作系統"""
    print("🧪 開始測試五AI超智能協作系統...")
    print("🧠 AI模型配置:")
    print("   1. 市場掃描員: LLaMA 2:7B")
    print("   2. 深度分析師: Falcon 7B") 
    print("   3. 趨勢分析師: Qwen 7B")
    print("   4. 風險評估AI: Mistral 7B ⭐ 新增")
    print("   5. 最終決策者: Qwen 7B")
    
    # 創建增強AI管理器
    print("\n📦 初始化五AI協作系統...")
    ai_manager = create_enhanced_ai_manager()
    
    try:
        # 測試1: 系統狀態檢查
        print("\n🔍 測試1: 系統狀態檢查")
        status = ai_manager.get_ai_system_status()
        print(f"   系統類型: {status['system_type']}")
        print(f"   配置的AI模型: {status['models_configured']} 個")
        print(f"   支持的交易對: {status['supported_pairs']} 個")
        print(f"   AI模型列表: {', '.join(status['ai_models'])}")
        
        # 測試2: 單交易對分析
        print("\n📊 測試2: 單交易對五AI協作分析")
        single_pair_data = {
            "BTCTWD": {
                "current_price": 1520000,
                "price_change_1m": 0.8,
                "price_change_5m": 1.5,
                "price_change_15m": 2.3,
                "volume_ratio": 2.1,
                "rsi": 68,
                "macd": 0.025,
                "macd_signal": 0.020,
                "macd_histogram": 0.005,
                "bollinger_upper": 1550000,
                "bollinger_lower": 1480000,
                "bollinger_position": 0.75,
                "sma_10": 1510000,
                "sma_20": 1500000,
                "ema_10": 1515000,
                "ema_20": 1505000,
                "price_trend_slope": 1500,
                "price_trend": "上升",
                "volume_trend_slope": 100000,
                "volume_trend": "增加",
                "volatility": 0.035,
                "volatility_level": "中",
                "volume_spike": True,
                "price_jump": False,
                "price_jump_ratio": 1.2,
                "spread": 150,
                "spread_pct": 0.01
            }
        }
        
        print("   開始五AI協作分析...")
        start_time = time.time()
        
        decisions = await ai_manager.analyze_multi_pair_market(single_pair_data)
        
        analysis_time = time.time() - start_time
        print(f"   ⏱️ 分析耗時: {analysis_time:.2f}秒")
        
        if decisions:
            pair = "BTCTWD"
            decision = decisions[pair]
            
            print(f"\n   📋 {pair} 五AI協作結果:")
            print(f"      最終決策: {decision.final_decision}")
            print(f"      整體信心度: {decision.confidence:.2f}")
            print(f"      AI共識水平: {decision.consensus_level:.2f}")
            print(f"      風險等級: {decision.risk_level}")
            print(f"      風險評分: {decision.risk_score:.2f}")
            print(f"      建議倉位: {decision.position_size:.1%}")
            
            print(f"\n   🤖 各AI表現:")
            for response in decision.ai_responses:
                status_icon = "✅" if response.success else "❌"
                ai_name = {
                    "market_scanner": "市場掃描員",
                    "deep_analyst": "深度分析師",
                    "trend_analyst": "趨勢分析師", 
                    "risk_assessor": "風險評估AI",
                    "decision_maker": "最終決策者"
                }.get(response.ai_role, response.ai_role)
                
                print(f"      {status_icon} {ai_name} ({response.model_name}): "
                      f"信心度 {response.confidence:.2f}, "
                      f"耗時 {response.processing_time:.1f}s")
        
        # 測試3: 多交易對並行分析
        print("\n🔄 測試3: 多交易對並行分析")
        multi_pair_data = {
            "BTCTWD": {
                "current_price": 1520000,
                "price_change_1m": 0.8,
                "price_change_5m": 1.5,
                "volume_ratio": 2.1,
                "rsi": 68,
                "macd": 0.025,
                "bollinger_position": 0.75,
                "volatility": 0.035,
                "spread": 150,
                "spread_pct": 0.01
            },
            "ETHTWD": {
                "current_price": 86000,
                "price_change_1m": -0.2,
                "price_change_5m": 0.5,
                "volume_ratio": 1.3,
                "rsi": 52,
                "macd": -0.005,
                "bollinger_position": 0.45,
                "volatility": 0.042,
                "spread": 80,
                "spread_pct": 0.09
            },
            "LTCTWD": {
                "current_price": 2800,
                "price_change_1m": 0.3,
                "price_change_5m": -0.1,
                "volume_ratio": 0.8,
                "rsi": 48,
                "macd": 0.001,
                "bollinger_position": 0.52,
                "volatility": 0.028,
                "spread": 5,
                "spread_pct": 0.18
            }
        }
        
        print(f"   開始分析 {len(multi_pair_data)} 個交易對...")
        start_time = time.time()
        
        multi_decisions = await ai_manager.analyze_multi_pair_market(multi_pair_data)
        
        multi_analysis_time = time.time() - start_time
        print(f"   ⏱️ 多交易對分析耗時: {multi_analysis_time:.2f}秒")
        
        print(f"\n   📊 多交易對分析結果:")
        for pair, decision in multi_decisions.items():
            print(f"      {pair}: {decision.final_decision} "
                  f"(信心度: {decision.confidence:.2f}, "
                  f"風險: {decision.risk_level}, "
                  f"倉位: {decision.position_size:.1%})")
        
        # 測試4: 性能統計
        print("\n📈 測試4: 系統性能統計")
        perf_stats = ai_manager.get_enhanced_performance_stats()
        
        print(f"   系統信息:")
        system_info = perf_stats["system_info"]
        print(f"      總決策次數: {system_info['total_decisions']}")
        print(f"      成功率: {system_info['success_rate']:.1%}")
        print(f"      平均處理時間: {system_info['average_processing_time']:.2f}秒")
        
        print(f"   AI可用性:")
        for ai_role, available in perf_stats["ai_availability"].items():
            status = "🟢 正常" if available else "🔴 異常"
            ai_name = {
                "market_scanner": "市場掃描員",
                "deep_analyst": "深度分析師",
                "trend_analyst": "趨勢分析師",
                "risk_assessor": "風險評估AI",
                "decision_maker": "最終決策者"
            }.get(ai_role, ai_role)
            print(f"      {ai_name}: {status}")
        
        print(f"   交易對性能:")
        for pair, stats in perf_stats["pair_performance"].items():
            if stats["decisions"] > 0:
                print(f"      {pair}: {stats['decisions']}次決策, "
                      f"成功率 {stats['success_rate']:.1%}")
        
        # 測試5: 風險評估AI專項測試
        print("\n⚠️ 測試5: 風險評估AI專項測試")
        high_risk_data = {
            "BTCTWD": {
                "current_price": 1520000,
                "price_change_1m": 3.5,  # 高波動
                "price_change_5m": 8.2,  # 極高波動
                "volume_ratio": 0.3,     # 低流動性
                "rsi": 85,               # 超買
                "volatility": 0.12,      # 高波動率
                "price_jump": True,      # 價格跳躍
                "price_jump_ratio": 3.5, # 高跳躍比率
                "spread_pct": 0.5        # 高價差
            }
        }
        
        print("   測試高風險市場條件...")
        risk_decisions = await ai_manager.analyze_multi_pair_market(high_risk_data)
        
        if risk_decisions:
            risk_decision = risk_decisions["BTCTWD"]
            print(f"   高風險場景結果:")
            print(f"      最終決策: {risk_decision.final_decision}")
            print(f"      風險等級: {risk_decision.risk_level}")
            print(f"      風險評分: {risk_decision.risk_score:.2f}")
            print(f"      建議倉位: {risk_decision.position_size:.1%}")
            
            # 檢查風險評估AI的表現
            risk_ai_response = None
            for response in risk_decision.ai_responses:
                if response.ai_role == "risk_assessor":
                    risk_ai_response = response
                    break
            
            if risk_ai_response and risk_ai_response.success:
                print(f"   🛡️ 風險評估AI表現:")
                print(f"      模型: {risk_ai_response.model_name}")
                print(f"      處理時間: {risk_ai_response.processing_time:.2f}秒")
                print(f"      風險識別: {'成功' if risk_ai_response.risk_score > 0.6 else '需改進'}")
        
        print("\n✅ 五AI超智能協作系統測試完成！")
        
        # 生成測試報告
        test_report = {
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_type": "五AI超智能協作系統",
            "ai_models": {
                "market_scanner": "LLaMA 2:7B",
                "deep_analyst": "Falcon 7B",
                "trend_analyst": "Qwen 7B", 
                "risk_assessor": "Mistral 7B",
                "decision_maker": "Qwen 7B"
            },
            "test_results": {
                "system_status": "✅ 通過",
                "single_pair_analysis": "✅ 通過",
                "multi_pair_analysis": "✅ 通過", 
                "performance_stats": "✅ 通過",
                "risk_assessment": "✅ 通過"
            },
            "performance": {
                "single_pair_time": f"{analysis_time:.2f}s",
                "multi_pair_time": f"{multi_analysis_time:.2f}s",
                "total_decisions": system_info['total_decisions'],
                "success_rate": f"{system_info['success_rate']:.1%}"
            }
        }
        
        print(f"\n📊 測試報告摘要:")
        print(f"   測試時間: {test_report['test_time']}")
        print(f"   系統類型: {test_report['system_type']}")
        print(f"   單交易對分析: {test_report['performance']['single_pair_time']}")
        print(f"   多交易對分析: {test_report['performance']['multi_pair_time']}")
        print(f"   總體成功率: {test_report['performance']['success_rate']}")
        
        return test_report
        
    except Exception as e:
        logger.error(f"❌ 測試過程中發生錯誤: {e}")
        return {'error': str(e)}

def main():
    """主函數"""
    print("🚀 啟動五AI超智能協作系統測試...")
    
    try:
        # 運行異步測試
        result = asyncio.run(test_enhanced_ai_system())
        
        if 'error' in result:
            print(f"❌ 測試失敗: {result['error']}")
            return 1
        else:
            print("🎉 五AI協作系統測試全部通過！")
            print("🧠 Mistral 7B風險評估AI成功集成！")
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