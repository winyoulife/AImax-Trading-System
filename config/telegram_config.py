#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram配置設置
"""

# Telegram Bot設置
TELEGRAM_BOT_TOKEN = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
TELEGRAM_CHAT_ID = "8164385222"

# 通知設置
NOTIFICATION_SETTINGS = {
    "send_trading_signals": True,      # 發送交易信號
    "send_backtest_summary": True,     # 發送回測總結
    "send_system_status": True,        # 發送系統狀態
    "send_error_alerts": True,         # 發送錯誤警報
}

# 消息格式設置
MESSAGE_SETTINGS = {
    "use_html": True,                  # 使用HTML格式
    "include_charts": False,           # 包含圖表（暫不支持）
    "timezone": "Asia/Taipei",         # 時區設置
}