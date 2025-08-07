#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能平衡策略專用Telegram通知服務
實時推送83.3%勝率策略的交易決策和執行狀況
"""

import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SmartBalancedTelegramNotifier:
    """智能平衡策略Telegram通知器"""
    
    def __init__(self):
        # 從環境變數獲取配置
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # 通知配置
        self.config = {
            'strategy_name': '智能平衡策略',
            'strategy_version': 'v1.0-smart-balanced',
            'target_win_rate': '83.3%',
            'notifications': {
                'trade_signals': True,
                'trade_execution': True,
                'performance_updates': True,
                'system_alerts': True,
                'daily_summary': True
            }
        }
    
    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """發送Telegram訊息"""
        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram配置未設定，跳過通知")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram訊息發送成功")
                return True
            else:
                logger.error(f"❌ Telegram訊息發送失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Telegram訊息發送異常: {e}")
            return False
    
    def notify_trade_signal(self, signal_data: Dict) -> bool:
        """通知交易信號"""
        if not self.config['notifications']['trade_signals']:
            return False
        
        try:
            signal_type = signal_data.get('signal_type', 'unknown')
            price = signal_data.get('close', 0)
            strength = signal_data.get('signal_strength', 0)
            validation_info = signal_data.get('validation_info', '')
            
            # 信號類型圖標
            signal_icon = "📈" if signal_type == 'buy' else "📉" if signal_type == 'sell' else "🔍"
            action_text = "買進" if signal_type == 'buy' else "賣出" if signal_type == 'sell' else "分析"
            
            message = f"""
🤖 <b>AImax 智能平衡策略信號</b>

{signal_icon} <b>{action_text}信號觸發</b>
💰 價格: <code>NT$ {price:,.0f}</code>
🎯 信號強度: <code>{strength:.1f}/100</code>
📊 策略版本: <code>{self.config['strategy_version']}</code>
🏆 目標勝率: <code>{self.config['target_win_rate']}</code>

📋 <b>驗證詳情:</b>
<code>{validation_info}</code>

🕐 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>🚀 智能平衡策略自動執行中</i>
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ 交易信號通知失敗: {e}")
            return False
    
    def notify_trade_execution(self, trade_data: Dict) -> bool:
        """通知交易執行結果"""
        if not self.config['notifications']['trade_execution']:
            return False
        
        try:
            action = trade_data.get('action', 'unknown')
            price = trade_data.get('price', 0)
            quantity = trade_data.get('quantity', 0)
            profit = trade_data.get('profit', 0)
            success = trade_data.get('success', False)
            
            # 執行結果圖標
            result_icon = "✅" if success else "❌"
            action_icon = "📈" if action == 'buy' else "📉"
            profit_icon = "💰" if profit > 0 else "📉" if profit < 0 else "➖"
            
            message = f"""
🤖 <b>AImax 智能平衡策略執行</b>

{result_icon} <b>交易執行{'成功' if success else '失敗'}</b>
{action_icon} 動作: <b>{'買進' if action == 'buy' else '賣出'}</b>
💰 價格: <code>NT$ {price:,.0f}</code>
📊 數量: <code>{quantity:.6f} BTC</code>
{profit_icon} 損益: <code>{profit:+,.0f} TWD</code>

🎯 <b>策略資訊:</b>
📋 版本: <code>{self.config['strategy_version']}</code>
🏆 目標勝率: <code>{self.config['target_win_rate']}</code>

🕐 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>🚀 智能平衡策略持續監控中</i>
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ 交易執行通知失敗: {e}")
            return False
    
    def notify_performance_update(self, performance_data: Dict) -> bool:
        """通知績效更新"""
        if not self.config['notifications']['performance_updates']:
            return False
        
        try:
            total_trades = performance_data.get('total_trades', 0)
            win_rate = performance_data.get('win_rate', 0)
            total_profit = performance_data.get('total_profit', 0)
            avg_profit = performance_data.get('avg_profit', 0)
            recent_trades = performance_data.get('recent_24h_trades', 0)
            
            # 績效狀態圖標
            performance_icon = "🏆" if win_rate >= 0.8 else "📊" if win_rate >= 0.7 else "⚠️"
            profit_icon = "💰" if total_profit > 0 else "📉" if total_profit < 0 else "➖"
            
            message = f"""
📊 <b>AImax 智能平衡策略績效報告</b>

{performance_icon} <b>整體表現</b>
🎯 總交易次數: <code>{total_trades}</code>
🏆 實際勝率: <code>{win_rate:.1%}</code>
{profit_icon} 總獲利: <code>{total_profit:+,.0f} TWD</code>
📈 平均獲利: <code>{avg_profit:+,.0f} TWD/筆</code>
📅 24小時交易: <code>{recent_trades}</code>

📋 <b>策略對比</b>
🎯 目標勝率: <code>{self.config['target_win_rate']}</code>
📊 實際勝率: <code>{win_rate:.1%}</code>
📈 達成率: <code>{(win_rate/0.833):.1%}</code>

🕐 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>🚀 智能平衡策略 {self.config['strategy_version']} 運行中</i>
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ 績效更新通知失敗: {e}")
            return False
    
    def notify_system_alert(self, alert_data: Dict) -> bool:
        """通知系統警報"""
        if not self.config['notifications']['system_alerts']:
            return False
        
        try:
            level = alert_data.get('level', 'info')
            message_text = alert_data.get('message', '未知警報')
            component = alert_data.get('component', 'system')
            
            # 警報等級圖標
            level_icons = {
                'critical': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️'
            }
            level_icon = level_icons.get(level, 'ℹ️')
            
            message = f"""
{level_icon} <b>AImax 智能平衡策略警報</b>

🔔 <b>警報等級:</b> {level.upper()}
🎯 <b>組件:</b> {component}
📝 <b>訊息:</b> {message_text}

📋 <b>策略資訊:</b>
🤖 策略: {self.config['strategy_name']}
📊 版本: <code>{self.config['strategy_version']}</code>
🏆 目標勝率: <code>{self.config['target_win_rate']}</code>

🕐 警報時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>🔍 請檢查系統狀況並採取必要行動</i>
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ 系統警報通知失敗: {e}")
            return False
    
    def notify_daily_summary(self, summary_data: Dict) -> bool:
        """發送每日摘要"""
        if not self.config['notifications']['daily_summary']:
            return False
        
        try:
            date = summary_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            daily_trades = summary_data.get('daily_trades', 0)
            daily_profit = summary_data.get('daily_profit', 0)
            system_status = summary_data.get('system_status', 'unknown')
            
            # 狀態圖標
            status_icons = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '🚨',
                'unknown': '❓'
            }
            status_icon = status_icons.get(system_status, '❓')
            profit_icon = "💰" if daily_profit > 0 else "📉" if daily_profit < 0 else "➖"
            
            message = f"""
📅 <b>AImax 智能平衡策略每日摘要</b>

🗓️ <b>日期:</b> {date}

📊 <b>今日表現</b>
🔢 交易次數: <code>{daily_trades}</code>
{profit_icon} 今日損益: <code>{daily_profit:+,.0f} TWD</code>
{status_icon} 系統狀態: <code>{system_status.upper()}</code>

🎯 <b>策略資訊</b>
🤖 策略: {self.config['strategy_name']}
📋 版本: <code>{self.config['strategy_version']}</code>
🏆 目標勝率: <code>{self.config['target_win_rate']}</code>

🕐 報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>🚀 智能平衡策略持續為您服務</i>
"""
            
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ 每日摘要通知失敗: {e}")
            return False
    
    def test_notification(self) -> bool:
        """測試通知功能"""
        message = f"""
🧪 <b>AImax 智能平衡策略通知測試</b>

✅ <b>通知系統正常運作</b>

🎯 <b>策略資訊:</b>
🤖 策略: {self.config['strategy_name']}
📋 版本: <code>{self.config['strategy_version']}</code>
🏆 目標勝率: <code>{self.config['target_win_rate']}</code>

🕐 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>🚀 智能平衡策略通知系統已就緒！</i>
"""
        
        return self.send_message(message)

def main():
    """測試通知功能"""
    print("🧪 測試智能平衡策略Telegram通知")
    
    notifier = SmartBalancedTelegramNotifier()
    
    if notifier.test_notification():
        print("✅ 通知測試成功")
    else:
        print("❌ 通知測試失敗")

if __name__ == "__main__":
    main()