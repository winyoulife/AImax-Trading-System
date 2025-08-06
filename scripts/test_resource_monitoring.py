#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 資源監控系統測試腳本 - 任務10實現
測試資源使用監控、GitHub Actions使用量監控和存儲優化功能
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.monitoring.resource_monitor import resource_monitor, start_resource_monitoring, get_resource_stats
from src.monitoring.github_usage_monitor import github_usage_monitor, get_github_quota, check_github_usage_alerts
from src.monitoring.storage_optimizer import storage_optimizer, get_storage_stats, cleanup_storage

def test_resource_monitor():
    """測試資源監控器"""
    print("📊 測試資源監控器...")
    
    # 收集當前資源使用情況
    current_usage = resource_monitor._collect_system_resources()
    print(f"✅ 系統資源收集成功:")
    print(f"   CPU使用率: {current_usage.cpu_percent:.1f}%")
    print(f"   記憶體使用率: {current_usage.memory_percent:.1f}%")
    print(f"   磁碟使用: {current_usage.disk_usage_gb:.2f} GB")
    print(f"   磁碟剩餘: {current_usage.disk_free_gb:.2f} GB")
    print(f"   文件數量: {current_usage.file_count:,}")
    
    # 測試清理臨時文件
    print("\n🧹 測試清理臨時文件...")
    cleanup_result = resource_monitor.cleanup_temporary_files()
    print(f"清理結果: 釋放 {cleanup_result['freed_space_mb']:.2f} MB 空間")
    
    # 獲取資源統計
    stats = get_resource_stats()
    if 'error' not in stats:
        print(f"\n📈 資源統計:")
        print(f"   當前CPU: {stats['current_usage']['cpu_percent']:.1f}%")
        print(f"   當前記憶體: {stats['current_usage']['memory_percent']:.1f}%")
        print(f"   監控數據點: {stats['data_points']}")
    
    # 生成優化建議
    recommendations = resource_monitor.generate_optimization_recommendations()
    if recommendations:
        print(f"\n💡 優化建議 ({len(recommendations)} 條):")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. {rec['category']}: {rec['issue']}")
    else:
        print("\n✅ 系統運行良好，無需優化建議")

def test_github_usage_monitor():
    """測試GitHub使用量監控"""
    print("\n🚀 測試GitHub使用量監控...")
    
    # 檢查GitHub API配置
    if not github_usage_monitor.can_access_github_api():
        print("⚠️ 無法訪問GitHub API，跳過GitHub使用量測試")
        print("   請設置 GITHUB_TOKEN 環境變量")
        return
    
    # 獲取當前配額
    quota = get_github_quota()
    if quota:
        print(f"✅ GitHub Actions配額信息:")
        print(f"   總配額: {quota.total_minutes} 分鐘/月")
        print(f"   已使用: {quota.used_minutes} 分鐘 ({quota.usage_percentage:.1f}%)")
        print(f"   剩餘: {quota.remaining_minutes} 分鐘")
        print(f"   配額重置: {quota.reset_date.strftime('%Y-%m-%d')}")
    else:
        print("❌ 無法獲取GitHub配額信息")
    
    # 獲取工作流運行記錄
    print("\n📋 獲取工作流運行記錄...")
    workflow_runs = github_usage_monitor.get_workflow_runs(days=7)
    print(f"✅ 獲取到 {len(workflow_runs)} 個工作流運行記錄")
    
    if workflow_runs:
        # 顯示最近的運行記錄
        print("最近的工作流運行:")
        for run in workflow_runs[:5]:
            status_emoji = "✅" if run.conclusion == "success" else "❌" if run.conclusion == "failure" else "⏸️"
            print(f"   {status_emoji} {run.name}: {run.duration_minutes:.1f}分鐘 ({run.status})")
    
    # 分析使用模式
    usage_analysis = github_usage_monitor.analyze_usage_patterns()
    if 'error' not in usage_analysis:
        print(f"\n📈 使用模式分析:")
        print(f"   總運行次數: {usage_analysis['total_runs']}")
        print(f"   總執行時間: {usage_analysis['total_duration_minutes']:.1f} 分鐘")
        print(f"   平均執行時間: {usage_analysis['avg_duration_per_run']:.1f} 分鐘/次")
        print(f"   最常用工作流: {usage_analysis['most_used_workflow'] or 'N/A'}")
    
    # 檢查使用量警告
    alerts = check_github_usage_alerts()
    if alerts:
        print(f"\n⚠️ 使用量警告 ({len(alerts)} 條):")
        for alert in alerts:
            print(f"   {alert['message']}")
    else:
        print("\n✅ GitHub Actions使用量正常")
    
    # 獲取優化建議
    suggestions = github_usage_monitor.get_optimization_suggestions()
    if suggestions:
        print(f"\n💡 GitHub優化建議 ({len(suggestions)} 條):")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"   {i}. {suggestion['category']}: {suggestion['issue']}")
    else:
        print("\n✅ GitHub Actions使用效率良好")

def test_storage_optimizer():
    """測試存儲優化器"""
    print("\n💾 測試存儲優化器...")
    
    # 掃描存儲使用情況
    print("🔍 掃描存儲使用情況...")
    storage_info = storage_optimizer.scan_storage_usage()
    
    if 'error' not in storage_info:
        print(f"✅ 存儲掃描完成:")
        print(f"   總大小: {storage_info['total_size_mb']:.2f} MB ({storage_info['total_size_gb']:.2f} GB)")
        print(f"   總文件數: {storage_info['total_files']:,}")
        print(f"   掃描時間: {storage_info['scan_time_seconds']:.2f} 秒")
        
        # 顯示最大目錄
        if 'largest_directories' in storage_info:
            print("\n📁 最大目錄 (前5名):")
            for dir_name, size_mb in storage_info['largest_directories'][:5]:
                print(f"   {dir_name}: {size_mb:.2f} MB")
        
        # 顯示文件類型分布
        if 'file_type_distribution' in storage_info:
            print("\n📄 文件類型分布 (前5名):")
            for ext, count in list(storage_info['file_type_distribution'].items())[:5]:
                ext_display = ext if ext else '(無擴展名)'
                print(f"   {ext_display}: {count} 個文件")
    else:
        print(f"❌ 存儲掃描失敗: {storage_info['error']}")
    
    # 測試清理功能
    print("\n🧹 測試存儲清理功能...")
    cleanup_results = cleanup_storage()
    
    total_freed = cleanup_results['total_freed_mb']
    print(f"✅ 存儲清理完成: 總共釋放 {total_freed:.2f} MB 空間")
    
    # 顯示各類清理結果
    for cleanup_type, result in cleanup_results.items():
        if cleanup_type != 'total_freed_mb' and hasattr(result, 'freed_space_mb'):
            if result.freed_space_mb > 0:
                print(f"   {cleanup_type}: 清理 {result.cleaned_files} 個文件，釋放 {result.freed_space_mb:.2f} MB")
    
    # 獲取存儲統計
    storage_stats = get_storage_stats()
    if 'current' in storage_stats:
        current = storage_stats['current']
        print(f"\n📊 當前存儲統計:")
        print(f"   總大小: {current['total_size_mb']:.2f} MB")
        print(f"   總文件數: {current['total_files']:,}")
        
        if 'trends' in storage_stats:
            trends = storage_stats['trends']
            size_change = trends['size_change_mb']
            files_change = trends['files_change']
            
            size_trend = "增加" if size_change > 0 else "減少" if size_change < 0 else "無變化"
            files_trend = "增加" if files_change > 0 else "減少" if files_change < 0 else "無變化"
            
            print(f"   大小變化: {size_trend} {abs(size_change):.2f} MB")
            print(f"   文件數變化: {files_trend} {abs(files_change)} 個")

def test_integrated_monitoring():
    """測試集成監控"""
    print("\n🎯 測試集成監控...")
    
    # 啟動短期監控測試
    print("🔍 啟動短期資源監控測試...")
    start_resource_monitoring()
    
    # 運行10秒
    print("監控運行中...")
    time.sleep(10)
    
    # 停止監控
    resource_monitor.stop_monitoring()
    
    # 獲取監控結果
    final_stats = get_resource_stats()
    if 'error' not in final_stats:
        print(f"✅ 監控測試完成:")
        print(f"   監控數據點: {final_stats['data_points']}")
        print(f"   監控時長: {final_stats['monitoring_duration_hours']:.2f} 小時")
        
        if 'averages_24h' in final_stats:
            print(f"   平均CPU使用率: {final_stats['averages_24h']['cpu_percent']:.1f}%")
            print(f"   平均記憶體使用率: {final_stats['averages_24h']['memory_percent']:.1f}%")

def generate_comprehensive_report():
    """生成綜合監控報告"""
    print("\n📋 生成綜合監控報告...")
    
    # 收集所有監控數據
    resource_stats = get_resource_stats()
    storage_stats = get_storage_stats()
    
    # GitHub數據（如果可用）
    github_quota = None
    github_alerts = []
    if github_usage_monitor.can_access_github_api():
        github_quota = get_github_quota()
        github_alerts = check_github_usage_alerts()
    
    # 生成報告
    report = f"""
📊 AImax 資源監控綜合報告
{'='*60}

🖥️ 系統資源狀態:
"""
    
    if 'error' not in resource_stats:
        current = resource_stats['current_usage']
        report += f"""   CPU使用率: {current['cpu_percent']:.1f}%
   記憶體使用率: {current['memory_percent']:.1f}%
   磁碟使用: {current['disk_usage_gb']:.2f} GB
   磁碟剩餘: {current['disk_free_gb']:.2f} GB
   文件數量: {current['file_count']:,}
"""
    else:
        report += "   ⚠️ 無法獲取系統資源數據\n"
    
    # 存儲狀態
    if 'current' in storage_stats:
        current_storage = storage_stats['current']
        report += f"""
💾 存儲空間狀態:
   總大小: {current_storage['total_size_mb']:.2f} MB ({current_storage['total_size_gb']:.2f} GB)
   總文件數: {current_storage['total_files']:,}
"""
    
    # GitHub Actions狀態
    if github_quota:
        report += f"""
🚀 GitHub Actions狀態:
   使用率: {github_quota.usage_percentage:.1f}%
   已用分鐘: {github_quota.used_minutes}
   剩餘分鐘: {github_quota.remaining_minutes}
"""
    else:
        report += "\n🚀 GitHub Actions狀態:\n   ⚠️ 無法獲取GitHub Actions數據\n"
    
    # 警告和建議
    all_alerts = github_alerts
    if all_alerts:
        report += f"\n⚠️ 警告事項:\n"
        for alert in all_alerts:
            report += f"   • {alert['message']}\n"
    
    report += f"\n{'='*60}\n"
    report += f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    print(report)
    
    # 保存報告
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"comprehensive_monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 綜合報告已保存: {report_file}")

def main():
    """主測試函數"""
    print("🚀 AImax 資源監控系統完整測試")
    print("=" * 60)
    
    try:
        # 運行各項測試
        test_resource_monitor()
        test_github_usage_monitor()
        test_storage_optimizer()
        test_integrated_monitoring()
        
        # 生成綜合報告
        generate_comprehensive_report()
        
        print("\n🎉 所有資源監控測試完成！")
        
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()