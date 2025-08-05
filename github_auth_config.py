#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub雲端部署專用認證配置
整合專屬帳號密碼系統到GitHub Pages靜態部署
"""

import hashlib
import json
import os

# 專屬認證配置
ADMIN_USERNAME = "lovejk1314"
ADMIN_PASSWORD_HASH = "898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae"  # Ichen5978

def generate_auth_config():
    """生成GitHub Pages用的認證配置"""
    auth_config = {
        "username": ADMIN_USERNAME,
        "password_hash": ADMIN_PASSWORD_HASH,
        "session_timeout": 3600,  # 1小時
        "max_login_attempts": 5,
        "lockout_duration": 300   # 5分鐘
    }
    
    return auth_config

def create_static_auth_js():
    """創建靜態JavaScript認證文件"""
    auth_js = f"""
// AImax 專屬認證系統
const AUTH_CONFIG = {{
    username: "{ADMIN_USERNAME}",
    passwordHash: "{ADMIN_PASSWORD_HASH}",
    sessionTimeout: 3600000, // 1小時 (毫秒)
    maxLoginAttempts: 5,
    lockoutDuration: 300000   // 5分鐘 (毫秒)
}};

class AuthManager {{
    constructor() {{
        this.loginAttempts = parseInt(localStorage.getItem('loginAttempts') || '0');
        this.lastAttempt = parseInt(localStorage.getItem('lastAttempt') || '0');
        this.sessionStart = parseInt(localStorage.getItem('sessionStart') || '0');
    }}
    
    hashPassword(password) {{
        // 使用Web Crypto API進行SHA-256哈希
        return crypto.subtle.digest('SHA-256', new TextEncoder().encode(password))
            .then(hashBuffer => {{
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            }});
    }}
    
    async authenticate(username, password) {{
        // 檢查是否被鎖定
        if (this.isLockedOut()) {{
            throw new Error('帳號已被鎖定，請稍後再試');
        }}
        
        // 驗證用戶名
        if (username !== AUTH_CONFIG.username) {{
            this.recordFailedAttempt();
            throw new Error('帳號或密碼錯誤');
        }}
        
        // 驗證密碼哈希
        const passwordHash = await this.hashPassword(password);
        if (passwordHash !== AUTH_CONFIG.passwordHash) {{
            this.recordFailedAttempt();
            throw new Error('帳號或密碼錯誤');
        }}
        
        // 認證成功
        this.clearFailedAttempts();
        this.startSession();
        return true;
    }}
    
    isLockedOut() {{
        if (this.loginAttempts >= AUTH_CONFIG.maxLoginAttempts) {{
            const timeSinceLastAttempt = Date.now() - this.lastAttempt;
            return timeSinceLastAttempt < AUTH_CONFIG.lockoutDuration;
        }}
        return false;
    }}
    
    recordFailedAttempt() {{
        this.loginAttempts++;
        this.lastAttempt = Date.now();
        localStorage.setItem('loginAttempts', this.loginAttempts.toString());
        localStorage.setItem('lastAttempt', this.lastAttempt.toString());
    }}
    
    clearFailedAttempts() {{
        this.loginAttempts = 0;
        localStorage.removeItem('loginAttempts');
        localStorage.removeItem('lastAttempt');
    }}
    
    startSession() {{
        this.sessionStart = Date.now();
        localStorage.setItem('sessionStart', this.sessionStart.toString());
        localStorage.setItem('authenticated', 'true');
    }}
    
    isAuthenticated() {{
        const authenticated = localStorage.getItem('authenticated') === 'true';
        if (!authenticated) return false;
        
        const sessionAge = Date.now() - this.sessionStart;
        if (sessionAge > AUTH_CONFIG.sessionTimeout) {{
            this.logout();
            return false;
        }}
        
        return true;
    }}
    
    logout() {{
        localStorage.removeItem('authenticated');
        localStorage.removeItem('sessionStart');
        window.location.reload();
    }}
    
    getRemainingLockoutTime() {{
        if (!this.isLockedOut()) return 0;
        const elapsed = Date.now() - this.lastAttempt;
        return Math.max(0, AUTH_CONFIG.lockoutDuration - elapsed);
    }}
}}

// 全局認證管理器
window.authManager = new AuthManager();
"""
    
    return auth_js

def create_github_secrets_template():
    """創建GitHub Secrets配置模板"""
    secrets_template = {
        "ADMIN_USERNAME": ADMIN_USERNAME,
        "ADMIN_PASSWORD_HASH": ADMIN_PASSWORD_HASH,
        "SESSION_SECRET": "your-random-session-secret-here",
        "TELEGRAM_BOT_TOKEN": "your-telegram-bot-token",
        "TELEGRAM_CHAT_ID": "your-telegram-chat-id",
        "BINANCE_API_KEY": "your-binance-api-key",
        "BINANCE_SECRET_KEY": "your-binance-secret-key"
    }
    
    return secrets_template

def main():
    """主函數 - 生成所有認證相關文件"""
    print("🔐 生成GitHub雲端部署認證配置...")
    
    # 創建認證配置
    auth_config = generate_auth_config()
    with open('static/auth_config.json', 'w') as f:
        json.dump(auth_config, f, indent=2)
    print("✅ 認證配置已生成: static/auth_config.json")
    
    # 創建JavaScript認證文件
    auth_js = create_static_auth_js()
    os.makedirs('static/js', exist_ok=True)
    with open('static/js/auth.js', 'w', encoding='utf-8') as f:
        f.write(auth_js)
    print("✅ JavaScript認證文件已生成: static/js/auth.js")
    
    # 創建GitHub Secrets模板
    secrets_template = create_github_secrets_template()
    with open('github_secrets_template.json', 'w') as f:
        json.dump(secrets_template, f, indent=2)
    print("✅ GitHub Secrets模板已生成: github_secrets_template.json")
    
    print("\n🎯 配置完成！")
    print(f"專屬帳號: {ADMIN_USERNAME}")
    print("專屬密碼: Ichen5978")
    print("密碼哈希: " + ADMIN_PASSWORD_HASH[:20] + "...")
    
    print("\n📝 下一步:")
    print("1. 將 github_secrets_template.json 中的值添加到GitHub Secrets")
    print("2. 部署到GitHub Pages時會自動使用這些認證配置")
    print("3. 用戶只能通過你的專屬帳號密碼訪問控制面板")

if __name__ == "__main__":
    main()