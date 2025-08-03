#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Telegram通知功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.notifications.telegram_service import initialize_telegram_service
from config.telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def test_telegram_notifications():
    """測試Telegram通知功能"""
    print("🔍 測試Telegram通知功能...")
    
    try:
        # 初始化Telegram服務
        telegram_service = initialize_telegram_service(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        
        # 測試1: 基本連接測試
        print("\n📱 測試1: 基本連接測試")
        if telegram_service.test_connection():
            print("✅ 連接測試成功")
        else:
            print("❌ 連接測試失敗")
            return
        
        # 測試2: 交易信號通知
        print("\n📊 測試2: 交易信號通知")
        test_macd_data = {
            'hist': 15.67,
            'macd': 25.43,
            'signal': 18.92
        }
        
        if telegram_service.send_trading_signal(
            signal_type='buy',
            price=3500000,
            sequence=1,
            macd_data=test_macd_data,
            additional_info="📋 這是一個測試買進信號"
        ):
            print("✅ 買進信號通知發送成功")
        else:
            print("❌ 買進信號通知發送失敗")
        
        # 測試3: 回測總結通知
        print("\n📈 測試3: 回測總結通知")
        test_statistics = {
            'total_profit': 108774,
            'complete_pairs': 8,
            'buy_count': 9,
            'sell_count': 8,
            'average_profit': 13597,
            'average_hold_time': 23.6,
            'position_status': '空倉',
            'next_trade_sequence': 10,
            'trade_pairs': [
                {'profit': 37504},
                {'profit': -5841},
                {'profit': -8913},
                {'profit': 28000},
                {'profit': 2958},
                {'profit': 50933},
                {'profit': -3445},
                {'profit': 7577}
            ]
        }
        
        if telegram_service.send_backtest_summary(test_statistics):
            print("✅ 回測總結通知發送成功")
        else:
            print("❌ 回測總結通知發送失敗")
        
        # 測試4: 系統狀態通知
        print("\n🔧 測試4: 系統狀態通知")
        if telegram_service.send_system_status(
            status="系統測試完成",
            details="所有Telegram通知功能測試完畢，系統運行正常。"
        ):
            print("✅ 系統狀態通知發送成功")
        else:
            print("❌ 系統狀態通知發送失敗")
        
        print("\n🎉 Telegram通知功能測試完成！")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_telegram_notifications()