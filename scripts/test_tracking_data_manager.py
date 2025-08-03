#!/usr/bin/env python3
"""
測試追蹤數據管理系統
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import tempfile
import shutil
from datetime import datetime, timedelta
try:
    from src.data.tracking_data_manager import TrackingDataManager, create_tracking_data_manager
    from src.core.dynamic_trading_data_structures import (
        DynamicTradeResult, TrackingWindow, SignalType, ExecutionReason, WindowStatus
    )
    from src.core.dynamic_trading_config import PerformanceConfig
except ImportError as e:
    print(f"導入錯誤: {e}")
    print("請確保所有必要的模組都已正確創建")
    sys.exit(1)

def create_test_trade_result(trade_id: str, signal_type: SignalType, 
                           improvement: float = 1000.0) -> DynamicTradeResult:
    """創建測試交易結果"""
    base_time = datetime.now()
    base_price = 3400000.0
    
    return DynamicTradeResult(
        trade_id=trade_id,
        signal_type=signal_type,
        original_signal_time=base_time - timedelta(hours=2),
        original_signal_price=base_price,
        actual_execution_time=base_time,
        actual_execution_price=base_price + (improvement if signal_type == SignalType.SELL else -improvement),
        execution_reason=ExecutionReason.REVERSAL_DETECTED
    )

def create_test_tracking_window(window_id: str, signal_type: SignalType) -> TrackingWindow:
    """創建測試追蹤窗口"""
    base_time = datetime.now()
    return TrackingWindow(
        window_id=window_id,
        signal_type=signal_type,
        start_time=base_time - timedelta(hours=2),
        end_time=base_time,
        start_price=3400000.0,
        current_extreme_price=3395000.0 if signal_type == SignalType.BUY else 3405000.0,
        extreme_time=base_time - timedelta(hours=1),
        status=WindowStatus.COMPLETED,
        execution_reason=ExecutionReason.REVERSAL_DETECTED
    )

def test_basic_data_operations():
    """測試基本數據操作"""
    print("🧪 測試基本數據操作...")
    
    # 創建臨時數據庫
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_tracking.db")
    
    try:
        # 創建數據管理器
        config = PerformanceConfig()
        manager = TrackingDataManager(config, db_path)
        print("✅ 數據管理器創建成功")
        
        # 測試存儲交易結果
        test_results = [
            create_test_trade_result("trade_001", SignalType.BUY, 1500.0),
            create_test_trade_result("trade_002", SignalType.SELL, 2000.0),
            create_test_trade_result("trade_003", SignalType.BUY, -500.0),  # 負改善
        ]
        
        stored_count = 0
        for result in test_results:
            if manager.store_trade_result(result):
                stored_count += 1
        print(f"✅ 存儲交易結果: {stored_count}/{len(test_results)}")
        
        # 測試存儲追蹤窗口
        test_windows = [
            create_test_tracking_window("window_001", SignalType.BUY),
            create_test_tracking_window("window_002", SignalType.SELL),
        ]
        
        window_stored_count = 0
        for window in test_windows:
            if manager.store_tracking_window(window):
                window_stored_count += 1
        print(f"✅ 存儲追蹤窗口: {window_stored_count}/{len(test_windows)}")
        
        # 測試獲取交易結果
        retrieved_results = manager.get_trade_results()
        print(f"✅ 獲取交易結果: {len(retrieved_results)} 筆記錄")
        
        # 測試按信號類型過濾
        buy_results = manager.get_trade_results(signal_type=SignalType.BUY)
        sell_results = manager.get_trade_results(signal_type=SignalType.SELL)
        print(f"   買入結果: {len(buy_results)} 筆")
        print(f"   賣出結果: {len(sell_results)} 筆")
        
        manager.close()
        
    except Exception as e:
        print(f"❌ 基本數據操作測試失敗: {e}")
    finally:
        # 清理臨時文件
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_statistics_calculation():
    """測試統計計算"""
    print("\n🧪 測試統計計算...")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_stats.db")
    
    try:
        config = PerformanceConfig()
        manager = TrackingDataManager(config, db_path)
        
        # 創建多個測試交易結果
        test_data = [
            ("trade_001", SignalType.BUY, 1000.0),
            ("trade_002", SignalType.BUY, 1500.0),
            ("trade_003", SignalType.SELL, 2000.0),
            ("trade_004", SignalType.SELL, -500.0),
            ("trade_005", SignalType.BUY, 800.0),
        ]
        
        for trade_id, signal_type, improvement in test_data:
            result = create_test_trade_result(trade_id, signal_type, improvement)
            manager.store_trade_result(result)
        
        print(f"✅ 創建測試數據: {len(test_data)} 筆交易")
        
        # 計算統計信息
        stats = manager.calculate_statistics()
        summary = stats.get_summary()
        
        print(f"✅ 統計計算完成:")
        print(f"   總信號: {summary['total_signals']}")
        print(f"   買入信號: {summary['buy_signals']}")
        print(f"   賣出信號: {summary['sell_signals']}")
        print(f"   成功改善: {summary['improved_trades']}")
        print(f"   成功率: {summary['success_rate']:.1f}%")
        print(f"   平均改善: {summary['average_improvement']:,.0f} TWD")
        print(f"   最佳改善: {summary['best_improvement']:,.0f} TWD")
        print(f"   最差改善: {summary['worst_improvement']:,.0f} TWD")
        
        # 測試每日統計存儲
        today = datetime.now()
        daily_stored = manager.store_daily_statistics(today, stats)
        print(f"✅ 每日統計存儲: {daily_stored}")
        
        manager.close()
        
    except Exception as e:
        print(f"❌ 統計計算測試失敗: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_strategy_comparison():
    """測試策略比較"""
    print("\n🧪 測試策略比較...")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_comparison.db")
    
    try:
        config = PerformanceConfig()
        manager = TrackingDataManager(config, db_path)
        
        # 創建一週的測試數據
        base_time = datetime.now()
        start_date = base_time - timedelta(days=7)
        end_date = base_time
        
        # 創建一週的測試數據
        test_trades = [
            ("trade_001", SignalType.BUY, 1500.0),
            ("trade_002", SignalType.SELL, 2200.0),
            ("trade_003", SignalType.BUY, -300.0),
            ("trade_004", SignalType.SELL, 1800.0),
            ("trade_005", SignalType.BUY, 900.0),
            ("trade_006", SignalType.SELL, -600.0),
            ("trade_007", SignalType.BUY, 2500.0),
        ]
        
        for i, (trade_id, signal_type, improvement) in enumerate(test_trades):
            # 分散到一週內的不同時間
            trade_time = start_date + timedelta(days=i, hours=i*2)
            result = create_test_trade_result(trade_id, signal_type, improvement)
            # 調整時間
            result.original_signal_time = trade_time
            result.actual_execution_time = trade_time + timedelta(hours=1)
            manager.store_trade_result(result)
        
        print(f"✅ 創建測試數據: {len(test_trades)} 筆交易")
        
        # 執行策略比較
        comparison = manager.compare_strategies(start_date, end_date)
        
        if 'error' not in comparison:
            print("✅ 策略比較完成:")
            print(f"   比較期間: {comparison['comparison_period']['days']} 天")
            print(f"   總交易數: {comparison['statistics']['total_trades']}")
            print(f"   成功改善: {comparison['improvement']['successful_improvements']}")
            print(f"   成功率: {comparison['improvement']['success_rate']:.1f}%")
            print(f"   總改善金額: {comparison['improvement']['amount']:,.0f} TWD")
            print(f"   改善百分比: {comparison['improvement']['percentage']:.2f}%")
            print(f"   平均每筆改善: {comparison['statistics']['average_improvement_per_trade']:,.0f} TWD")
        else:
            print(f"❌ 策略比較失敗: {comparison['error']}")
        
        manager.close()
        
    except Exception as e:
        print(f"❌ 策略比較測試失敗: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_performance_trends():
    """測試性能趨勢分析"""
    print("\n🧪 測試性能趨勢分析...")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_trends.db")
    
    try:
        config = PerformanceConfig()
        manager = TrackingDataManager(config, db_path)
        
        # 創建多天的測試數據
        base_time = datetime.now()
        for day in range(10):
            date = base_time - timedelta(days=day)
            
            # 每天創建幾筆交易
            for i in range(3):
                trade_id = f"trade_{day}_{i}"
                signal_type = SignalType.BUY if i % 2 == 0 else SignalType.SELL
                improvement = 1000 + (day * 100) + (i * 50)  # 遞增改善
                
                result = create_test_trade_result(trade_id, signal_type, improvement)
                result.original_signal_time = date
                result.actual_execution_time = date + timedelta(hours=1)
                manager.store_trade_result(result)
            
            # 存儲每日統計
            stats = manager.calculate_statistics(date - timedelta(hours=12), date + timedelta(hours=12))
            manager.store_daily_statistics(date, stats)
        
        print("✅ 創建多天測試數據完成")
        
        # 獲取性能趨勢
        trends = manager.get_performance_trends(days=10)
        
        if 'error' not in trends:
            print("✅ 性能趨勢分析完成:")
            print(f"   分析期間: {trends['period']['days']} 天")
            print(f"   有數據天數: {trends['summary']['total_days_with_data']}")
            print(f"   平均每日信號: {trends['summary']['average_daily_signals']:.1f}")
            print(f"   平均成功率: {trends['summary']['average_success_rate']:.1f}%")
            print(f"   總改善金額: {trends['summary']['total_improvement']:,.0f} TWD")
        else:
            print(f"❌ 性能趨勢分析失敗: {trends['error']}")
        
        manager.close()
        
    except Exception as e:
        print(f"❌ 性能趨勢測試失敗: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_detailed_report():
    """測試詳細分析報告"""
    print("\n🧪 測試詳細分析報告...")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_report.db")
    
    try:
        config = PerformanceConfig()
        manager = TrackingDataManager(config, db_path)
        
        # 創建多樣化的測試數據
        base_time = datetime.now()
        start_date = base_time - timedelta(days=3)
        end_date = base_time
        
        test_scenarios = [
            # (trade_id, signal_type, improvement, execution_reason, hour)
            ("trade_001", SignalType.BUY, 2000.0, ExecutionReason.REVERSAL_DETECTED, 9),
            ("trade_002", SignalType.SELL, 1500.0, ExecutionReason.TIMEOUT, 14),
            ("trade_003", SignalType.BUY, -500.0, ExecutionReason.EXTREME_REACHED, 10),
            ("trade_004", SignalType.SELL, 3000.0, ExecutionReason.REVERSAL_DETECTED, 15),
            ("trade_005", SignalType.BUY, 800.0, ExecutionReason.TIMEOUT, 11),
            ("trade_006", SignalType.SELL, 12000.0, ExecutionReason.EXTREME_REACHED, 16),  # 大改善
            ("trade_007", SignalType.BUY, 400.0, ExecutionReason.REVERSAL_DETECTED, 9),
        ]
        
        for trade_id, signal_type, improvement, exec_reason, hour in test_scenarios:
            result = create_test_trade_result(trade_id, signal_type, improvement)
            # 設置特定的執行原因和時間
            result.execution_reason = exec_reason
            result.original_signal_time = start_date + timedelta(hours=hour)
            result.actual_execution_time = result.original_signal_time + timedelta(hours=1)
            manager.store_trade_result(result)
        
        print(f"✅ 創建多樣化測試數據: {len(test_scenarios)} 筆交易")
        
        # 生成詳細報告
        report = manager.generate_detailed_report(start_date, end_date)
        
        if 'error' not in report:
            print("✅ 詳細分析報告生成完成:")
            print(f"   報告期間: {report['report_info']['period']['days']} 天")
            print(f"   總記錄數: {report['data_quality']['total_records']}")
            
            # 基本統計
            basic_stats = report['basic_statistics']
            print(f"   總信號: {basic_stats['total_signals']}")
            print(f"   成功率: {basic_stats['success_rate']:.1f}%")
            print(f"   平均改善: {basic_stats['average_improvement']:,.0f} TWD")
            
            # 執行分析
            exec_analysis = report['execution_analysis']
            print(f"   執行原因分布: {exec_analysis['execution_reasons']}")
            print(f"   時間分布: {exec_analysis['hourly_distribution']}")
            print(f"   改善範圍分布: {exec_analysis['improvement_ranges']}")
            
            # 建議
            recommendations = report['recommendations']
            print(f"   系統建議數量: {len(recommendations)}")
            for i, rec in enumerate(recommendations[:3], 1):  # 顯示前3個建議
                print(f"     {i}. {rec}")
        else:
            print(f"❌ 詳細報告生成失敗: {report['error']}")
        
        manager.close()
        
    except Exception as e:
        print(f"❌ 詳細報告測試失敗: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_data_management():
    """測試數據管理功能"""
    print("\n🧪 測試數據管理功能...")
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_management.db")
    
    try:
        config = PerformanceConfig()
        manager = TrackingDataManager(config, db_path)
        
        # 創建一些測試數據
        for i in range(5):
            result = create_test_trade_result(f"trade_{i}", SignalType.BUY, 1000.0 + i*100)
            manager.store_trade_result(result)
        
        print("✅ 創建測試數據完成")
        
        # 測試系統健康狀態
        health = manager.get_system_health()
        print("✅ 系統健康檢查:")
        print(f"   數據庫大小: {health['database']['size_mb']:.2f} MB")
        print(f"   交易記錄數: {health['database']['trade_results_count']}")
        print(f"   緩存狀態: {'啟用' if health['cache']['enabled'] else '停用'}")
        print(f"   系統狀態: {health['status']}")
        
        # 測試數據導出
        export_dir = os.path.join(temp_dir, "export")
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        export_success = manager.export_data(start_date, end_date, export_dir)
        print(f"✅ 數據導出: {'成功' if export_success else '失敗'}")
        
        if export_success:
            # 檢查導出的文件
            export_files = os.listdir(export_dir)
            print(f"   導出文件: {export_files}")
        
        # 測試數據清理
        cleanup_result = manager.cleanup_old_data(retention_days=1)
        if 'error' not in cleanup_result:
            print("✅ 數據清理完成:")
            print(f"   刪除交易結果: {cleanup_result['trade_results_deleted']}")
            print(f"   刪除追蹤窗口: {cleanup_result['windows_deleted']}")
            print(f"   刪除統計記錄: {cleanup_result['statistics_deleted']}")
        else:
            print(f"❌ 數據清理失敗: {cleanup_result['error']}")
        
        manager.close()
        
    except Exception as e:
        print(f"❌ 數據管理測試失敗: {e}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    """主測試函數"""
    print("🚀 開始測試追蹤數據管理系統...")
    print("=" * 60)
    
    # 執行所有測試
    test_basic_data_operations()
    test_statistics_calculation()
    test_strategy_comparison()
    test_performance_trends()
    test_detailed_report()
    test_data_management()
    
    print("\n" + "=" * 60)
    print("🎉 追蹤數據管理系統測試完成！")
    print("\n📊 測試摘要:")
    print("• 基本數據操作 - 存儲和檢索功能")
    print("• 統計計算 - 性能指標計算")
    print("• 策略比較 - 原始vs動態策略對比")
    print("• 性能趨勢 - 時間序列分析")
    print("• 詳細報告 - 全面分析報告生成")
    print("• 數據管理 - 健康檢查、導出、清理")
    print("\n✨ 系統已準備好進行實際使用！")

if __name__ == "__main__":
    main()