#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試用戶的Telegram設置
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.notifications.telegram_service import TelegramService

def test_telegram():
    """測試Telegram通知"""
    
    # 用戶的Telegram設置
    bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
    chat_id = "8164385222"
    
    print("🔧 測試Telegram連接...")
    
    try:
        # 創建Telegram服務
        telegram_service = TelegramService(bot_token, chat_id)
        
        # 測試基本連接
        print("📱 發送測試消息...")
        if telegram_service.test_connection():
            print("✅ 基本連接測試成功！")
        else:
            print("❌ 基本連接測試失敗")
            return
        
        # 測試交易信號通知
        print("📊 測試交易信號通知...")
        macd_data = {
            'hist': 25.67,
            'macd': -45.23,
            'signal': -70.90
        }
        
        additional_info = """
📊 <b>信號分析</b>:
信號強度: 🔥 強
🟢 低風險 - 深度超賣反彈
💎 優質信號，建議執行

🔍 <b>技術細節</b>:
• MACD柱狀圖轉正，動能增強
• MACD背離度: 25.67
• 柱狀圖動能: 25.67

💡 <b>操作建議</b>: 💎 優質信號，建議執行
        """.strip()
        
        if telegram_service.send_trading_signal("buy", 3500000, 9, macd_data, additional_info):
            print("✅ 交易信號通知測試成功！")
        else:
            print("❌ 交易信號通知測試失敗")
        
        # 測試回測總結通知
        print("📈 測試回測總結通知...")
        statistics = {
            'total_profit': 108774,
            'complete_pairs': 8,
            'buy_count': 9,
            'sell_count': 8,
            'average_profit': 13597,
            'average_hold_time': 23.6,
            'position_status': '持倉',
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
        
        if telegram_service.send_backtest_summary(statistics):
            print("✅ 回測總結通知測試成功！")
        else:
            print("❌ 回測總結通知測試失敗")
        
        # 測試系統狀態通知
        print("🔔 測試系統狀態通知...")
        if telegram_service.send_system_status("即時監控已啟動", "系統將每小時自動檢測新的MACD交易信號"):
            print("✅ 系統狀態通知測試成功！")
        else:
            print("❌ 系統狀態通知測試失敗")
        
        print("\n🎉 所有Telegram通知測試完成！")
        print("現在你可以在即時監控系統中使用Telegram通知功能了。")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_telegram()