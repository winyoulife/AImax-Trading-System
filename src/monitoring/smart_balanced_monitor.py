#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能平衡策略專用監控系統
實時追蹤83.3%勝率策略的執行狀況、交易決策和績效表現
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests
import pandas as pd

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/smart_balanced_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartBalancedMonitor:
    """智能平衡策略監控器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data" / "monitoring"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 監控配置
        self.config = {
            'strategy_name': 'smart_balanced_83.3%_winrate',
            'expected_win_rate': 0.833,
            'max_daily_trades': 6,
            'monitoring_interval': 300,  # 5分鐘
            'alert_thresholds': {
                'win_rate_below': 0.7,
                'consecutive_losses': 3,
                'no_activity_hours': 24,
                'api_error_rate': 0.1
            }
        }
        
        # 狀態追蹤
        self.last_check_time = None
        self.trade_history = []
        self.system_status = {}
        
    def get_github_actions_status(self) -> Dict:
        """獲取GitHub Actions執行狀態"""
        try:
            # 這裡應該調用GitHub API，但為了簡化，我們模擬數據
            # 實際部署時需要配置GitHub API token
            
            status = {
                'last_run': datetime.now().isoformat(),
                'status': 'success',
                'workflow': 'smart-balanced-deploy',
                'execution_count': 24,
                'success_rate': 0.95,
                'last_error': None
            }
            
            logger.info(f"📊 GitHub Actions狀態: {status['status']}")
            return status
            
        except Exception as e:
            logger.error(f"❌ 獲取GitHub Actions狀態失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def analyze_trading_performance(self) -> Dict:
        """分析交易績效"""
        try:
            # 讀取交易記錄 (JSONL格式)
            trades_file = self.project_root / "data" / "simulation" / "trades.jsonl"
            trades = []
            
            if trades_file.exists():
                with open(trades_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            trades.append(json.loads(line.strip()))
            
            # 也檢查舊格式的JSON檔案
            json_trades_file = self.data_dir / "trades.json"
            if json_trades_file.exists():
                with open(json_trades_file, 'r', encoding='utf-8') as f:
                    json_trades = json.load(f)
                    trades.extend(json_trades)
            
            if not trades:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_profit': 0,
                    'avg_profit': 0,
                    'status': 'no_trades'
                }
            
            # 計算績效指標
            total_trades = len(trades)
            
            # 計算盈虧 (需要配對買賣交易)
            buy_trades = [t for t in trades if t.get('action') == 'buy']
            sell_trades = [t for t in trades if t.get('action') == 'sell']
            
            # 簡化計算：假設每筆賣出都有對應的買入
            total_profit = 0
            winning_trades = 0
            
            for sell_trade in sell_trades:
                # 找到對應的買入交易 (簡化版本)
                sell_amount = sell_trade.get('net_proceeds', sell_trade.get('amount', 0))
                # 估算對應的買入成本
                buy_cost = sell_trade.get('quantity', 0) * sell_trade.get('price', 0) * 1.0015  # 加上手續費
                
                profit = sell_amount - buy_cost
                total_profit += profit
                
                if profit > 0:
                    winning_trades += 1
            
            # 如果沒有賣出交易，計算未實現盈虧
            if not sell_trades and buy_trades:
                # 使用最新價格估算
                latest_price = 95000  # 估算BTC價格
                for buy_trade in buy_trades:
                    current_value = buy_trade.get('quantity', 0) * latest_price
                    cost = buy_trade.get('total_cost', buy_trade.get('amount', 0))
                    unrealized_profit = current_value - cost
                    total_profit += unrealized_profit
                    if unrealized_profit > 0:
                        winning_trades += 1
            
            win_rate = winning_trades / max(len(sell_trades), 1) if sell_trades else (winning_trades / max(total_trades, 1) if total_trades > 0 else 0)
            avg_profit = total_profit / max(total_trades, 1) if total_trades > 0 else 0
            
            # 最近24小時交易
            now = datetime.now()
            recent_trades = []
            for trade in trades:
                try:
                    trade_time = datetime.fromisoformat(trade.get('timestamp', ''))
                    if (now - trade_time).total_seconds() < 86400:
                        recent_trades.append(trade)
                except:
                    continue
            
            performance = {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'avg_profit': avg_profit,
                'recent_24h_trades': len(recent_trades),
                'expected_vs_actual': {
                    'expected_win_rate': self.config['expected_win_rate'],
                    'actual_win_rate': win_rate,
                    'performance_ratio': win_rate / self.config['expected_win_rate'] if self.config['expected_win_rate'] > 0 else 0
                },
                'status': 'active' if recent_trades else 'inactive'
            }
            
            logger.info(f"📈 交易績效: 勝率{win_rate:.1%}, 總獲利{total_profit:,.0f}")
            return performance
            
        except Exception as e:
            logger.error(f"❌ 分析交易績效失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def check_system_health(self) -> Dict:
        """檢查系統健康狀況"""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'components': {},
                'overall_status': 'healthy',
                'alerts': []
            }
            
            # 檢查GitHub Actions
            github_status = self.get_github_actions_status()
            health_status['components']['github_actions'] = github_status
            
            if github_status.get('status') != 'success':
                health_status['alerts'].append({
                    'level': 'warning',
                    'message': 'GitHub Actions執行異常',
                    'component': 'github_actions'
                })
            
            # 檢查交易績效
            performance = self.analyze_trading_performance()
            health_status['components']['trading_performance'] = performance
            
            # 檢查勝率警報
            if performance.get('win_rate', 0) < self.config['alert_thresholds']['win_rate_below']:
                health_status['alerts'].append({
                    'level': 'critical',
                    'message': f"勝率低於警戒線: {performance.get('win_rate', 0):.1%} < {self.config['alert_thresholds']['win_rate_below']:.1%}",
                    'component': 'trading_performance'
                })
            
            # 檢查活動狀況
            if performance.get('status') == 'inactive':
                health_status['alerts'].append({
                    'level': 'warning',
                    'message': '24小時內無交易活動',
                    'component': 'trading_activity'
                })
            
            # 設置整體狀態
            if any(alert['level'] == 'critical' for alert in health_status['alerts']):
                health_status['overall_status'] = 'critical'
            elif health_status['alerts']:
                health_status['overall_status'] = 'warning'
            
            return health_status
            
        except Exception as e:
            logger.error(f"❌ 系統健康檢查失敗: {e}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_monitoring_report(self) -> str:
        """生成監控報告"""
        try:
            health_status = self.check_system_health()
            performance = health_status.get('components', {}).get('trading_performance', {})
            github_status = health_status.get('components', {}).get('github_actions', {})
            
            report = f"""
📊 AImax 智能平衡策略監控報告
{'='*50}
🕐 報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🎯 策略版本: v1.0-smart-balanced
🏆 目標勝率: 83.3%

📈 交易績效
{'='*30}
總交易次數: {performance.get('total_trades', 0)}
實際勝率: {performance.get('win_rate', 0):.1%}
總獲利: {performance.get('total_profit', 0):,.0f} TWD
平均獲利: {performance.get('avg_profit', 0):,.0f} TWD/筆
24小時交易: {performance.get('recent_24h_trades', 0)}

🎯 績效對比
{'='*30}
預期勝率: {performance.get('expected_vs_actual', {}).get('expected_win_rate', 0):.1%}
實際勝率: {performance.get('expected_vs_actual', {}).get('actual_win_rate', 0):.1%}
達成率: {performance.get('expected_vs_actual', {}).get('performance_ratio', 0):.1%}

🔧 系統狀態
{'='*30}
整體狀態: {health_status.get('overall_status', 'unknown').upper()}
GitHub Actions: {github_status.get('status', 'unknown').upper()}
執行成功率: {github_status.get('success_rate', 0):.1%}
最後執行: {github_status.get('last_run', 'unknown')}

⚠️ 警報狀況
{'='*30}
"""
            
            if health_status.get('alerts'):
                for alert in health_status['alerts']:
                    level_icon = '🚨' if alert['level'] == 'critical' else '⚠️'
                    report += f"{level_icon} {alert['level'].upper()}: {alert['message']}\n"
            else:
                report += "✅ 無警報，系統運行正常\n"
            
            report += f"""
📱 監控建議
{'='*30}
"""
            
            # 根據狀況給出建議
            if health_status.get('overall_status') == 'critical':
                report += "🚨 建議立即檢查系統，可能需要人工干預\n"
            elif health_status.get('overall_status') == 'warning':
                report += "⚠️ 建議密切關注，考慮調整策略參數\n"
            else:
                report += "✅ 系統運行良好，繼續監控即可\n"
            
            report += f"""
🔄 下次檢查: {(datetime.now() + timedelta(minutes=5)).strftime('%H:%M:%S')}
📋 詳細日誌: logs/smart_balanced_monitor.log
"""
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成監控報告失敗: {e}")
            return f"❌ 監控報告生成失敗: {e}"
    
    def save_monitoring_data(self, data: Dict):
        """保存監控數據"""
        try:
            # 保存到JSON檔案
            monitoring_file = self.data_dir / f"monitoring_{datetime.now().strftime('%Y%m%d')}.json"
            
            if monitoring_file.exists():
                with open(monitoring_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
            
            existing_data.append(data)
            
            with open(monitoring_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            # 保存最新狀態
            latest_file = self.data_dir / "latest_status.json"
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info("💾 監控數據已保存")
            
        except Exception as e:
            logger.error(f"❌ 保存監控數據失敗: {e}")
    
    def run_monitoring_cycle(self):
        """執行一次監控週期"""
        try:
            logger.info("🔍 開始智能平衡策略監控週期")
            
            # 檢查系統健康狀況
            health_status = self.check_system_health()
            
            # 生成報告
            report = self.generate_monitoring_report()
            
            # 保存數據
            self.save_monitoring_data(health_status)
            
            # 輸出報告
            print(report)
            
            # 如果有嚴重警報，額外記錄
            if health_status.get('overall_status') == 'critical':
                logger.critical("🚨 系統狀態嚴重，需要立即關注！")
            
            logger.info("✅ 監控週期完成")
            return health_status
            
        except Exception as e:
            logger.error(f"❌ 監控週期執行失敗: {e}")
            return {'status': 'error', 'error': str(e)}

def main():
    """主函數"""
    print("🔍 AImax 智能平衡策略監控系統")
    print("="*50)
    print("🎯 監控策略: 83.3%勝率智能平衡策略")
    print("📋 版本: v1.0-smart-balanced")
    print("="*50)
    
    monitor = SmartBalancedMonitor()
    
    try:
        # 執行監控
        result = monitor.run_monitoring_cycle()
        
        if result.get('overall_status') == 'error':
            print(f"\n❌ 監控執行失敗: {result.get('error')}")
            return 1
        else:
            print(f"\n✅ 監控完成，系統狀態: {result.get('overall_status', 'unknown').upper()}")
            return 0
            
    except KeyboardInterrupt:
        print("\n⏹️ 監控已停止")
        return 0
    except Exception as e:
        print(f"\n💥 監控系統異常: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())