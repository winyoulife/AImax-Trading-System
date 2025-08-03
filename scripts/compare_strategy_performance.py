#!/usr/bin/env python3
"""
策略性能比較分析器
比較原版MACD策略 vs 動態追蹤策略的獲利表現
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def find_latest_csv_files():
    """找到最新的CSV結果文件"""
    data_dir = "AImax/data"
    
    # 查找原版策略的CSV文件
    original_files = glob.glob(f"{data_dir}/improved_macd_7day_backtest_*.csv")
    original_latest = max(original_files, key=os.path.getctime) if original_files else None
    
    # 查找動態策略的CSV文件
    dynamic_files = glob.glob(f"{data_dir}/dynamic_macd_7day_backtest_*.csv")
    dynamic_latest = max(dynamic_files, key=os.path.getctime) if dynamic_files else None
    
    return original_latest, dynamic_latest

def analyze_strategy_performance(csv_file, strategy_name):
    """分析單個策略的性能"""
    if not csv_file or not os.path.exists(csv_file):
        print(f"❌ 找不到 {strategy_name} 的CSV文件")
        return None
    
    print(f"📊 分析 {strategy_name} 策略...")
    df = pd.read_csv(csv_file)
    
    # 檢查CSV文件結構並提取交易信號
    if 'signal_type' in df.columns:
        # 動態策略格式
        buy_signals = df[df['signal_type'].isin(['buy', 'observe_buy'])]
        sell_signals = df[df['signal_type'].isin(['sell', 'observe_sell'])]
        signal_col = 'signal_type'
        time_col = 'datetime'
        price_col = 'close'
        sequence_col = 'trade_sequence'
    elif '信號類型' in df.columns:
        # 原版策略格式
        buy_signals = df[df['信號類型'].isin(['buy'])]
        sell_signals = df[df['信號類型'].isin(['sell'])]
        signal_col = '信號類型'
        time_col = '時間'
        price_col = '價格'
        sequence_col = '交易序號'
    else:
        print(f"❌ 無法識別 {strategy_name} 的CSV格式")
        return None
    
    # 計算交易對
    trades = []
    current_buy = None
    
    for _, row in df.iterrows():
        if row[signal_col] in ['buy', 'observe_buy'] and current_buy is None:
            current_buy = {
                'buy_time': row[time_col],
                'buy_price': row[price_col],
                'buy_sequence': row.get(sequence_col, 0)
            }
        elif row[signal_col] in ['sell', 'observe_sell'] and current_buy is not None:
            trade = {
                **current_buy,
                'sell_time': row[time_col],
                'sell_price': row[price_col],
                'sell_sequence': row.get(sequence_col, 0),
                'profit': row[price_col] - current_buy['buy_price'],
                'profit_pct': ((row[price_col] - current_buy['buy_price']) / current_buy['buy_price']) * 100
            }
            trades.append(trade)
            current_buy = None
    
    # 統計信息
    total_trades = len(trades)
    profitable_trades = len([t for t in trades if t['profit'] > 0])
    total_profit = sum(t['profit'] for t in trades)
    avg_profit = total_profit / total_trades if total_trades > 0 else 0
    win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
    
    # 計算最大回撤
    cumulative_profit = 0
    max_profit = 0
    max_drawdown = 0
    
    for trade in trades:
        cumulative_profit += trade['profit']
        if cumulative_profit > max_profit:
            max_profit = cumulative_profit
        drawdown = max_profit - cumulative_profit
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    return {
        'strategy_name': strategy_name,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'total_profit': total_profit,
        'avg_profit': avg_profit,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'trades': trades,
        'buy_signals': len(buy_signals),
        'sell_signals': len(sell_signals)
    }

def create_comparison_report(original_stats, dynamic_stats):
    """創建比較報告"""
    print("\n" + "="*80)
    print("📈 策略性能比較報告")
    print("="*80)
    
    if not original_stats or not dynamic_stats:
        print("❌ 無法生成比較報告，缺少數據")
        return
    
    # 創建比較表格
    comparison_data = []
    
    for stats in [original_stats, dynamic_stats]:
        comparison_data.append({
            '策略': stats['strategy_name'],
            '總交易次數': stats['total_trades'],
            '獲利交易': stats['profitable_trades'],
            '勝率(%)': f"{stats['win_rate']:.1f}%",
            '總利潤': f"{stats['total_profit']:,.0f}",
            '平均利潤': f"{stats['avg_profit']:,.0f}",
            '最大回撤': f"{stats['max_drawdown']:,.0f}",
            '買進信號': stats['buy_signals'],
            '賣出信號': stats['sell_signals']
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print("\n📊 性能比較表:")
    print(comparison_df.to_string(index=False))
    
    # 計算改進幅度
    profit_improvement = ((dynamic_stats['total_profit'] - original_stats['total_profit']) / original_stats['total_profit']) * 100
    win_rate_improvement = dynamic_stats['win_rate'] - original_stats['win_rate']
    
    print(f"\n🎯 改進分析:")
    print(f"  利潤提升: {profit_improvement:+.1f}%")
    print(f"  勝率提升: {win_rate_improvement:+.1f}%")
    
    # 詳細交易分析
    print(f"\n📋 詳細交易分析:")
    print(f"  原版策略 - 平均持倉時間: {calculate_avg_hold_time(original_stats['trades']):.1f} 小時")
    print(f"  動態策略 - 平均持倉時間: {calculate_avg_hold_time(dynamic_stats['trades']):.1f} 小時")
    
    return comparison_df

def calculate_avg_hold_time(trades):
    """計算平均持倉時間"""
    if not trades:
        return 0
    
    hold_times = []
    for trade in trades:
        buy_time = pd.to_datetime(trade['buy_time'])
        sell_time = pd.to_datetime(trade['sell_time'])
        hold_time = (sell_time - buy_time).total_seconds() / 3600  # 小時
        hold_times.append(hold_time)
    
    return np.mean(hold_times)

def create_visualization(original_stats, dynamic_stats):
    """創建視覺化圖表"""
    if not original_stats or not dynamic_stats:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('策略性能比較分析', fontsize=16, fontweight='bold')
    
    # 1. 利潤比較
    strategies = ['原版策略', '動態策略']
    profits = [original_stats['total_profit'], dynamic_stats['total_profit']]
    
    axes[0, 0].bar(strategies, profits, color=['#FF6B6B', '#4ECDC4'])
    axes[0, 0].set_title('總利潤比較')
    axes[0, 0].set_ylabel('利潤 (TWD)')
    for i, v in enumerate(profits):
        axes[0, 0].text(i, v + max(profits)*0.01, f'{v:,.0f}', ha='center', va='bottom')
    
    # 2. 勝率比較
    win_rates = [original_stats['win_rate'], dynamic_stats['win_rate']]
    
    axes[0, 1].bar(strategies, win_rates, color=['#FF6B6B', '#4ECDC4'])
    axes[0, 1].set_title('勝率比較')
    axes[0, 1].set_ylabel('勝率 (%)')
    axes[0, 1].set_ylim(0, 100)
    for i, v in enumerate(win_rates):
        axes[0, 1].text(i, v + 1, f'{v:.1f}%', ha='center', va='bottom')
    
    # 3. 交易次數比較
    trade_counts = [original_stats['total_trades'], dynamic_stats['total_trades']]
    
    axes[1, 0].bar(strategies, trade_counts, color=['#FF6B6B', '#4ECDC4'])
    axes[1, 0].set_title('交易次數比較')
    axes[1, 0].set_ylabel('交易次數')
    for i, v in enumerate(trade_counts):
        axes[1, 0].text(i, v + 0.1, str(v), ha='center', va='bottom')
    
    # 4. 累積利潤曲線
    original_cumulative = np.cumsum([t['profit'] for t in original_stats['trades']])
    dynamic_cumulative = np.cumsum([t['profit'] for t in dynamic_stats['trades']])
    
    axes[1, 1].plot(range(len(original_cumulative)), original_cumulative, 
                    label='原版策略', color='#FF6B6B', linewidth=2)
    axes[1, 1].plot(range(len(dynamic_cumulative)), dynamic_cumulative, 
                    label='動態策略', color='#4ECDC4', linewidth=2)
    axes[1, 1].set_title('累積利潤曲線')
    axes[1, 1].set_xlabel('交易序號')
    axes[1, 1].set_ylabel('累積利潤 (TWD)')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存圖表
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chart_path = f"AImax/reports/strategy_comparison_{timestamp}.png"
    os.makedirs(os.path.dirname(chart_path), exist_ok=True)
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"\n📊 比較圖表已保存: {chart_path}")
    
    plt.show()

def main():
    """主函數"""
    print("🔍 開始策略性能比較分析...")
    
    # 找到最新的CSV文件
    original_file, dynamic_file = find_latest_csv_files()
    
    print(f"📁 原版策略文件: {original_file}")
    print(f"📁 動態策略文件: {dynamic_file}")
    
    # 分析兩個策略
    original_stats = analyze_strategy_performance(original_file, "原版MACD策略")
    dynamic_stats = analyze_strategy_performance(dynamic_file, "動態追蹤策略")
    
    # 創建比較報告
    comparison_df = create_comparison_report(original_stats, dynamic_stats)
    
    # 創建視覺化
    if original_stats and dynamic_stats:
        create_visualization(original_stats, dynamic_stats)
    
    # 保存比較報告
    if comparison_df is not None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"AImax/reports/strategy_comparison_{timestamp}.csv"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        comparison_df.to_csv(report_path, index=False, encoding='utf-8-sig')
        print(f"\n📄 比較報告已保存: {report_path}")
    
    print("\n✅ 策略性能比較分析完成！")

if __name__ == "__main__":
    main() 