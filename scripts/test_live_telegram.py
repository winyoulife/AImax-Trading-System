#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試即時監控系統的Telegram通知功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.notifications.telegram_service import initialize_telegram_service

def test_live_telegram():
    """測試即時監控系統的Telegram設置"""
    
    print("🔧 測試即時監控系統的Telegram通知...")
    
    try:
        # 使用與live_macd_monitor_gui.py相同的設置
        bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
        chat_id = "8164385222"
        
        # 初始化服務
        telegram_service = initialize_telegram_service(bot_token, chat_id)
        
        # 發送系統啟動通知
        startup_message = """
🚀 <b>AImax即時監控系統已啟動</b>

📊 <b>系統功能</b>:
• 1小時MACD策略監控
• 每小時自動更新數據
• 即時交易信號通知
• 詳細技術分析

💰 <b>歷史表現</b>:
• 總獲利: 108,774 TWD
• 勝率: 62.5%
• 平均每筆: 13,597 TWD

🔔 <b>通知設置</b>:
✅ Telegram通知已啟用
✅ 詳細信號分析已啟用
✅ 自動監控已準備就緒

💡 <i>系統將在每個整點小時自動檢測新的交易信號</i>
        """.strip()
        
        if telegram_service.send_message_sync(startup_message):
            print("✅ 系統啟動通知發送成功！")
        else:
            print("❌ 系統啟動通知發送失敗")
            return
        
        # 模擬一個交易信號通知
        print("📊 發送模擬交易信號...")
        
        macd_data = {
            'hist': 32.45,
            'macd': -67.89,
            'signal': -100.34
        }
        
        additional_info = """
📊 <b>信號分析</b>:
信號強度: 🔥 強
🟢 低風險 - 深度超賣反彈
💎 優質信號，建議執行

🔍 <b>技術細節</b>:
• MACD柱狀圖轉正，動能增強
• MACD背離度: 32.45
• 柱狀圖動能: 32.45

💡 <b>操作建議</b>: 💎 優質信號，建議執行

⚠️ <i>這是測試信號，非實際交易建議</i>
        """.strip()
        
        if telegram_service.send_trading_signal("buy", 3520000, 10, macd_data, additional_info):
            print("✅ 模擬交易信號發送成功！")
        else:
            print("❌ 模擬交易信號發送失敗")
        
        print("\n🎉 即時監控系統的Telegram通知測試完成！")
        print("你應該已經在Telegram中收到了系統啟動通知和模擬交易信號。")
        print("現在可以啟動即時監控系統了：python scripts/live_macd_monitor_gui.py")
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_live_telegram()