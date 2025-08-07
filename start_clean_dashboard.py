#!/usr/bin/env python3
"""
啟動簡潔版儀表板
包含 MAX API 代理服務器
"""

import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

# 添加當前目錄到 Python 路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def start_proxy_server():
    """啟動代理服務器"""
    try:
        from max_api_proxy import app
        print("🚀 啟動 MAX API 代理服務器...")
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ 代理服務器啟動失敗: {e}")

def open_dashboard():
    """打開儀表板"""
    time.sleep(2)  # 等待服務器啟動
    dashboard_path = current_dir / 'static' / 'clean-dashboard.html'
    
    if dashboard_path.exists():
        print(f"🌐 打開儀表板: {dashboard_path}")
        webbrowser.open(f'file://{dashboard_path.absolute()}')
    else:
        print(f"❌ 找不到儀表板文件: {dashboard_path}")

def main():
    print("=" * 50)
    print("🤖 AImax v1.0-smart-balanced 簡潔版交易儀表板")
    print("=" * 50)
    
    # 檢查必要文件
    proxy_file = current_dir / 'max_api_proxy.py'
    dashboard_file = current_dir / 'static' / 'clean-dashboard.html'
    
    if not proxy_file.exists():
        print(f"❌ 找不到代理服務器文件: {proxy_file}")
        return
    
    if not dashboard_file.exists():
        print(f"❌ 找不到儀表板文件: {dashboard_file}")
        return
    
    print("📋 啟動信息:")
    print(f"   • 代理服務器: http://localhost:5000")
    print(f"   • 儀表板文件: {dashboard_file}")
    print(f"   • 登入帳號: admin")
    print(f"   • 登入密碼: aimax2025")
    print()
    
    try:
        # 在後台線程中打開瀏覽器
        browser_thread = threading.Thread(target=open_dashboard)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 啟動代理服務器（主線程）
        start_proxy_server()
        
    except KeyboardInterrupt:
        print("\n🛑 用戶中斷，正在關閉服務器...")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == '__main__':
    main()