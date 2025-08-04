#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
緊急停止腳本
可以立即停止所有交易活動
"""

import os
import json
from datetime import datetime

def emergency_stop():
    """執行緊急停止"""
    print("🚨 執行緊急停止...")
    
    # 創建緊急停止文件
    with open("EMERGENCY_STOP", 'w') as f:
        f.write(f"Emergency stop requested at {datetime.now()}\n")
        f.write("All trading activities should be stopped immediately.\n")
    
    # 更新狀態文件
    status_file = "trading_status.json"
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
        except:
            status = {}
    else:
        status = {}
    
    status.update({
        "is_running": False,
        "emergency_stop": True,
        "system_status": "emergency_stopped",
        "last_update": datetime.now().isoformat()
    })
    
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"更新狀態文件失敗: {e}")
    
    print("✅ 緊急停止已執行！")
    print("📁 已創建 EMERGENCY_STOP 文件")
    print("📊 已更新系統狀態")
    print("\n⚠️  請檢查是否有未平倉的持倉需要手動處理！")

def remove_emergency_stop():
    """移除緊急停止狀態"""
    if os.path.exists("EMERGENCY_STOP"):
        os.remove("EMERGENCY_STOP")
        print("✅ 緊急停止文件已移除")
    else:
        print("ℹ️  沒有找到緊急停止文件")
    
    # 更新狀態文件
    status_file = "trading_status.json"
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            
            status.update({
                "emergency_stop": False,
                "system_status": "stopped",
                "last_update": datetime.now().isoformat()
            })
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
            
            print("✅ 系統狀態已重置")
        except Exception as e:
            print(f"更新狀態文件失敗: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        remove_emergency_stop()
    else:
        emergency_stop()
    
    print("\n使用方法:")
    print("python emergency_stop.py        # 執行緊急停止")
    print("python emergency_stop.py reset  # 重置緊急停止狀態")