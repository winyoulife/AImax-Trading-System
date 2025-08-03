#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Telegram機器人功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.telegram_config import telegram_config
from src.notifications.telegram_service import TelegramService

async def test_basic_message():
    """測試基本消息發送"""
    print("🔧 測試基本消息發送...")
    
    if not telegram_config.is_configured():
        print("❌ Telegram配置不完整，請先運行 setup_telegram_bot.py")
        return False
    
    service = TelegramService(
        telegram_config.get_bot_token(),
        telegram_config.get_chat_id()
    )
    
    test_message = f"""
🧪 <b>Telegram機器人測試</b>

✅ 基本消息發送測試
⏰ 測試時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

💡 如果你看到這條消息，說明機器人配置正確！
    """.strip()
    
    success = await service.send_message_async(test_message)
    
    if success:
        print("✅ 基本消息發送成功")
        return True
    else:
        print("❌ 基本消息發送失敗")
        return False

async def test_trading_signal():
    """測試交易信號通知"""
    print("🔧 測試交易信號通知...")
    
    service = TelegramService(
        telegram_config.get_bot_token(),
        telegram_config.get_chat_id()
    )
    
    # 模擬交易信號數據
    macd_data = {
        'hist': 25.67,
        'macd': 123.45,
        'signal': 98.78
    }
    
    success = service.send_trading_signal(
        signal_type='buy',
        price=45123.45,
        sequence=1,
        macd_data=macd_data,
        additional_info="🔥 強信號 - 建議執行\n💡 深度超賣區域反彈"
    )
    
    if success:
        print("✅ 交易信號通知發送成功")
        return True
    else:
        print("❌ 交易信號通知發送失敗")
        return False

async def test_system_status():
    """測試系統狀態通知"""
    print("🔧 測試系統狀態通知...")
    
    service = TelegramService(
        telegram_config.get_bot_token(),
        telegram_config.get_chat_id()
    )
    
    success = service.send_system_status(
        status="測試成功",
        details="所有功能測試通過，系統運行正常。"
    )
    
    if success:
        print("✅ 系統狀態通知發送成功")
        return True
    else:
        print("❌ 系統狀態通知發送失敗")
        return False

async def test_backtest_summary():
    """測試回測總結通知"""
    print("🔧 測試回測總結通知...")
    
    service = TelegramService(
        telegram_config.get_bot_token(),
        telegram_config.get_chat_id()
    )
    
    # 模擬回測統計數據
    statistics = {
        'total_profit': 108774,
        'complete_pairs': 54,
        'buy_count': 54,
        'sell_count': 54,
        'average_profit': 2014,
        'average_hold_time': 48.5,
        'position_status': '空倉',
        'next_trade_sequence': 55,
        'trade_pairs': [
            {'profit': 1500}, {'profit': 2300}, {'profit': -800},
            {'profit': 3200}, {'profit': 1100}
        ]
    }
    
    success = service.send_backtest_summary(statistics)
    
    if success:
        print("✅ 回測總結通知發送成功")
        return True
    else:
        print("❌ 回測總結通知發送失敗")
        return False

async def main():
    """主測試函數"""
    print("🧪 AImax Telegram機器人功能測試")
    print("=" * 50)
    
    # 檢查配置
    if not telegram_config.is_configured():
        print("❌ Telegram配置不完整！")
        print("請先運行: python scripts/setup_telegram_bot.py")
        return
    
    print(f"📱 Chat ID: {telegram_config.get_chat_id()}")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    # 執行測試
    tests = [
        ("基本消息", test_basic_message),
        ("交易信號", test_trading_signal),
        ("系統狀態", test_system_status),
        ("回測總結", test_backtest_summary)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"❌ {test_name}測試時發生錯誤: {e}")
            results.append((test_name, False))
            print()
    
    # 顯示測試結果
    print("📊 測試結果總結")
    print("-" * 20)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 總體結果: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！機器人配置正確，可以正常使用。")
    else:
        print("⚠️ 部分測試失敗，請檢查配置和網絡連接。")

if __name__ == "__main__":
    asyncio.run(main())