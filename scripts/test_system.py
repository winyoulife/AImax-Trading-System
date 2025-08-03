#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax系統測試腳本
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加src目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai.ai_manager import create_ai_manager

async def test_aimax_system():
    """測試AImax多AI協作系統"""
    print("🚀 AImax多AI協作交易系統測試")
    print("=" * 60)
    
    try:
        # 創建AI管理器
        print("🤖 初始化AI協作管理器...")
        ai_manager = create_ai_manager(str(project_root / "config" / "ai_models.json"))
        
        # 檢查AI狀態
        ai_status = ai_manager.get_ai_status()
        print(f"✅ AI系統狀態:")
        print(f"   配置模型數量: {ai_status['models_configured']}")
        print(f"   協作模式: {'啟用' if ai_status['collaboration_enabled'] else '禁用'}")
        print(f"   備用機制: {'啟用' if ai_status['fallback_enabled'] else '禁用'}")
        
        # 模擬真實市場數據
        print("\n📊 模擬市場數據分析...")
        test_market_data = {
            "current_price": 1520000,  # BTC/TWD當前價格
            "price_change_1m": 0.8,    # 1分鐘漲幅
            "price_change_5m": 2.1,    # 5分鐘漲幅
            "volume": 2500000,         # 成交量
            "volume_change": 45,       # 成交量變化
            "technical_indicators": {
                "rsi": 68,
                "macd": "金叉向上",
                "ema_trend": "上升"
            },
            "volume_analysis": {
                "volume_spike": True,
                "volume_ratio": 1.45
            }
        }
        
        print("市場數據:")
        print(f"   當前價格: {test_market_data['current_price']:,} TWD")
        print(f"   5分鐘漲幅: +{test_market_data['price_change_5m']}%")
        print(f"   成交量變化: +{test_market_data['volume_change']}%")
        print(f"   RSI: {test_market_data['technical_indicators']['rsi']}")
        
        # 執行AI協作分析
        print("\n🧠 開始三AI協作分析...")
        print("   🚀 市場掃描員 (llama2:7b) - 快速掃描中...")
        print("   🔍 深度分析師 (qwen:14b) - 技術分析中...")
        print("   🧠 最終決策者 (qwen2.5:14b) - 策略決策中...")
        
        decision = await ai_manager.analyze_market_collaboratively(test_market_data)
        
        # 顯示協作結果
        print("\n" + "=" * 60)
        print("🎯 AI協作決策結果")
        print("=" * 60)
        
        print(f"📋 最終決策: {decision.final_decision}")
        print(f"💪 整體信心度: {decision.confidence:.1%}")
        print(f"🤝 AI共識水平: {decision.consensus_level:.1%}")
        print(f"⚠️ 風險等級: {decision.risk_level}")
        print(f"⏱️ 決策時間: {decision.timestamp.strftime('%H:%M:%S')}")
        
        print(f"\n📝 決策推理:")
        print(decision.reasoning)
        
        # 顯示各AI的詳細回應
        print(f"\n🤖 各AI詳細分析:")
        print("-" * 40)
        
        for response in decision.ai_responses:
            if response.success:
                print(f"\n{response.ai_role} ({response.model_name}):")
                print(f"   信心度: {response.confidence:.1%}")
                print(f"   處理時間: {response.processing_time:.2f}秒")
                print(f"   分析摘要: {response.response[:150]}...")
            else:
                print(f"\n{response.ai_role}: ❌ 執行失敗 - {response.error_message}")
        
        # 顯示性能統計
        stats = ai_manager.get_performance_stats()
        print(f"\n📊 系統性能統計:")
        print(f"   總決策次數: {stats['total_decisions']}")
        print(f"   成功決策次數: {stats['successful_decisions']}")
        print(f"   平均處理時間: {stats['average_processing_time']:.2f}秒")
        
        print("\n" + "=" * 60)
        print("🎉 AImax系統測試完成！")
        
        # 根據決策給出建議
        if decision.final_decision == "BUY":
            print("💡 系統建議: 考慮買入，但請注意風險控制")
        elif decision.final_decision == "SELL":
            print("💡 系統建議: 考慮賣出，注意市場變化")
        else:
            print("💡 系統建議: 保持觀望，等待更好機會")
        
        return True
        
    except Exception as e:
        print(f"❌ 系統測試失敗: {str(e)}")
        print("\n請檢查:")
        print("1. Ollama是否正在運行")
        print("2. AI模型是否已下載 (llama2:7b, qwen:14b, qwen2.5:14b)")
        print("3. 配置文件是否正確")
        return False

def main():
    """主函數"""
    print("🔧 準備測試AImax系統...")
    
    # 檢查配置文件
    config_file = project_root / "config" / "ai_models.json"
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        return
    
    # 運行異步測試
    success = asyncio.run(test_aimax_system())
    
    if success:
        print("\n✅ 系統測試成功！可以開始實際交易開發")
    else:
        print("\n❌ 系統測試失敗，請檢查配置")

if __name__ == "__main__":
    main()