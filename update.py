#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 AImax 雲端更新快捷腳本
這是唯一正確的更新方法！
"""

import os
import sys

def main():
    print("🚀 AImax 雲端更新快捷腳本")
    print("=" * 40)
    print("📋 正在執行終極雲端部署...")
    print()
    
    # 執行終極雲端部署
    exit_code = os.system("python scripts/ultimate_cloud_deploy.py")
    
    if exit_code == 0:
        print()
        print("🎉 雲端更新成功完成！")
        print("📖 詳細說明請查看: CLOUD_UPDATE_GUIDE.md")
    else:
        print()
        print("❌ 雲端更新失敗！")
        print("📖 故障排除請查看: CLOUD_UPDATE_GUIDE.md")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())