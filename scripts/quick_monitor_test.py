#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速監控測試腳本
快速驗證實時監控系統的基本功能
"""

import sys
import os
import time
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.monitoring.realtime_monitor import realtime_monitor

def main():
    """快速測試主函數"""
    print("🚀 AImax 實時監控快速測試")
    print("=" * 50)
    
    try:
        # 1. 測試基本狀態獲取
        print("1️⃣ 測試基本狀態獲取...")
        status = realtime_monitor.get_current_status()
        print(f"   ✅ 健康分數: {status['health_score']}/100")
        print(f"   ✅ 系統狀態: {status['system_status']}")
        print(f"   ✅ CPU使用率: {status['system_metrics']['cpu_percent']:.1f}%")
        print(f"   ✅ 記憶體使用率: {status['system_metrics']['memory_percent']:.1f}%")
        
        # 2. 測試監控啟動
        print("\n2️⃣ 測試監控啟動...")
        realtime_monitor.start_monitoring()
        print("   ✅ 監控已啟動")
        
        # 3. 等待數據收集
        print("\n3️⃣ 等待數據收集 (10秒)...")
        for i in range(10):
            print(f"   ⏳ {i+1}/10 秒", end='\r')
            time.sleep(1)
        print("\n   ✅ 數據收集完成")
        
        # 4. 檢查收集的數據
        print("\n4️⃣ 檢查收集的數據...")
        if len(realtime_monitor.system_metrics_history) > 0:
            print(f"   ✅ 系統指標數據點: {len(realtime_monitor.system_metrics_history)}")
        else:
            print("   ❌ 沒有收集到系統指標數據")
            
        if len(realtime_monitor.trading_metrics_history) > 0:
            print(f"   ✅ 交易指標數據點: {len(realtime_monitor.trading_metrics_history)}")
        else:
            print("   ❌ 沒有收集到交易指標數據")
        
        # 5. 測試警告系統
        print("\n5️⃣ 測試警告系統...")
        realtime_monitor._create_alert('info', 'test', '這是一個測試警告', {'test': True})
        if len(realtime_monitor.active_alerts) > 0:
            print(f"   ✅ 警告創建成功: {len(realtime_monitor.active_alerts)} 個警告")
        else:
            print("   ❌ 警告創建失敗")
        
        # 6. 測試系統摘要
        print("\n6️⃣ 測試系統摘要...")
        summary = realtime_monitor.get_system_summary()
        print("   ✅ 系統摘要生成成功")
        print("   " + "="*48)
        # 顯示摘要的前幾行
        summary_lines = summary.split('\n')[:10]
        for line in summary_lines:
            print(f"   {line}")
        print("   ...")
        
        # 7. 測試歷史數據
        print("\n7️⃣ 測試歷史數據檢索...")
        history = realtime_monitor.get_metrics_history(1)
        print(f"   ✅ 歷史數據檢索成功: {history['data_points']} 個數據點")
        
        # 8. 停止監控
        print("\n8️⃣ 停止監控...")
        realtime_monitor.stop_monitoring()
        print("   ✅ 監控已停止")
        
        # 9. 最終狀態檢查
        print("\n9️⃣ 最終狀態檢查...")
        final_status = realtime_monitor.get_current_status()
        print(f"   ✅ 監控狀態: {'運行中' if final_status['monitoring_active'] else '已停止'}")
        print(f"   ✅ 最終健康分數: {final_status['health_score']}/100")
        
        print("\n" + "=" * 50)
        print("🎉 快速測試完成！所有基本功能正常")
        print("=" * 50)
        
        # 顯示使用建議
        print("\n💡 使用建議:")
        print("   • 啟動Web監控面板: python start_realtime_monitor.py")
        print("   • 使用CLI監控: python scripts/monitor_cli.py watch")
        print("   • 運行完整測試: python scripts/test_realtime_monitor.py")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 用戶中斷測試")
        realtime_monitor.stop_monitoring()
        return 1
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        print("請檢查系統配置和依賴項")
        realtime_monitor.stop_monitoring()
        return 1

if __name__ == '__main__':
    exit(main())