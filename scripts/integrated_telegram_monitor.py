#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合的Telegram監控系統 - 結合交易信號推送和雙向指令回覆
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.notifications.telegram_bot import TelegramBot
from src.data.data_fetcher import DataFetcher
from src.core.improved_max_macd_calculator import ImprovedMaxMACDCalculator
from src.core.improved_trading_signals import SignalDetectionEngine
from config.telegram_config import telegram_config

class IntegratedTelegramMonitor:
    """整合的Telegram監控系統"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        
        # 初始化機器人
        self.bot = TelegramBot(bot_token, chat_id)
        
        # 初始化交易組件
        self.data_fetcher = DataFetcher()
        self.macd_calculator = ImprovedMaxMACDCalculator()
        self.signal_engine = SignalDetectionEngine()
        
        # 監控狀態
        self.running = False
        self.last_signal_time = None
        self.last_price_alert_time = None
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
    
    def _calculate_macd_data(self, df):
        """計算MACD數據的輔助方法"""
        import numpy as np
        
        prices = df['close'].tolist()
        timestamps = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        
        macd_line, signal_line, hist = self.macd_calculator.calculate_macd(prices, timestamps)
        
        # 創建包含MACD數據的DataFrame
        macd_df = df.copy()
        macd_df['datetime'] = df['timestamp']
        
        # 填充MACD數據（前面的數據用NaN填充）
        macd_len = len(macd_line)
        total_len = len(df)
        
        macd_df['macd'] = [np.nan] * (total_len - macd_len) + macd_line
        macd_df['macd_signal'] = [np.nan] * (total_len - macd_len) + signal_line
        macd_df['macd_hist'] = [np.nan] * (total_len - macd_len) + hist
        
        # 移除NaN行
        macd_df = macd_df.dropna().reset_index(drop=True)
        
        return macd_df
    
    async def check_trading_signals(self):
        """檢查交易信號"""
        try:
            # 獲取數據
            df = await asyncio.get_event_loop().run_in_executor(
                None, self.data_fetcher.fetch_data, 'BTCUSDT', '1h', 100
            )
            
            if df is None or df.empty:
                return
            
            # 計算MACD和信號
            macd_df = self._calculate_macd_data(df)
            signals_df = self.signal_engine.detect_smart_balanced_signals(macd_df)
            
            # 檢查最新信號
            latest = signals_df.iloc[-1]
            
            if latest['signal_type'] in ['buy', 'sell']:
                # 檢查是否是新信號（避免重複發送）
                current_time = latest['datetime']
                
                if (self.last_signal_time is None or 
                    current_time > self.last_signal_time):
                    
                    # 發送信號通知
                    await self.send_signal_notification(latest)
                    self.last_signal_time = current_time
                    
                    self.logger.info(f"發送交易信號: {latest['signal']} at {latest['close']}")
            
        except Exception as e:
            self.logger.error(f"檢查交易信號時發生錯誤: {e}")
    
    async def send_signal_notification(self, signal_data):
        """發送信號通知"""
        try:
            signal_type = "買進" if signal_data['signal_type'] == 'buy' else "賣出"
            emoji = "🟢" if signal_data['signal_type'] == 'buy' else "🔴"
            
            message = f"""
{emoji} <b>MACD交易信號</b> {emoji}

🎯 <b>動作</b>: {signal_type}
💰 <b>價格</b>: ${signal_data['close']:,.0f}
⏰ <b>時間</b>: {signal_data['datetime'].strftime("%Y-%m-%d %H:%M:%S")}

📊 <b>技術指標</b>:
• MACD: {signal_data['macd']:.1f}
• 信號線: {signal_data['macd_signal']:.1f}
• 柱狀圖: {signal_data['macd_hist']:.1f}

💡 <i>AImax 1小時MACD策略</i>

回覆 "狀態" 查看更多信息
            """.strip()
            
            await self.bot.send_message(message)
            
        except Exception as e:
            self.logger.error(f"發送信號通知時發生錯誤: {e}")
    
    async def check_price_alerts(self):
        """檢查價格警報"""
        try:
            # 獲取最新價格
            df = await asyncio.get_event_loop().run_in_executor(
                None, self.data_fetcher.fetch_data, 'BTCUSDT', '1h', 2
            )
            
            if df is None or df.empty:
                return
            
            latest_price = df['close'].iloc[-1]
            prev_price = df['close'].iloc[-2] if len(df) > 1 else latest_price
            
            # 計算價格變化
            change_pct = ((latest_price - prev_price) / prev_price) * 100 if prev_price != 0 else 0
            
            # 如果價格變化超過5%，發送警報
            if abs(change_pct) >= 5.0:
                current_time = datetime.now()
                
                # 避免頻繁發送警報（至少間隔1小時）
                if (self.last_price_alert_time is None or 
                    current_time - self.last_price_alert_time > timedelta(hours=1)):
                    
                    await self.send_price_alert(latest_price, change_pct)
                    self.last_price_alert_time = current_time
            
        except Exception as e:
            self.logger.error(f"檢查價格警報時發生錯誤: {e}")
    
    async def send_price_alert(self, price: float, change_pct: float):
        """發送價格警報"""
        try:
            if change_pct > 0:
                emoji = "📈"
                direction = "上漲"
                color = "綠色"
            else:
                emoji = "📉"
                direction = "下跌"
                color = "紅色"
            
            message = f"""
{emoji} <b>價格警報</b> {emoji}

💰 <b>當前價格</b>: ${price:,.2f}
📊 <b>變化幅度</b>: {change_pct:+.2f}%
🎨 <b>趨勢</b>: {direction} ({color})
⏰ <b>時間</b>: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

⚠️ <b>注意</b>: 價格波動較大，請注意風險控制

💡 回覆 "價格" 獲取最新價格信息
            """.strip()
            
            await self.bot.send_message(message)
            
        except Exception as e:
            self.logger.error(f"發送價格警報時發生錯誤: {e}")
    
    async def send_daily_summary(self):
        """發送每日總結"""
        try:
            current_time = datetime.now()
            
            # 獲取今日數據
            df = await asyncio.get_event_loop().run_in_executor(
                None, self.data_fetcher.fetch_data, 'BTCUSDT', '1h', 24
            )
            
            if df is None or df.empty:
                return
            
            # 計算今日統計
            today_high = df['high'].max()
            today_low = df['low'].min()
            current_price = df['close'].iloc[-1]
            start_price = df['open'].iloc[0]
            
            daily_change = current_price - start_price
            daily_change_pct = (daily_change / start_price) * 100 if start_price != 0 else 0
            
            # 計算MACD信號
            macd_df = self._calculate_macd_data(df)
            signals_df = self.signal_engine.detect_smart_balanced_signals(macd_df)
            
            # 統計今日信號
            today_signals = signals_df[signals_df['signal_type'].isin(['buy', 'sell'])]
            buy_signals = len(today_signals[today_signals['signal_type'] == 'buy'])
            sell_signals = len(today_signals[today_signals['signal_type'] == 'sell'])
            
            message = f"""
📊 <b>每日市場總結</b>

📅 <b>日期</b>: {current_time.strftime("%Y-%m-%d")}

💰 <b>價格統計</b>:
• 當前價格: ${current_price:,.0f}
• 今日最高: ${today_high:,.0f}
• 今日最低: ${today_low:,.0f}
• 日內變化: ${daily_change:+,.0f} ({daily_change_pct:+.2f}%)

📡 <b>信號統計</b>:
• 買進信號: {buy_signals} 個
• 賣出信號: {sell_signals} 個
• 總信號數: {buy_signals + sell_signals} 個

💡 <i>AImax 每日監控報告</i>

回覆 "幫助" 查看可用指令
            """.strip()
            
            await self.bot.send_message(message)
            
        except Exception as e:
            self.logger.error(f"發送每日總結時發生錯誤: {e}")
    
    async def monitoring_loop(self):
        """監控循環"""
        self.logger.info("開始監控循環...")
        
        last_daily_summary = None
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # 檢查交易信號（每分鐘）
                await self.check_trading_signals()
                
                # 檢查價格警報（每5分鐘）
                if current_time.minute % 5 == 0:
                    await self.check_price_alerts()
                
                # 發送每日總結（每天早上9點）
                if (current_time.hour == 9 and current_time.minute == 0 and
                    (last_daily_summary is None or 
                     current_time.date() > last_daily_summary.date())):
                    
                    await self.send_daily_summary()
                    last_daily_summary = current_time
                
                # 等待1分鐘
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"監控循環中發生錯誤: {e}")
                await asyncio.sleep(60)  # 錯誤時也等待1分鐘
    
    async def run(self):
        """運行整合監控系統"""
        self.running = True
        self.logger.info("整合Telegram監控系統啟動...")
        
        # 發送啟動通知
        await self.bot.send_message("""
🚀 <b>AImax整合監控系統已啟動</b>

✅ <b>功能已啟用</b>:
• 🤖 雙向指令回覆
• 📡 自動交易信號推送
• ⚠️ 價格警報通知
• 📊 每日市場總結

💡 發送 /help 查看所有可用指令

系統開始監控...
        """.strip())
        
        try:
            # 同時運行機器人和監控循環
            await asyncio.gather(
                self.bot.run(),
                self.monitoring_loop()
            )
        except Exception as e:
            self.logger.error(f"運行時發生錯誤: {e}")
        finally:
            self.running = False
            self.logger.info("整合監控系統已停止")

async def main():
    """主函數"""
    print("🚀 AImax整合Telegram監控系統")
    print("=" * 50)
    
    # 檢查配置
    if not telegram_config.is_configured():
        print("❌ Telegram配置不完整！")
        print("請先運行: python scripts/setup_telegram_bot.py")
        return
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/integrated_monitor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # 創建監控系統
        monitor = IntegratedTelegramMonitor(
            telegram_config.get_bot_token(),
            telegram_config.get_chat_id()
        )
        
        print(f"✅ 系統配置完成")
        print(f"📱 Chat ID: {telegram_config.get_chat_id()}")
        print(f"⏰ 啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n🔄 監控功能:")
        print("   • 交易信號自動推送")
        print("   • 價格警報通知")
        print("   • 雙向指令回覆")
        print("   • 每日市場總結")
        print("\n💡 支持的指令:")
        print("   /help, /status, /price, /macd, /signals, /profit")
        print("   狀態, 價格, 指標, 信號, 獲利, 幫助")
        print("\n按 Ctrl+C 停止系統")
        print("-" * 50)
        
        # 運行監控系統
        await monitor.run()
        
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信號，正在關閉系統...")
        logger.info("系統被用戶手動停止")
    except Exception as e:
        print(f"\n❌ 系統運行時發生錯誤: {e}")
        logger.error(f"系統運行錯誤: {e}")
    finally:
        print("👋 系統已停止運行")

if __name__ == "__main__":
    # 確保logs目錄存在
    os.makedirs('logs', exist_ok=True)
    
    # 運行系統
    asyncio.run(main())