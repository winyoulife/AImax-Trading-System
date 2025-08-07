#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速更新工具
處理常見的更新需求
"""

import os
import sys
import argparse
from datetime import datetime

def update_btc_price():
    """更新BTC價格為真實API"""
    print("🔧 更新BTC價格為真實API...")
    
    dashboard_file = "static/smart-balanced-dashboard.html"
    
    if not os.path.exists(dashboard_file):
        print(f"❌ 文件不存在: {dashboard_file}")
        return False
    
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經有真實API
    if 'fetchRealBTCPrice' in content and 'max-api.maicoin.com' in content:
        print("✅ BTC價格API已經是最新版本")
        return True
    
    # 添加真實API函數
    api_function = '''
        // 獲取真實的MAX API BTC價格
        async function fetchRealBTCPrice() {
            try {
                const proxyUrl = 'https://api.allorigins.win/raw?url=';
                const maxApiUrl = 'https://max-api.maicoin.com/api/v2/tickers/btctwd';
                
                const response = await fetch(proxyUrl + encodeURIComponent(maxApiUrl));
                const data = await response.json();
                
                if (data && data.ticker && data.ticker.last) {
                    const btcPrice = parseFloat(data.ticker.last);
                    document.getElementById('btc-price').textContent = `NT$ ${formatNumber(btcPrice)}`;
                    
                    const btcAmount = 0.010544;
                    const positionValue = btcPrice * btcAmount;
                    document.getElementById('position-value').textContent = `NT$ ${formatNumber(Math.round(positionValue))}`;
                    
                    console.log(`✅ BTC價格已更新: NT$ ${formatNumber(btcPrice)}`);
                } else {
                    throw new Error('API數據格式錯誤');
                }
            } catch (error) {
                console.error('❌ 獲取BTC價格失敗:', error);
                const fallbackPrice = 3000000;
                document.getElementById('btc-price').textContent = `NT$ ${formatNumber(fallbackPrice)} (備用)`;
            }
        }
'''
    
    # 替換refreshData函數
    import re
    old_refresh = r'function refreshData\(\) \{[^}]+\}'
    new_refresh = '''function refreshData() {
            fetchRealBTCPrice();
            document.getElementById('last-update').textContent = new Date().toLocaleString('zh-TW');
            console.log('數據已刷新');
        }'''
    
    # 添加API函數
    script_pos = content.find('function formatNumber')
    if script_pos != -1:
        content = content[:script_pos] + api_function + '\n        ' + content[script_pos:]
    
    # 替換refreshData
    content = re.sub(old_refresh, new_refresh, content, flags=re.DOTALL)
    
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ BTC價格API已更新")
    return True

def update_version(version_tag=None):
    """更新版本標識"""
    if not version_tag:
        version_tag = f"v2.3-updated-{datetime.now().strftime('%m%d')}"
    
    print(f"📅 更新版本標識: {version_tag}")
    
    dashboard_file = "static/smart-balanced-dashboard.html"
    
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新版本標識
    import re
    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")
    
    version_pattern = r'版本: v[\d\.]+-\w+ \| 更新時間: [\d/]+ [\d:]+'
    new_version = f'版本: {version_tag} | 更新時間: {timestamp}'
    content = re.sub(version_pattern, new_version, content)
    
    # 更新右下角版本
    corner_pattern = r'🔄 v[\d\.]+-\w+ \| [\d/]+ [\d:]+ \|'
    new_corner = f'🔄 {version_tag} | {timestamp} |'
    content = re.sub(corner_pattern, new_corner, content)
    
    with open(dashboard_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 版本已更新: {version_tag}")
    return True

def sync_files():
    """同步所有相關文件"""
    print("🔄 同步所有相關文件...")
    
    main_file = "static/smart-balanced-dashboard.html"
    target_files = [
        "static/smart-balanced-dashboard-static.html"
    ]
    
    if not os.path.exists(main_file):
        print(f"❌ 主文件不存在: {main_file}")
        return False
    
    import shutil
    for target in target_files:
        shutil.copy2(main_file, target)
        print(f"✅ 同步: {target}")
    
    return True

def deploy():
    """部署到雲端"""
    print("🚀 部署到雲端...")
    
    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")
    commit_msg = f"🔄 快速更新 - {timestamp}"
    
    os.system("git add .")
    os.system(f'git commit -m "{commit_msg}"')
    os.system("git push origin main")
    
    print("✅ 部署完成")

def main():
    parser = argparse.ArgumentParser(description='AImax 快速更新工具')
    parser.add_argument('--btc-price', action='store_true', help='更新BTC價格API')
    parser.add_argument('--version', type=str, help='更新版本標識')
    parser.add_argument('--sync', action='store_true', help='同步文件')
    parser.add_argument('--deploy', action='store_true', help='部署到雲端')
    parser.add_argument('--all', action='store_true', help='執行所有更新')
    
    args = parser.parse_args()
    
    print("⚡ AImax 快速更新工具")
    print("=" * 50)
    
    if args.all or not any(vars(args).values()):
        # 執行所有更新
        update_btc_price()
        update_version()
        sync_files()
        deploy()
    else:
        if args.btc_price:
            update_btc_price()
        if args.version:
            update_version(args.version)
        if args.sync:
            sync_files()
        if args.deploy:
            deploy()
    
    print("=" * 50)
    print("🎉 更新完成！")
    print("🌐 請等待2-3分鐘後刷新頁面查看更新")

if __name__ == "__main__":
    main()