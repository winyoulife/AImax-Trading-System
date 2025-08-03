#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram通知服務
"""

import requests
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TelegramService:
    """Telegram通知服務"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    def send_message_sync(self, message: str, parse_mode: str = "HTML") -> bool:
        """同步發送消息"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram消息發送成功")
                return True
            else:
                logger.error(f"Telegram消息發送失敗: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"發送Telegram消息時發生錯誤: {e}")
            return False
    
    async def send_message_async(self, message: str, parse_mode: str = "HTML") -> bool:
        """異步發送消息"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, timeout=10) as response:
                    if response.status == 200:
                        logger.info("Telegram消息發送成功")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"Telegram消息發送失敗: {response.status} - {text}")
                        return False
                        
        except Exception as e:
            logger.error(f"發送Telegram消息時發生錯誤: {e}")
            return False
    
    def send_trading_signal(self, signal_type: str, price: float, sequence: int, 
                          macd_data: dict, additional_info: str = "") -> bool:
        """發送交易信號通知"""
        
        # 根據信號類型設置emoji和顏色
        if signal_type.lower() == 'buy':
            emoji = "🟢"
            action = "買進"
            color = "綠色"
        elif signal_type.lower() == 'sell':
            emoji = "🔴"
            action = "賣出"
            color = "紅色"
        else:
            emoji = "⚪"
            action = "信號"
            color = "白色"
        
        # 格式化時間
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 構建消息
        message = f"""
{emoji} <b>MACD交易信號通知</b> {emoji}

🎯 <b>動作</b>: {action}
💰 <b>價格</b>: {price:,.0f} TWD
🔢 <b>序號</b>: {sequence}
⏰ <b>時間</b>: {current_time}

📊 <b>MACD指標</b>:
• 柱狀圖: {macd_data.get('hist', 0):.2f}
• MACD線: {macd_data.get('macd', 0):.2f}
• 信號線: {macd_data.get('signal', 0):.2f}

{additional_info}

💡 <i>AImax 1小時MACD策略</i>
        """.strip()
        
        return self.send_message_sync(message)
    
    def send_backtest_summary(self, statistics: dict) -> bool:
        """發送回測總結通知"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 計算勝率
        win_rate = 0
        if statistics.get('complete_pairs', 0) > 0:
            winning_trades = sum(1 for pair in statistics.get('trade_pairs', []) 
                               if pair.get('profit', 0) > 0)
            win_rate = (winning_trades / statistics['complete_pairs']) * 100
        
        message = f"""
📈 <b>MACD策略回測總結</b> 📈

💰 <b>總獲利</b>: {statistics.get('total_profit', 0):,.0f} TWD
📊 <b>完整交易對</b>: {statistics.get('complete_pairs', 0)} 對
🟢 <b>買進信號</b>: {statistics.get('buy_count', 0)} 個
🔴 <b>賣出信號</b>: {statistics.get('sell_count', 0)} 個
🎯 <b>勝率</b>: {win_rate:.1f}%
📈 <b>平均獲利</b>: {statistics.get('average_profit', 0):,.0f} TWD
⏱️ <b>平均持倉</b>: {statistics.get('average_hold_time', 0):.1f} 小時

📋 <b>當前狀態</b>: {statistics.get('position_status', '未知')}
🔢 <b>下一序號</b>: {statistics.get('next_trade_sequence', 1)}

⏰ <b>更新時間</b>: {current_time}

💡 <i>AImax 1小時MACD策略回測</i>
        """.strip()
        
        return self.send_message_sync(message)
    
    def send_system_status(self, status: str, details: str = "") -> bool:
        """發送系統狀態通知"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 根據狀態設置emoji
        if "成功" in status or "完成" in status:
            emoji = "✅"
        elif "錯誤" in status or "失敗" in status:
            emoji = "❌"
        elif "警告" in status:
            emoji = "⚠️"
        else:
            emoji = "ℹ️"
        
        message = f"""
{emoji} <b>系統狀態通知</b>

📋 <b>狀態</b>: {status}
⏰ <b>時間</b>: {current_time}

{details}

💡 <i>AImax 交易系統</i>
        """.strip()
        
        return self.send_message_sync(message)
    
    def test_connection(self) -> bool:
        """測試Telegram連接"""
        try:
            test_message = f"""
🔧 <b>Telegram連接測試</b>

✅ 連接成功！
⏰ 測試時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

💡 <i>AImax 交易系統已準備就緒</i>
            """.strip()
            
            return self.send_message_sync(test_message)
            
        except Exception as e:
            logger.error(f"Telegram連接測試失敗: {e}")
            return False

# 全局Telegram服務實例
_telegram_service = None

def get_telegram_service() -> Optional[TelegramService]:
    """獲取Telegram服務實例"""
    return _telegram_service

def initialize_telegram_service(bot_token: str, chat_id: str) -> TelegramService:
    """初始化Telegram服務"""
    global _telegram_service
    _telegram_service = TelegramService(bot_token, chat_id)
    return _telegram_service

def send_quick_message(message: str) -> bool:
    """快速發送消息"""
    service = get_telegram_service()
    if service:
        return service.send_message_sync(message)
    return False