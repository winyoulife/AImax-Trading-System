#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停止所有Telegram機器人實例
"""

import requests
import time

def stop_all_bots():
    """停止所有機器人實例"""
    print("🛑 停止所有Telegram機器人實例...")
    
    bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
    
    try:
        # 1. 刪除webhook（如果有的話）
        print("1️⃣ 刪除webhook...")
        delete_webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        response = requests.post(delete_webhook_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook已刪除")
        
        # 2. 獲取並清空所有pending updates
        print("2️⃣ 清空pending updates...")
        updates_url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        # 獲取所有updates
        response = requests.get(updates_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('result'):
                # 獲取最後一個update_id
                last_update_id = data['result'][-1]['update_id']
                
                # 確認所有updates
                confirm_url = f"{updates_url}?offset={last_update_id + 1}"
                requests.get(confirm_url, timeout=10)
                
                print(f"✅ 已清空 {len(data['result'])} 個pending updates")
            else:
                print("✅ 沒有pending updates")
        
        # 3. 等待一下讓所有實例停止
        print("3️⃣ 等待所有實例停止...")
        time.sleep(3)
        
        # 4. 測試是否可以正常獲取updates
        print("4️⃣ 測試getUpdates...")
        response = requests.get(updates_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ getUpdates現在可以正常工作")
            print("🎉 所有機器人實例已停止，可以啟動新的實例了")
        else:
            print(f"❌ 仍然有問題: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 停止過程中發生錯誤: {e}")

if __name__ == "__main__":
    stop_all_bots()