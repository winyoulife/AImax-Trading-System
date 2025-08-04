#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax Web服務器啟動腳本
用於在雲端服務器上啟動Web控制面板
"""

import os
import sys
import subprocess
import signal
import time
from datetime import datetime

def check_dependencies():
    """檢查依賴"""
    print("🔍 檢查系統依賴...")
    
    try:
        import flask
        import flask_cors
        print("✅ Flask 已安裝")
    except ImportError:
        print("❌ Flask 未安裝，正在安裝...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"])
    
    # 檢查其他依賴
    required_modules = ['pandas', 'numpy', 'requests']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} 已安裝")
        except ImportError:
            print(f"❌ {module} 未安裝")
            return False
    
    return True

def start_web_server():
    """啟動Web服務器"""
    print("🚀 啟動 AImax Web 控制面板...")
    print("=" * 50)
    
    # 檢查依賴
    if not check_dependencies():
        print("❌ 依賴檢查失敗，請先安裝必要的依賴包")
        return False
    
    # 設置環境變數
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = '0'
    
    try:
        # 啟動Web應用
        from web_app import app
        
        print("✅ Web服務器啟動成功！")
        print("📱 控制面板地址:")
        print("   本地訪問: http://localhost:5000")
        print("   遠程訪問: http://[你的服務器IP]:5000")
        print()
        print("🔐 專屬登入資訊:")
        print("   帳號: lovejk1314")
        print("   密碼: Ichen5978")
        print()
        print("⚠️  重要提醒:")
        print("   • 已設置專屬密碼")
        print("   • 如需修改密碼請使用 python change_password.py")
        print("   • 建議配置防火牆限制訪問")
        print()
        print("🛑 按 Ctrl+C 停止服務器")
        print("=" * 50)
        
        # 運行應用
        app.run(
            host='0.0.0.0',  # 允許外部訪問
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Web服務器已停止")
        return True
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        return False

def show_help():
    """顯示幫助資訊"""
    print("AImax Web服務器啟動工具")
    print()
    print("用法:")
    print("  python start_web_server.py        # 啟動Web服務器")
    print("  python start_web_server.py --help # 顯示此幫助")
    print()
    print("功能:")
    print("  • 自動檢查和安裝依賴")
    print("  • 啟動Web控制面板")
    print("  • 支持遠程訪問")
    print("  • 安全身份驗證")
    print()
    print("安全建議:")
    print("  • 立即修改預設密碼")
    print("  • 配置防火牆規則")
    print("  • 使用HTTPS（生產環境）")
    print("  • 定期更新系統")

def main():
    """主函數"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        show_help()
        return 0
    
    print(f"⏰ 啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if start_web_server():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())