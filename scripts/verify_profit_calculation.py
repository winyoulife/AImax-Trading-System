#!/usr/bin/env python3
"""
驗證總盈虧計算是否正確
"""

def verify_profit_calculation():
    print("🔍 驗證總盈虧計算...")
    print("=" * 50)
    
    # 從測試結果中的交易對詳情
    print("📊 完整交易對詳情 (從測試結果):")
    print("-" * 60)
    print(f"{'序號':>4s} {'買進時間':15s} {'賣出時間':15s} {'盈虧':>10s}")
    print("-" * 60)
    
    # 測試結果顯示的交易對
    trade_pairs = [
        {"sequence": 1, "buy_time": "07-24 06:00", "sell_time": "07-25 06:00", "profit": 2958.4},
        {"sequence": 2, "buy_time": "07-25 20:00", "sell_time": "07-27 05:00", "profit": 50932.8}
    ]
    
    total_profit = 0
    for pair in trade_pairs:
        print(f"{pair['sequence']:4d} {pair['buy_time']:15s} {pair['sell_time']:15s} {pair['profit']:10.1f}")
        total_profit += pair['profit']
    
    print("-" * 60)
    print(f"總盈虧計算: {trade_pairs[0]['profit']:.1f} + {trade_pairs[1]['profit']:.1f} = {total_profit:.1f} TWD")
    
    # 檢查是否與測試結果一致
    expected_total = 53891.2
    print(f"\n🎯 驗證結果:")
    print(f"計算得出: {total_profit:.1f} TWD")
    print(f"測試顯示: {expected_total:.1f} TWD")
    print(f"差異: {abs(total_profit - expected_total):.1f} TWD")
    
    if abs(total_profit - expected_total) < 0.1:
        print("✅ 計算正確！")
    else:
        print("❌ 計算有誤，需要檢查")
    
    print("\n💡 盈虧計算邏輯:")
    print("每筆交易的盈虧 = 賣出價格 - 買進價格")
    print("總盈虧 = 所有完整交易對的盈虧總和")
    print("注意：未平倉的交易不計入總盈虧")
    
    # 讓我們檢查實際的價格數據
    print("\n🔍 讓我們檢查實際的買賣價格...")
    
    # 從CSV文件中查找實際的買賣價格
    try:
        import pandas as pd
        df = pd.read_csv('AImax/data/test_improved_macd_signals_20250730_194404.csv')
        
        print("\n📈 實際交易價格驗證:")
        print("-" * 80)
        print(f"{'時間':15s} {'信號':12s} {'價格':>12s} {'說明':20s}")
        print("-" * 80)
        
        # 查找買賣信號的實際價格
        signals = df[df['交易信號'].str.contains('買|賣', na=False)]
        
        buy_prices = []
        sell_prices = []
        
        for _, row in signals.iterrows():
            time_str = row['時間'].split(' ')[1][:5]
            signal = row['交易信號']
            price = float(row['價格'])
            
            if '買' in signal:
                buy_prices.append(price)
                print(f"{time_str:15s} {signal:12s} {price:12,.0f} 買進價格")
            elif '賣' in signal:
                sell_prices.append(price)
                print(f"{time_str:15s} {signal:12s} {price:12,.0f} 賣出價格")
        
        print("\n💰 重新計算盈虧:")
        print("-" * 40)
        
        total_recalc = 0
        for i in range(min(len(buy_prices), len(sell_prices))):
            profit = sell_prices[i] - buy_prices[i]
            total_recalc += profit
            print(f"交易對 {i+1}: {sell_prices[i]:,.0f} - {buy_prices[i]:,.0f} = {profit:,.1f} TWD")
        
        print(f"\n重新計算總盈虧: {total_recalc:,.1f} TWD")
        print(f"系統計算總盈虧: {expected_total:,.1f} TWD")
        print(f"差異: {abs(total_recalc - expected_total):,.1f} TWD")
        
    except Exception as e:
        print(f"❌ 無法讀取CSV文件進行驗證: {e}")

if __name__ == "__main__":
    verify_profit_calculation()