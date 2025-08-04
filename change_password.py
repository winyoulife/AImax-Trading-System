#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 密碼修改工具
用於修改Web控制面板的登入密碼
"""

import hashlib
import getpass
import sys

def hash_password(password):
    """生成密碼哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def change_password():
    """修改密碼"""
    print("🔐 AImax 密碼修改工具")
    print("=" * 40)
    
    # 獲取新密碼
    while True:
        new_password = getpass.getpass("請輸入新密碼: ")
        if len(new_password) < 6:
            print("❌ 密碼長度至少需要6個字符")
            continue
        
        confirm_password = getpass.getpass("請再次輸入新密碼: ")
        if new_password != confirm_password:
            print("❌ 兩次輸入的密碼不一致")
            continue
        
        break
    
    # 生成哈希
    password_hash = hash_password(new_password)
    
    print("\n✅ 密碼哈希已生成！")
    print("請將以下哈希值複製到 web_app.py 中的 ADMIN_PASSWORD_HASH 變數：")
    print("-" * 60)
    print(f'ADMIN_PASSWORD_HASH = "{password_hash}"')
    print("-" * 60)
    
    # 提供修改指引
    print("\n📝 修改步驟：")
    print("1. 打開 web_app.py 文件")
    print("2. 找到 ADMIN_PASSWORD_HASH 變數")
    print("3. 將上面的哈希值替換原有值")
    print("4. 保存文件並重啟Web服務")
    
    print("\n⚠️  安全提醒：")
    print("• 請使用強密碼（包含大小寫字母、數字、特殊字符）")
    print("• 定期更換密碼")
    print("• 不要在公共場所輸入密碼")

if __name__ == "__main__":
    try:
        change_password()
    except KeyboardInterrupt:
        print("\n\n👋 密碼修改已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        sys.exit(1)