#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速AI系統測試 - 使用本地數據庫緩存，大幅提升速度
"""

import sys
import os
import asyncio
from pathlib import Path
import time

# 添加src目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai.ai_manager import create_ai_manager
from data.market_enhancer import create_market_enhancer
from data.historical_data_manager import create_historical_manager

async def test_fast_ai_system():
    """測試快速AI系統（使用本地數據庫）"""
    print("🚀 快速AI交易系統測試（本地數據庫版本）")
    print("=" * 60)
    
    market_enhancer = None
    historical_manager = None
    
    try:
        # 步驟1: 初始化歷史數據管理器
        print("📊 初始化歷史數據管理器...")
        historical_manager = create_historical_manager()
        
        # 檢查數據庫狀態
        stats = historical_manager.get_data_statistics("btctwd")
        print(f"   💾 數據庫大小: {stats.get('database_size_mb', 0):.2f} MB")
        
        timeframe_stats = stats.get('timeframe_stats', {})
        if timeframe_stats:
            print("   📈 現有數據:")
            for tf, info in timeframe_stats.items():
                print(f"     {tf}: {info['count']} 條記錄 (覆蓋 {info['coverage_hours']:.1f} 小時)")
        else:
            print("   📋 數據庫為空，將進行首次初始化...")
            
            # 首次初始化數據集
            print("🔄 正在初始化完整數據集...")
            init_start = time.time()
            success = await historical_manager.initialize_full_dataset("btctwd")
            init_time = time.time() - init_start
            
            if success:
                print(f"✅ 數據集初始化完成 ({init_time:.1f}秒)")
                
                # 重新獲取統計
                stats = historical_manager.get_data_statistics("btctwd")
                timeframe_stats = stats.get('timeframe_stats', {})
                print("   📈 初始化後數據:")
                for tf, info in timeframe_stats.items():
                    print(f"     {tf}: {info['count']} 條記錄")
            else:
                print("❌ 數據集初始化失敗")
                return False
        
        # 步驟2: 創建市場數據增強器
        print("\n🔧 初始化市場數據增強器...")
        market_enhancer = create_market_enhancer()
        
        # 步驟3: 創建AI管理器
        print("🤖 初始化AI協作管理器...")
        ai_manager = create_ai_manager(str(project_root / "config" / "ai_models.json"))
        
        # 步驟4: 測試數據獲取速度
        print("\n⚡ 測試數據獲取速度...")
        data_start = time.time()
        
        enhanced_data = await market_enhancer.get_enhanced_market_data("btctwd")
        
        data_time = time.time() - data_start
        
        if not enhanced_data:
            print("❌ 無法獲取增強市場數據")
            return False
        
        print(f"✅ 數據獲取完成 ({data_time:.2f}秒)")
        print(f"   📊 質量分數: {enhanced_data.quality_score:.1%}")
        print(f"   📈 技術指標數量: {len(enhanced_data.technical_indicators)}")
        
        # 檢查數據來源
        system_status = market_enhancer.get_system_status()
        data_sources = system_status['data_sources']
        print(f"   📡 數據來源狀態:")
        print(f"     MAX API: {'✅' if data_sources['max_api'] else '❌'}")
        print(f"     歷史數據庫: {'✅' if data_sources['historical_database'] else '❌'}")
        print(f"     技術指標: {'✅' if data_sources['technical_indicators'] else '❌'}")
        
        # 步驟5: 測試AI分析速度
        print("\n🧠 測試AI分析速度...")
        ai_start = time.time()
        
        # 準備AI輸入數據
        ai_input_data = enhanced_data.basic_data.copy()
        ai_input_data.update(enhanced_data.technical_indicators)
        ai_input_data['ai_formatted_data'] = enhanced_data.ai_formatted_data
        
        # AI協作分析
        decision = await ai_manager.analyze_market_collaboratively(ai_input_data)
        
        ai_time = time.time() - ai_start
        total_time = data_time + ai_time
        
        # 步驟6: 顯示結果
        print("\n" + "=" * 60)
        print("⚡ 快速AI系統測試結果")
        print("=" * 60)
        
        print(f"📋 AI最終決策: {decision.final_decision}")
        print(f"💪 整體信心度: {decision.confidence:.1%}")
        print(f"🤝 AI共識水平: {decision.consensus_level:.1%}")
        print(f"⚠️ 風險等級: {decision.risk_level}")
        
        # 性能對比
        print(f"\n⚡ 性能統計:")
        print(f"   📊 數據獲取時間: {data_time:.2f}秒")
        print(f"   🧠 AI分析時間: {ai_time:.2f}秒")
        print(f"   🎯 總處理時間: {total_time:.2f}秒")
        
        # 與目標性能對比
        target_times = {
            'data_acquisition': 10,  # 目標10秒內
            'ai_analysis': 60,       # 目標60秒內
            'total': 70              # 總目標70秒內
        }
        
        print(f"\n🎯 性能目標對比:")
        print(f"   📊 數據獲取: {data_time:.1f}s / {target_times['data_acquisition']}s {'✅' if data_time <= target_times['data_acquisition'] else '❌'}")
        print(f"   🧠 AI分析: {ai_time:.1f}s / {target_times['ai_analysis']}s {'✅' if ai_time <= target_times['ai_analysis'] else '❌'}")
        print(f"   🎯 總時間: {total_time:.1f}s / {target_times['total']}s {'✅' if total_time <= target_times['total'] else '❌'}")
        
        # 顯示關鍵市場指標
        print(f"\n📊 關鍵市場指標:")
        current_price = ai_input_data.get('current_price', 0)
        rsi = ai_input_data.get('medium_rsi', ai_input_data.get('rsi', 50))
        macd_signal = ai_input_data.get('medium_macd_signal_type', ai_input_data.get('macd_trend', '中性'))
        dominant_trend = ai_input_data.get('dominant_trend', '震盪')
        
        print(f"   💰 當前BTC價格: {current_price:,.0f} TWD")
        print(f"   📊 RSI指標: {rsi:.1f}")
        print(f"   🔄 MACD信號: {macd_signal}")
        print(f"   📈 主導趨勢: {dominant_trend}")
        
        # 各AI模型表現
        print(f"\n🤖 各AI模型表現:")
        for response in decision.ai_responses:
            if response.success:
                print(f"   {response.ai_role}: ✅ {response.processing_time:.1f}秒 (信心度: {response.confidence:.1%})")
            else:
                print(f"   {response.ai_role}: ❌ 失敗")
        
        # 數據庫效率統計
        print(f"\n💾 數據庫效率:")
        if data_sources['historical_database']:
            print("   ✅ 成功使用本地數據庫，避免重複API調用")
            print("   🚀 數據獲取速度大幅提升")
        else:
            print("   ⚠️ 回退到API獲取，建議檢查數據庫狀態")
        
        # 系統建議
        print(f"\n💡 系統優化建議:")
        if total_time > target_times['total']:
            print("   ⚡ 總處理時間超過目標，需要優化")
            if data_time > target_times['data_acquisition']:
                print("     📊 數據獲取較慢，檢查網絡或數據庫")
            if ai_time > target_times['ai_analysis']:
                print("     🧠 AI分析較慢，考慮優化提示詞或模型")
        else:
            print("   ✅ 系統性能達標，可以進入下一階段開發")
        
        print("\n" + "=" * 60)
        print("🎉 快速AI系統測試完成！")
        
        # 最終評估
        if total_time <= target_times['total'] and decision.confidence > 0.5:
            print("💡 評估結果: 系統性能優秀，準備進入實際交易測試")
            print("🚀 下一步: 按照MULTI_AI_TRADING_SYSTEM_PLAN進行Day 5-7的AI提示工程優化")
        elif total_time <= target_times['total'] * 1.5:
            print("💡 評估結果: 系統性能良好，需要微調")
            print("🔧 建議: 優化AI提示詞和決策邏輯")
        else:
            print("💡 評估結果: 系統需要進一步優化")
            print("⚠️ 建議: 檢查數據庫配置和AI模型設置")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if market_enhancer:
            await market_enhancer.close()
        if historical_manager:
            await historical_manager.close()

def main():
    """主函數"""
    print("🔧 準備測試快速AI系統...")
    
    # 檢查配置文件
    config_file = project_root / "config" / "ai_models.json"
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        return
    
    # 運行異步測試
    success = asyncio.run(test_fast_ai_system())
    
    if success:
        print("\n✅ 快速AI系統測試成功！")
        print("🚀 系統優勢:")
        print("   📊 本地數據庫緩存，避免重複API調用")
        print("   ⚡ 大幅提升數據獲取速度")
        print("   🔢 豐富的技術指標計算")
        print("   🤖 三AI協作決策")
        print("   📈 高質量的交易建議")
        print("\n📋 準備進入AI提示工程優化階段...")
    else:
        print("\n❌ 快速AI系統測試失敗")

if __name__ == "__main__":
    main()