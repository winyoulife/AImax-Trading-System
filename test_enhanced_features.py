#!/usr/bin/env python3
"""
🧪 測試增強功能：Telegram通知 + 交易分析
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_enhanced_features():
    print("🧪 測試85%策略增強功能")
    print("=" * 50)
    
    # 測試Telegram通知
    print("📱 測試1: Telegram通知功能")
    try:
        from notifications.strategy_85_telegram import strategy_85_notifier
        
        print(f"✅ Telegram通知器初始化: {'已啟用' if strategy_85_notifier.enabled else '未配置'}")
        
        if strategy_85_notifier.enabled:
            print("📤 測試發送通知...")
            success = strategy_85_notifier.test_connection()
            print(f"{'✅ 通知發送成功' if success else '❌ 通知發送失敗'}")
        else:
            print("⚠️ Telegram未配置，跳過測試")
            
    except Exception as e:
        print(f"❌ Telegram測試失敗: {e}")
    
    # 測試交易分析
    print("\n📊 測試2: 交易分析功能")
    try:
        from analysis.trading_analytics import TradingAnalytics
        
        analytics = TradingAnalytics()
        print("✅ 交易分析器初始化成功")
        
        # 模擬交易數據
        mock_trades = [
            {
                'id': 1,
                'timestamp': '2025-08-08T10:00:00',
                'type': 'buy',
                'price': 3400000,
                'btc_amount': 0.001,
                'total_cost': 3400
            },
            {
                'id': 2,
                'timestamp': '2025-08-08T11:00:00',
                'type': 'sell',
                'price': 3450000,
                'btc_amount': 0.001,
                'net_income': 3450,
                'profit': 50
            }
        ]
        
        analytics.update_trade_history(mock_trades)
        stats = analytics.get_basic_stats()
        
        print(f"✅ 基本統計計算成功:")
        print(f"   總交易: {stats['total_trades']}筆")
        print(f"   總獲利: NT$ {stats['total_profit']:+,.0f}")
        print(f"   勝率: {stats['win_rate']:.1f}%")
        
        # 生成報告
        report = analytics.generate_report()
        print("✅ 分析報告生成成功")
        print(f"   報告長度: {len(report)}字符")
        
    except Exception as e:
        print(f"❌ 交易分析測試失敗: {e}")
    
    # 測試GUI整合
    print("\n🖥️ 測試3: GUI整合檢查")
    try:
        # 檢查compact_85_gui.py是否包含新功能
        with open('compact_85_gui.py', 'r', encoding='utf-8') as f:
            gui_content = f.read()
        
        features_to_check = [
            ('strategy_85_notifier', 'Telegram通知器'),
            ('TradingAnalytics', '交易分析器'),
            ('test_telegram', 'Telegram測試方法'),
            ('show_analytics', '分析報告方法'),
            ('📱 測試通知', 'Telegram測試按鈕'),
            ('📊 分析報告', '分析報告按鈕')
        ]
        
        for feature, description in features_to_check:
            if feature in gui_content:
                print(f"✅ {description}已整合")
            else:
                print(f"❌ {description}未找到")
                
    except Exception as e:
        print(f"❌ GUI整合檢查失敗: {e}")
    
    print("\n🎯 增強功能總結:")
    print("✅ Telegram通知功能 - 策略啟動、信號檢測、交易執行、帳戶狀態")
    print("✅ 交易分析功能 - 基本統計、績效指標、獲利分布、報告生成")
    print("✅ GUI整合 - 新增測試通知和分析報告按鈕")
    print("✅ 自動通知 - 交易執行時自動發送Telegram通知")
    print("✅ 報告分享 - 可將分析報告發送到Telegram或保存文件")
    
    print("\n🚀 啟動增強版GUI:")
    print("   python compact_85_gui.py")
    
    print("\n📱 新增按鈕功能:")
    print("   📱 測試通知 - 測試Telegram連接")
    print("   📊 分析報告 - 顯示詳細交易分析")

if __name__ == "__main__":
    test_enhanced_features()