#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風險監控和預警系統簡化測試腳本
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_risk_monitoring_system():
    """測試風險監控系統"""
    print("🧪 開始風險監控和預警系統測試")
    print("=" * 60)
    
    try:
        # 嘗試導入風險監控系統
        from src.monitoring.risk_monitoring_system import RiskMonitoringSystem, RiskMonitoringConfig
        
        print("✅ 成功導入風險監控系統模組")
        
        # 創建配置
        config = RiskMonitoringConfig()
        print(f"✅ 創建配置成功")
        print(f"   監控間隔: {config.monitoring_interval} 秒")
        print(f"   自動處理: {'啟用' if config.enable_auto_actions else '禁用'}")
        
        # 創建監控系統
        monitor = RiskMonitoringSystem(config)
        print("✅ 創建風險監控系統成功")
        
        # 測試基本功能
        print("\n🔍 測試基本功能")
        print("-" * 40)
        
        # 測試狀態獲取
        status = monitor.get_monitoring_status()
        print(f"✅ 獲取監控狀態: {type(status)}")
        
        # 測試風險摘要
        summary = monitor.get_risk_summary()
        print(f"✅ 獲取風險摘要: {type(summary)}")
        
        # 測試短時間監控
        print("\n🔍 測試監控循環 (3秒)")
        print("-" * 40)
        
        # 啟動監控任務
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # 運行3秒
        await asyncio.sleep(3)
        
        # 停止監控
        await monitor.stop_monitoring()
        monitoring_task.cancel()
        
        print("✅ 監控循環測試完成")
        
        # 最終狀態
        final_status = monitor.get_monitoring_status()
        final_summary = monitor.get_risk_summary()
        
        print(f"\n📊 最終測試結果:")
        print(f"   監控狀態: {final_status.get('is_monitoring', 'unknown')}")
        print(f"   風險等級: {final_summary.get('overall_risk_level', 'unknown')}")
        print(f"   系統健康: {final_status.get('current_metrics', {}).get('system_health_score', 'unknown')}")
        
        print("\n🎉 風險監控和預警系統測試完成！")
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

async def main():
    """主函數"""
    success = await test_risk_monitoring_system()
    
    # 保存簡化測試報告
    report = {
        'test_name': 'risk_monitoring_system_simple_test',
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'message': '風險監控系統簡化測試' + ('成功' if success else '失敗')
    }
    
    report_file = f"AImax/logs/risk_monitoring_simple_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 測試報告已保存: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())