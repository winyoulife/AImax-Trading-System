#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 策略管理系統測試腳本 - 任務12實現
測試策略配置管理、回測引擎和版本管理功能
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.strategy.strategy_config_manager import (
    strategy_config_manager, StrategyType, RiskLevel,
    create_strategy, update_strategy_config, set_active_strategy
)
from src.strategy.backtest_engine import backtest_engine, run_strategy_backtest, compare_strategies
from src.strategy.version_manager import (
    version_manager, create_strategy_version, rollback_strategy, get_strategy_versions
)

def test_strategy_config_manager():
    """測試策略配置管理器"""
    print("⚙️ 測試策略配置管理器...")
    
    # 創建測試策略
    print("\n📝 創建測試策略...")
    strategy_id1 = strategy_config_manager.create_strategy(
        "保守型MACD策略", 
        StrategyType.MACD, 
        RiskLevel.CONSERVATIVE,
        "適合穩健投資者的保守型策略"
    )
    print(f"✅ 創建保守型策略: {strategy_id1}")
    
    strategy_id2 = strategy_config_manager.create_strategy(
        "激進型MACD策略",
        StrategyType.MACD,
        RiskLevel.AGGRESSIVE,
        "適合風險偏好投資者的激進型策略"
    )
    print(f"✅ 創建激進型策略: {strategy_id2}")
    
    # 測試策略列表
    print("\n📋 策略列表:")
    strategies = strategy_config_manager.list_strategies()
    for strategy in strategies:
        print(f"  • {strategy['strategy_name']} (v{strategy['version']}) - {strategy['strategy_type']}")
    
    # 測試策略更新
    print("\n🔧 測試策略更新...")
    update_result = update_strategy_config(strategy_id1, {
        'description': '更新後的保守型策略描述',
        'macd_config': {
            'min_confidence': 0.95,
            'volume_threshold': 2.5
        },
        'risk_config': {
            'max_position_size': 0.03,
            'stop_loss_pct': 0.02
        }
    })
    
    if update_result:
        print("✅ 策略更新成功")
        updated_strategy = strategy_config_manager.get_strategy(strategy_id1)
        print(f"   新版本: v{updated_strategy.version}")
        print(f"   最小信心度: {updated_strategy.macd_config.min_confidence}")
    else:
        print("❌ 策略更新失敗")
    
    # 測試設置活躍策略
    print("\n🎯 設置活躍策略...")
    if set_active_strategy(strategy_id1):
        print("✅ 設置活躍策略成功")
        active_strategy = strategy_config_manager.get_active_strategy()
        if active_strategy:
            print(f"   當前活躍策略: {active_strategy.strategy_name}")
    
    # 測試策略驗證
    print("\n✅ 測試策略驗證...")
    validation_result = strategy_config_manager.validate_strategy_config(strategy_id1)
    print(f"策略驗證結果: {'有效' if validation_result['valid'] else '無效'}")
    
    if validation_result['errors']:
        print("   錯誤:")
        for error in validation_result['errors']:
            print(f"     • {error}")
    
    if validation_result['warnings']:
        print("   警告:")
        for warning in validation_result['warnings']:
            print(f"     • {warning}")
    
    # 測試策略克隆
    print("\n📋 測試策略克隆...")
    cloned_strategy_id = strategy_config_manager.clone_strategy(strategy_id1, "保守型策略副本")
    if cloned_strategy_id:
        print(f"✅ 策略克隆成功: {cloned_strategy_id}")
    
    # 測試策略導出導入
    print("\n📤 測試策略導出導入...")
    export_data = strategy_config_manager.export_strategy(strategy_id1)
    if export_data:
        print("✅ 策略導出成功")
        
        # 導入為新策略
        imported_strategy_id = strategy_config_manager.import_strategy(export_data, "導入的策略")
        if imported_strategy_id:
            print(f"✅ 策略導入成功: {imported_strategy_id}")
    
    # 獲取統計信息
    print("\n📊 策略統計信息:")
    stats = strategy_config_manager.get_strategy_statistics()
    print(f"   總策略數: {stats['total_strategies']}")
    print(f"   活躍策略數: {stats['active_strategies']}")
    print(f"   策略類型分布: {stats['strategy_types']}")
    print(f"   風險分布: {stats['risk_distribution']}")
    
    return [strategy_id1, strategy_id2, cloned_strategy_id, imported_strategy_id]

def test_backtest_engine(strategy_ids):
    """測試回測引擎"""
    print("\n📈 測試回測引擎...")
    
    if not strategy_ids:
        print("⚠️ 沒有可用的策略進行回測")
        return
    
    # 測試單個策略回測
    print("\n🔄 運行單個策略回測...")
    strategy_id = strategy_ids[0]
    
    backtest_result = run_strategy_backtest(strategy_id, 'BTCUSDT', 7)  # 7天回測
    
    if backtest_result:
        print("✅ 回測完成:")
        print(f"   策略ID: {backtest_result.strategy_id}")
        print(f"   回測期間: {backtest_result.start_date.strftime('%Y-%m-%d')} 到 {backtest_result.end_date.strftime('%Y-%m-%d')}")
        print(f"   初始資金: ${backtest_result.initial_balance:,.2f}")
        print(f"   最終資金: ${backtest_result.final_balance:,.2f}")
        print(f"   總回報率: {backtest_result.total_return:.2f}%")
        print(f"   總交易次數: {backtest_result.total_trades}")
        print(f"   勝率: {backtest_result.win_rate:.1f}%")
        print(f"   最大回撤: {backtest_result.max_drawdown:.2f}%")
        print(f"   夏普比率: {backtest_result.sharpe_ratio:.3f}")
        
        if backtest_result.trades:
            print(f"   最近交易:")
            for trade in backtest_result.trades[-3:]:  # 顯示最後3筆交易
                profit_str = f"盈虧: ${trade.profit_loss:.2f}" if trade.profit_loss != 0 else ""
                print(f"     {trade.timestamp.strftime('%m-%d %H:%M')} {trade.action.upper()} "
                      f"${trade.price:.2f} x{trade.quantity:.6f} {profit_str}")
    else:
        print("❌ 回測失敗")
    
    # 測試策略比較
    if len(strategy_ids) >= 2:
        print("\n📊 測試策略比較...")
        comparison_result = compare_strategies(strategy_ids[:2], 'BTCUSDT', 5)  # 5天比較
        
        if comparison_result and 'results' in comparison_result:
            print("✅ 策略比較完成:")
            print(f"   比較期間: {comparison_result['backtest_days']} 天")
            print(f"   比較策略數: {comparison_result['strategies_compared']}")
            
            if comparison_result['best_strategy']:
                best_id, best_result = comparison_result['best_strategy']
                print(f"   最佳策略: {best_result['strategy_name']}")
                print(f"   最佳回報: {best_result['total_return']:.2f}%")
            
            print("   所有策略表現:")
            for strategy_id, result in comparison_result['results'].items():
                print(f"     • {result['strategy_name']}: {result['total_return']:.2f}% "
                      f"(勝率: {result['win_rate']:.1f}%)")
        else:
            print("❌ 策略比較失敗")

def test_version_manager(strategy_ids):
    """測試版本管理器"""
    print("\n📚 測試版本管理器...")
    
    if not strategy_ids:
        print("⚠️ 沒有可用的策略進行版本管理測試")
        return
    
    strategy_id = strategy_ids[0]
    
    # 創建版本
    print("\n📝 創建策略版本...")
    version1 = create_strategy_version(
        strategy_id,
        "初始版本優化",
        ["調整MACD參數", "優化風險控制", "提高信心度閾值"]
    )
    
    if version1:
        print(f"✅ 創建版本成功: v{version1}")
    
    # 再次更新策略並創建新版本
    print("\n🔧 更新策略並創建新版本...")
    update_strategy_config(strategy_id, {
        'macd_config': {
            'min_confidence': 0.90,
            'fast_period': 10,
            'slow_period': 24
        }
    })
    
    version2 = create_strategy_version(
        strategy_id,
        "參數微調版本",
        ["調整MACD快慢線週期", "提高最小信心度"]
    )
    
    if version2:
        print(f"✅ 創建版本成功: v{version2}")
    
    # 獲取版本歷史
    print("\n📋 版本歷史:")
    version_history = get_strategy_versions(strategy_id)
    if version_history:
        print(f"   策略: {version_history.strategy_name}")
        print(f"   當前版本: v{version_history.current_version}")
        print(f"   版本數量: {len(version_history.versions)}")
        
        print("   版本列表:")
        for version_info in version_history.versions:
            stable_mark = " [穩定]" if version_info.is_stable else ""
            print(f"     • v{version_info.version}{stable_mark} - {version_info.description}")
            print(f"       創建時間: {version_info.created_at.strftime('%Y-%m-%d %H:%M')}")
            if version_info.changes:
                print(f"       變更: {', '.join(version_info.changes)}")
    
    # 測試版本比較
    if len(version_history.versions) >= 2:
        print("\n🔍 測試版本比較...")
        v1 = version_history.versions[0].version
        v2 = version_history.versions[1].version
        
        comparison = version_manager.compare_versions(strategy_id, v1, v2)
        if 'differences' in comparison:
            print(f"✅ 版本比較完成: v{v1} vs v{v2}")
            
            if comparison['differences']:
                print("   發現差異:")
                for config_type, diffs in comparison['differences'].items():
                    print(f"     {config_type}:")
                    for key, change in diffs.items():
                        print(f"       {key}: {change['old_value']} -> {change['new_value']}")
            else:
                print("   沒有發現差異")
    
    # 測試標記穩定版本
    if version_history and version_history.versions:
        print("\n✅ 測試標記穩定版本...")
        first_version = version_history.versions[0].version
        if version_manager.mark_version_as_stable(strategy_id, first_version):
            print(f"✅ 標記穩定版本成功: v{first_version}")
            
            stable_version = version_manager.get_stable_version(strategy_id)
            print(f"   當前穩定版本: v{stable_version}")
    
    # 測試版本回滾
    if len(version_history.versions) >= 2:
        print("\n🔄 測試版本回滾...")
        target_version = version_history.versions[0].version
        
        if rollback_strategy(strategy_id, target_version):
            print(f"✅ 回滾成功: 回滾到 v{target_version}")
            
            # 驗證回滾結果
            current_strategy = strategy_config_manager.get_strategy(strategy_id)
            if current_strategy:
                print(f"   當前策略版本: v{current_strategy.version}")
        else:
            print("❌ 回滾失敗")
    
    # 測試版本導出
    print("\n📤 測試版本導出...")
    if version_history and version_history.versions:
        export_version = version_history.versions[0].version
        export_data = version_manager.export_version(strategy_id, export_version)
        
        if export_data:
            print(f"✅ 版本導出成功: v{export_version}")
            print(f"   導出數據大小: {len(json.dumps(export_data))} 字符")

def generate_strategy_management_report():
    """生成策略管理報告"""
    print("\n📋 生成策略管理綜合報告...")
    
    # 收集策略統計
    strategy_stats = strategy_config_manager.get_strategy_statistics()
    
    # 收集版本統計
    version_stats = {
        'total_strategies_with_versions': len(version_manager.version_histories),
        'total_versions': sum(len(vh.versions) for vh in version_manager.version_histories.values()),
        'stable_versions': 0
    }
    
    for vh in version_manager.version_histories.values():
        for v in vh.versions:
            if v.is_stable:
                version_stats['stable_versions'] += 1
    
    # 生成報告
    report = f"""
⚙️ AImax 策略管理系統報告
{'='*60}

📊 策略配置統計:
   總策略數: {strategy_stats['total_strategies']}
   活躍策略數: {strategy_stats['active_strategies']}
   非活躍策略數: {strategy_stats['inactive_strategies']}
   
   策略類型分布:
"""
    
    for strategy_type, count in strategy_stats['strategy_types'].items():
        report += f"     {strategy_type}: {count}\n"
    
    report += f"""
   風險等級分布:
     保守型: {strategy_stats['risk_distribution']['conservative']}
     適中型: {strategy_stats['risk_distribution']['moderate']}
     激進型: {strategy_stats['risk_distribution']['aggressive']}

📚 版本管理統計:
   有版本管理的策略: {version_stats['total_strategies_with_versions']}
   總版本數: {version_stats['total_versions']}
   穩定版本數: {version_stats['stable_versions']}

🎯 當前活躍策略:
"""
    
    active_strategy = strategy_config_manager.get_active_strategy()
    if active_strategy:
        report += f"   策略名稱: {active_strategy.strategy_name}\n"
        report += f"   策略類型: {active_strategy.strategy_type.value}\n"
        report += f"   當前版本: v{active_strategy.version}\n"
        report += f"   最小信心度: {active_strategy.macd_config.min_confidence}\n"
        report += f"   最大倉位: {active_strategy.risk_config.max_position_size * 100:.1f}%\n"
        report += f"   止損比例: {active_strategy.risk_config.stop_loss_pct * 100:.1f}%\n"
        
        if active_strategy.performance_metrics:
            report += f"   性能指標:\n"
            for metric, value in active_strategy.performance_metrics.items():
                report += f"     {metric}: {value}\n"
    else:
        report += "   無活躍策略\n"
    
    report += f"""
{'='*60}
報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    print(report)
    
    # 保存報告
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"strategy_management_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 報告已保存: {report_file}")

def main():
    """主測試函數"""
    print("🚀 AImax 策略管理系統完整測試")
    print("=" * 60)
    
    try:
        # 運行各項測試
        strategy_ids = test_strategy_config_manager()
        test_backtest_engine(strategy_ids)
        test_version_manager(strategy_ids)
        
        # 生成綜合報告
        generate_strategy_management_report()
        
        print("\n🎉 所有策略管理測試完成！")
        
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()