#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強制清除瀏覽器緩存
解決頁面不更新的問題
"""

import os
import sys
import time
from datetime import datetime

def force_cache_clear():
    """強制清除緩存"""
    print("🔥 強制清除瀏覽器緩存")
    print("=" * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 創建多個版本的文件來確保更新
    base_file = "static/smart-balanced-dashboard-static.html"
    
    if os.path.exists(base_file):
        # 創建帶時間戳的版本
        new_files = [
            f"static/dashboard-latest-{timestamp}.html",
            f"static/dashboard-fresh.html",
            f"static/dashboard-nocache.html"
        ]
        
        for new_file in new_files:
            print(f"📋 創建新版本: {new_file}")
            
            # 讀取原文件
            with open(base_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 添加更強的緩存控制
            cache_control = f'''
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate, max-age=0">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="cache-buster" content="{timestamp}">
    <meta name="last-modified" content="{datetime.now().isoformat()}">
    <script>
        // 強制刷新
        if (performance.navigation.type !== 1) {{
            window.location.reload(true);
        }}
    </script>'''
            
            # 插入緩存控制
            content = content.replace('<title>', cache_control + '\n    <title>')
            
            # 更新版本信息
            content = content.replace(
                'v2.1-stable | 2025/08/07 22:35',
                f'v2.1-FRESH | {datetime.now().strftime("%Y/%m/%d %H:%M")}'
            )
            
            # 寫入新文件
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n✅ 創建了 {len(new_files)} 個新版本文件")
        
        # 創建索引頁面
        index_content = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AImax 儀表板 - 選擇版本</title>
    <meta http-equiv="Cache-Control" content="no-cache">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
        .version-card {{ background: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #007bff; }}
        .btn {{ display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; }}
        .btn:hover {{ background: #0056b3; }}
        .fresh {{ border-left-color: #28a745; }}
        .fresh .btn {{ background: #28a745; }}
    </style>
</head>
<body>
    <h1>🔥 AImax 儀表板 - 強制更新版本</h1>
    <p>如果主頁面沒有更新，請嘗試以下版本：</p>
    
    <div class="version-card fresh">
        <h3>🔥 最新版本 (推薦)</h3>
        <p>時間戳: {timestamp}</p>
        <a href="./dashboard-latest-{timestamp}.html" class="btn">🚀 訪問最新版本</a>
    </div>
    
    <div class="version-card">
        <h3>📋 原始版本</h3>
        <a href="./smart-balanced-dashboard-static.html" class="btn">訪問原始版本</a>
    </div>
    
    <div class="version-card">
        <h3>🔄 其他版本</h3>
        <a href="./dashboard-fresh.html" class="btn">Fresh版本</a>
        <a href="./dashboard-nocache.html" class="btn">NoCache版本</a>
        <a href="./dashboard-v2-updated.html" class="btn">V2版本</a>
    </div>
    
    <div class="version-card">
        <h3>💡 清除緩存方法</h3>
        <p>1. 按 Ctrl+F5 強制刷新</p>
        <p>2. 按 Ctrl+Shift+R 硬刷新</p>
        <p>3. 開啟無痕模式訪問</p>
        <p>4. 清除瀏覽器緩存</p>
    </div>
    
    <p><strong>更新時間:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</body>
</html>'''
        
        with open("static/index-versions.html", 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"📋 創建版本選擇頁面: static/index-versions.html")
        
    else:
        print(f"❌ 找不到基礎文件: {base_file}")
    
    print(f"\n" + "=" * 60)
    print("🔥 緩存清除完成")
    print(f"\n🌐 訪問地址:")
    print(f"• 版本選擇: https://winyoulife.github.io/AImax-Trading-System/index-versions.html")
    print(f"• 最新版本: https://winyoulife.github.io/AImax-Trading-System/dashboard-latest-{timestamp}.html")
    print(f"• 原始版本: https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-static.html")

if __name__ == "__main__":
    force_cache_clear()