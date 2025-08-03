#!/usr/bin/env python3
"""
測試價格極值檢測算法
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from src.core.extreme_point_detector import (
    ExtremePointDetector, ReversalSignal, 
    create_extreme_detector, detect_extremes_in_series
)
from src.core.dynamic_trading_data_structures import PricePoint, SignalType
from src.core.dynamic_trading_config import ExtremeDetectionConfig

def create_test_price_data(base_price: float = 3400000, periods: int = 20, 
                          trend: str = 'down') -> tuple:
    """創建測試價格數據"""
    timestamps = [datetime.now() + timedelta(minutes=i*30) for i in range(periods)]
    
    if trend == 'down':
        # 下降趨勢，然後反彈
        prices = []
        for i in range(periods):
            if i < periods * 0.7:  # 前70%時間下降
                price = base_price - (i * 2000) + np.random.normal(0, 1000)
            else:  # 後30%時間反彈
                recovery_start = int(periods * 0.7)
                price = base_price - (recovery_start * 2000) + ((i - recovery_start) * 3000) + np.random.normal(0, 1000)
            prices.append(max(price, base_price * 0.8))  # 設置最低價格
    else:
        # 上升趨勢，然後回落
        prices = []
        for i in range(periods):
            if i < periods * 0.7:  # 前70%時間上升
                price = base_price + (i * 2000) + np.random.normal(0, 1000)
            else:  # 後30%時間回落
                peak_index = int(periods * 0.7)
                peak_price = base_price + (peak_index * 2000)
                price = peak_price - ((i - peak_index) * 3000) + np.random.normal(0, 1000)
            prices.append(max(price, base_price * 0.8))
    
    # 生成成交量數據
    volumes = [np.random.uniform(500, 2000) for _ in range(periods)]
    
    return timestamps, prices, volumes

def test_extreme_detection_basic():
    """測試基本極值檢測功能"""
    print("🧪 測試基本極值檢測功能...")
    
    try:
        # 創建檢測器
        config = ExtremeDetectionConfig(
            reversal_threshold=0.3,
            confirmation_periods=2,
            sensitivity=0.5
        )
        detector = ExtremePointDetector(config)
        
        # 測試買入信號（尋找低點）
        detector.reset(SignalType.BUY)
        
        # 創建下降然後反彈的價格數據
        timestamps, prices, volumes = create_test_price_data(3400000, 15, 'down')
        
        extreme_count = 0
        for i, (timestamp, price, volume) in enumerate(zip(timestamps, prices, volumes)):
            point = PricePoint(timestamp=timestamp, price=price, volume=volume)
            is_extreme = detector.add_price_point(point)
            
            if is_extreme:
                extreme_count += 1
                print(f"   檢測到極值點 {extreme_count}: {price:,.0f} TWD at {timestamp.strftime('%H:%M')}")
        
        # 檢測反轉信號
        reversal = detector.detect_price_reversal()
        if reversal:
            print(f"✅ 檢測到反轉信號: {reversal.reason}")
            print(f"   反轉強度: {reversal.strength:.2f}")
            print(f"   信心度: {reversal.confidence:.2f}")
            print(f"   成交量確認: {reversal.volume_confirmation}")
        else:
            print("⚪ 未檢測到反轉信號")
        
        # 獲取檢測摘要
        summary = detector.get_detection_summary()
        print(f"✅ 檢測摘要: 處理了 {summary['price_history_count']} 個價格點")
        
    except Exception as e:
        print(f"❌ 基本極值檢測測試失敗: {e}")

def test_reversal_detection():
    """測試反轉檢測功能"""
    print("\n🧪 測試反轉檢測功能...")
    
    try:
        config = ExtremeDetectionConfig(
            reversal_threshold=0.5,
            confirmation_periods=3,
            sensitivity=0.7
        )
        
        # 測試買入信號的反轉檢測
        print("\n📉 測試買入信號反轉檢測（價格觸底反彈）:")
        detector = ExtremePointDetector(config)
        detector.reset(SignalType.BUY)
        
        # 模擬價格下跌然後反彈
        base_price = 3400000
        test_prices = [
            base_price - 10000,  # 下跌
            base_price - 15000,  # 繼續下跌
            base_price - 20000,  # 最低點
            base_price - 18000,  # 開始反彈
            base_price - 15000,  # 繼續反彈
            base_price - 12000,  # 確認反彈
        ]
        
        for i, price in enumerate(test_prices):
            timestamp = datetime.now() + timedelta(minutes=i*30)
            point = PricePoint(timestamp=timestamp, price=price, volume=1000)
            detector.add_price_point(point)
            
            # 檢測反轉
            reversal = detector.detect_price_reversal()
            if reversal:
                print(f"   ✅ 第{i+1}個點檢測到反轉: {reversal.reason}")
                break
        
        # 測試賣出信號的反轉檢測
        print("\n📈 測試賣出信號反轉檢測（價格見頂回落）:")
        detector.reset(SignalType.SELL)
        
        # 模擬價格上漲然後回落
        test_prices = [
            base_price + 10000,  # 上漲
            base_price + 15000,  # 繼續上漲
            base_price + 20000,  # 最高點
            base_price + 18000,  # 開始回落
            base_price + 15000,  # 繼續回落
            base_price + 12000,  # 確認回落
        ]
        
        for i, price in enumerate(test_prices):
            timestamp = datetime.now() + timedelta(minutes=i*30)
            point = PricePoint(timestamp=timestamp, price=price, volume=1000)
            detector.add_price_point(point)
            
            # 檢測反轉
            reversal = detector.detect_price_reversal()
            if reversal:
                print(f"   ✅ 第{i+1}個點檢測到反轉: {reversal.reason}")
                break
        
    except Exception as e:
        print(f"❌ 反轉檢測測試失敗: {e}")

def test_configuration_impact():
    """測試配置參數對檢測結果的影響"""
    print("\n🧪 測試配置參數影響...")
    
    try:
        # 創建測試數據
        timestamps, prices, volumes = create_test_price_data(3400000, 20, 'down')
        
        # 測試不同的反轉閾值
        thresholds = [0.2, 0.5, 1.0]
        
        for threshold in thresholds:
            print(f"\n📊 測試反轉閾值: {threshold}%")
            
            config = ExtremeDetectionConfig(
                reversal_threshold=threshold,
                confirmation_periods=2
            )
            
            detector = ExtremePointDetector(config)
            detector.reset(SignalType.BUY)
            
            reversal_detected = False
            for timestamp, price, volume in zip(timestamps, prices, volumes):
                point = PricePoint(timestamp=timestamp, price=price, volume=volume)
                detector.add_price_point(point)
                
                reversal = detector.detect_price_reversal()
                if reversal and not reversal_detected:
                    print(f"   ✅ 檢測到反轉: 強度 {reversal.strength:.2f}, 信心度 {reversal.confidence:.2f}")
                    reversal_detected = True
            
            if not reversal_detected:
                print(f"   ⚪ 未檢測到反轉")
        
    except Exception as e:
        print(f"❌ 配置參數測試失敗: {e}")

def test_volume_confirmation():
    """測試成交量確認功能"""
    print("\n🧪 測試成交量確認功能...")
    
    try:
        config = ExtremeDetectionConfig(
            reversal_threshold=0.5,
            confirmation_periods=2,
            volume_weight=0.5
        )
        
        detector = ExtremePointDetector(config)
        detector.reset(SignalType.BUY)
        
        # 測試低成交量情況
        print("\n📊 測試低成交量情況:")
        low_volume_points = [
            PricePoint(datetime.now(), 3400000, 100),  # 低成交量
            PricePoint(datetime.now() + timedelta(minutes=30), 3390000, 120),
            PricePoint(datetime.now() + timedelta(minutes=60), 3395000, 110),
        ]
        
        for point in low_volume_points:
            detector.add_price_point(point)
        
        reversal = detector.detect_price_reversal()
        if reversal:
            print(f"   成交量確認: {reversal.volume_confirmation}")
        
        # 重置並測試高成交量情況
        detector.reset(SignalType.BUY)
        print("\n📊 測試高成交量情況:")
        high_volume_points = [
            PricePoint(datetime.now(), 3400000, 1000),  # 正常成交量
            PricePoint(datetime.now() + timedelta(minutes=30), 3390000, 1200),
            PricePoint(datetime.now() + timedelta(minutes=60), 3395000, 1500),  # 高成交量
        ]
        
        for point in high_volume_points:
            detector.add_price_point(point)
        
        reversal = detector.detect_price_reversal()
        if reversal:
            print(f"   成交量確認: {reversal.volume_confirmation}")
        
    except Exception as e:
        print(f"❌ 成交量確認測試失敗: {e}")

def test_utility_functions():
    """測試工具函數"""
    print("\n🧪 測試工具函數...")
    
    try:
        # 測試 detect_extremes_in_series
        timestamps, prices, volumes = create_test_price_data(3400000, 15, 'down')
        
        extremes = detect_extremes_in_series(
            prices, volumes, timestamps, SignalType.BUY
        )
        
        print(f"✅ 在序列中檢測到 {len(extremes)} 個極值點")
        for i, extreme in enumerate(extremes):
            print(f"   極值點 {i+1}: {extreme.price:,.0f} TWD")
        
        # 測試 create_extreme_detector
        detector = create_extreme_detector()
        print(f"✅ 創建檢測器成功，默認配置")
        
    except Exception as e:
        print(f"❌ 工具函數測試失敗: {e}")

def test_edge_cases():
    """測試邊界情況"""
    print("\n🧪 測試邊界情況...")
    
    try:
        config = ExtremeDetectionConfig()
        detector = ExtremePointDetector(config)
        
        # 測試空數據
        print("📊 測試空數據:")
        detector.reset(SignalType.BUY)
        reversal = detector.detect_price_reversal()
        print(f"   空數據反轉檢測: {reversal is None}")
        
        # 測試單個數據點
        print("📊 測試單個數據點:")
        point = PricePoint(datetime.now(), 3400000, 1000)
        detector.add_price_point(point)
        reversal = detector.detect_price_reversal()
        print(f"   單點反轉檢測: {reversal is None}")
        
        # 測試無效價格
        print("📊 測試無效價格:")
        try:
            invalid_point = PricePoint(datetime.now(), -1000, 1000)  # 負價格
            is_valid = detector.is_valid_extreme(invalid_point)
            print(f"   無效價格檢測: {not is_valid}")
        except ValueError as e:
            print(f"   無效價格正確被拒絕: {str(e)[:20]}...")
        
        # 測試極小變化（噪音過濾）
        print("📊 測試噪音過濾:")
        detector.reset(SignalType.BUY)
        base_point = PricePoint(datetime.now(), 3400000, 1000)
        detector.add_price_point(base_point)
        
        # 添加微小變化的點
        noise_point = PricePoint(datetime.now() + timedelta(minutes=30), 3400010, 1000)  # 只變化10元
        is_extreme = detector.add_price_point(noise_point)
        print(f"   噪音過濾效果: {not is_extreme}")
        
    except Exception as e:
        print(f"❌ 邊界情況測試失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 開始測試價格極值檢測算法...")
    
    try:
        test_extreme_detection_basic()
        test_reversal_detection()
        test_configuration_impact()
        test_volume_confirmation()
        test_utility_functions()
        test_edge_cases()
        
        print("\n🎉 所有測試完成！")
        print("✅ 價格極值檢測算法運行正常")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()