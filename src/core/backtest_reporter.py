#!/usr/bin/env python3
"""
AImax 回測報告生成器
生成專業的回測分析報告，包含圖表和統計分析
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional
import os
from pathlib import Path

class BacktestReporter:
    """回測報告生成器"""
    
    def __init__(self):
        self.report_data = {}
        self.charts = []
        
    def generate_report(self, backtest_results: Dict[str, Any], 
                       output_dir: str = "reports") -> str:
        """
        生成完整的回測報告
        
        Args:
            backtest_results: 回測結果數據
            output_dir: 輸出目錄
            
        Returns:
            str: 報告文件路徑
        """
        try:
            # 確保輸出目錄存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 解析回測數據
            self._parse_backtest_data(backtest_results)
            
            # 生成統計分析
            stats = self._calculate_statistics()
            
            # 生成圖表
            charts = self._generate_charts(output_dir)
            
            # 生成HTML報告
            report_path = self._generate_html_report(stats, charts, output_dir)
            
            # 生成JSON數據文件
            self._save_json_data(stats, output_dir)
            
            return report_path
            
        except Exception as e:
            print(f"❌ 生成回測報告失敗: {e}")
            return ""
    
    def _parse_backtest_data(self, results: Dict[str, Any]):
        """解析回測數據"""
        self.report_data = {
            'trades': results.get('trades', []),
            'equity_curve': results.get('equity_curve', []),
            'daily_returns': results.get('daily_returns', []),
            'positions': results.get('positions', []),
            'start_date': results.get('start_date', ''),
            'end_date': results.get('end_date', ''),
            'initial_capital': results.get('initial_capital', 10000),
            'final_capital': results.get('final_capital', 10000),
            'model_name': results.get('model_name', 'Unknown'),
            'strategy': results.get('strategy', 'Unknown')
        }
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """計算統計指標"""
        trades = self.report_data['trades']
        equity_curve = self.report_data['equity_curve']
        daily_returns = self.report_data['daily_returns']
        
        if not trades or not equity_curve:
            return self._get_empty_stats()
        
        # 基本統計
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 收益統計
        total_return = self.report_data['final_capital'] - self.report_data['initial_capital']
        total_return_pct = (total_return / self.report_data['initial_capital'] * 100) if self.report_data['initial_capital'] > 0 else 0
        
        # 風險指標
        if daily_returns:
            returns_array = np.array(daily_returns)
            volatility = np.std(returns_array) * np.sqrt(252)  # 年化波動率
            sharpe_ratio = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
            
            # 最大回撤
            equity_array = np.array([e['value'] for e in equity_curve])
            running_max = np.maximum.accumulate(equity_array)
            drawdown = (equity_array - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
        else:
            volatility = 0
            sharpe_ratio = 0
            max_drawdown = 0
        
        # 交易統計
        if trades:
            pnls = [t.get('pnl', 0) for t in trades]
            avg_win = np.mean([p for p in pnls if p > 0]) if any(p > 0 for p in pnls) else 0
            avg_loss = np.mean([p for p in pnls if p < 0]) if any(p < 0 for p in pnls) else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        else:
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        return {
            'basic_stats': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_return': round(total_return, 2),
                'total_return_pct': round(total_return_pct, 2),
                'initial_capital': self.report_data['initial_capital'],
                'final_capital': round(self.report_data['final_capital'], 2)
            },
            'risk_metrics': {
                'volatility': round(volatility * 100, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'profit_factor': round(profit_factor, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2)
            },
            'period': {
                'start_date': self.report_data['start_date'],
                'end_date': self.report_data['end_date'],
                'model_name': self.report_data['model_name'],
                'strategy': self.report_data['strategy']
            }
        }
    
    def _get_empty_stats(self) -> Dict[str, Any]:
        """返回空統計數據"""
        return {
            'basic_stats': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'total_return_pct': 0,
                'initial_capital': self.report_data['initial_capital'],
                'final_capital': self.report_data['final_capital']
            },
            'risk_metrics': {
                'volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0
            },
            'period': {
                'start_date': self.report_data.get('start_date', ''),
                'end_date': self.report_data.get('end_date', ''),
                'model_name': self.report_data.get('model_name', 'Unknown'),
                'strategy': self.report_data.get('strategy', 'Unknown')
            }
        }
    
    def _generate_charts(self, output_dir: str) -> List[str]:
        """生成圖表"""
        chart_files = []
        
        try:
            # 設置中文字體
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 1. 資產曲線圖
            if self.report_data['equity_curve']:
                equity_file = self._create_equity_curve_chart(output_dir)
                if equity_file:
                    chart_files.append(equity_file)
            
            return chart_files
            
        except Exception as e:
            print(f"❌ 生成圖表失敗: {e}")
            return []
    
    def _create_equity_curve_chart(self, output_dir: str) -> str:
        """創建資產曲線圖"""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            equity_data = self.report_data['equity_curve']
            dates = [datetime.strptime(e['date'], '%Y-%m-%d') if isinstance(e['date'], str) 
                    else e['date'] for e in equity_data]
            values = [e['value'] for e in equity_data]
            
            ax.plot(dates, values, linewidth=2, color='#2196F3')
            ax.fill_between(dates, values, alpha=0.3, color='#2196F3')
            
            ax.set_title('資產曲線', fontsize=16, fontweight='bold')
            ax.set_xlabel('日期', fontsize=12)
            ax.set_ylabel('資產價值', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # 格式化日期軸
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            chart_file = os.path.join(output_dir, 'equity_curve.png')
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            return chart_file
            
        except Exception as e:
            print(f"❌ 創建資產曲線圖失敗: {e}")
            return ""
    
    def _generate_html_report(self, stats: Dict[str, Any], 
                            charts: List[str], output_dir: str) -> str:
        """生成HTML報告"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AImax 回測報告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 20px;
        }}
        .header h1 {{
            color: #2196F3;
            margin: 0;
            font-size: 2.5em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1.2em;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AImax 回測報告</h1>
            <p>模型: {stats['period']['model_name']} | 策略: {stats['period']['strategy']}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>📊 總收益</h3>
                <div class="value">{stats['basic_stats']['total_return_pct']:.2f}%</div>
            </div>
            
            <div class="stat-card">
                <h3>🎯 勝率</h3>
                <div class="value">{stats['basic_stats']['win_rate']:.1f}%</div>
            </div>
        </div>
        
        <div class="footer">
            <p>📅 報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>🤖 由 AImax AI交易系統 自動生成</p>
        </div>
    </div>
</body>
</html>
"""
            
            # 保存HTML文件
            report_file = os.path.join(output_dir, 'backtest_report.html')
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return report_file
            
        except Exception as e:
            print(f"❌ 生成HTML報告失敗: {e}")
            return ""
    
    def _save_json_data(self, stats: Dict[str, Any], output_dir: str):
        """保存JSON數據文件"""
        try:
            json_file = os.path.join(output_dir, 'backtest_data.json')
            
            json_data = {
                'statistics': stats,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'generator': 'AImax Backtest Reporter v1.0'
                }
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON數據已保存: {json_file}")
            
        except Exception as e:
            print(f"❌ 保存JSON數據失敗: {e}")


def create_sample_backtest_report():
    """創建示例回測報告"""
    # 生成示例數據
    sample_data = {
        'trades': [
            {'date': '2024-01-15', 'symbol': 'BTC/USDT', 'side': 'buy', 'amount': 0.1, 'price': 45000, 'pnl': 500},
            {'date': '2024-01-16', 'symbol': 'ETH/USDT', 'side': 'sell', 'amount': 2, 'price': 2800, 'pnl': -200},
            {'date': '2024-01-17', 'symbol': 'BTC/USDT', 'side': 'sell', 'amount': 0.1, 'price': 46000, 'pnl': 1000},
        ],
        'equity_curve': [
            {'date': '2024-01-01', 'value': 10000},
            {'date': '2024-01-15', 'value': 10500},
            {'date': '2024-01-16', 'value': 10300},
            {'date': '2024-01-17', 'value': 11300},
        ],
        'daily_returns': [0.05, -0.02, 0.097],
        'start_date': '2024-01-01',
        'end_date': '2024-01-17',
        'initial_capital': 10000,
        'final_capital': 11300,
        'model_name': 'XGBoost',
        'strategy': '智能網格交易'
    }
    
    reporter = BacktestReporter()
    report_path = reporter.generate_report(sample_data)
    
    if report_path:
        print(f"✅ 示例回測報告已生成: {report_path}")
    else:
        print("❌ 生成示例報告失敗")


if __name__ == "__main__":
    create_sample_backtest_report()