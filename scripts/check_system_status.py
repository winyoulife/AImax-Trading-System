#!/usr/bin/env python3
"""
AImax系統狀態檢查腳本
用於監控交易系統是否正常運行
"""

import json
import os
from datetime import datetime, timedelta
import sys

def check_system_status():
    """檢查系統運行狀態"""
    print("🔍 檢查AImax交易系統狀態...")
    
    # 檢查執行狀態文件
    status_file = "data/simulation/execution_status.json"
    if not os.path.exists(status_file):
        print("❌ 找不到執行狀態文件")
        return False
    
    try:
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        print(f"📊 系統狀態: {status.get('system_status', 'unknown')}")
        print(f"💰 當前BTC價格: ${status.get('current_btc_price', 0):,.2f}")
        print(f"🕐 最後執行: {status.get('last_execution', 'unknown')}")
        print(f"🎯 交易策略: {status.get('strategy', 'unknown')}")
        
        # 檢查最後執行時間
        last_exec = status.get('timestamp')
        if last_exec:
            last_time = datetime.fromisoformat(last_exec.replace('Z', '+00:00'))
            now = datetime.now(last_time.tzinfo)
            time_diff = now - last_time
            
            if time_diff < timedelta(minutes=15):
                print(f"✅ 系統正常運行 (最後執行: {time_diff.total_seconds()/60:.1f}分鐘前)")
                return True
            else:
                print(f"⚠️  系統可能停止 (最後執行: {time_diff.total_seconds()/60:.1f}分鐘前)")
                return False
        
    except Exception as e:
        print(f"❌ 讀取狀態文件錯誤: {e}")
        return False

def check_recent_trades():
    """檢查最近的交易記錄"""
    print("\n📈 檢查最近交易記錄...")
    
    trades_file = "data/simulation/trades.jsonl"
    if not os.path.exists(trades_file):
        print("❌ 找不到交易記錄文件")
        return
    
    try:
        with open(trades_file, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            print("📝 暫無交易記錄")
            return
        
        # 顯示最近5筆交易
        recent_trades = lines[-5:]
        print(f"📊 顯示最近 {len(recent_trades)} 筆交易:")
        
        for line in recent_trades:
            trade = json.loads(line.strip())
            timestamp = trade.get('timestamp', '')
            action = trade.get('action', '')
            price = trade.get('price', 0)
            confidence = trade.get('confidence', 0)
            
            print(f"  {timestamp[:19]} | {action.upper()} | ${price:,.2f} | 信心度: {confidence:.0%}")
            
    except Exception as e:
        print(f"❌ 讀取交易記錄錯誤: {e}")

if __name__ == "__main__":
    print("🚀 AImax智能交易系統狀態檢查")
    print("=" * 50)
    
    # 切換到項目根目錄
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    # 檢查系統狀態
    is_running = check_system_status()
    
    # 檢查交易記錄
    check_recent_trades()
    
    print("\n" + "=" * 50)
    if is_running:
        print("✅ 系統運行正常！")
        sys.exit(0)
    else:
        print("⚠️  系統可能需要檢查")
        sys.exit(1)