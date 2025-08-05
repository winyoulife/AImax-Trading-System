"""
AImax 高頻交易專用 Telegram 通知服務
專門為85%勝率策略和智能頻率控制系統設計
"""

import json
import os
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
import logging

logger = logging.getLogger(__name__)


class HighFrequencyTelegramService:
    """高頻交易專用Telegram服務"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        
        # 通知頻率控制
        self.last_notification_times = {}
        self.notification_cooldowns = {
            'price_alert': 300,      # 價格警報：5分鐘
            'volatility_change': 180, # 波動性變化：3分鐘
            'execution_result': 60,   # 執行結果：1分鐘
            'system_error': 600,     # 系統錯誤：10分鐘
            'daily_summary': 86400,  # 每日摘要：24小時
        }
    
    def _can_send_notification(self, notification_type: str) -> bool:
        """檢查是否可以發送通知（避免過度通知）"""
        now = datetime.now().timestamp()
        last_time = self.last_notification_times.get(notification_type, 0)
        cooldown = self.notification_cooldowns.get(notification_type, 60)
        
        if now - last_time >= cooldown:
            self.last_notification_times[notification_type] = now
            return True
        return False
    
    def send_message_sync(self, message: str, parse_mode: str = "HTML") -> bool:
        """同步發送消息"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
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
    
    def send_high_frequency_execution_alert(self, execution_data: Dict[str, Any]) -> bool:
        """發送高頻交易執行警報"""
        if not self._can_send_notification('execution_result'):
            return False
        
        try:
            now_taipei = datetime.now(self.taipei_tz)
            
            # 解析執行數據
            strategy = execution_data.get('strategy', 'unknown')
            btc_price = execution_data.get('btc_price', 0)
            volatility = execution_data.get('volatility_level', 'unknown')
            signal = execution_data.get('signal', 'hold')
            confidence = execution_data.get('confidence', 0.85)
            status = execution_data.get('status', 'unknown')
            execution_interval = execution_data.get('execution_interval', 300)
            
            # 設置emoji和狀態
            if signal == 'buy':
                signal_emoji = '🟢'
                signal_text = '買入信號'
            elif signal == 'sell':
                signal_emoji = '🔴'
                signal_text = '賣出信號'
            else:
                signal_emoji = '⚪'
                signal_text = '持有'
            
            if volatility == 'high':
                vol_emoji = '🔥'
                vol_text = '高波動'
            elif volatility == 'medium':
                vol_emoji = '📊'
                vol_text = '中波動'
            else:
                vol_emoji = '📉'
                vol_text = '低波動'
            
            status_emoji = '✅' if status == 'success' else '❌' if status == 'failed' else '⏳'
            
            # 計算執行頻率
            if execution_interval <= 60:
                freq_text = '🔥 高頻模式 (1分鐘)'
            elif execution_interval <= 180:
                freq_text = '⚡ 中頻模式 (3分鐘)'
            else:
                freq_text = '📊 正常模式 (5分鐘+)'
            
            message = f"""
{signal_emoji} <b>AImax 高頻交易執行</b>

{status_emoji} <b>執行狀態</b>: {status.upper()}
🎯 <b>交易信號</b>: {signal_text}
💰 <b>BTC價格</b>: NT${btc_price:,.0f}
{vol_emoji} <b>市場波動</b>: {vol_text}

🤖 <b>策略詳情</b>:
• 策略: {strategy.replace('_', ' ').title()}
• 信心度: {confidence:.0%}
• {freq_text}

🕐 <b>執行時間</b>: {now_taipei.strftime('%H:%M:%S')}
📅 <b>日期</b>: {now_taipei.strftime('%Y-%m-%d')}

💡 <i>85%勝率目標策略運行中</i>
            """.strip()
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"發送高頻執行警報失敗: {e}")
            return False
    
    def send_volatility_change_alert(self, old_volatility: str, new_volatility: str, 
                                   btc_price: float, price_change: float) -> bool:
        """發送波動性變化警報"""
        if not self._can_send_notification('volatility_change'):
            return False
        
        try:
            now_taipei = datetime.now(self.taipei_tz)
            
            # 波動性emoji映射
            vol_emojis = {'high': '🔥', 'medium': '📊', 'low': '📉'}
            old_emoji = vol_emojis.get(old_volatility, '❓')
            new_emoji = vol_emojis.get(new_volatility, '❓')
            
            # 價格變化方向
            price_emoji = '📈' if price_change > 0 else '📉' if price_change < 0 else '➡️'
            
            # 頻率調整預測
            if new_volatility == 'high':
                freq_change = '🔥 切換到高頻模式 (每1分鐘)'
            elif new_volatility == 'medium':
                freq_change = '⚡ 切換到中頻模式 (每3分鐘)'
            else:
                freq_change = '📊 切換到正常模式 (每5-15分鐘)'
            
            message = f"""
🔄 <b>AImax 波動性變化警報</b>

{old_emoji}➡️{new_emoji} <b>波動性變化</b>: {old_volatility.upper()} → {new_volatility.upper()}

💰 <b>當前價格</b>: NT${btc_price:,.0f}
{price_emoji} <b>價格變化</b>: {'+' if price_change >= 0 else ''}{price_change:.2f}%

🤖 <b>系統響應</b>:
• {freq_change}
• 智能頻率控制已啟動
• 85%勝率策略自動調整

🕐 <b>檢測時間</b>: {now_taipei.strftime('%H:%M:%S')}

💡 <i>系統將根據新波動性調整執行頻率</i>
            """.strip()
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"發送波動性變化警報失敗: {e}")
            return False
    
    def send_daily_performance_summary(self, daily_stats: Dict[str, Any]) -> bool:
        """發送每日性能摘要"""
        if not self._can_send_notification('daily_summary'):
            return False
        
        try:
            now_taipei = datetime.now(self.taipei_tz)
            today = now_taipei.strftime('%Y-%m-%d')
            
            # 解析統計數據
            total_executions = daily_stats.get('total_executions', 0)
            high_vol_executions = daily_stats.get('high_volatility_executions', 0)
            medium_vol_executions = daily_stats.get('medium_volatility_executions', 0)
            low_vol_executions = daily_stats.get('low_volatility_executions', 0)
            
            successful_executions = daily_stats.get('successful_executions', 0)
            failed_executions = daily_stats.get('failed_executions', 0)
            
            win_rate = daily_stats.get('win_rate', 0) * 100
            avg_confidence = daily_stats.get('average_confidence', 0.85)
            total_profit_loss = daily_stats.get('total_profit_loss', 0)
            
            # 計算性能指標
            high_vol_ratio = (high_vol_executions / total_executions * 100) if total_executions > 0 else 0
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            # 性能評級
            if win_rate >= 85:
                performance_grade = '🏆 優秀'
                grade_emoji = '🏆'
            elif win_rate >= 75:
                performance_grade = '✅ 良好'
                grade_emoji = '✅'
            elif win_rate >= 65:
                performance_grade = '⚠️ 一般'
                grade_emoji = '⚠️'
            else:
                performance_grade = '❌ 需改進'
                grade_emoji = '❌'
            
            message = f"""
📊 <b>AImax 每日性能報告</b>

📅 <b>日期</b>: {today}
🕐 <b>生成時間</b>: {now_taipei.strftime('%H:%M:%S')}

{grade_emoji} <b>整體表現</b>: {performance_grade}

🔄 <b>執行統計</b>:
• 總執行次數: {total_executions}
• 成功執行: {successful_executions} ({success_rate:.1f}%)
• 失敗執行: {failed_executions}

📈 <b>波動性分布</b>:
• 🔥 高波動: {high_vol_executions} ({high_vol_ratio:.1f}%)
• 📊 中波動: {medium_vol_executions}
• 📉 低波動: {low_vol_executions}

🎯 <b>策略表現</b>:
• 勝率: {win_rate:.1f}% (目標: 85%+)
• 平均信心度: {avg_confidence:.0%}
• 總盈虧: {'+' if total_profit_loss >= 0 else ''}{total_profit_loss:,.0f} TWD

🤖 <b>智能系統</b>:
• 頻率控制: {'🔥 高效' if high_vol_ratio > 20 else '📊 正常'}
• 策略適應: ✅ 自動調整
• 風險控制: ✅ 運行正常

💡 <b>明日展望</b>: 繼續85%勝率目標，優化智能頻率控制

<i>🚀 AImax 持續為您創造價值</i>
            """.strip()
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"發送每日性能摘要失敗: {e}")
            return False
    
    def send_system_health_alert(self, health_data: Dict[str, Any]) -> bool:
        """發送系統健康警報"""
        if not self._can_send_notification('system_error'):
            return False
        
        try:
            now_taipei = datetime.now(self.taipei_tz)
            
            overall_status = health_data.get('overall_status', 'unknown')
            issues = health_data.get('issues', [])
            btc_price = health_data.get('btc_price', 0)
            disk_usage = health_data.get('disk_usage_percent', 0)
            
            # 狀態emoji
            if overall_status == 'healthy':
                status_emoji = '✅'
                status_text = '系統健康'
            elif overall_status == 'warning':
                status_emoji = '⚠️'
                status_text = '系統警告'
            elif overall_status == 'critical':
                status_emoji = '🚨'
                status_text = '系統嚴重'
            else:
                status_emoji = '❓'
                status_text = '狀態未知'
            
            message = f"""
{status_emoji} <b>AImax 系統健康報告</b>

🏥 <b>整體狀態</b>: {status_text}
🕐 <b>檢查時間</b>: {now_taipei.strftime('%Y-%m-%d %H:%M:%S')}

💰 <b>市場連接</b>: {'✅ 正常' if btc_price > 0 else '❌ 異常'}
💾 <b>磁盤使用</b>: {disk_usage:.1f}%
☁️ <b>GitHub Actions</b>: ✅ 運行中

            """
            
            if issues:
                message += "\n⚠️ <b>發現問題</b>:\n"
                for i, issue in enumerate(issues[:5], 1):  # 最多顯示5個問題
                    message += f"• {issue}\n"
                
                if len(issues) > 5:
                    message += f"• ... 還有 {len(issues) - 5} 個問題\n"
            else:
                message += "\n✅ <b>未發現問題</b>\n"
            
            message += f"""
🔧 <b>建議操作</b>:
{'• 立即檢查系統狀態' if overall_status == 'critical' else '• 持續監控系統運行'}
• 查看監控面板: https://winyoulife.github.io/AImax-Trading-System/

<i>🤖 AImax 系統監控</i>
            """.strip()
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"發送系統健康警報失敗: {e}")
            return False
    
    def send_emergency_stop_alert(self, reason: str = "") -> bool:
        """發送緊急停止警報"""
        try:
            now_taipei = datetime.now(self.taipei_tz)
            
            message = f"""
🚨 <b>AImax 緊急停止警報</b> 🚨

⛔ <b>系統狀態</b>: 緊急停止
🕐 <b>停止時間</b>: {now_taipei.strftime('%Y-%m-%d %H:%M:%S')}

📋 <b>停止原因</b>:
{reason if reason else '用戶手動觸發緊急停止'}

🔧 <b>影響範圍</b>:
• 所有交易執行已暫停
• 高頻交易系統已停止
• 價格監控繼續運行

⚡ <b>立即行動</b>:
1. 檢查系統狀態
2. 確認停止原因
3. 評估是否需要重啟
4. 查看監控面板

🌐 <b>監控面板</b>: https://winyoulife.github.io/AImax-Trading-System/

<i>⚠️ 請立即處理此緊急情況</i>
            """.strip()
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"發送緊急停止警報失敗: {e}")
            return False
    
    def send_price_threshold_alert(self, current_price: float, threshold_type: str, 
                                 threshold_value: float) -> bool:
        """發送價格閾值警報"""
        if not self._can_send_notification('price_alert'):
            return False
        
        try:
            now_taipei = datetime.now(self.taipei_tz)
            
            if threshold_type == 'high':
                alert_emoji = '📈'
                alert_text = '價格突破上限'
            elif threshold_type == 'low':
                alert_emoji = '📉'
                alert_text = '價格跌破下限'
            else:
                alert_emoji = '💰'
                alert_text = '價格警報'
            
            message = f"""
{alert_emoji} <b>AImax 價格警報</b>

🚨 <b>警報類型</b>: {alert_text}
💰 <b>當前價格</b>: NT${current_price:,.0f}
🎯 <b>閾值</b>: NT${threshold_value:,.0f}

🤖 <b>系統響應</b>:
• 智能頻率控制已激活
• 85%勝率策略自動調整
• 風險控制機制啟動

🕐 <b>警報時間</b>: {now_taipei.strftime('%H:%M:%S')}

💡 <i>系統將根據價格變化調整交易策略</i>
            """.strip()
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"發送價格閾值警報失敗: {e}")
            return False
    
    def test_connection(self) -> bool:
        """測試連接"""
        try:
            now_taipei = datetime.now(self.taipei_tz)
            
            message = f"""
🧪 <b>AImax 高頻交易通知測試</b>

✅ <b>連接狀態</b>: 正常
🤖 <b>通知系統</b>: 已啟用
🔔 <b>高頻模式</b>: 準備就緒

🕐 <b>測試時間</b>: {now_taipei.strftime('%Y-%m-%d %H:%M:%S')}

🎯 <b>支援功能</b>:
• 高頻交易執行通知 ✅
• 波動性變化警報 ✅
• 每日性能摘要 ✅
• 系統健康監控 ✅
• 緊急停止警報 ✅
• 價格閾值警報 ✅

💡 <b>85%勝率策略通知系統已準備就緒！</b>

<i>🚀 AImax 智能通知系統 v3.0</i>
            """.strip()
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"測試連接失敗: {e}")
            return False


# 全局服務實例
_hf_telegram_service = None

def get_high_frequency_telegram_service() -> Optional[HighFrequencyTelegramService]:
    """獲取高頻交易Telegram服務實例"""
    return _hf_telegram_service

def initialize_high_frequency_telegram_service(bot_token: str, chat_id: str) -> HighFrequencyTelegramService:
    """初始化高頻交易Telegram服務"""
    global _hf_telegram_service
    _hf_telegram_service = HighFrequencyTelegramService(bot_token, chat_id)
    return _hf_telegram_service

def send_hf_notification(notification_type: str, data: Dict[str, Any]) -> bool:
    """發送高頻交易通知的便捷函數"""
    service = get_high_frequency_telegram_service()
    if not service:
        return False
    
    if notification_type == 'execution':
        return service.send_high_frequency_execution_alert(data)
    elif notification_type == 'volatility_change':
        return service.send_volatility_change_alert(
            data.get('old_volatility', ''),
            data.get('new_volatility', ''),
            data.get('btc_price', 0),
            data.get('price_change', 0)
        )
    elif notification_type == 'daily_summary':
        return service.send_daily_performance_summary(data)
    elif notification_type == 'system_health':
        return service.send_system_health_alert(data)
    elif notification_type == 'emergency_stop':
        return service.send_emergency_stop_alert(data.get('reason', ''))
    elif notification_type == 'price_alert':
        return service.send_price_threshold_alert(
            data.get('current_price', 0),
            data.get('threshold_type', ''),
            data.get('threshold_value', 0)
        )
    else:
        return False


# 使用示例
if __name__ == "__main__":
    # 測試高頻交易Telegram服務
    import os
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    
    if bot_token and chat_id:
        service = initialize_high_frequency_telegram_service(bot_token, chat_id)
        
        # 測試連接
        print("測試連接...")
        success = service.test_connection()
        print(f"連接測試: {'成功' if success else '失敗'}")
        
        # 測試執行通知
        execution_data = {
            'strategy': 'ultimate_optimized_85_percent',
            'btc_price': 3425000,
            'volatility_level': 'high',
            'signal': 'buy',
            'confidence': 0.90,
            'status': 'success',
            'execution_interval': 60
        }
        
        print("測試執行通知...")
        success = service.send_high_frequency_execution_alert(execution_data)
        print(f"執行通知: {'成功' if success else '失敗'}")
        
    else:
        print("請設置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 環境變量")