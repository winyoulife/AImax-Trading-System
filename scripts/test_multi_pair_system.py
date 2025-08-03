#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對系統整合測試
測試多交易對MAX API客戶端和交易對管理器的協作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import time
from datetime import datetime
from data.multi_pair_max_client import create_multi_pair_client
from data.trading_pair_manager import create_trading_pair_manager

async def test_multi_pair_integration():
    """測試多交易對系統整合"""
    print("🚀 AImax 多交易對系統整合測試")
    print("=" * 50)
    
    # 創建組件
    print("🔧 初始化系統組件...")
    client = create_multi_pair_client()
    manager = create_trading_pair_manager()
    
    try:
        # 1. 測試交易對管理器
        print("\n📋 測試交易對管理器...")
        summary = manager.get_configuration_summary()
        print(f"   配置的交易對: {summary['enabled_count']} 個")
        print(f"   總風險權重: {summary['total_risk_weight']:.3f}")
        
        # 2. 測試客戶端狀態
        print("\n📊 測試多交易對客戶端...")
        status = client.get_pair_status_summary()
        print(f"   活躍交易對: {status['active_count']} 個")
        print(f"   錯誤交易對: {status['error_count']} 個")
        
        # 3. 測試數據獲取性能
        print("\n⚡ 測試數據獲取性能...")
        start_time = time.time()
        
        market_data = await client.get_multi_pair_market_data()
        
        fetch_time = time.time() - start_time
        print(f"   獲取耗時: {fetch_time:.3f} 秒")
        print(f"   成功獲取: {len(market_data)} 個交易對")
        
        # 4. 顯示市場數據摘要
        if market_data:
            print("\n💰 市場數據摘要:")
            for pair, data in market_data.items():
                price = data.get('current_price', 0)
                change_1m = data.get('price_change_1m', 0)
                change_5m = data.get('price_change_5m', 0)
                rsi = data.get('rsi', 50)
                volume_ratio = data.get('volume_ratio', 1.0)
                api_latency = data.get('api_latency', 0)
                
                print(f"   {pair:8} | {price:>10,.0f} TWD | "
                      f"1m:{change_1m:+6.2f}% | 5m:{change_5m:+6.2f}% | "
                      f"RSI:{rsi:5.1f} | Vol:{volume_ratio:4.1f}x | "
                      f"延遲:{api_latency*1000:4.0f}ms")
        
        # 5. 測試配置自動優化
        print("\n🔧 測試配置自動優化...")
        if market_data:
            optimization_result = manager.optimize_configurations(market_data)
            
            if optimization_result.get('optimized_pairs'):
                print(f"   優化項目: {len(optimization_result['optimized_pairs'])} 個")
                for item in optimization_result['optimized_pairs']:
                    print(f"     • {item}")
            else:
                print("   無需優化或優化間隔未到")
        
        # 6. 測試緩存效果
        print("\n💾 測試數據緩存效果...")
        start_time = time.time()
        
        cached_data = await client.get_multi_pair_market_data()
        
        cached_fetch_time = time.time() - start_time
        print(f"   緩存獲取耗時: {cached_fetch_time:.3f} 秒")
        print(f"   性能提升: {((fetch_time - cached_fetch_time) / fetch_time * 100):.1f}%")
        
        # 7. 測試錯誤處理
        print("\n🛡️ 測試錯誤處理...")
        
        # 嘗試獲取不存在的交易對
        invalid_data = await client.get_multi_pair_market_data(['INVALID'])
        print(f"   無效交易對處理: {'正常' if not invalid_data else '異常'}")
        
        # 檢查系統狀態
        final_status = client.get_pair_status_summary()
        print(f"   系統狀態: {final_status['active_count']} 活躍, {final_status['error_count']} 錯誤")
        
        # 8. 性能統計
        print("\n📈 性能統計:")
        print(f"   平均每個交易對獲取時間: {fetch_time / len(market_data):.3f} 秒")
        print(f"   並發效率: {len(market_data) / fetch_time:.1f} 交易對/秒")
        print(f"   緩存命中率: {((fetch_time - cached_fetch_time) / fetch_time * 100):.1f}%")
        
        # 9. 系統健康檢查
        print("\n🏥 系統健康檢查:")
        health_score = 0
        
        # 檢查數據完整性
        if market_data and len(market_data) >= 3:
            health_score += 25
            print("   ✅ 數據完整性: 良好")
        else:
            print("   ❌ 數據完整性: 問題")
        
        # 檢查響應時間
        if fetch_time < 2.0:
            health_score += 25
            print("   ✅ 響應時間: 優秀")
        elif fetch_time < 5.0:
            health_score += 15
            print("   ⚠️ 響應時間: 一般")
        else:
            print("   ❌ 響應時間: 過慢")
        
        # 檢查錯誤率
        if final_status['error_count'] == 0:
            health_score += 25
            print("   ✅ 錯誤率: 無錯誤")
        else:
            print(f"   ⚠️ 錯誤率: {final_status['error_count']} 個錯誤")
        
        # 檢查配置狀態
        if summary['enabled_count'] >= 3:
            health_score += 25
            print("   ✅ 配置狀態: 正常")
        else:
            print("   ⚠️ 配置狀態: 交易對過少")
        
        print(f"\n🎯 系統健康評分: {health_score}/100")
        
        if health_score >= 80:
            print("✅ 系統狀態: 優秀，可以投入生產使用")
        elif health_score >= 60:
            print("⚠️ 系統狀態: 良好，建議進行優化")
        else:
            print("❌ 系統狀態: 需要改進")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理資源
        await client.close()
        print("\n🔒 系統資源已清理")

def main():
    """主函數"""
    print(f"🕐 測試開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 運行異步測試
    asyncio.run(test_multi_pair_integration())
    
    print(f"\n🕐 測試結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 多交易對系統整合測試完成！")

if __name__ == "__main__":
    main()