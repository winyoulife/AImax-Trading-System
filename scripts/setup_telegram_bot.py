#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram機器人設置助手
"""

import os
import sys
import requests
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.telegram_config import telegram_config

def print_header():
    """打印標題"""
    print("🤖 AImax Telegram機器人設置助手")
    print("=" * 50)

def get_bot_info(bot_token: str) -> dict:
    """獲取機器人信息"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"❌ 獲取機器人信息時發生錯誤: {e}")
        return None

def test_chat_access(bot_token: str, chat_id: str) -> bool:
    """測試聊天訪問權限"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": "🔧 AImax機器人配置測試\n\n✅ 連接成功！機器人已準備就緒。"
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            print(f"❌ 發送測試消息失敗: {response.status_code}")
            print(f"響應: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 測試聊天訪問時發生錯誤: {e}")
        return False

def setup_wizard():
    """設置向導"""
    print("\n📋 Telegram機器人設置向導")
    print("-" * 30)
    
    print("\n步驟1: 創建Telegram機器人")
    print("1. 在Telegram中搜索 @BotFather")
    print("2. 發送 /newbot 創建新機器人")
    print("3. 按提示設置機器人名稱和用戶名")
    print("4. 獲取Bot Token (格式: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)")
    
    bot_token = input("\n請輸入你的Bot Token: ").strip()
    
    if not bot_token:
        print("❌ Bot Token不能為空")
        return False
    
    # 驗證Bot Token
    print("\n🔍 驗證Bot Token...")
    bot_info = get_bot_info(bot_token)
    
    if not bot_info or not bot_info.get('ok'):
        print("❌ Bot Token無效，請檢查後重試")
        return False
    
    bot_data = bot_info['result']
    print(f"✅ 機器人驗證成功!")
    print(f"   名稱: {bot_data.get('first_name', 'Unknown')}")
    print(f"   用戶名: @{bot_data.get('username', 'Unknown')}")
    
    print("\n步驟2: 獲取Chat ID")
    print("1. 在Telegram中搜索你剛創建的機器人")
    print("2. 點擊 'START' 或發送 /start")
    print("3. 發送任意消息給機器人")
    print("4. 訪問以下URL獲取Chat ID:")
    print(f"   https://api.telegram.org/bot{bot_token}/getUpdates")
    print("5. 在返回的JSON中找到 'chat' -> 'id' 的值")
    
    chat_id = input("\n請輸入你的Chat ID: ").strip()
    
    if not chat_id:
        print("❌ Chat ID不能為空")
        return False
    
    # 測試連接
    print("\n🔍 測試機器人連接...")
    if test_chat_access(bot_token, chat_id):
        print("✅ 連接測試成功!")
        
        # 保存配置
        telegram_config.set_credentials(bot_token, chat_id)
        print("💾 配置已保存到 config/telegram_secrets.txt")
        
        return True
    else:
        print("❌ 連接測試失敗，請檢查Chat ID是否正確")
        return False

def show_current_config():
    """顯示當前配置"""
    print("\n📊 當前配置狀態")
    print("-" * 20)
    
    if telegram_config.is_configured():
        print("✅ 配置完整")
        print(f"📱 Chat ID: {telegram_config.get_chat_id()}")
        
        # 獲取機器人信息
        bot_info = get_bot_info(telegram_config.get_bot_token())
        if bot_info and bot_info.get('ok'):
            bot_data = bot_info['result']
            print(f"🤖 機器人: @{bot_data.get('username', 'Unknown')}")
            print(f"📝 名稱: {bot_data.get('first_name', 'Unknown')}")
        
        # 測試連接
        print("\n🔍 測試連接...")
        if test_chat_access(telegram_config.get_bot_token(), telegram_config.get_chat_id()):
            print("✅ 連接正常")
        else:
            print("❌ 連接異常")
    else:
        print("❌ 配置不完整")
        if not telegram_config.get_bot_token():
            print("   缺少: Bot Token")
        if not telegram_config.get_chat_id():
            print("   缺少: Chat ID")

def main():
    """主函數"""
    print_header()
    
    while True:
        print("\n📋 請選擇操作:")
        print("1. 查看當前配置")
        print("2. 設置機器人配置")
        print("3. 測試機器人連接")
        print("4. 退出")
        
        choice = input("\n請輸入選項 (1-4): ").strip()
        
        if choice == '1':
            show_current_config()
        elif choice == '2':
            if setup_wizard():
                print("\n🎉 設置完成！你現在可以運行機器人了:")
                print("   python scripts/run_telegram_bot.py")
        elif choice == '3':
            if telegram_config.is_configured():
                print("\n🔍 測試機器人連接...")
                if test_chat_access(telegram_config.get_bot_token(), telegram_config.get_chat_id()):
                    print("✅ 連接測試成功!")
                else:
                    print("❌ 連接測試失敗")
            else:
                print("❌ 請先完成機器人配置")
        elif choice == '4':
            print("\n👋 再見!")
            break
        else:
            print("❌ 無效選項，請重新選擇")

if __name__ == "__main__":
    main()