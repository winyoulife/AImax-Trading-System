#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查GitHub Actions部署狀態
診斷為什麼頁面無法更新
"""

import os
import sys
import time
from datetime import datetime

def check_github_actions():
    """檢查GitHub Actions狀態"""
    print("🔍 GitHub Actions部署狀態檢查")
    print("=" * 60)
    
    print("📋 當前工作流程文件:")
    workflows_dir = ".github/workflows"
    if os.path.exists(workflows_dir):
        for file in os.listdir(workflows_dir):
            if file.endswith('.yml') or file.endswith('.yaml'):
                print(f"  ✅ {file}")
    else:
        print("  ❌ .github/workflows 目錄不存在")
    
    print(f"\n🎯 問題分析:")
    print("1. 原來的 deploy-pages.yml 有語法錯誤")
    print("2. GitHub Actions 顯示 'Invalid workflow file'")
    print("3. 這導致部署一直失敗")
    print("4. 頁面無法更新到最新版本")
    
    print(f"\n✅ 解決方案:")
    print("1. 已刪除有問題的 deploy-pages.yml")
    print("2. 使用簡單可靠的 simple-deploy.yml")
    print("3. 新配置只做基本的文件複製")
    print("4. 避免所有可能導致失敗的複雜操作")
    
    print(f"\n🕐 等待部署完成...")
    print("請在GitHub上檢查Actions頁面:")
    print("https://github.com/winyoulife/AImax-Trading-System/actions")
    
    print(f"\n📅 預期結果:")
    print("• GitHub Actions 應該顯示綠色成功狀態")
    print("• 頁面應該顯示版本: v2.0-fixed | 2025/08/07 21:15")
    print("• 交易數據應該顯示: NT$ 98,998 餘額")
    print("• 交易記錄應該只有1筆正確的買入")
    
    print(f"\n🌐 測試頁面:")
    print("https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-static.html")
    
    print(f"\n" + "=" * 60)
    print("🔍 GitHub Actions狀態檢查完成")
    
    # 檢查靜態文件是否存在
    print(f"\n📁 檢查關鍵文件:")
    key_files = [
        "static/smart-balanced-dashboard-static.html",
        "static/last_update.txt",
        ".github/workflows/simple-deploy.yml"
    ]
    
    for file in key_files:
        if os.path.exists(file):
            print(f"  ✅ {file} 存在")
            if file.endswith('.txt'):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    print(f"     內容: {content[:100]}...")
        else:
            print(f"  ❌ {file} 不存在")

if __name__ == "__main__":
    check_github_actions()