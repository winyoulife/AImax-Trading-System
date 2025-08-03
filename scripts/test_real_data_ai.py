#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試AI系統使用真實MAX數據進行分析
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加src目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai.ai_manager import create_ai_manager
from data.max_client import create_max_client

async def test_ai_with_real_data():
    """測試AI系統使用真實MAX數據"""
    print("🚀 AI系統 + 真實MAX數據測試")
    print("=" * 60)
    
    max_client = None
    
    try:
        # 創建數據客戶端和AI管理器
        print("📊 初始化數據客戶端...")
        max_client = create_max_client()
        
        print("🤖 初始化AI協作管理器...")
        ai_manager = create_ai_manager(str(project_root / "config" / "ai_models.json"))
        
        # 獲取真實市場數據
        print("\n📈 獲取台灣MAX真實市場數據...")
        real_market_data = await max_client.get_enhanced_market_data("btctwd")
        
        if not real_market_data:
            print("❌ 無法獲取市場數據")
            return False
        
        # 顯示獲取的數據
        formatted_data = max_client.format_data_for_ai(real_market_data)
        print("✅ 成功獲取真實市場數據:")
        print(formatted_data)
        
        # 讓AI分析真實數據
        print("\n🧠 AI協作分析真實市場數據...")
        print("   🚀 市場掃描員分析中...")
        print("   🔍 深度分析師評估中...")
        print("   🧠 最終決策者決策中...")
        
        decision = await ai_manager.analyze_market_collaboratively(real_market_data)
        
        # 顯示AI分析結果
        print("\n" + "=" * 60)
        print("🎯 AI對真實市場的分析結果")
        print("=" * 60)
        
        print(f"📋 AI最終決策: {decision.final_decision}")
        print(f"💪 整體信心度: {decision.confidence:.1%}")
        print(f"🤝 AI共識水平: {decision.consensus_level:.1%}")
        print(f"⚠️ 風險等級: {decision.risk_level}")
        
        # 顯示決策理由
        print(f"\n📝 AI決策推理:")
        reasoning_lines = decision.reasoning.split('\n')
        for line in reasoning_lines[:10]:  # 只顯示前10行
            if line.strip():
                print(f"   {line.strip()}")
        
        # 分析AI對真實數據的反應
        print(f"\n🔍 AI對真實市場數據的反應分析:")
        
        current_price = real_market_data.get('current_price', 0)
        rsi = real_market_data.get('rsi', 50)
        volume_ratio = real_market_data.get('volume_ratio', 1.0)
        macd_trend = real_market_data.get('macd_trend', '中性')
        
        print(f"   💰 當前BTC價格: {current_price:,.0f} TWD")
        print(f"   📊 RSI指標: {rsi:.1f} ({'超買' if rsi > 70 else '超賣' if rsi < 30 else '中性'})")
        print(f"   📈 成交量: {volume_ratio:.2f}倍 ({'異常' if volume_ratio > 1.5 else '正常'})")
        print(f"   🔄 MACD趨勢: {macd_trend}")
        
        # 評估AI決策的合理性
        print(f"\n🎯 AI決策合理性評估:")
        
        decision_score = 0
        explanations = []
        
        # RSI合理性
        if rsi < 30 and decision.final_decision == "BUY":
            decision_score += 30
            explanations.append("✅ RSI超賣時建議買入，合理")
        elif rsi > 70 and decision.final_decision == "SELL":
            decision_score += 30
            explanations.append("✅ RSI超買時建議賣出，合理")
        elif 30 <= rsi <= 70 and decision.final_decision == "HOLD":
            decision_score += 20
            explanations.append("✅ RSI中性時保持觀望，穩健")
        
        # 成交量合理性
        if volume_ratio > 1.5 and decision.final_decision != "HOLD":
            decision_score += 25
            explanations.append("✅ 成交量異常時積極決策，敏銳")
        elif volume_ratio <= 1.5 and decision.final_decision == "HOLD":
            decision_score += 15
            explanations.append("✅ 成交量正常時保守決策，穩健")
        
        # MACD合理性
        if "金叉" in macd_trend and decision.final_decision == "BUY":
            decision_score += 25
            explanations.append("✅ MACD金叉時建議買入，正確")
        elif "死叉" in macd_trend and decision.final_decision == "SELL":
            decision_score += 25
            explanations.append("✅ MACD死叉時建議賣出，正確")
        
        # 信心度合理性
        if decision.confidence > 0.7:
            decision_score += 20
            explanations.append("✅ 高信心度決策，AI很確定")
        elif decision.confidence > 0.5:
            decision_score += 10
            explanations.append("✅ 中等信心度，AI較為謹慎")
        
        print(f"   📊 決策合理性評分: {decision_score}/100")
        for explanation in explanations:
            print(f"   {explanation}")
        
        # 顯示各AI的表現
        print(f"\n🤖 各AI模型表現:")
        for response in decision.ai_responses:
            if response.success:
                print(f"   {response.ai_role}: ✅ 成功 ({response.processing_time:.1f}秒)")
            else:
                print(f"   {response.ai_role}: ❌ 失敗")
        
        # 性能統計
        stats = ai_manager.get_performance_stats()
        print(f"\n📊 系統性能:")
        print(f"   平均處理時間: {stats['average_processing_time']:.1f}秒")
        print(f"   決策成功率: {stats['successful_decisions']}/{stats['total_decisions']}")
        
        print("\n" + "=" * 60)
        print("🎉 AI真實數據分析測試完成！")
        
        # 給出最終評估
        if decision_score >= 80:
            print("💡 評估結果: AI決策非常合理，可以考慮實際應用")
        elif decision_score >= 60:
            print("💡 評估結果: AI決策基本合理，需要進一步優化")
        elif decision_score >= 40:
            print("💡 評估結果: AI決策有一定邏輯，但需要改進")
        else:
            print("💡 評估結果: AI決策需要大幅改進")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False
    
    finally:
        if max_client:
            await max_client.close()

def main():
    """主函數"""
    print("🔧 準備測試AI系統使用真實數據...")
    
    # 運行異步測試
    success = asyncio.run(test_ai_with_real_data())
    
    if success:
        print("\n✅ 真實數據AI測試成功！")
        print("🚀 AI已經能夠分析真實的台灣MAX市場數據")
        print("📈 下一步可以考慮實際交易整合")
    else:
        print("\n❌ 真實數據AI測試失敗")

if __name__ == "__main__":
    main()