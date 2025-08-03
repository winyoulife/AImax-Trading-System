#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
穩定的Telegram機器人測試
"""

import asyncio
import sys
import os
import logging

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.notifications.telegram_bot import TelegramBot

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_stable_bot():
    """穩定的機器人測試"""
    print("🤖 啟動穩定的Telegram雙向機器人...")
    
    # 使用你的配置
    bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
    chat_id = "8164385222"
    
    try:
        # 創建機器人
        bot = TelegramBot(bot_token, chat_id)
        
        print("✅ 機器人已創建並初始化")
        print("📱 支持的指令:")
        print("   中文: 狀態、價格、指標、信號、獲利、幫助")
        print("   英文: /status, /price, /macd, /signals, /profit, /help")
        print("\n🔄 機器人開始監聽...")
        print("💡 在手機上發送指令測試，按 Ctrl+C 停止")
        print("-" * 50)
        
        # 運行機器人
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信號")
        print("👋 機器人已停止運行")
    except Exception as e:
        print(f"\n❌ 機器人運行時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stable_bot())