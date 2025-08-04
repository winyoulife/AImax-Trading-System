#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Web登入功能
"""

import hashlib
import requests
import time
import threading
from web_app import app

def hash_password(password):
    """生成密碼哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def test_login_credentials():
    """測試登入憑證"""
    print("🔐 測試登入憑證...")
    
    # 測試帳號密碼
    username = "lovejk1314"
    password = "Ichen5978"
    expected_hash = "898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae"
    
    # 生成哈希
    actual_hash = hash_password(password)
    
    print(f"帳號: {username}")
    print(f"密碼: {password}")
    print(f"預期哈希: {expected_hash}")
    print(f"實際哈希: {actual_hash}")
    
    if actual_hash == expected_hash:
        print("✅ 密碼哈希驗證成功！")
        return True
    else:
        print("❌ 密碼哈希驗證失敗！")
        return False

def start_test_server():
    """啟動測試服務器"""
    print("🚀 啟動測試Web服務器...")
    app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)

def test_web_access():
    """測試Web訪問"""
    print("🌐 測試Web訪問...")
    
    # 等待服務器啟動
    time.sleep(2)
    
    try:
        # 測試主頁（應該重定向到登入頁）
        response = requests.get('http://127.0.0.1:5001/', timeout=5)
        print(f"主頁訪問狀態: {response.status_code}")
        
        # 測試登入頁
        response = requests.get('http://127.0.0.1:5001/login', timeout=5)
        print(f"登入頁狀態: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Web服務器運行正常！")
            return True
        else:
            print("❌ Web服務器訪問失敗！")
            return False
            
    except Exception as e:
        print(f"❌ Web訪問測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 50)
    print("🧪 AImax Web系統測試")
    print("=" * 50)
    
    # 測試登入憑證
    if not test_login_credentials():
        print("❌ 登入憑證測試失敗")
        return False
    
    print("\n" + "-" * 30)
    
    # 啟動測試服務器（在後台線程）
    server_thread = threading.Thread(target=start_test_server, daemon=True)
    server_thread.start()
    
    # 測試Web訪問
    if not test_web_access():
        print("❌ Web訪問測試失敗")
        return False
    
    print("\n" + "=" * 50)
    print("✅ 所有測試通過！")
    print("🌐 你可以訪問: http://localhost:5000")
    print(f"🔐 帳號: lovejk1314")
    print(f"🔑 密碼: Ichen5978")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 測試已取消")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")