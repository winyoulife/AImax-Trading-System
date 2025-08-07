#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動智能平衡策略監控系統
持續監控83.3%勝率策略的執行狀況
"""

import sys
import time
import signal
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.monitoring.smart_balanced_monitor import SmartBalancedMonitor

class MonitoringService:
    """監控服務"""
    
    def __init__(self):
        self.monitor = SmartBalancedMonitor()
        self.running = True
        self.monitoring_interval = 300  # 5分鐘
        
    def signal_handler(self, signum, frame):
        """處理停止信號"""
        print("\n⏹️ 收到停止信號，正在關閉監控服務...")
        self.running = False
    
    def start(self):
        """啟動監控服務"""
        # 註冊信號處理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🚀 啟動智能平衡策略監控服務")
        print("="*50)
        print(f"📊 監控間隔: {self.monitoring_interval}秒 ({self.monitoring_interval//60}分鐘)")
        print(f"🎯 目標策略: 83.3%勝率智能平衡策略")
        print(f"⏹️ 按 Ctrl+C 停止監控")
        print("="*50)
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                print(f"\n🔄 監控週期 #{cycle_count}")
                print("-" * 30)
                
                # 執行監控
                result = self.monitor.run_monitoring_cycle()
                
                # 檢查結果
                if result.get('overall_status') == 'critical':
                    print("🚨 發現嚴重問題，建議立即檢查！")
                elif result.get('overall_status') == 'warning':
                    print("⚠️ 發現警告，請注意監控")
                else:
                    print("✅ 系統運行正常")
                
                # 等待下次檢查
                if self.running:
                    print(f"\n⏰ 等待 {self.monitoring_interval} 秒後進行下次檢查...")
                    for i in range(self.monitoring_interval):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                        # 每分鐘顯示一次倒計時
                        remaining = self.monitoring_interval - i
                        if remaining % 60 == 0 and remaining > 0:
                            print(f"⏳ 還有 {remaining//60} 分鐘...")
                
            except KeyboardInterrupt:
                print("\n⏹️ 收到中斷信號，正在停止...")
                break
            except Exception as e:
                print(f"\n❌ 監控週期執行失敗: {e}")
                print("🔄 5秒後重試...")
                time.sleep(5)
        
        print("\n✅ 監控服務已停止")

def main():
    """主函數"""
    service = MonitoringService()
    service.start()

if __name__ == "__main__":
    main()