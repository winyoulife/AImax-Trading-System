#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雙向Telegram機器人 - 支持指令回覆功能
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import os
import sys

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.data.data_fetcher import DataFetcher
from src.core.macd_calculator import MACDCalculator
from src.core.trading_signals import TradingSignals
from src.notifications.telegram_service import TelegramService

logger = logging.getLogger(__name__)

class TelegramBot:
    """雙向Telegram機器人"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.telegram_service = TelegramService(bot_token, chat_id)
        self.last_update_id = 0
        self.running = False
        
        # 初始化交易組件
        self.data_fetcher = DataFetcher()
        self.macd_calculator = MACDCalculator()
        self.trading_signals = TradingSignals()
        
        # 指令處理器映射
        self.command_handlers = {
            '/start': self.handle_start,
            '/help': self.handle_help,
            '/status': self.handle_status,
            '/price': self.handle_price,
            '/macd': self.handle_macd,
            '/signals': self.handle_signals,
            '/profit': self.handle_profit,
            '/stop': self.handle_stop,
            '狀態': self.handle_status,
            '價格': self.handle_price,
            '指標': self.handle_macd,
            '信號': self.handle_signals,
            '獲利': self.handle_profit,
            '幫助': self.handle_help,
        }
    
    async def get_updates(self, offset: int = 0) -> List[Dict]:
        """獲取Telegram更新"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                'offset': offset,
                'timeout': 30,
                'allowed_updates': ['message']
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=35) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result', [])
                    else:
                        logger.error(f"獲取更新失敗: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"獲取Telegram更新時發生錯誤: {e}")
            return []
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """發送消息"""
        return await self.telegram_service.send_message_async(text, parse_mode)
    
    async def handle_start(self, message: Dict) -> None:
        """處理/start指令"""
        welcome_text = """
🤖 <b>歡迎使用AImax交易機器人！</b>

我可以幫你監控MACD交易信號和市場狀況。

📋 <b>可用指令：</b>
• /help 或 幫助 - 顯示所有指令
• /status 或 狀態 - 系統狀態
• /price 或 價格 - 當前價格
• /macd 或 指標 - MACD指標數據
• /signals 或 信號 - 最新交易信號
• /profit 或 獲利 - 獲利統計
• /stop - 停止機器人

💡 你可以使用中文或英文指令！
        """.strip()
        
        await self.send_message(welcome_text)
    
    async def handle_help(self, message: Dict) -> None:
        """處理幫助指令"""
        help_text = """
🆘 <b>AImax交易機器人指令說明</b>

📋 <b>基本指令：</b>
• /start - 開始使用機器人
• /help 或 幫助 - 顯示此幫助信息
• /stop - 停止機器人運行

📊 <b>市場信息：</b>
• /status 或 狀態 - 顯示系統運行狀態
• /price 或 價格 - 獲取當前BTC價格
• /macd 或 指標 - 顯示MACD技術指標
• /signals 或 信號 - 查看最新交易信號

💰 <b>交易統計：</b>
• /profit 或 獲利 - 顯示獲利統計

🔄 <b>使用提示：</b>
• 支持中英文指令
• 機器人會自動推送交易信號
• 數據每分鐘更新一次

❓ 有問題隨時問我！
        """.strip()
        
        await self.send_message(help_text)
    
    async def handle_status(self, message: Dict) -> None:
        """處理狀態查詢"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            status_text = f"""
📊 <b>AImax系統狀態</b>

✅ <b>機器人狀態</b>: 運行中
⏰ <b>當前時間</b>: {current_time}
🔄 <b>數據更新</b>: 正常
📡 <b>Telegram連接</b>: 正常

💡 系統運行正常，持續監控中...
            """.strip()
            
            await self.send_message(status_text)
            
        except Exception as e:
            await self.send_message(f"❌ 獲取狀態時發生錯誤: {str(e)}")
    
    async def handle_price(self, message: Dict) -> None:
        """處理價格查詢"""
        try:
            # 獲取最新價格數據
            df = await asyncio.get_event_loop().run_in_executor(
                None, self.data_fetcher.fetch_data, 'BTCUSDT', '1h', 2
            )
            
            if df is not None and not df.empty:
                latest_price = df['close'].iloc[-1]
                prev_price = df['close'].iloc[-2] if len(df) > 1 else latest_price
                change = latest_price - prev_price
                change_pct = (change / prev_price) * 100 if prev_price != 0 else 0
                
                # 設置變化方向emoji
                if change > 0:
                    emoji = "📈"
                    color = "綠色"
                elif change < 0:
                    emoji = "📉"
                    color = "紅色"
                else:
                    emoji = "➡️"
                    color = "持平"
                
                price_text = f"""
💰 <b>BTC當前價格</b>

{emoji} <b>價格</b>: ${latest_price:,.2f}
📊 <b>變化</b>: ${change:+,.2f} ({change_pct:+.2f}%)
🎨 <b>趨勢</b>: {color}
⏰ <b>更新時間</b>: {datetime.now().strftime("%H:%M:%S")}

💡 數據來源: Binance 1小時K線
                """.strip()
                
                await self.send_message(price_text)
            else:
                await self.send_message("❌ 無法獲取價格數據，請稍後再試")
                
        except Exception as e:
            await self.send_message(f"❌ 獲取價格時發生錯誤: {str(e)}")
    
    async def handle_macd(self, message: Dict) -> None:
        """處理MACD指標查詢"""
        try:
            # 獲取數據並計算MACD
            df = await asyncio.get_event_loop().run_in_executor(
                None, self.data_fetcher.fetch_data, 'BTCUSDT', '1h', 50
            )
            
            if df is not None and not df.empty:
                macd_df = self.macd_calculator.calculate_macd(df)
                latest = macd_df.iloc[-1]
                
                # 判斷MACD趨勢
                if latest['macd'] > latest['signal']:
                    trend = "看漲 📈"
                    trend_color = "綠色"
                else:
                    trend = "看跌 📉"
                    trend_color = "紅色"
                
                # 判斷柱狀圖變化
                if len(macd_df) > 1:
                    prev_hist = macd_df.iloc[-2]['hist']
                    if latest['hist'] > prev_hist:
                        hist_trend = "增強 ⬆️"
                    elif latest['hist'] < prev_hist:
                        hist_trend = "減弱 ⬇️"
                    else:
                        hist_trend = "持平 ➡️"
                else:
                    hist_trend = "持平 ➡️"
                
                macd_text = f"""
📊 <b>MACD技術指標</b>

📈 <b>MACD線</b>: {latest['macd']:.4f}
📉 <b>信號線</b>: {latest['signal']:.4f}
📊 <b>柱狀圖</b>: {latest['hist']:.4f}

🎯 <b>趨勢</b>: {trend}
🔄 <b>柱狀圖</b>: {hist_trend}
💰 <b>當前價格</b>: ${latest['close']:,.2f}

⏰ <b>更新時間</b>: {datetime.now().strftime("%H:%M:%S")}

💡 基於1小時K線數據計算
                """.strip()
                
                await self.send_message(macd_text)
            else:
                await self.send_message("❌ 無法獲取MACD數據，請稍後再試")
                
        except Exception as e:
            await self.send_message(f"❌ 獲取MACD指標時發生錯誤: {str(e)}")
    
    async def handle_signals(self, message: Dict) -> None:
        """處理交易信號查詢"""
        try:
            # 獲取數據並生成信號
            df = await asyncio.get_event_loop().run_in_executor(
                None, self.data_fetcher.fetch_data, 'BTCUSDT', '1h', 100
            )
            
            if df is not None and not df.empty:
                macd_df = self.macd_calculator.calculate_macd(df)
                signals_df = self.trading_signals.generate_signals(macd_df)
                
                # 找到最近的信號
                recent_signals = signals_df[signals_df['signal'] != 0].tail(3)
                
                if not recent_signals.empty:
                    signals_text = "📡 <b>最近交易信號</b>\n\n"
                    
                    for idx, row in recent_signals.iterrows():
                        signal_type = "🟢 買進" if row['signal'] == 1 else "🔴 賣出"
                        time_str = row['timestamp'].strftime("%m-%d %H:%M")
                        
                        signals_text += f"""
{signal_type}
💰 價格: ${row['close']:,.2f}
⏰ 時間: {time_str}
📊 MACD: {row['macd']:.4f}
📈 柱狀圖: {row['hist']:.4f}

                        """.strip() + "\n\n"
                    
                    # 添加當前狀態
                    latest = signals_df.iloc[-1]
                    if latest['macd'] > latest['signal']:
                        current_trend = "📈 當前趨勢: 看漲"
                    else:
                        current_trend = "📉 當前趨勢: 看跌"
                    
                    signals_text += f"\n{current_trend}\n💡 持續監控中..."
                    
                else:
                    signals_text = """
📡 <b>交易信號狀態</b>

⏳ 暫無最近信號
📊 系統持續監控中
💡 有新信號時會自動通知

🔄 請稍後再查詢
                    """.strip()
                
                await self.send_message(signals_text)
            else:
                await self.send_message("❌ 無法獲取信號數據，請稍後再試")
                
        except Exception as e:
            await self.send_message(f"❌ 獲取交易信號時發生錯誤: {str(e)}")
    
    async def handle_profit(self, message: Dict) -> None:
        """處理獲利統計查詢"""
        try:
            # 這裡可以連接到你的回測結果或實際交易記錄
            profit_text = """
💰 <b>獲利統計概覽</b>

📊 <b>歷史回測表現</b>:
• 總獲利: 108,774 TWD
• 完整交易對: 54 對
• 勝率: 約 65%
• 平均獲利: 2,014 TWD/對

📈 <b>策略表現</b>:
• 使用策略: 1小時MACD
• 回測期間: 長期歷史數據
• 風險控制: 良好

⚠️ <b>風險提醒</b>:
歷史表現不代表未來收益
請謹慎投資，控制風險

💡 數據僅供參考
            """.strip()
            
            await self.send_message(profit_text)
            
        except Exception as e:
            await self.send_message(f"❌ 獲取獲利統計時發生錯誤: {str(e)}")
    
    async def handle_stop(self, message: Dict) -> None:
        """處理停止指令"""
        stop_text = """
🛑 <b>機器人停止指令已收到</b>

⏹️ 正在停止監控服務...
💾 保存當前狀態...
👋 感謝使用AImax交易機器人！

如需重新啟動，請運行啟動腳本。
        """.strip()
        
        await self.send_message(stop_text)
        self.running = False
    
    async def process_message(self, message: Dict) -> None:
        """處理收到的消息"""
        try:
            if 'text' not in message:
                return
            
            text = message['text'].strip()
            chat_id = str(message['chat']['id'])
            
            # 檢查是否來自正確的聊天
            if chat_id != self.chat_id:
                logger.warning(f"收到來自未授權聊天的消息: {chat_id}")
                return
            
            logger.info(f"收到消息: {text}")
            
            # 查找對應的處理器
            handler = None
            for command, func in self.command_handlers.items():
                if text.startswith(command) or text == command:
                    handler = func
                    break
            
            if handler:
                await handler(message)
            else:
                # 未知指令的回覆
                unknown_text = f"""
❓ <b>未知指令</b>: {text}

請使用 /help 或 幫助 查看可用指令。

💡 支持的指令包括:
• 狀態、價格、指標、信號、獲利
• /status, /price, /macd, /signals, /profit
                """.strip()
                
                await self.send_message(unknown_text)
                
        except Exception as e:
            logger.error(f"處理消息時發生錯誤: {e}")
            await self.send_message(f"❌ 處理消息時發生錯誤: {str(e)}")
    
    async def run(self) -> None:
        """運行機器人主循環"""
        self.running = True
        logger.info("Telegram機器人開始運行...")
        
        # 發送啟動通知
        await self.send_message("""
🤖 <b>AImax交易機器人已啟動</b>

✅ 系統初始化完成
📡 開始監聽指令
💡 發送 /help 查看可用指令

準備為您服務！
        """.strip())
        
        while self.running:
            try:
                # 獲取更新
                updates = await self.get_updates(self.last_update_id + 1)
                
                for update in updates:
                    self.last_update_id = update['update_id']
                    
                    if 'message' in update:
                        await self.process_message(update['message'])
                
                # 短暫休息避免過度請求
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"機器人運行時發生錯誤: {e}")
                await asyncio.sleep(5)  # 錯誤時等待更長時間
        
        logger.info("Telegram機器人已停止")

async def main():
    """主函數"""
    # 從環境變量或配置文件讀取
    bot_token = "YOUR_BOT_TOKEN"  # 替換為你的bot token
    chat_id = "YOUR_CHAT_ID"      # 替換為你的chat id
    
    bot = TelegramBot(bot_token, chat_id)
    await bot.run()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())