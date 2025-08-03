#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型性能測試 - 比較不同模型配置的速度和質量
"""

import sys
import os
import asyncio
from pathlib import Path
import time
import json

# 添加src目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai.ai_manager import create_ai_manager
from data.market_enhancer import create_market_enhancer

async def test_model_configuration(config_name: str, config_path: str):
    """測試特定模型配置"""
    print(f"\n🧪 測試配置: {config_name}")
    print("-" * 50)
    
    market_enhancer = None
    
    try:
        # 創建市場數據增強器
        market_enhancer = create_market_enhancer()
        
        # 創建AI管理器（使用指定配置）
        ai_manager = create_ai_manager(config_path)
        
        # 獲取市場數據
        data_start = time.time()
        enhanced_data = await market_enhancer.get_enhanced_market_data("btctwd")
        data_time = time.time() - data_start
        
        if not enhanced_data:
            print("❌ 無法獲取市場數據")
            return None
        
        # 準備AI輸入數據
        ai_input_data = enhanced_data.basic_data.copy()
        ai_input_data.update(enhanced_data.technical_indicators)
        ai_input_data['ai_formatted_data'] = enhanced_data.ai_formatted_data
        
        # AI分析
        ai_start = time.time()
        decision = await ai_manager.analyze_market_collaboratively(ai_input_data)
        ai_time = time.time() - ai_start
        
        total_time = data_time + ai_time
        
        # 計算各AI模型的時間
        ai_times = {}
        for response in decision.ai_responses:
            if response.success:
                ai_times[response.ai_role] = response.processing_time
        
        # 返回測試結果
        result = {
            'config_name': config_name,
            'data_time': data_time,
            'ai_time': ai_time,
            'total_time': total_time,
            'ai_times': ai_times,
            'decision': decision.final_decision,
            'confidence': decision.confidence,
            'consensus': decision.consensus_level,
            'risk_level': decision.risk_level,
            'success_count': sum(1 for r in decision.ai_responses if r.success),
            'total_ai_count': len(decision.ai_responses)
        }
        
        # 顯示結果
        print(f"⏱️ 數據獲取: {data_time:.2f}秒")
        print(f"🧠 AI分析: {ai_time:.2f}秒")
        print(f"🎯 總時間: {total_time:.2f}秒")
        print(f"📋 決策: {decision.final_decision} (信心度: {decision.confidence:.1%})")
        print(f"🤝 共識: {decision.consensus_level:.1%}")
        
        print("🤖 各AI表現:")
        for role, processing_time in ai_times.items():
            print(f"   {role}: {processing_time:.2f}秒")
        
        return result
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return None
    
    finally:
        if market_enhancer:
            await market_enhancer.close()

async def run_performance_comparison():
    """運行性能比較測試"""
    print("🚀 AI模型性能比較測試")
    print("=" * 60)
    
    # 測試配置列表
    test_configs = [
        ("原始配置 (qwen:14b + qwen2.5:14b)", str(project_root / "config" / "ai_models.json")),
        ("Mistral快速配置", str(project_root / "config" / "ai_models_fast.json")),
        ("Qwen7b中文配置", str(project_root / "config" / "ai_models_qwen7b.json")),
        ("混合最佳配置", str(project_root / "config" / "ai_models_hybrid.json"))
    ]
    
    results = []
    
    # 逐一測試每個配置
    for config_name, config_path in test_configs:
        if Path(config_path).exists():
            result = await test_model_configuration(config_name, config_path)
            if result:
                results.append(result)
            
            # 短暫延遲，避免模型切換問題
            await asyncio.sleep(2)
        else:
            print(f"⚠️ 配置文件不存在: {config_path}")
    
    # 分析和比較結果
    if results:
        print("\n" + "=" * 60)
        print("📊 性能比較分析")
        print("=" * 60)
        
        # 按總時間排序
        results_by_speed = sorted(results, key=lambda x: x['total_time'])
        
        print("🏃 速度排名:")
        for i, result in enumerate(results_by_speed, 1):
            print(f"{i}. {result['config_name']}: {result['total_time']:.2f}秒")
        
        # 按信心度排序
        results_by_confidence = sorted(results, key=lambda x: x['confidence'], reverse=True)
        
        print("\n💪 信心度排名:")
        for i, result in enumerate(results_by_confidence, 1):
            print(f"{i}. {result['config_name']}: {result['confidence']:.1%}")
        
        # 按共識水平排序
        results_by_consensus = sorted(results, key=lambda x: x['consensus'], reverse=True)
        
        print("\n🤝 共識水平排名:")
        for i, result in enumerate(results_by_consensus, 1):
            print(f"{i}. {result['config_name']}: {result['consensus']:.1%}")
        
        # 綜合評分
        print("\n🎯 綜合評分 (速度40% + 信心度30% + 共識30%):")
        
        # 計算標準化分數
        max_time = max(r['total_time'] for r in results)
        min_time = min(r['total_time'] for r in results)
        
        for result in results:
            # 速度分數 (時間越短分數越高)
            speed_score = (max_time - result['total_time']) / (max_time - min_time) if max_time != min_time else 1.0
            
            # 信心度分數
            confidence_score = result['confidence']
            
            # 共識分數
            consensus_score = result['consensus']
            
            # 綜合分數
            composite_score = speed_score * 0.4 + confidence_score * 0.3 + consensus_score * 0.3
            
            result['composite_score'] = composite_score
        
        # 按綜合分數排序
        results_by_composite = sorted(results, key=lambda x: x['composite_score'], reverse=True)
        
        for i, result in enumerate(results_by_composite, 1):
            print(f"{i}. {result['config_name']}: {result['composite_score']:.3f}")
            print(f"   (速度: {result['total_time']:.1f}s, 信心: {result['confidence']:.1%}, 共識: {result['consensus']:.1%})")
        
        # 推薦最佳配置
        best_config = results_by_composite[0]
        print(f"\n🏆 推薦配置: {best_config['config_name']}")
        print(f"   總時間: {best_config['total_time']:.2f}秒")
        print(f"   信心度: {best_config['confidence']:.1%}")
        print(f"   共識水平: {best_config['consensus']:.1%}")
        
        # 檢查是否達到性能目標
        target_time = 70  # 目標總時間
        
        print(f"\n🎯 性能目標達成情況:")
        for result in results:
            status = "✅" if result['total_time'] <= target_time else "❌"
            print(f"   {result['config_name']}: {result['total_time']:.1f}s / {target_time}s {status}")
        
        # 保存結果到文件
        results_file = project_root / "performance_test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 詳細結果已保存到: {results_file}")
        
        return best_config
    
    else:
        print("❌ 沒有成功的測試結果")
        return None

def main():
    """主函數"""
    print("🔧 準備進行AI模型性能比較...")
    
    # 運行異步測試
    best_config = asyncio.run(run_performance_comparison())
    
    if best_config:
        print(f"\n✅ 性能測試完成！")
        print(f"🏆 最佳配置: {best_config['config_name']}")
        print(f"📈 建議使用此配置進行後續開發")
        
        # 根據結果給出下一步建議
        if best_config['total_time'] <= 70:
            print("🚀 性能達標，可以進入實際交易測試階段")
        else:
            print("⚡ 需要進一步優化AI提示詞和參數")
    else:
        print("\n❌ 性能測試失敗")

if __name__ == "__main__":
    main()