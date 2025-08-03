#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 系統集成測試和優化
執行端到端測試，驗證完整流程，並進行性能優化
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import threading
import tempfile
import shutil
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import psutil
import gc

def create_comprehensive_test_data(days: int = 7, interval_minutes: int = 1) -> pd.DataFrame:
    """創建全面的測試數據"""
    print(f"🔧 創建 {days} 天的綜合測試數據...")
    
    # 生成時間序列
    start_time = datetime.now() - timedelta(days=days)
    end_time = datetime.now()
    timestamps = pd.date_range(start=start_time, end=end_time, freq=f'{interval_minutes}min')
    
    # 生成更真實的價格數據
    base_price = 3400000  # 基礎價格
    price_data = []
    current_price = base_price
    
    # 添加趨勢和波動
    trend_factor = 0.0001  # 長期趨勢
    volatility = 0.002     # 短期波動
    
    for i, timestamp in enumerate(timestamps):
        # 長期趨勢
        trend = trend_factor * np.sin(i / 1000) * (i / len(timestamps))
        
        # 短期波動
        volatility_change = np.random.normal(0, volatility)
        
        # 偶爾的大波動（模擬市場事件）
        if np.random.random() < 0.001:  # 0.1% 概率
            volatility_change += np.random.choice([-0.02, 0.02])  # ±2% 大波動
        
        # 更新價格
        price_change = trend + volatility_change
        current_price *= (1 + price_change)
        
        # 確保價格在合理範圍內
        current_price = max(current_price, base_price * 0.7)
        current_price = min(current_price, base_price * 1.3)
        
        # 生成 OHLCV 數據
        high_factor = abs(np.random.normal(0, 0.001))
        low_factor = abs(np.random.normal(0, 0.001))
        
        high = current_price * (1 + high_factor)
        low = current_price * (1 - low_factor)
        open_price = current_price + np.random.normal(0, current_price * 0.0005)
        close_price = current_price + np.random.normal(0, current_price * 0.0005)
        volume = np.random.randint(100, 2000)
        
        price_data.append({
            'timestamp': timestamp,
            'open': max(low, min(high, open_price)),
            'high': max(high, open_price, close_price),
            'low': min(low, open_price, close_price),
            'close': max(low, min(high, close_price)),
            'volume': volume
        })
    
    df = pd.DataFrame(price_data)
    print(f"✅ 綜合測試數據創建完成: {len(df)} 個數據點")
    return df

def test_system_initialization():
    """測試系統初始化"""
    print("\n🧪 測試系統初始化...")
    try:
        from src.core.dynamic_trading_config import DynamicTradingConfig
        from src.core.dynamic_error_handler import DynamicErrorHandler
        from src.core.simple_recovery_manager import SimpleRecoveryManager
        from src.core.simple_backtest_engine import SimpleBacktestEngine
        
        temp_dir = tempfile.mkdtemp()
        try:
            # 初始化各個組件
            config = DynamicTradingConfig()
            print("   ✓ 配置系統初始化成功")
            
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            print("   ✓ 錯誤處理系統初始化成功")
            
            recovery_manager = SimpleRecoveryManager(backup_dir=os.path.join(temp_dir, "backups"))
            print("   ✓ 恢復管理系統初始化成功")
            
            backtest_engine = SimpleBacktestEngine(config)
            print("   ✓ 回測引擎初始化成功")
            
            # 驗證配置
            validation_results = config.validate_all()
            if all(validation_results.values()):
                print("   ✓ 系統配置驗證通過")
            else:
                print(f"   ⚠️ 配置驗證問題: {validation_results}")
            
            print("✅ 系統初始化測試成功")
            return True
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 系統初始化測試失敗: {e}")
        return False

def test_end_to_end_backtest():
    """測試端到端回測流程"""
    print("\n🧪 測試端到端回測流程...")
    try:
        from src.core.dynamic_trading_config import DynamicTradingConfig
        from src.core.simple_backtest_engine import SimpleBacktestEngine
        
        # 創建測試數據
        test_data = create_comprehensive_test_data(days=2)  # 2天數據用於快速測試
        
        # 初始化系統
        config = DynamicTradingConfig()
        backtest_engine = DynamicBacktestEngine(config)
        
        # 執行回測
        print("   開始執行端到端回測...")
        start_time = time.time()
        
        result = backtest_engine.run_backtest(test_data)
        
        execution_time = time.time() - start_time
        
        print(f"✅ 端到端回測完成")
        print(f"   執行時間: {execution_time:.2f} 秒")
        print(f"   處理數據點: {len(test_data)}")
        print(f"   處理速度: {len(test_data)/execution_time:.0f} 數據點/秒")
        print(f"   總交易數: {result.total_trades}")
        print(f"   成功率: {result.success_rate:.1f}%")
        
        backtest_engine.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ 端到端回測測試失敗: {e}")
        return False

def test_performance_under_load():
    """測試高負載下的性能"""
    print("\n🧪 測試高負載下的性能...")
    try:
        from src.core.dynamic_trading_config import DynamicTradingConfig
        from src.core.dynamic_backtest_engine import DynamicBacktestEngine
        
        # 創建大量測試數據
        test_data = create_comprehensive_test_data(days=7)  # 7天數據
        
        # 初始化系統
        config = DynamicTradingConfig()
        backtest_engine = DynamicBacktestEngine(config)
        
        # 監控系統資源
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"   初始內存使用: {initial_memory:.1f} MB")
        print(f"   測試數據量: {len(test_data)} 個數據點")
        
        # 執行高負載測試
        start_time = time.time()
        
        result = backtest_engine.run_backtest(test_data)
        
        execution_time = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"✅ 高負載性能測試完成")
        print(f"   執行時間: {execution_time:.2f} 秒")
        print(f"   處理速度: {len(test_data)/execution_time:.0f} 數據點/秒")
        print(f"   最終內存使用: {final_memory:.1f} MB")
        print(f"   內存增長: {memory_increase:.1f} MB")
        print(f"   總交易數: {result.total_trades}")
        
        # 性能基準檢查
        performance_ok = True
        if len(test_data)/execution_time < 1000:  # 至少1000數據點/秒
            print("   ⚠️ 處理速度低於預期")
            performance_ok = False
        
        if memory_increase > 500:  # 內存增長不應超過500MB
            print("   ⚠️ 內存使用增長過多")
            performance_ok = False
        
        backtest_engine.cleanup()
        gc.collect()  # 強制垃圾回收
        
        return performance_ok
        
    except Exception as e:
        print(f"❌ 高負載性能測試失敗: {e}")
        return False

def test_concurrent_operations():
    """測試並發操作"""
    print("\n🧪 測試並發操作...")
    try:
        from src.core.dynamic_trading_config import DynamicTradingConfig
        from src.core.dynamic_backtest_engine import DynamicBacktestEngine
        
        # 創建測試數據
        test_data = create_comprehensive_test_data(days=1)
        
        results = []
        errors = []
        
        def run_backtest(thread_id):
            """線程執行函數"""
            try:
                config = DynamicTradingConfig()
                engine = DynamicBacktestEngine(config)
                
                result = engine.run_backtest(test_data)
                results.append((thread_id, result))
                
                engine.cleanup()
                
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # 創建多個線程
        threads = []
        num_threads = 3
        
        print(f"   啟動 {num_threads} 個並發回測...")
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=run_backtest, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        execution_time = time.time() - start_time
        
        print(f"✅ 並發操作測試完成")
        print(f"   總執行時間: {execution_time:.2f} 秒")
        print(f"   成功完成: {len(results)} 個線程")
        print(f"   發生錯誤: {len(errors)} 個線程")
        
        if errors:
            print("   錯誤詳情:")
            for thread_id, error in errors:
                print(f"     線程 {thread_id}: {error}")
        
        # 檢查結果一致性
        if len(results) > 1:
            first_result = results[0][1]
            consistent = all(r[1].total_trades == first_result.total_trades for _, r in results)
            if consistent:
                print("   ✓ 並發結果一致性檢查通過")
            else:
                print("   ⚠️ 並發結果不一致")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ 並發操作測試失敗: {e}")
        return False

def test_error_recovery_integration():
    """測試錯誤恢復集成"""
    print("\n🧪 測試錯誤恢復集成...")
    try:
        from src.core.dynamic_error_handler import DynamicErrorHandler
        from src.core.simple_recovery_manager import SimpleRecoveryManager
        
        temp_dir = tempfile.mkdtemp()
        try:
            # 初始化錯誤處理和恢復系統
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            recovery_manager = SimpleRecoveryManager(backup_dir=os.path.join(temp_dir, "backups"))
            
            # 創建測試組件
            class TestTradingComponent:
                def __init__(self):
                    self.position = 0
                    self.balance = 1000000
                    self.trades = []
                
                def get_state(self):
                    return {
                        "position": self.position,
                        "balance": self.balance,
                        "trades": self.trades
                    }
                
                def restore_state(self, state):
                    self.position = state["position"]
                    self.balance = state["balance"]
                    self.trades = state["trades"]
                
                def execute_trade(self, amount):
                    if amount > self.balance:
                        raise ValueError("餘額不足")
                    self.position += amount
                    self.balance -= amount
                    self.trades.append({"amount": amount, "time": datetime.now()})
            
            # 註冊組件
            trading_component = TestTradingComponent()
            recovery_manager.register_component("trading", trading_component)
            
            # 創建初始快照
            snapshot = recovery_manager.create_snapshot()
            print(f"   ✓ 初始快照創建: {snapshot.snapshot_id}")
            
            # 執行一些操作
            trading_component.execute_trade(100000)
            trading_component.execute_trade(50000)
            print(f"   執行交易後 - 餘額: {trading_component.balance}, 持倉: {trading_component.position}")
            
            # 模擬錯誤
            try:
                trading_component.execute_trade(2000000)  # 超過餘額
            except ValueError as e:
                error_record = error_handler.handle_error(
                    error=e,
                    component="trading",
                    function_name="execute_trade",
                    context_data={"attempted_amount": 2000000}
                )
                print(f"   ✓ 錯誤處理: {error_record.error_id}")
            
            # 恢復到快照
            success = recovery_manager.restore_from_snapshot(snapshot.snapshot_id)
            if success:
                print(f"   ✓ 系統恢復成功")
                print(f"   恢復後 - 餘額: {trading_component.balance}, 持倉: {trading_component.position}")
                
                if trading_component.balance == 1000000 and trading_component.position == 0:
                    print("✅ 錯誤恢復集成測試成功")
                    return True
                else:
                    print("❌ 恢復狀態不正確")
                    return False
            else:
                print("❌ 系統恢復失敗")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 錯誤恢復集成測試失敗: {e}")
        return False

def test_memory_optimization():
    """測試內存優化"""
    print("\n🧪 測試內存優化...")
    try:
        from src.core.dynamic_trading_config import DynamicTradingConfig
        from src.core.dynamic_backtest_engine import DynamicBacktestEngine
        
        # 監控內存使用
        process = psutil.Process()
        
        def get_memory_mb():
            return process.memory_info().rss / 1024 / 1024
        
        initial_memory = get_memory_mb()
        print(f"   初始內存: {initial_memory:.1f} MB")
        
        # 創建多個引擎實例來測試內存管理
        engines = []
        memory_readings = []
        
        for i in range(5):
            config = DynamicTradingConfig()
            engine = DynamicBacktestEngine(config)
            engines.append(engine)
            
            current_memory = get_memory_mb()
            memory_readings.append(current_memory)
            print(f"   引擎 {i+1} 創建後內存: {current_memory:.1f} MB")
        
        # 清理引擎
        for engine in engines:
            engine.cleanup()
        
        engines.clear()
        gc.collect()  # 強制垃圾回收
        
        final_memory = get_memory_mb()
        memory_recovered = memory_readings[-1] - final_memory
        
        print(f"   清理後內存: {final_memory:.1f} MB")
        print(f"   回收內存: {memory_recovered:.1f} MB")
        
        # 檢查內存洩漏
        memory_leak = final_memory - initial_memory
        if memory_leak < 50:  # 允許50MB的內存增長
            print("✅ 內存優化測試通過")
            return True
        else:
            print(f"⚠️ 可能存在內存洩漏: {memory_leak:.1f} MB")
            return False
            
    except Exception as e:
        print(f"❌ 內存優化測試失敗: {e}")
        return False

def test_data_validation():
    """測試數據驗證"""
    print("\n🧪 測試數據驗證...")
    try:
        from src.core.dynamic_backtest_engine import DynamicBacktestEngine
        from src.core.dynamic_trading_config import DynamicTradingConfig
        
        config = DynamicTradingConfig()
        engine = DynamicBacktestEngine(config)
        
        # 測試有效數據
        valid_data = create_comprehensive_test_data(days=1)
        try:
            processed_data = engine._preprocess_data(valid_data)
            print("   ✓ 有效數據處理成功")
        except Exception as e:
            print(f"   ❌ 有效數據處理失敗: {e}")
            return False
        
        # 測試無效數據
        test_cases = [
            ("空數據", pd.DataFrame()),
            ("缺少列", pd.DataFrame({'timestamp': [datetime.now()], 'close': [100]})),
            ("無效數據類型", pd.DataFrame({
                'timestamp': [datetime.now()],
                'open': ['invalid'],
                'high': [100],
                'low': [90],
                'close': [95],
                'volume': [1000]
            }))
        ]
        
        for test_name, invalid_data in test_cases:
            try:
                engine._preprocess_data(invalid_data)
                print(f"   ❌ {test_name} 應該拋出異常")
                return False
            except Exception:
                print(f"   ✓ {test_name} 正確拋出異常")
        
        engine.cleanup()
        print("✅ 數據驗證測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 數據驗證測試失敗: {e}")
        return False

def generate_performance_report():
    """生成性能報告"""
    print("\n📊 生成性能報告...")
    try:
        from src.core.dynamic_trading_config import DynamicTradingConfig
        from src.core.dynamic_backtest_engine import DynamicBacktestEngine
        
        # 不同數據量的性能測試
        test_sizes = [1, 3, 7]  # 天數
        performance_data = []
        
        for days in test_sizes:
            test_data = create_comprehensive_test_data(days=days)
            
            config = DynamicTradingConfig()
            engine = DynamicBacktestEngine(config)
            
            start_time = time.time()
            result = engine.run_backtest(test_data)
            execution_time = time.time() - start_time
            
            performance_data.append({
                'days': days,
                'data_points': len(test_data),
                'execution_time': execution_time,
                'throughput': len(test_data) / execution_time,
                'total_trades': result.total_trades,
                'success_rate': result.success_rate
            })
            
            engine.cleanup()
        
        # 生成報告
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': {
                'platform': os.name,
                'cpu_count': psutil.cpu_count(),
                'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024  # GB
            },
            'performance_tests': performance_data,
            'summary': {
                'max_throughput': max(p['throughput'] for p in performance_data),
                'avg_success_rate': sum(p['success_rate'] for p in performance_data) / len(performance_data),
                'scalability': 'Good' if performance_data[-1]['throughput'] > 1000 else 'Needs Improvement'
            }
        }
        
        # 保存報告
        report_file = f"dynamic_system_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 性能報告已生成: {report_file}")
        print(f"   最大吞吐量: {report['summary']['max_throughput']:.0f} 數據點/秒")
        print(f"   平均成功率: {report['summary']['avg_success_rate']:.1f}%")
        print(f"   可擴展性: {report['summary']['scalability']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能報告生成失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始動態價格追蹤 MACD 系統集成測試和優化...")
    print("=" * 70)
    
    test_results = []
    
    # 執行各項測試
    test_results.append(("系統初始化", test_system_initialization()))
    test_results.append(("端到端回測", test_end_to_end_backtest()))
    test_results.append(("高負載性能", test_performance_under_load()))
    test_results.append(("並發操作", test_concurrent_operations()))
    test_results.append(("錯誤恢復集成", test_error_recovery_integration()))
    test_results.append(("內存優化", test_memory_optimization()))
    test_results.append(("數據驗證", test_data_validation()))
    test_results.append(("性能報告生成", generate_performance_report()))
    
    # 顯示測試結果
    print("\n" + "=" * 70)
    print("📊 系統集成測試結果摘要:")
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{len(test_results)} 項測試通過")
    
    if passed == len(test_results):
        print("\n🎉 所有系統集成測試通過！系統已準備就緒！")
        print("\n📋 系統能力驗證:")
        print("• 完整的端到端回測流程")
        print("• 高負載下的穩定性能")
        print("• 多線程並發處理")
        print("• 完善的錯誤恢復機制")
        print("• 優化的內存管理")
        print("• 嚴格的數據驗證")
        print("• 詳細的性能監控")
        
        print("\n🔧 系統優化建議:")
        print("• 定期監控內存使用情況")
        print("• 根據數據量調整並發參數")
        print("• 定期清理歷史快照文件")
        print("• 監控錯誤率和恢復成功率")
        
    else:
        print(f"\n⚠️  有 {len(test_results) - passed} 項測試失敗，需要進一步優化")
        print("\n🔍 建議檢查:")
        print("• 系統資源配置")
        print("• 依賴組件版本")
        print("• 配置參數設置")
        print("• 錯誤日誌詳情")
    
    print("\n✨ 動態價格追蹤 MACD 系統集成測試完成！")

if __name__ == "__main__":
    main()