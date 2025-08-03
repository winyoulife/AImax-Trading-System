#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復Telegram Webhook問題
"""

import requests
import sys
import os

def fix_webhook_issue():
    """修復webhook問題"""
    print("🔧 修復Telegram Webhook問題...")
    
    # 使用你的Bot Token
    bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
    
    try:
        # 1. 檢查當前webhook狀態
        print("1️⃣ 檢查當前webhook狀態...")
        webhook_info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        response = requests.get(webhook_info_url, timeout=10)
        
        if response.status_code == 200:
            webhook_info = response.json()
            print(f"✅ Webhook信息獲取成功")
            
            if webhook_info['result']['url']:
                print(f"🔗 當前webhook URL: {webhook_info['result']['url']}")
                print("❌ 檢測到活躍的webhook，需要刪除")
            else:
                print("✅ 沒有設置webhook")
        
        # 2. 刪除webhook
        print("\n2️⃣ 刪除webhook...")
        delete_webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        response = requests.post(delete_webhook_url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                print("✅ Webhook已成功刪除")
            else:
                print(f"❌ 刪除webhook失敗: {result}")
        else:
            print(f"❌ 刪除webhook請求失敗: {response.status_code}")
        
        # 3. 測試getUpdates
        print("\n3️⃣ 測試getUpdates...")
        updates_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(updates_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ getUpdates現在可以正常工作了！")
            
            if data.get('result'):
                print(f"📨 找到 {len(data['result'])} 條更新")
                
                # 顯示最近的消息
                print("\n📱 最近的消息:")
                for update in data['result'][-5:]:  # 顯示最近5條
                    if 'message' in update:
                        msg = update['message']
                        text = msg.get('text', '(無文字)')
                        from_user = msg.get('from', {}).get('first_name', '未知用戶')
                        timestamp = msg.get('date', 0)
                        
                        # 轉換時間戳
                        from datetime import datetime
                        dt = datetime.fromtimestamp(timestamp)
                        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                        
                        print(f"   👤 {from_user}: {text}")
                        print(f"   ⏰ 時間: {time_str}")
                        print()
            else:
                print("📭 沒有找到更新")
                
        else:
            print(f"❌ getUpdates仍然失敗: {response.status_code}")
            print(f"響應: {response.text}")
        
        print("\n🎉 修復完成！現在可以啟動雙向機器人了。")
        
    except Exception as e:
        print(f"❌ 修復過程中發生錯誤: {e}")

if __name__ == "__main__":
    fix_webhook_issue()