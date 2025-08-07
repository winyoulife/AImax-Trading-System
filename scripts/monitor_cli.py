#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 命令行監控工具
提供簡潔的命令行界面來監控系統狀態
"""

import sys
import os
import time
import argparse
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.monitoring.realtime_monitor import realtime_monitor

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印標題"""
    print("🚀 AImax 實時監控 CLI")
    print("=" * 60)

def print_status_bar(status):
    """打印狀態欄"""
    health_score = status['health_score']
    system_status = status['system_status']
    
    # 狀態顏色
    if system_status == 'healthy':
        status_color = '🟢'
    elif system_status == 'warning':
        status_color = '🟡'
    else:
        status_color = '🔴'
    
    print(f"{status_color} 系統狀態: {system_status.upper()} | 健康分數: {health_score}/100")
    print("-" * 60)

def print_system_metrics(status):
    """打印系統指標"""
    metrics = status['system_metrics']
    
    print("💻 系統資源:")
    print(f"   CPU 使用率:    {metrics['cpu_percent']:6.1f}% {'🔥' if metrics['cpu_percent'] > 80 else '✅'}")
    print(f"   記憶體使用率:  {metrics['memory_percent']:6.1f}% {'🔥' if metrics['memory_percent'] > 80 else '✅'}")
    print(f"   磁碟使用:      {metrics['disk_usage_gb']:6.2f} GB")
    print(f"   活躍線程:      {metrics['active_threads']:6d}")
    print(f"   運行時間:      {metrics['uptime_hours']:6.1f} 小時")

def print_trading_metrics(status):
    """打印交易指標"""
    metrics = status['trading_metrics']
    
    print("\n💰 交易狀態:")
    print(f"   活躍策略:      {metrics['active_strategies']:2d}/{metrics['total_strategies']:2d}")
    print(f"   當前餘額:      ${metrics['current_balance']:>10,.2f}")
    
    pnl = metrics['daily_pnl']
    pnl_indicator = '📈' if pnl > 0 else '📉' if pnl < 0 else '➡️'
    print(f"   今日盈虧:      ${pnl:>+10,.2f} {pnl_indicator}")

def print_alerts(status):
    """打印警告信息"""
    alerts = status['alerts']
    
    print(f"\n⚠️ 警告狀態: (總計 {alerts['total_active']} 個)")
    
    if alerts['total_active'] == 0:
        print("   🎉 目前沒有警告")
        return
    
    by_level = alerts['by_level']
    if by_level['critical'] > 0:
        print(f"   🔴 危險: {by_level['critical']} 個")
    if by_level['warning'] > 0:
        print(f"   🟡 警告: {by_level['warning']} 個")
    if by_level['info'] > 0:
        print(f"   🔵 信息: {by_level['info']} 個")
    
    # 顯示最近的警告
    if alerts['recent_alerts']:
        print("\n   最近警告:")
        for alert in alerts['recent_alerts'][-3:]:  # 只顯示最近3個
            level_icon = {'critical': '🔴', 'warning': '🟡', 'info': '🔵'}.get(alert['level'], '⚪')
            print(f"   {level_icon} {alert['message']}")

def print_monitoring_status(status):
    """打印監控狀態"""
    monitoring_active = status['monitoring_active']
    status_text = "運行中 🟢" if monitoring_active else "已停止 🔴"
    print(f"\n🔍 監控狀態: {status_text}")

def print_footer():
    """打印頁腳"""
    print("-" * 60)
    print(f"⏰ 更新時間: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("按 Ctrl+C 退出")

def watch_mode(interval=5):
    """監控模式 - 持續顯示狀態"""
    print("🔄 進入監控模式...")
    print(f"📊 更新間隔: {interval} 秒")
    print("按 Ctrl+C 退出\n")
    
    try:
        while True:
            clear_screen()
            
            try:
                status = realtime_monitor.get_current_status()
                
                print_header()
                print_status_bar(status)
                print_system_metrics(status)
                print_trading_metrics(status)
                print_alerts(status)
                print_monitoring_status(status)
                print_footer()
                
            except Exception as e:
                print(f"❌ 獲取狀態失敗: {e}")
                print("請檢查監控服務是否正常運行")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n👋 退出監控模式")

def show_summary():
    """顯示系統摘要"""
    try:
        summary = realtime_monitor.get_system_summary()
        print(summary)
    except Exception as e:
        print(f"❌ 獲取摘要失敗: {e}")

def show_history(hours=1):
    """顯示歷史數據"""
    try:
        history = realtime_monitor.get_metrics_history(hours)
        
        print(f"📈 過去 {hours} 小時的監控數據")
        print("=" * 50)
        print(f"數據點數量: {history['data_points']}")
        
        if history['system_metrics']:
            print("\n系統指標趨勢:")
            recent_metrics = history['system_metrics'][-5:]  # 最近5個數據點
            
            for i, metric in enumerate(recent_metrics):
                timestamp = metric['timestamp']
                cpu = metric['cpu_percent']
                memory = metric['memory_percent']
                errors = metric['error_count']
                
                print(f"  {timestamp}: CPU {cpu:5.1f}% | 記憶體 {memory:5.1f}% | 錯誤 {errors:3d}")
        
        if history['trading_metrics']:
            print("\n交易指標趨勢:")
            recent_trading = history['trading_metrics'][-5:]  # 最近5個數據點
            
            for i, metric in enumerate(recent_trading):
                timestamp = metric['timestamp']
                strategies = metric['active_strategies']
                signals = metric['signals_generated']
                success_rate = metric['success_rate']
                
                print(f"  {timestamp}: 策略 {strategies:2d} | 信號 {signals:3d} | 成功率 {success_rate:5.1f}%")
                
    except Exception as e:
        print(f"❌ 獲取歷史數據失敗: {e}")

def control_monitoring(action):
    """控制監控服務"""
    try:
        if action == 'start':
            realtime_monitor.start_monitoring()
            print("✅ 實時監控已啟動")
        elif action == 'stop':
            realtime_monitor.stop_monitoring()
            print("⏹️ 實時監控已停止")
        elif action == 'restart':
            realtime_monitor.stop_monitoring()
            time.sleep(1)
            realtime_monitor.start_monitoring()
            print("🔄 實時監控已重啟")
        else:
            print(f"❌ 未知操作: {action}")
            
    except Exception as e:
        print(f"❌ 控制監控失敗: {e}")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='AImax 實時監控 CLI 工具')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 狀態命令
    status_parser = subparsers.add_parser('status', help='顯示當前狀態')
    
    # 監控模式命令
    watch_parser = subparsers.add_parser('watch', help='持續監控模式')
    watch_parser.add_argument('-i', '--interval', type=int, default=5, 
                             help='更新間隔（秒，默認5秒）')
    
    # 摘要命令
    summary_parser = subparsers.add_parser('summary', help='顯示系統摘要')
    
    # 歷史命令
    history_parser = subparsers.add_parser('history', help='顯示歷史數據')
    history_parser.add_argument('-h', '--hours', type=int, default=1,
                               help='歷史數據時間範圍（小時，默認1小時）')
    
    # 控制命令
    control_parser = subparsers.add_parser('control', help='控制監控服務')
    control_parser.add_argument('action', choices=['start', 'stop', 'restart'],
                               help='控制操作')
    
    args = parser.parse_args()
    
    if not args.command:
        # 默認顯示狀態
        args.command = 'status'
    
    try:
        if args.command == 'status':
            status = realtime_monitor.get_current_status()
            print_header()
            print_status_bar(status)
            print_system_metrics(status)
            print_trading_metrics(status)
            print_alerts(status)
            print_monitoring_status(status)
            print_footer()
            
        elif args.command == 'watch':
            watch_mode(args.interval)
            
        elif args.command == 'summary':
            show_summary()
            
        elif args.command == 'history':
            show_history(args.hours)
            
        elif args.command == 'control':
            control_monitoring(args.action)
            
    except Exception as e:
        print(f"❌ 執行命令失敗: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())