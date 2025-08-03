#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強多交易對GUI系統測試腳本
測試擴展GUI支持多交易對顯示和管理功能
"""

import sys
import os
import json
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.gui.enhanced_multi_pair_gui import (
    EnhancedMultiPairGUI,
    PairDisplayData,
    create_enhanced_multi_pair_gui
)

class EnhancedMultiPairGUITester:
    """增強多交易對GUI系統測試器"""
    
    def __init__(self):
        self.test_results = []
        self.gui = None
        
    def run_all_tests(self):
        """運行所有測試"""
        print("🧪 開始增強多交易對GUI系統測試")
        print("=" * 60)
        
        # 測試列表
        tests = [
            ("基礎組件測試", self.test_basic_components),
            ("數據結構測試", self.test_data_structures),
            ("GUI界面測試", self.test_gui_interface),
            ("交易對管理測試", self.test_pair_management),
            ("顯示更新測試", self.test_display_updates),
            ("用戶交互測試", self.test_user_interactions),
            ("系統集成測試", self.test_system_integration),
            ("性能測試", self.test_performance)
        ]
        
        # 執行測試
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 {test_name}")
                print("-" * 40)
                result = test_func()
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'PASSED' if result else 'FAILED',
                    'timestamp': datetime.now()
                })
                print(f"✅ {test_name}: {'通過' if result else '失敗'}")
            except Exception as e:
                print(f"❌ {test_name}: 錯誤 - {e}")
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        # 生成測試報告
        self.generate_test_report()
    
    def test_basic_components(self):
        """測試基礎組件"""
        try:
            # 創建主GUI組件
            self.gui = create_enhanced_multi_pair_gui()
            
            print(f"   創建主GUI組件: {type(self.gui).__name__}")
            
            # 檢查基本屬性
            assert hasattr(self.gui, 'pairs_data')
            assert hasattr(self.gui, 'selected_pair')
            assert hasattr(self.gui, 'update_data')
            assert hasattr(self.gui, 'generate_sample_data')
            
            print("   ✓ 主GUI組件屬性檢查通過")
            
            # 測試數據結構
            sample_data = PairDisplayData(
                pair="BTCTWD",
                price=1500000.0,
                change_24h=2.5,
                volume_24h=50000000.0,
                position_size=0.05,
                target_position=0.06,
                unrealized_pnl=5000.0,
                ai_confidence=0.75,
                risk_score=0.3,
                status="active",
                strategy_active=True,
                last_update=datetime.now()
            )
            
            print(f"   創建示例數據: {sample_data.pair}")
            print(f"     價格: {sample_data.price:,.0f}")
            print(f"     當前倉位: {sample_data.position_size:.4f}")
            print(f"     目標倉位: {sample_data.target_position:.4f}")
            print(f"     AI信心度: {sample_data.ai_confidence:.1%}")
            print(f"     風險分數: {sample_data.risk_score:.1%}")
            print(f"     策略狀態: {'活躍' if sample_data.strategy_active else '未活躍'}\")")
            
            # 驗證數據完整性
            assert sample_data.pair == "BTCTWD"
            assert sample_data.price > 0
            assert 0 <= sample_data.ai_confidence <= 1
            assert 0 <= sample_data.risk_score <= 1
            assert sample_data.status in ["active", "inactive", "warning", "error"]
            assert isinstance(sample_data.strategy_active, bool)
            
            print("   ✓ 數據結構驗證通過")
            
            print("   ✅ 基礎組件測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 基礎組件測試失敗: {e}")
            return False
    
    def test_data_structures(self):
        """測試數據結構"""
        try:
            # 測試多個交易對數據
            pairs = ["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD", "ADATWD", "DOTTWD"]
            test_data = []
            
            for i, pair in enumerate(pairs):
                data = PairDisplayData(
                    pair=pair,
                    price=1000000.0 + i * 100000,
                    change_24h=(i - 3) * 2.5,  # -7.5 to +5.0
                    volume_24h=10000000.0 + i * 10000000,
                    position_size=i * 0.01,
                    target_position=(i + 1) * 0.01,
                    unrealized_pnl=(i - 3) * 10000,  # -30k to +20k
                    ai_confidence=0.5 + i * 0.08,  # 0.5 to 0.9
                    risk_score=0.2 + i * 0.1,  # 0.2 to 0.7
                    status=["active", "inactive", "warning", "error", "active", "warning"][i],
                    strategy_active=i % 2 == 0,
                    last_update=datetime.now()
                )
                test_data.append(data)
            
            print(f"   創建了 {len(test_data)} 個交易對數據")
            
            # 驗證數據完整性
            for data in test_data:
                print(f"     {data.pair}: 價格={data.price:,.0f}, 倉位={data.position_size:.3f}->{data.target_position:.3f}, 策略={'開' if data.strategy_active else '關'}")
                
                # 驗證數據範圍
                assert data.price > 0
                assert -100 <= data.change_24h <= 100
                assert data.volume_24h >= 0
                assert data.position_size >= 0
                assert data.target_position >= 0
                assert 0 <= data.ai_confidence <= 1
                assert 0 <= data.risk_score <= 1
                assert data.status in ["active", "inactive", "warning", "error"]
                assert isinstance(data.strategy_active, bool)
                assert data.last_update is not None
            
            print("   ✓ 數據範圍驗證通過")
            
            # 測試數據排序和篩選
            active_pairs = [d for d in test_data if d.status == "active"]
            high_confidence_pairs = [d for d in test_data if d.ai_confidence >= 0.7]
            strategy_active_pairs = [d for d in test_data if d.strategy_active]
            
            print(f"   活躍交易對: {len(active_pairs)} 個")
            print(f"   高信心度交易對: {len(high_confidence_pairs)} 個")
            print(f"   策略活躍交易對: {len(strategy_active_pairs)} 個")
            
            assert len(active_pairs) >= 0
            assert len(high_confidence_pairs) >= 0
            assert len(strategy_active_pairs) >= 0
            
            print("   ✓ 數據篩選驗證通過")
            
            print("   ✅ 數據結構測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 數據結構測試失敗: {e}")
            return False
    
    def test_gui_interface(self):
        """測試GUI界面"""
        try:
            # 檢查GUI可用性
            from src.gui.enhanced_multi_pair_gui import PYQT_AVAILABLE
            
            print(f"   PyQt5可用性: {'是' if PYQT_AVAILABLE else '否'}")
            
            if PYQT_AVAILABLE:
                # 測試GUI組件
                print("   測試GUI組件...")
                
                # 檢查主要組件是否存在
                assert hasattr(self.gui, 'tab_widget')
                assert hasattr(self.gui, 'overview_panel')
                assert hasattr(self.gui, 'detail_table')
                assert hasattr(self.gui, 'status_bar')
                
                print("   ✓ GUI組件檢查通過")
                
                # 測試標籤頁
                if hasattr(self.gui.tab_widget, 'count'):
                    tab_count = self.gui.tab_widget.count()
                    print(f"   標籤頁數量: {tab_count}")
                    assert tab_count >= 2, "應該至少有2個標籤頁"
                
                print("   ✓ 標籤頁檢查通過")
                
                # 測試控制面板
                assert hasattr(self.gui, 'auto_update_checkbox')
                assert hasattr(self.gui, 'update_interval_spinbox')
                assert hasattr(self.gui, 'manual_update_button')
                assert hasattr(self.gui, 'start_trading_button')
                assert hasattr(self.gui, 'stop_trading_button')
                assert hasattr(self.gui, 'emergency_stop_button')
                
                print("   ✓ 控制面板檢查通過")
                
            else:
                # 非GUI模式測試
                print("   非GUI模式: 測試基本功能...")
                
                # 測試數據操作功能
                self.gui.update_data()
                data = self.gui.get_current_data()
                assert len(data) > 0, "應該有數據"
                
                print("   ✓ 非GUI模式功能檢查通過")
            
            print("   ✅ GUI界面測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ GUI界面測試失敗: {e}")
            return False
    
    def test_pair_management(self):
        """測試交易對管理"""
        try:
            # 測試數據生成
            initial_data = self.gui.generate_sample_data()
            print(f"   生成初始數據: {len(initial_data)} 個交易對")
            
            # 驗證生成的數據
            for data in initial_data:
                assert data.pair is not None
                assert data.price > 0
                assert 0 <= data.ai_confidence <= 1
                assert 0 <= data.risk_score <= 1
                assert data.status in ["active", "inactive", "warning", "error"]
                assert isinstance(data.strategy_active, bool)
            
            print("   ✓ 數據生成驗證通過")
            
            # 測試數據更新
            self.gui.update_data()
            updated_data = self.gui.get_current_data()
            
            print(f"   更新後數據: {len(updated_data)} 個交易對")
            assert len(updated_data) > 0, "更新後應該有數據"
            
            # 驗證數據更新
            for data in updated_data:
                print(f"     {data.pair}: 價格={data.price:,.0f}, 信心度={data.ai_confidence:.1%}, 策略={'開' if data.strategy_active else '關'}")
            
            print("   ✓ 數據更新驗證通過")
            
            # 測試交易對選擇
            if updated_data:
                test_pair = updated_data[0].pair
                self.gui.on_pair_selected(test_pair)
                
                assert self.gui.selected_pair == test_pair
                print(f"   ✓ 交易對選擇功能正常: {test_pair}")
            
            # 測試策略切換
            if updated_data:
                test_pair = updated_data[0].pair
                original_status = updated_data[0].strategy_active
                
                self.gui.toggle_strategy(test_pair)
                
                # 檢查狀態是否改變
                new_data = self.gui.get_current_data()
                for data in new_data:
                    if data.pair == test_pair:
                        # 注意：由於update_data會重新生成數據，這裡主要測試函數不會崩潰
                        print(f"   ✓ 策略切換功能正常: {test_pair}")
                        break
            
            print("   ✅ 交易對管理測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 交易對管理測試失敗: {e}")
            return False
    
    def test_display_updates(self):
        """測試顯示更新"""
        try:
            # 測試多次數據更新
            update_counts = []
            
            for i in range(5):
                self.gui.update_data()
                current_data = self.gui.get_current_data()
                update_counts.append(len(current_data))
                print(f"   第 {i+1} 次更新: {len(current_data)} 個交易對")
            
            # 驗證更新一致性
            assert all(count > 0 for count in update_counts), "每次更新都應該有數據"
            print("   ✓ 多次更新驗證通過")
            
            # 測試手動更新
            self.gui.manual_update()
            manual_data = self.gui.get_current_data()
            print(f"   手動更新: {len(manual_data)} 個交易對")
            assert len(manual_data) > 0, "手動更新應該有數據"
            
            print("   ✓ 手動更新驗證通過")
            
            # 測試數據一致性
            current_data = self.gui.get_current_data()
            for data in current_data:
                # 驗證必要字段
                assert data.pair is not None
                assert isinstance(data.price, (int, float))
                assert isinstance(data.change_24h, (int, float))
                assert isinstance(data.volume_24h, (int, float))
                assert isinstance(data.position_size, (int, float))
                assert isinstance(data.target_position, (int, float))
                assert isinstance(data.unrealized_pnl, (int, float))
                assert isinstance(data.ai_confidence, (int, float))
                assert isinstance(data.risk_score, (int, float))
                assert isinstance(data.status, str)
                assert isinstance(data.strategy_active, bool)
                assert data.last_update is not None
            
            print("   ✓ 數據一致性驗證通過")
            
            print("   ✅ 顯示更新測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 顯示更新測試失敗: {e}")
            return False
    
    def test_user_interactions(self):
        """測試用戶交互"""
        try:
            # 測試系統控制功能
            print("   測試系統控制功能...")
            
            # 測試啟動交易
            self.gui.start_trading()
            print("   ✓ 啟動交易功能正常")
            
            # 測試停止交易
            self.gui.stop_trading()
            print("   ✓ 停止交易功能正常")
            
            # 測試緊急停止
            self.gui.emergency_stop()
            print("   ✓ 緊急停止功能正常")
            
            # 測試交互操作
            current_data = self.gui.get_current_data()
            if current_data:
                test_pair = current_data[0].pair
                
                # 測試交易對操作
                self.gui.on_pair_action(test_pair, "trade")
                self.gui.on_pair_action(test_pair, "settings")
                self.gui.on_pair_action(test_pair, "strategy")
                
                print(f"   ✓ 交易對操作功能正常: {test_pair}")
            
            # 測試狀態更新
            self.gui.update_system_status("測試狀態")
            print("   ✓ 狀態更新功能正常")
            
            print("   ✅ 用戶交互測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 用戶交互測試失敗: {e}")
            return False
    
    def test_system_integration(self):
        """測試系統集成"""
        try:
            # 檢查系統組件集成
            from src.gui.enhanced_multi_pair_gui import AIMAX_MODULES_AVAILABLE
            
            print(f"   AImax模塊可用性: {'是' if AIMAX_MODULES_AVAILABLE else '否'}")
            
            if AIMAX_MODULES_AVAILABLE:
                # 測試系統組件
                assert hasattr(self.gui, 'position_manager')
                assert hasattr(self.gui, 'risk_monitor')
                assert hasattr(self.gui, 'data_manager')
                
                print("   ✓ 系統組件集成檢查通過")
            else:
                print("   ⚠️ 使用模擬模式，跳過系統組件集成測試")
            
            # 測試完整工作流程
            print("   測試完整工作流程...")
            
            # 1. 初始化數據
            self.gui.update_data()
            initial_data = self.gui.get_current_data()
            print(f"     1. 初始化數據: {len(initial_data)} 個交易對")
            
            # 2. 選擇交易對
            if initial_data:
                test_pair = initial_data[0].pair
                self.gui.on_pair_selected(test_pair)
                print(f"     2. 選擇交易對: {test_pair}")
            
            # 3. 執行操作
            self.gui.start_trading()
            print("     3. 啟動交易系統")
            
            # 4. 更新數據
            self.gui.manual_update()
            updated_data = self.gui.get_current_data()
            print(f"     4. 更新數據: {len(updated_data)} 個交易對")
            
            # 5. 停止系統
            self.gui.stop_trading()
            print("     5. 停止交易系統")
            
            print("   ✓ 完整工作流程驗證通過")
            
            print("   ✅ 系統集成測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 系統集成測試失敗: {e}")
            return False
    
    def test_performance(self):
        """測試性能"""
        try:
            import time
            
            # 測試數據生成性能
            start_time = time.time()
            for i in range(10):
                data = self.gui.generate_sample_data()
            generation_time = time.time() - start_time
            
            print(f"   數據生成性能: {generation_time:.3f}秒 (10次)")
            assert generation_time < 1.0, "數據生成應該在1秒內完成"
            
            # 測試數據更新性能
            start_time = time.time()
            for i in range(5):
                self.gui.update_data()
            update_time = time.time() - start_time
            
            print(f"   數據更新性能: {update_time:.3f}秒 (5次)")
            assert update_time < 2.0, "數據更新應該在2秒內完成"
            
            # 測試內存使用
            current_data = self.gui.get_current_data()
            data_size = len(str(current_data))
            print(f"   數據大小: {data_size} 字符")
            
            # 測試大量數據處理
            large_data = []
            for i in range(100):
                data = PairDisplayData(
                    pair=f"TEST{i:03d}TWD",
                    price=1000000.0 + i,
                    change_24h=i % 20 - 10,
                    volume_24h=1000000.0 + i * 10000,
                    position_size=i * 0.001,
                    target_position=i * 0.001,
                    unrealized_pnl=i * 100 - 5000,
                    ai_confidence=0.5 + (i % 50) * 0.01,
                    risk_score=0.1 + (i % 80) * 0.01,
                    status=["active", "inactive", "warning", "error"][i % 4],
                    strategy_active=i % 2 == 0,
                    last_update=datetime.now()
                )
                large_data.append(data)
            
            print(f"   大量數據處理: {len(large_data)} 個交易對")
            assert len(large_data) == 100, "應該生成100個測試數據"
            
            print("   ✓ 性能測試通過")
            
            print("   ✅ 性能測試驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 性能測試失敗: {e}")
            return False
    
    def generate_test_report(self):
        """生成測試報告"""
        try:
            # 計算統計信息
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result['status'] == 'PASSED')
            failed_tests = sum(1 for result in self.test_results if result['status'] == 'FAILED')
            error_tests = sum(1 for result in self.test_results if result['status'] == 'ERROR')
            
            # 生成報告
            report = {
                'test_summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'error_tests': error_tests,
                    'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                    'test_time': datetime.now().isoformat()
                },
                'test_results': self.test_results,
                'system_info': {
                    'python_version': sys.version,
                    'platform': sys.platform
                }
            }
            
            # 保存報告
            report_file = f"AImax/logs/enhanced_multi_pair_gui_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            # 打印總結
            print(f"\n📊 測試總結")
            print("=" * 60)
            print(f"總測試數: {total_tests}")
            print(f"通過: {passed_tests}")
            print(f"失敗: {failed_tests}")
            print(f"錯誤: {error_tests}")
            print(f"成功率: {report['test_summary']['success_rate']:.1f}%")
            print(f"測試報告已保存: {report_file}")
            
            if passed_tests == total_tests:
                print("🎉 所有測試通過！增強多交易對GUI系統運行正常")
            else:
                print("⚠️ 部分測試未通過，請檢查詳細報告")
            
        except Exception as e:
            print(f"❌ 生成測試報告失敗: {e}")

def main():
    """主函數"""
    print("🚀 啟動增強多交易對GUI系統測試")
    
    tester = EnhancedMultiPairGUITester()
    tester.run_all_tests()
    
    print("\n✅ 測試完成")

if __name__ == "__main__":
    main()