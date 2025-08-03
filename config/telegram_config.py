#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram機器人配置
"""

import os
from typing import Optional

class TelegramConfig:
    """Telegram配置管理"""
    
    def __init__(self):
        # 從環境變量讀取配置
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
        
        # 如果環境變量為空，嘗試從配置文件讀取
        if not self.bot_token or not self.chat_id:
            self._load_from_file()
    
    def _load_from_file(self):
        """從配置文件讀取設置"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'telegram_secrets.txt')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line.startswith('BOT_TOKEN='):
                            self.bot_token = line.split('=', 1)[1]
                        elif line.startswith('CHAT_ID='):
                            self.chat_id = line.split('=', 1)[1]
        except Exception as e:
            print(f"讀取配置文件時發生錯誤: {e}")
    
    def is_configured(self) -> bool:
        """檢查是否已正確配置"""
        return bool(self.bot_token and self.chat_id)
    
    def get_bot_token(self) -> str:
        """獲取機器人token"""
        return self.bot_token
    
    def get_chat_id(self) -> str:
        """獲取聊天ID"""
        return self.chat_id
    
    def set_credentials(self, bot_token: str, chat_id: str):
        """設置憑證"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        
        # 保存到配置文件
        self._save_to_file()
    
    def _save_to_file(self):
        """保存到配置文件"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'telegram_secrets.txt')
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(f"BOT_TOKEN={self.bot_token}\n")
                f.write(f"CHAT_ID={self.chat_id}\n")
        except Exception as e:
            print(f"保存配置文件時發生錯誤: {e}")

# 全局配置實例
telegram_config = TelegramConfig()