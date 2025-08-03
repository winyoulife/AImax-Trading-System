#!/usr/bin/env python3
"""
分析7/29為什麼沒有買進信號
"""

import pandas as pd

# 從CSV文件中讀取7/29的數據
def analyze_729_signals():
    print("🔍 分析7/29為什麼沒有買進信號...")
    print("=" * 50)
    
    # 讀取測試數據
    df = pd.read_csv('AImax/data/test_improved_macd_signals_20250730_194404.csv')
    
    # 篩選7/29的數據
    df_729 = df[df['時間'].str.contains('2025-07-29')]
    
    print("📊 7/29的MACD數據分析:")
    print("-" * 80)
    print(f"{'時間':15s} {'MACD線':>8s} {'信號線':>8s} {'柱狀圖':>8s} {'MACD<0':>8s} {'信號<0':>8s} {'柱<0':>6s}")
    print("-" * 80)
    
    for _, row in df_729.iterrows():
        time_str = row['時間'].split(' ')[1][:5]  # 只取時間部分
        macd = float(row['MACD線'])
        signal = float(row['信號線'])
        hist = float(row['柱狀圖'])
        
        macd_neg = macd < 0
        signal_neg = signal < 0
        hist_neg = hist < 0
        
        print(f"{time_str:15s} {macd:8.1f} {signal:8.1f} {hist:8.1f} {str(macd_neg):>8s} {str(signal_neg):>8s} {str(hist_neg):>6s}")
    
    print("\n🎯 買進信號條件分析:")
    print("買進信號需要滿足以下所有條件:")
    print("1. MACD柱為負 (macd_hist < 0)")
    print("2. MACD線突破信號線向上 (前一時點 macd <= signal，當前時點 macd > signal)")
    print("3. MACD線為負 (macd < 0)")
    print("4. 信號線為負 (signal < 0)")
    print("5. 當前為空倉狀態")
    
    print("\n📈 7/29的情況分析:")
    
    # 檢查每個時點是否滿足條件
    for i in range(1, len(df_729)):
        current = df_729.iloc[i]
        previous = df_729.iloc[i-1]
        
        time_str = current['時間'].split(' ')[1][:5]
        macd_curr = float(current['MACD線'])
        signal_curr = float(current['信號線'])
        hist_curr = float(current['柱狀圖'])
        
        macd_prev = float(previous['MACD線'])
        signal_prev = float(previous['信號線'])
        hist_prev = float(previous['柱狀圖'])
        
        # 檢查買進條件
        cond1 = hist_prev < 0  # MACD柱為負
        cond2 = macd_prev <= signal_prev and macd_curr > signal_curr  # MACD線突破信號線
        cond3 = macd_curr < 0  # MACD線為負
        cond4 = signal_curr < 0  # 信號線為負
        
        if cond2:  # 如果有突破，詳細分析
            print(f"\n⚡ {time_str} 發生MACD線突破信號線:")
            print(f"   條件1 (柱為負): {cond1} (前柱狀圖: {hist_prev:.1f})")
            print(f"   條件2 (線突破): {cond2} (前MACD: {macd_prev:.1f} <= 前信號: {signal_prev:.1f}, 當前MACD: {macd_curr:.1f} > 當前信號: {signal_curr:.1f})")
            print(f"   條件3 (MACD<0): {cond3} (當前MACD: {macd_curr:.1f})")
            print(f"   條件4 (信號<0): {cond4} (當前信號: {signal_curr:.1f})")
            print(f"   🎯 買進信號: {'✅' if all([cond1, cond2, cond3, cond4]) else '❌'}")
    
    print("\n💡 結論:")
    print("7/29期間，MACD和信號線都處於正值區域，不符合我們的買進條件。")
    print("我們的改進版規則要求：")
    print("- 買進信號必須在MACD和信號線都為負值時才觸發（低點買入）")
    print("- 7/29的MACD和信號線都是正值，所以沒有產生買進信號")
    print("- 這正是我們想要的效果：避免在高位買入！")

if __name__ == "__main__":
    analyze_729_signals()