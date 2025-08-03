#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動Telegram雙向機器人
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.notifications.telegram_bot import TelegramBot
from config.telegram_config import telegram_config

def setup_logging():
    """設置日誌"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/telegram_bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def check_configuration():
    """檢查配置"""
    if not telegram_config.is_configured():
        print("❌ Telegram配置不完整！")
        print("\n請設置以下配置：")
        print("1. 創建Telegram機器人並獲取Bot Token")
        print("2. 獲取你的Chat ID")
        print("3. 在config/telegram_secrets.txt中設置：")
        print("   BOT_TOKEN=你的機器人token")
        print("   CHAT_ID=你的聊天ID")
        print("\n或者設置環境變量：")
        print("   TELEGRAM_BOT_TOKEN=你的機器人token")
        print("   TELEGRAM_CHAT_ID=你的聊天ID")
        return False
    return True

async def main():
    """主函數"""
    print("🤖 AImax Telegram雙向機器人")
    print("=" * 50)
    
    # 檢查配置
    if not check_configuration():
        return
    
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 創建機器人實例
        bot = TelegramBot(
            telegram_config.get_bot_token(),
            telegram_config.get_chat_id()
        )
        
        print(f"✅ 機器人配置完成")
        print(f"📱 Chat ID: {telegram_config.get_chat_id()}")
        print(f"⏰ 啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🚀 機器人開始運行...")
        print("\n💡 支持的指令：")
        print("   /help 或 幫助 - 顯示幫助")
        print("   /status 或 狀態 - 系統狀態")
        print("   /price 或 價格 - 當前價格")
        print("   /macd 或 指標 - MACD指標")
        print("   /signals 或 信號 - 交易信號")
        print("   /profit 或 獲利 - 獲利統計")
        print("   /stop - 停止機器人")
        print("\n按 Ctrl+C 停止機器人")
        print("-" * 50)
        
        # 運行機器人
        await bot.run()
        
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信號，正在關閉機器人...")
        logger.info("機器人被用戶手動停止")
    except Exception as e:
        print(f"\n❌ 機器人運行時發生錯誤: {e}")
        logger.error(f"機器人運行錯誤: {e}")
    finally:
        print("👋 機器人已停止運行")

if __name__ == "__main__":
    # 確保logs目錄存在
    os.makedirs('logs', exist_ok=True)
    
    # 運行機器人
    asyncio.run(main())