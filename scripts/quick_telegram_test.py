#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試Telegram雙向機器人
"""

import asyncio
import sys
import os

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.notifications.telegram_bot import TelegramBot

async def test_bot():
    """測試機器人"""
    print("🤖 啟動Telegram雙向機器人測試...")
    
    # 使用你的配置
    bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
    chat_id = "8164385222"
    
    # 創建機器人
    bot = TelegramBot(bot_token, chat_id)
    
    print("✅ 機器人已創建")
    print("📱 現在可以在手機上發送指令測試：")
    print("   • /help 或 幫助")
    print("   • /status 或 狀態") 
    print("   • /price 或 價格")
    print("   • /macd 或 指標")
    print("   • /signals 或 信號")
    print("   • /profit 或 獲利")
    print("\n🔄 機器人開始監聽...")
    print("按 Ctrl+C 停止")
    
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n👋 機器人已停止")

if __name__ == "__main__":
    asyncio.run(test_bot())