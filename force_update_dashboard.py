#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 強制更新儀表板 - 解決緩存問題
確保混合高頻策略正確部署到線上
"""

import os
import shutil
from datetime import datetime

def force_update_dashboard():
    """強制更新儀表板，解決緩存問題"""
    
    print("🔥 強制更新儀表板 - 解決緩存問題")
    print("=" * 50)
    
    # 1. 確保主文件包含混合高頻策略
    main_file = "static/smart-balanced-dashboard.html"
    
    if not os.path.exists(main_file):
        print(f"❌ 主文件不存在: {main_file}")
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否包含混合高頻策略
    if 'fetchBTCPriceHybrid' not in content:
        print("❌ 主文件不包含混合高頻策略")
        return False
    
    print("✅ 主文件包含混合高頻策略")
    
    # 2. 強制更新版本號和時間戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    version_tag = f"v2.3-hybrid-{timestamp}"
    
    # 更新版本標識
    import re
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    version_pattern = r'版本: v[\d\.]+-[\w-]+ \| 更新時間: [\d/]+ [\d:]+'
    new_version = f'版本: {version_tag} | 更新時間: {current_time}'
    content = re.sub(version_pattern, new_version, content)
    
    # 添加緩存破壞器
    cache_buster = f"?v={timestamp}"
    
    # 在頁面頭部添加強制刷新meta標籤
    meta_tags = f'''    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="version" content="{version_tag}">
'''
    
    if '<meta charset="UTF-8">' in content:
        content = content.replace('<meta charset="UTF-8">', f'<meta charset="UTF-8">\n{meta_tags}')
    
    # 在JavaScript中添加版本檢查
    version_check_js = f'''
        // 版本檢查和強制刷新
        console.log('🚀 AImax 混合高頻策略 - {version_tag}');
        console.log('📅 部署時間: {current_time}');
        
        // 檢查是否為最新版本
        const currentVersion = '{version_tag}';
        const storedVersion = localStorage.getItem('aimax_version');
        
        if (storedVersion && storedVersion !== currentVersion) {{
            console.log('🔄 檢測到新版本，清除緩存...');
            localStorage.clear();
            sessionStorage.clear();
        }}
        
        localStorage.setItem('aimax_version', currentVersion);
'''
    
    # 在頁面載入事件前添加版本檢查
    if 'document.addEventListener(\'DOMContentLoaded\'' in content:
        content = content.replace(
            'document.addEventListener(\'DOMContentLoaded\'',
            version_check_js + '\n        document.addEventListener(\'DOMContentLoaded\''
        )
    
    # 保存更新後的主文件
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 主文件已更新版本: {version_tag}")
    
    # 3. 同步到所有相關文件
    target_files = [
        "static/smart-balanced-dashboard-static.html",
        "static/index.html"
    ]
    
    for target in target_files:
        if os.path.exists(target):
            shutil.copy2(main_file, target)
            print(f"✅ 同步到: {target}")
    
    # 4. 創建帶時間戳的新版本文件
    timestamped_file = f"static/smart-balanced-dashboard-{timestamp}.html"
    shutil.copy2(main_file, timestamped_file)
    print(f"✅ 創建時間戳版本: {timestamped_file}")
    
    # 5. 創建版本信息文件
    version_info = {
        "version": version_tag,
        "timestamp": timestamp,
        "update_time": current_time,
        "features": [
            "混合高頻價格更新策略",
            "每30秒CORS代理實時數據",
            "每2分鐘GitHub Actions備援",
            "三層容錯機制",
            "強制緩存刷新"
        ],
        "urls": [
            f"https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard.html{cache_buster}",
            f"https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-{timestamp}.html"
        ]
    }
    
    import json
    with open('static/version_info.json', 'w', encoding='utf-8') as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)
    
    print("✅ 版本信息文件已創建")
    
    # 6. Git提交和推送
    print("\n🚀 部署到GitHub...")
    
    os.system("git add .")
    commit_msg = f"🔥 強制更新混合高頻策略 - {version_tag}"
    os.system(f'git commit -m "{commit_msg}"')
    os.system("git push origin main")
    
    print("✅ 部署完成")
    
    # 7. 顯示訪問信息
    print("\n" + "=" * 50)
    print("🎉 強制更新完成！")
    print("=" * 50)
    print(f"📅 版本: {version_tag}")
    print(f"⏰ 時間: {current_time}")
    print("\n🌐 訪問地址 (選擇任一個):")
    print(f"1. 主頁面: https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard.html{cache_buster}")
    print(f"2. 時間戳版本: https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-{timestamp}.html")
    print("\n💡 如果還是看不到更新:")
    print("1. 按 Ctrl+F5 強制刷新")
    print("2. 清除瀏覽器緩存")
    print("3. 使用無痕模式訪問")
    print("4. 等待2-3分鐘後再試")
    
    return True

if __name__ == "__main__":
    force_update_dashboard()