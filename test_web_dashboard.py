#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試Web控制面板
啟動本地服務器預覽控制面板
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def start_web_server():
    """啟動Web服務器"""
    # 切換到static目錄
    static_dir = Path(__file__).parent / "static"
    if not static_dir.exists():
        print("❌ static目錄不存在")
        return False
    
    os.chdir(static_dir)
    
    # 設置端口
    PORT = 8081
    
    try:
        # 創建HTTP服務器
        Handler = http.server.SimpleHTTPRequestHandler
        
        # 添加CORS頭部支持
        class CORSRequestHandler(Handler):
            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                super().end_headers()
        
        with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
            print("=" * 60)
            print("🌐 AImax Web控制面板測試服務器")
            print("=" * 60)
            print(f"📱 本地訪問: http://localhost:{PORT}")
            print(f"🔐 測試帳號: lovejk1314")
            print(f"🔑 測試密碼: Ichen5978")
            print("=" * 60)
            print("🚀 服務器啟動成功！")
            print("🛑 按 Ctrl+C 停止服務器")
            print("=" * 60)
            
            # 自動打開瀏覽器
            try:
                webbrowser.open(f'http://localhost:{PORT}')
                print("🌐 已自動打開瀏覽器")
            except:
                print("⚠️ 無法自動打開瀏覽器，請手動訪問上述地址")
            
            # 啟動服務器
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 服務器已停止")
        return True
    except Exception as e:
        print(f"❌ 啟動服務器失敗: {e}")
        return False

def main():
    """主函數"""
    print("🧪 AImax Web控制面板測試工具")
    print()
    
    # 檢查文件是否存在
    static_dir = Path(__file__).parent / "static"
    required_files = [
        "index.html",
        "css/dashboard.css", 
        "js/auth.js",
        "js/dashboard.js",
        "js/github-api.js"
    ]
    
    missing_files = []
    for file in required_files:
        if not (static_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n請確保所有Web文件都已創建")
        return 1
    
    print("✅ 所有必要文件都存在")
    print()
    
    # 啟動服務器
    if start_web_server():
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())