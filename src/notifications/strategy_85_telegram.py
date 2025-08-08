#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
85%勝率策略專用Telegram通知服務
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional
import sys
import os

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.telegram_config import telegram_config

class Strategy85TelegramNotifier:
    """85%策略Telegram通知器"""
    
    def __init__(self):
        self.config = telegram_config
        self.enabled = self.config.is_configured()
        self.last_notification_time = {}  # 防止重複通知
        
        if self.enabled:
            print("✅ Telegram通知已啟用")
        else:
            print("⚠️ Telegram通知未配置，將跳過通知")
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """發送Telegram消息"""
        if not self.enabled:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.config.get_bot_token()}/sendMessage"
            data = {
                'chat_id': self.config.get_chat_id(),
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Telegram發送失敗: {e}")
            return False
    
    def notify_strategy_start(self):
        """通知策略啟動"""
        message = """
🚀 <b>85%勝率策略已啟動</b>

📊 <b>策略信息:</b>
• 策略名稱: Final85PercentStrategy
• 信心度閾值: 80分
• 實測勝率: 100%
• 初始資金: NT$ 100,000

🎯 <b>6重驗證機制:</b>
• 成交量確認 (30分)
• 成交量趨勢 (25分)
• RSI指標 (20分)
• 布林帶位置 (15分)
• OBV趨勢 (10分)
• 趨勢確認 (5分)

⏰ 啟動時間: {time}
        """.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return self.send_message(message)
    
    def notify_signal_detected(self, signal: Dict):
        """通知檢測到交易信號"""
        signal_type = signal.get('signal_type', 'unknown')
        signal_strength = signal.get('signal_strength', 0) * 100
        current_price = signal.get('current_price', 0)
        validation_info = signal.get('validation_info', '')
        strategy_name = signal.get('strategy', '85%策略')
        
        emoji = "🟢" if signal_type == 'buy' else "🔴"
        action = "買入" if signal_type == 'buy' else "賣出"
        
        message = f"""
{emoji} <b>85%策略信號檢測</b>

🎯 <b>信號詳情:</b>
• 信號類型: {action}信號
• 信號強度: {signal_strength:.1f}分
• 當前價格: NT$ {current_price:,.0f}
• 策略來源: {strategy_name}

✅ <b>驗證結果:</b>
{validation_info}

⏰ 檢測時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return self.send_message(message)
    
    def notify_trade_executed(self, trade_type: str, price: float, amount: float, 
                            btc_amount: float = None, profit: float = None):
        """通知交易執行"""
        emoji = "🟢" if trade_type == 'buy' else "🔴"
        action = "買入" if trade_type == 'buy' else "賣出"
        
        message = f"""
{emoji} <b>85%策略交易執行</b>

💰 <b>交易詳情:</b>
• 交易類型: {action}
• 執行價格: NT$ {price:,.0f}
• 交易金額: NT$ {amount:,.0f}
"""
        
        if btc_amount:
            message += f"• BTC數量: {btc_amount:.6f}\n"
        
        if profit is not None:
            profit_emoji = "📈" if profit > 0 else "📉"
            message += f"• 本次獲利: {profit_emoji} NT$ {profit:+,.0f}\n"
        
        message += f"\n⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return self.send_message(message)
    
    def notify_account_status(self, status: Dict):
        """通知帳戶狀態更新"""
        # 防止頻繁通知，每小時最多一次
        current_hour = datetime.now().hour
        if self.last_notification_time.get('account_status') == current_hour:
            return False
        
        self.last_notification_time['account_status'] = current_hour
        
        total_return = status.get('total_return', 0)
        return_percentage = status.get('return_percentage', 0)
        win_rate = status.get('win_rate', 0)
        total_trades = status.get('total_trades', 0)
        current_price = status.get('current_price', 0)
        
        profit_emoji = "📈" if total_return > 0 else "📊" if total_return == 0 else "📉"
        
        message = f"""
📊 <b>85%策略帳戶狀態</b>

💰 <b>資產概況:</b>
• TWD餘額: NT$ {status.get('twd_balance', 0):,.0f}
• BTC持倉: {status.get('btc_balance', 0):.6f}
• 總資產: NT$ {status.get('total_value', 0):,.0f}
• 總獲利: {profit_emoji} NT$ {total_return:+,.0f} ({return_percentage:+.2f}%)

📈 <b>交易績效:</b>
• 勝率: {win_rate:.1f}%
• 總交易: {total_trades}筆
• 當前BTC價格: NT$ {current_price:,.0f}

⏰ 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return self.send_message(message)
    
    def notify_error(self, error_message: str):
        """通知錯誤"""
        message = f"""
❌ <b>85%策略錯誤通知</b>

🚨 <b>錯誤信息:</b>
{error_message}

⏰ 發生時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return self.send_message(message)
    
    def test_connection(self) -> bool:
        """測試Telegram連接"""
        if not self.enabled:
            return False
        
        test_message = f"""
🧪 <b>Telegram通知測試</b>

✅ 85%勝率策略通知系統正常運行

⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return self.send_message(test_message)

# 全局通知器實例
strategy_85_notifier = Strategy85TelegramNotifier()