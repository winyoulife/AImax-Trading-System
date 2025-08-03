#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對數據初始化腳本
初始化所有交易對的歷史數據和實時數據流
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import time
from datetime import datetime
from data.multi_pair_data_manager import create_multi_pair_data_manager

async def initialize_multi_pair_data():
    """初始化多交易對數據"""
    print("🚀 AImax 多交易對數據初始化")
    print("=" * 50)
    
    # 創建數據管理器
    print("🔧 初始化多交易對數據管理器...")
    manager = create_multi_pair_data_manager()
    
    try:
        # 1. 檢查當前狀態
        print("\n📊 檢查當前系統狀態...")
        status = manager.get_sync_status_summary()
        print(f"   配置的交易對: {status['total_pairs']} 個")
        print(f"   活躍交易對: {status['active_count']} 個")
        
        # 2. 初始化歷史數據
        print("\n📚 開始初始化歷史數據...")
        
        pairs_to_initialize = ['BTCTWD', 'ETHTWD', 'LTCTWD', 'BCHTWD']
        timeframes = ['1h', '5m', '1m']  # 從長期到短期
        
        total_initialized = 0
        
        for pair in pairs_to_initialize:
            print(f"\n🔄 初始化 {pair} 歷史數據...")
            
            for timeframe in timeframes:
                print(f"   📊 獲取 {timeframe} 數據...")
                
                try:
                    # 模擬歷史數據同步
                    start_time = time.time()
                    
                    # 檢查是否需要更新
                    needs_update = await manager._needs_historical_update(pair, timeframe)
                    
                    if needs_update:
                        # 獲取並保存歷史數據
                        synced_count = await manager._fetch_and_save_historical(pair, timeframe)
                        
                        elapsed_time = time.time() - start_time
                        
                        if synced_count > 0:
                            print(f"     ✅ 成功: {synced_count} 條記錄 ({elapsed_time:.2f}秒)")
                            total_initialized += synced_count
                        else:
                            print(f"     ⚠️ 無數據獲取")
                    else:
                        print(f"     ✅ 數據已是最新")
                    
                    # 避免API限制
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"     ❌ 失敗: {e}")
        
        print(f"\n📈 歷史數據初始化完成，總計: {total_initialized} 條記錄")
        
        # 3. 測試實時數據獲取
        print("\n📡 測試實時數據獲取...")
        
        # 獲取一次實時數據
        market_data = await manager.max_client.get_multi_pair_market_data()
        
        if market_data:
            print(f"   ✅ 成功獲取 {len(market_data)} 個交易對的實時數據")
            
            # 處理實時數據
            for pair, data in market_data.items():
                await manager._process_real_time_data(pair, data)
            
            print("   ✅ 實時數據處理完成")
        else:
            print("   ❌ 實時數據獲取失敗")
        
        # 4. 驗證數據完整性
        print("\n🔍 驗證數據完整性...")
        
        # 檢查歷史數據
        historical_data = manager.get_multi_pair_historical_data(
            pairs=pairs_to_initialize,
            timeframe='5m',
            limit=10
        )
        
        print(f"   歷史數據: {len(historical_data)} 個交易對")
        for pair, df in historical_data.items():
            print(f"     {pair}: {len(df)} 條記錄")
        
        # 檢查實時數據
        real_time_summary = manager.get_real_time_data_summary()
        print(f"   實時數據: {len(real_time_summary)} 個交易對")
        for pair, data in real_time_summary.items():
            price = data.get('price', 0)
            print(f"     {pair}: {price:,.0f} TWD")
        
        # 5. 更新同步狀態
        print("\n🔄 更新同步狀態...")
        
        final_status = manager.get_sync_status_summary()
        print(f"   活躍交易對: {final_status['active_count']}")
        print(f"   錯誤交易對: {final_status['error_count']}")
        
        # 6. 生成初始化報告
        print("\n📋 初始化報告:")
        print(f"   • 處理交易對: {len(pairs_to_initialize)} 個")
        print(f"   • 時間框架: {len(timeframes)} 個")
        print(f"   • 歷史記錄: {total_initialized} 條")
        print(f"   • 實時數據: {len(real_time_summary)} 個交易對")
        print(f"   • 數據庫文件: {manager.db_path}")
        
        # 7. 系統就緒檢查
        print("\n✅ 系統就緒檢查:")
        
        ready_score = 0
        
        if len(historical_data) >= 3:
            ready_score += 25
            print("   ✅ 歷史數據: 就緒")
        else:
            print("   ⚠️ 歷史數據: 不足")
        
        if len(real_time_summary) >= 3:
            ready_score += 25
            print("   ✅ 實時數據: 就緒")
        else:
            print("   ⚠️ 實時數據: 不足")
        
        if final_status['error_count'] == 0:
            ready_score += 25
            print("   ✅ 錯誤狀態: 無錯誤")
        else:
            print(f"   ⚠️ 錯誤狀態: {final_status['error_count']} 個錯誤")
        
        if total_initialized > 0:
            ready_score += 25
            print("   ✅ 數據初始化: 完成")
        else:
            print("   ⚠️ 數據初始化: 未完成")
        
        print(f"\n🎯 系統就緒評分: {ready_score}/100")
        
        if ready_score >= 80:
            print("🎉 系統初始化成功！多交易對數據管理系統已就緒")
        elif ready_score >= 60:
            print("⚠️ 系統基本就緒，建議檢查警告項目")
        else:
            print("❌ 系統初始化不完整，需要進一步處理")
        
    except Exception as e:
        print(f"❌ 初始化過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理資源
        await manager.close()
        print("\n🔒 系統資源已清理")

def main():
    """主函數"""
    print(f"🕐 初始化開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 運行異步初始化
    asyncio.run(initialize_multi_pair_data())
    
    print(f"\n🕐 初始化結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 多交易對數據初始化完成！")

if __name__ == "__main__":
    main()