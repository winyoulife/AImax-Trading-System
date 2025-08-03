#!/usr/bin/env python3
"""
比對我們計算的 MACD 數值與你提供的參考數據

檢查我們的實時 MACD 服務是否與你之前給的 MAX 參考數據一致
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from datetime import datetime
from src.data.live_macd_service import LiveMACDService

# 你之前提供的參考數據 (7小時連續數據)
YOUR_REFERENCE_DATA = [
    {
        'timestamp': '2025-07-30 05:00',
        'price': 3520000.0,
        'histogram': -2877.2,
        'macd': -3124.9,
        'signal': -247.7
    },
    {
        'timestamp': '2025-07-30 06:00',
        'price': 3519738.5,
        'histogram': -2160.4,
        'macd': -2948.2,
        'signal': -787.8
    },
    {
        'timestamp': '2025-07-30 07:00',
        'price': 3519738.5,
        'histogram': -1317.1,
        'macd': -2434.1,
        'signal': -1117.1
    },
    {
        'timestamp': '2025-07-30 08:00',
        'price': 3520000.0,
        'histogram': -1059.5,
        'macd': -2441.4,
        'signal': -1381.9
    },
    {
        'timestamp': '2025-07-30 09:00',
        'price': 3520000.0,
        'histogram': -756.2,
        'macd': -2327.2,
        'signal': -1571.0
    },
    {
        'timestamp': '2025-07-30 10:00',
        'price': 3520945.1,
        'histogram': -83.9,
        'macd': -1675.8,
        'signal': -1592.0
    },
    {
        'timestamp': '2025-07-30 11:00',
        'price': 3522000.0,
        'histogram': 731.6,
        'macd': -677.4,
        'signal': -1409.0
    }
]

async def compare_with_reference():
    """比對我們的計算結果與參考數據"""
    
    print("🔍 比對 MACD 計算結果與參考數據")
    print("=" * 80)
    print("參考數據來源: 你之前提供的 MAX 真實數據 (2025-07-30 05:00-11:00)")
    print("計算數據來源: 我們的實時 MACD 服務 (使用 MAX API)")
    print()
    
    service = LiveMACDService()
    
    try:
        # 獲取當前的 MACD 數據
        print("📡 正在獲取當前 MACD 數據...")
        current_macd = await service.get_live_macd("btctwd", "60")
        
        if not current_macd:
            print("❌ 無法獲取當前 MACD 數據")
            return
        
        print(f"✅ 獲取成功，當前時間: {current_macd['timestamp']}")
        print()
        
        # 顯示參考數據
        print("📋 你提供的參考數據:")
        print("-" * 80)
        print(f"{'時間':15s} {'價格':>10s} {'柱狀圖':>10s} {'MACD':>10s} {'信號線':>10s}")
        print("-" * 80)
        
        for ref in YOUR_REFERENCE_DATA:
            print(f"{ref['timestamp']:15s} "
                  f"{ref['price']:10.0f} "
                  f"{ref['histogram']:10.1f} "
                  f"{ref['macd']:10.1f} "
                  f"{ref['signal']:10.1f}")
        
        print()
        
        # 顯示當前計算結果
        print("🧮 我們當前的計算結果:")
        print("-" * 80)
        current_time = current_macd['timestamp'].strftime('%Y-%m-%d %H:%M')
        macd_data = current_macd['macd']
        
        print(f"{current_time:15s} "
              f"{current_macd['price']:10.0f} "
              f"{macd_data['histogram']:10.1f} "
              f"{macd_data['macd_line']:10.1f} "
              f"{macd_data['signal_line']:10.1f}")
        
        print()
        
        # 檢查是否有匹配的時間點
        matching_ref = None
        for ref in YOUR_REFERENCE_DATA:
            if ref['timestamp'] == current_time:
                matching_ref = ref
                break
        
        if matching_ref:
            print("🎯 找到匹配的時間點，進行精確比對:")
            print("=" * 80)
            
            # 計算差異
            hist_diff = abs(macd_data['histogram'] - matching_ref['histogram'])
            macd_diff = abs(macd_data['macd_line'] - matching_ref['macd'])
            signal_diff = abs(macd_data['signal_line'] - matching_ref['signal'])
            
            print(f"{'指標':10s} {'參考值':>10s} {'計算值':>10s} {'差異':>10s} {'狀態':>10s}")
            print("-" * 60)
            print(f"{'柱狀圖':10s} {matching_ref['histogram']:10.1f} {macd_data['histogram']:10.1f} {hist_diff:10.1f} {'✅' if hist_diff < 1 else '❌'}")
            print(f"{'MACD線':10s} {matching_ref['macd']:10.1f} {macd_data['macd_line']:10.1f} {macd_diff:10.1f} {'✅' if macd_diff < 1 else '❌'}")
            print(f"{'信號線':10s} {matching_ref['signal']:10.1f} {macd_data['signal_line']:10.1f} {signal_diff:10.1f} {'✅' if signal_diff < 1 else '❌'}")
            
            # 總體評估
            total_diff = hist_diff + macd_diff + signal_diff
            print(f"\n📊 總體差異: {total_diff:.1f}")
            
            if total_diff < 3:
                print("🎉 結果: 非常接近，計算方法基本正確！")
            elif total_diff < 10:
                print("✅ 結果: 相當接近，可能有小的參數差異")
            elif total_diff < 50:
                print("⚠️  結果: 有一定差異，可能需要調整計算方法")
            else:
                print("❌ 結果: 差異較大，計算方法可能不同")
        
        else:
            print("⏰ 當前時間點不在參考數據範圍內")
            print("參考數據時間範圍: 2025-07-30 05:00 - 11:00")
            print(f"當前時間: {current_time}")
            print()
            print("💡 建議:")
            print("1. 等待到參考數據的時間點再進行比對")
            print("2. 或者獲取歷史數據進行比對")
        
        # 顯示趨勢比較
        print("\n📈 趨勢分析比較:")
        print("-" * 40)
        
        # 參考數據的趨勢 (從負值到正值的金叉過程)
        print("參考數據趨勢:")
        print("  05:00-11:00 顯示了完整的金叉過程")
        print("  柱狀圖從 -2877.2 上升到 +731.6")
        print("  這是典型的 MACD 金叉信號")
        
        print(f"\n當前計算趨勢:")
        print(f"  信號: {current_macd['trend']['signal']}")
        print(f"  動能: {current_macd['trend']['trend']}")
        
    finally:
        await service.close()

async def get_historical_comparison():
    """嘗試獲取歷史數據進行比對"""
    print("\n🕐 嘗試獲取歷史數據進行比對...")
    
    service = LiveMACDService()
    
    try:
        # 獲取更多歷史數據
        klines = await service._fetch_klines("btctwd", "60", 200)
        
        if klines is None:
            print("❌ 無法獲取歷史數據")
            return
        
        # 計算 MACD
        macd_df = service._calculate_macd(klines, 12, 26, 9)
        
        if macd_df is None:
            print("❌ 無法計算歷史 MACD")
            return
        
        print(f"✅ 獲取了 {len(macd_df)} 個歷史數據點")
        
        # 查找匹配的時間點
        matches_found = 0
        total_diff = 0
        
        print("\n🔍 查找匹配的歷史數據點:")
        print("-" * 100)
        print(f"{'時間':15s} {'參考柱狀':>10s} {'計算柱狀':>10s} {'差異':>8s} {'參考MACD':>10s} {'計算MACD':>10s} {'差異':>8s} {'狀態':>8s}")
        print("-" * 100)
        
        for _, row in macd_df.iterrows():
            row_time = row['datetime'].strftime('%Y-%m-%d %H:%M')
            
            # 查找匹配的參考數據
            matching_ref = None
            for ref in YOUR_REFERENCE_DATA:
                if ref['timestamp'] == row_time:
                    matching_ref = ref
                    break
            
            if matching_ref:
                hist_diff = abs(row['macd_hist'] - matching_ref['histogram'])
                macd_diff = abs(row['macd'] - matching_ref['macd'])
                
                status = "✅" if (hist_diff + macd_diff) < 10 else "❌"
                
                print(f"{row_time:15s} "
                      f"{matching_ref['histogram']:10.1f} "
                      f"{row['macd_hist']:10.1f} "
                      f"{hist_diff:8.1f} "
                      f"{matching_ref['macd']:10.1f} "
                      f"{row['macd']:10.1f} "
                      f"{macd_diff:8.1f} "
                      f"{status:>8s}")
                
                matches_found += 1
                total_diff += hist_diff + macd_diff
        
        if matches_found > 0:
            avg_diff = total_diff / matches_found
            print(f"\n📊 比對結果:")
            print(f"   匹配點數: {matches_found}")
            print(f"   平均差異: {avg_diff:.1f}")
            
            if avg_diff < 5:
                print("🎉 結論: 我們的計算與你的參考數據非常接近！")
            elif avg_diff < 20:
                print("✅ 結論: 計算結果相當準確，有小的差異")
            else:
                print("⚠️  結論: 存在一定差異，可能需要調整算法")
        else:
            print("\n❌ 沒有找到匹配的歷史數據點")
            print("可能的原因:")
            print("1. 參考數據的時間點不在當前獲取的歷史數據範圍內")
            print("2. 時間格式不匹配")
            print("3. MAX API 的歷史數據有限")
    
    finally:
        await service.close()

async def main():
    """主函數"""
    print("🔬 MACD 數值比對工具")
    print("=" * 50)
    
    # 先進行當前數據比對
    await compare_with_reference()
    
    # 再嘗試歷史數據比對
    await get_historical_comparison()
    
    print("\n" + "=" * 50)
    print("💡 總結:")
    print("1. 如果差異很小(<5)，說明我們的計算方法正確")
    print("2. 如果差異較大，可能是:")
    print("   - 使用了不同的歷史數據")
    print("   - EMA 計算方法略有不同")
    print("   - 數據更新時間差異")
    print("3. 最準確的比對方式是在相同時間點進行實時比對")

if __name__ == "__main__":
    asyncio.run(main())