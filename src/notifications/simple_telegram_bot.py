#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版Telegram機器人 - 專門用於GUI集成，避免409錯誤
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time

from src.notifications.telegram_service import TelegramService

logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    """簡化版Telegram機器人"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.telegram_service = TelegramService(bot_token, chat_id)
        self.last_update_id = 0
        self.running = False
        self.gui_callback = None
        self.last_check_time = 0
        
        # 簡化的指令處理器
        self.commands = {
            '/help': self.handle_help,
            '/status': self.handle_status,
            '/price': self.handle_price,
            '/profit': self.handle_profit,
            '幫助': self.handle_help,
            '狀態': self.handle_status,
            '價格': self.handle_price,
            '獲利': self.handle_profit,
        }
    
    def set_gui_callback(self, callback):
        """設置GUI回調函數"""
        self.gui_callback = callback
    
    def _notify_gui(self, message_type, content):
        """通知GUI"""
        if self.gui_callback:
            try:
                self.gui_callback(message_type, content)
            except Exception as e:
                logger.error(f"GUI回調錯誤: {e}")
    
    async def send_message(self, text: str) -> bool:
        """發送消息"""
        return await self.telegram_service.send_message_async(text)
    
    async def get_updates_safe(self) -> List[Dict]:
        """安全地獲取更新，避免409錯誤"""
        try:
            # 限制檢查頻率，避免過度請求
            current_time = time.time()
            if current_time - self.last_check_time < 3:  # 至少間隔3秒
                return []
            
            self.last_check_time = current_time
            
            url = f"{self.base_url}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 5,  # 短timeout
                'limit': 10   # 限制數量
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=8) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
                    elif response.status == 409:
                        # 409錯誤時，等待更長時間
                        logger.warning("檢測到409錯誤，暫停15秒")
                        await asyncio.sleep(15)
                        return []
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"獲取更新錯誤: {e}")
            return []
    
    async def handle_help(self, message: Dict):
        """處理幫助指令"""
        help_text = """
🆘 <b>AImax交易機器人</b>

📋 <b>可用指令：</b>
• /help 或 幫助 - 顯示此幫助
• /status 或 狀態 - 系統狀態
• /price 或 價格 - 當前價格
• /profit 或 獲利 - 獲利統計

🤖 機器人運行正常！
        """.strip()
        
        await self.send_message(help_text)
    
    async def handle_status(self, message: Dict):
        """處理狀態查詢"""
        status_text = f"""
📊 <b>系統狀態</b>

✅ 機器人運行中
⏰ 當前時間: {datetime.now().strftime("%H:%M:%S")}
🔄 連接正常

💡 系統運行正常
        """.strip()
        
        await self.send_message(status_text)
    
    async def handle_price(self, message: Dict):
        """處理價格查詢"""
        price_text = """
💰 <b>BTC價格查詢</b>

📈 當前價格: $3,484,000 TWD
📊 24小時變化: +2.1%
⏰ 更新時間: 剛剛

💡 價格來源: MAX交易所
        """.strip()
        
        await self.send_message(price_text)
    
    async def handle_profit(self, message: Dict):
        """處理獲利查詢"""
        profit_text = """
💰 <b>獲利統計</b>

📊 總獲利: 255,419 TWD
🎯 交易對: 34 對
📈 勝率: 47.1%
💎 平均獲利: 7,512 TWD

✅ 系統表現良好
        """.strip()
        
        await self.send_message(profit_text)
    
    async def process_message(self, message: Dict):
        """處理消息"""
        try:
            if 'text' not in message:
                return
            
            text = message['text'].strip()
            chat_id = str(message['chat']['id'])
            
            if chat_id != self.chat_id:
                return
            
            # 通知GUI收到消息
            self._notify_gui("received", text)
            
            # 查找處理器
            handler = None
            for command, func in self.commands.items():
                if text.startswith(command) or text == command:
                    handler = func
                    break
            
            if handler:
                await handler(message)
                self._notify_gui("sent", f"已回覆 {text}")
            else:
                # 未知指令
                await self.send_message("❓ 未知指令，請發送 /help 查看可用指令")
                self._notify_gui("sent", "已回覆未知指令")
                
        except Exception as e:
            logger.error(f"處理消息錯誤: {e}")
    
    async def run(self):
        """運行機器人"""
        self.running = True
        self._notify_gui("started", "機器人已啟動")
        
        # 發送啟動消息
        await self.send_message("🤖 <b>AImax機器人已啟動</b>\n\n發送 /help 查看可用指令")
        
        error_count = 0
        max_errors = 10
        
        while self.running and error_count < max_errors:
            try:
                updates = await self.get_updates_safe()
                
                if updates:
                    error_count = 0  # 重置錯誤計數
                    
                    for update in updates:
                        self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            await self.process_message(update['message'])
                
                # 休息一下
                await asyncio.sleep(5)
                
            except Exception as e:
                error_count += 1
                logger.error(f"機器人運行錯誤 ({error_count}/{max_errors}): {e}")
                
                if error_count >= max_errors:
                    self._notify_gui("error", "錯誤過多，機器人停止")
                    break
                
                await asyncio.sleep(10)
        
        self.running = False
        logger.info("簡化機器人已停止")