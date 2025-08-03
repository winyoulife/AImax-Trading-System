#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單的Telegram連接測試
"""

import sys
import os

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.notifications.telegram_service import TelegramService

def test_simple_message():
    """測試簡單消息發送"""
    print("📱 測試Telegram基本連接...")
    
    # 使用你的配置
    bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
    chat_id = "8164385222"
    
    # 創建服務
    service = TelegramService(bot_token, chat_id)
    
    # 發送測試消息
    test_message = """
🔧 <b>Telegram連接測試</b>

✅ 如果你看到這條消息，說明基本連接正常！

現在讓我們測試雙向功能...
    """.strip()
    
    success = service.send_message_sync(test_message)
    
    if success:
        print("✅ 測試消息發送成功！")
        print("📱 請檢查你的手機是否收到消息")
        
        # 現在測試獲取更新
        print("\n🔍 測試獲取Telegram更新...")
        test_get_updates(bot_token)
        
    else:
        print("❌ 測試消息發送失敗")

def test_get_updates(bot_token):
    """測試獲取更新"""
    import requests
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功獲取更新，狀態碼: {response.status_code}")
            
            if data.get('result'):
                print(f"📨 找到 {len(data['result'])} 條更新")
                
                # 顯示最近的消息
                for update in data['result'][-3:]:  # 顯示最近3條
                    if 'message' in update:
                        msg = update['message']
                        text = msg.get('text', '(無文字)')
                        timestamp = msg.get('date', 0)
                        print(f"   消息: {text} (時間戳: {timestamp})")
            else:
                print("📭 沒有找到更新")
                
        else:
            print(f"❌ 獲取更新失敗，狀態碼: {response.status_code}")
            print(f"響應: {response.text}")
            
    except Exception as e:
        print(f"❌ 獲取更新時發生錯誤: {e}")

if __name__ == "__main__":
    test_simple_message()