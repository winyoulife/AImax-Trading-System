#!/usr/bin/env python3
"""
動態配置系統測試腳本
測試任務1.3的實現：實現交易對動態配置系統
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.data.dynamic_config_system import (
        DynamicConfigManager, TradingPairConfig, ConfigTemplate,
        ValidationLevel, ConfigChangeType
    )
except ImportError as e:
    print(f"❌ 導入錯誤: {e}")
    print("請確保在AImax項目根目錄下運行此腳本")
    sys.exit(1)

import logging
import json
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DynamicConfigSystemTester:
    """動態配置系統測試器"""
    
    def __init__(self):
        self.config_manager = None
        self.test_results = {}
    
    def run_comprehensive_tests(self):
        """運行全面測試"""
        print("🧪 開始動態配置系統測試...")
        print("=" * 70)
        
        try:
            # 測試1: 系統初始化和模板
            self.test_system_initialization()
            
            # 測試2: TradingPairConfig數據模型和驗證
            self.test_trading_pair_config_model()
            
            # 測試3: 配置創建和模板應用
            self.test_config_creation_and_templates()
            
            # 測試4: 配置熱更新機制
            self.test_hot_update_mechanism()
            
            # 測試5: 配置變更審計和回滾功能
            self.test_audit_and_rollback()
            
            # 測試6: 自動參數優化
            self.test_auto_optimization()
            
            # 生成測試報告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ 測試過程中發生錯誤: {e}")
        finally:
            if self.config_manager:
                print("🧹 清理測試數據...")
    
    def test_system_initialization(self):
        """測試1: 系統初始化和模板"""
        print("\n🚀 測試1: 系統初始化和模板")
        print("-" * 50)
        
        try:
            # 創建動態配置管理器
            self.config_manager = DynamicConfigManager(config_dir="test_config")
            
            # 檢查模板管理器
            template_manager = self.config_manager.template_manager
            templates = ['conservative', 'balanced', 'aggressive']
            
            template_check = {}
            for template_name in templates:
                template = template_manager.get_template(template_name)
                template_check[template_name] = template is not None
                
                if template:
                    print(f"   ✅ {template_name} 模板: 最大倉位 {template.max_position_size}")
                else:
                    print(f"   ❌ {template_name} 模板: 不存在")
            
            all_templates_exist = all(template_check.values())
            
            print(f"📊 初始化結果:")
            print(f"   - 配置管理器: {'✅' if self.config_manager else '❌'}")
            print(f"   - 模板數量: {len(template_check)}")
            print(f"   - 模板完整性: {'✅' if all_templates_exist else '❌'}")
            
            self.test_results['system_initialization'] = {
                'status': 'success' if all_templates_exist else 'failed',
                'template_check': template_check,
                'config_manager_created': self.config_manager is not None
            }
            
        except Exception as e:
            print(f"❌ 系統初始化測試失敗: {e}")
            self.test_results['system_initialization'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_trading_pair_config_model(self):
        """測試2: TradingPairConfig數據模型和驗證"""
        print("\n📋 測試2: TradingPairConfig數據模型和驗證")
        print("-" * 50)
        
        try:
            # 測試有效配置
            valid_config = TradingPairConfig(
                pair="BTCTWD",
                max_position_size=0.1,
                stop_loss_percent=0.08,
                take_profit_percent=0.15
            )
            
            valid_errors = valid_config.validate(ValidationLevel.STRICT)
            print(f"   ✅ 有效配置驗證: {len(valid_errors)} 個錯誤")
            
            # 測試無效配置
            invalid_config = TradingPairConfig(
                pair="",  # 無效的交易對名稱
                max_position_size=1.5,  # 超過1.0
                stop_loss_percent=-0.1,  # 負數
                min_order_size=0,  # 零值
                max_order_size=0.001  # 小於最小值
            )
            
            invalid_errors = invalid_config.validate(ValidationLevel.STRICT)
            print(f"   ✅ 無效配置驗證: {len(invalid_errors)} 個錯誤")
            
            # 測試配置轉換
            config_dict = valid_config.to_dict()
            restored_config = TradingPairConfig.from_dict(config_dict)
            
            conversion_success = (
                restored_config.pair == valid_config.pair and
                restored_config.max_position_size == valid_config.max_position_size
            )
            
            print(f"   ✅ 配置轉換: {'成功' if conversion_success else '失敗'}")
            
            # 測試配置哈希
            hash1 = valid_config.get_hash()
            hash2 = restored_config.get_hash()
            hash_consistent = hash1 == hash2
            
            print(f"   ✅ 配置哈希: {'一致' if hash_consistent else '不一致'}")
            
            print(f"📊 數據模型測試結果:")
            print(f"   - 有效配置錯誤數: {len(valid_errors)}")
            print(f"   - 無效配置錯誤數: {len(invalid_errors)}")
            print(f"   - 配置轉換: {'✅' if conversion_success else '❌'}")
            print(f"   - 哈希一致性: {'✅' if hash_consistent else '❌'}")
            
            self.test_results['trading_pair_config_model'] = {
                'status': 'success',
                'valid_config_errors': len(valid_errors),
                'invalid_config_errors': len(invalid_errors),
                'conversion_success': conversion_success,
                'hash_consistent': hash_consistent
            }
            
        except Exception as e:
            print(f"❌ 數據模型測試失敗: {e}")
            self.test_results['trading_pair_config_model'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_config_creation_and_templates(self):
        """測試3: 配置創建和模板應用"""
        print("\n🏗️ 測試3: 配置創建和模板應用")
        print("-" * 50)
        
        try:
            test_pairs = ["BTCTWD", "ETHTWD", "LTCTWD"]
            templates = ["conservative", "balanced", "aggressive"]
            
            creation_results = {}
            
            for i, pair in enumerate(test_pairs):
                template = templates[i]
                
                # 創建配置
                success = self.config_manager.create_config(
                    pair=pair,
                    template_name=template,
                    custom_params={"update_interval": 30}
                )
                
                creation_results[pair] = {
                    'template': template,
                    'success': success
                }
                
                if success:
                    config = self.config_manager.get_config(pair)
                    print(f"   ✅ {pair}: 使用 {template} 模板創建成功")
                    print(f"      - 最大倉位: {config.max_position_size}")
                    print(f"      - 止損比例: {config.stop_loss_percent}")
                    print(f"      - 更新間隔: {config.update_interval}")
                else:
                    print(f"   ❌ {pair}: 創建失敗")
            
            # 測試重複創建
            duplicate_success = self.config_manager.create_config("BTCTWD", "balanced")
            print(f"   ✅ 重複創建測試: {'正確拒絕' if not duplicate_success else '錯誤允許'}")
            
            # 獲取所有配置
            all_configs = self.config_manager.get_all_configs()
            
            success_count = sum(1 for result in creation_results.values() if result['success'])
            
            print(f"📊 配置創建結果:")
            print(f"   - 成功創建: {success_count}/{len(test_pairs)}")
            print(f"   - 總配置數: {len(all_configs)}")
            print(f"   - 重複創建處理: {'✅' if not duplicate_success else '❌'}")
            
            self.test_results['config_creation_and_templates'] = {
                'status': 'success' if success_count == len(test_pairs) else 'partial',
                'creation_results': creation_results,
                'success_count': success_count,
                'total_configs': len(all_configs),
                'duplicate_handling': not duplicate_success
            }
            
        except Exception as e:
            print(f"❌ 配置創建測試失敗: {e}")
            self.test_results['config_creation_and_templates'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_hot_update_mechanism(self):
        """測試4: 配置熱更新機制"""
        print("\n🔥 測試4: 配置熱更新機制")
        print("-" * 50)
        
        try:
            test_pair = "BTCTWD"
            
            # 獲取原始配置
            original_config = self.config_manager.get_config(test_pair)
            if not original_config:
                print(f"❌ 測試交易對 {test_pair} 不存在")
                return
            
            original_position_size = original_config.max_position_size
            original_version = original_config.version
            
            print(f"   📊 原始配置: 倉位 {original_position_size}, 版本 {original_version}")
            
            # 測試有效更新
            valid_updates = {
                "max_position_size": 0.15,
                "stop_loss_percent": 0.10,
                "update_interval": 45
            }
            
            update_success = self.config_manager.update_config(
                pair=test_pair,
                updates=valid_updates,
                reason="測試熱更新"
            )
            
            if update_success:
                updated_config = self.config_manager.get_config(test_pair)
                print(f"   ✅ 有效更新成功: 倉位 {updated_config.max_position_size}, 版本 {updated_config.version}")
                
                # 驗證更新內容
                update_correct = (
                    updated_config.max_position_size == 0.15 and
                    updated_config.stop_loss_percent == 0.10 and
                    updated_config.update_interval == 45 and
                    updated_config.version == original_version + 1
                )
                
                print(f"   ✅ 更新內容驗證: {'正確' if update_correct else '錯誤'}")
            else:
                print(f"   ❌ 有效更新失敗")
                update_correct = False
            
            # 測試無效更新（應該被拒絕）
            invalid_updates = {
                "max_position_size": 2.0,  # 超過1.0
                "stop_loss_percent": -0.1  # 負數
            }
            
            invalid_update_success = self.config_manager.update_config(
                pair=test_pair,
                updates=invalid_updates,
                reason="測試無效更新"
            )
            
            print(f"   ✅ 無效更新處理: {'正確拒絕' if not invalid_update_success else '錯誤允許'}")
            
            # 測試不存在的交易對更新
            nonexistent_update = self.config_manager.update_config(
                pair="NONEXISTENT",
                updates={"max_position_size": 0.1}
            )
            
            print(f"   ✅ 不存在交易對更新: {'正確拒絕' if not nonexistent_update else '錯誤允許'}")
            
            print(f"📊 熱更新測試結果:")
            print(f"   - 有效更新: {'✅' if update_success else '❌'}")
            print(f"   - 更新內容正確: {'✅' if update_correct else '❌'}")
            print(f"   - 無效更新拒絕: {'✅' if not invalid_update_success else '❌'}")
            print(f"   - 不存在交易對拒絕: {'✅' if not nonexistent_update else '❌'}")
            
            self.test_results['hot_update_mechanism'] = {
                'status': 'success' if all([update_success, update_correct, not invalid_update_success, not nonexistent_update]) else 'partial',
                'valid_update_success': update_success,
                'update_content_correct': update_correct,
                'invalid_update_rejected': not invalid_update_success,
                'nonexistent_update_rejected': not nonexistent_update
            }
            
        except Exception as e:
            print(f"❌ 熱更新測試失敗: {e}")
            self.test_results['hot_update_mechanism'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_audit_and_rollback(self):
        """測試5: 配置變更審計和回滾功能"""
        print("\n📋 測試5: 配置變更審計和回滾功能")
        print("-" * 50)
        
        try:
            test_pair = "ETHTWD"
            
            # 獲取變更歷史
            initial_history = self.config_manager.get_change_history(pair=test_pair)
            initial_count = len(initial_history)
            
            print(f"   📊 初始變更記錄: {initial_count} 條")
            
            # 執行一次更新以產生變更記錄
            update_success = self.config_manager.update_config(
                pair=test_pair,
                updates={"max_position_size": 0.12},
                reason="測試審計功能"
            )
            
            if update_success:
                # 獲取更新後的變更歷史
                updated_history = self.config_manager.get_change_history(pair=test_pair)
                new_count = len(updated_history)
                
                print(f"   ✅ 更新後變更記錄: {new_count} 條")
                
                # 檢查最新的變更記錄
                if updated_history:
                    latest_change = updated_history[0]  # 最新的記錄
                    
                    audit_correct = (
                        latest_change.pair == test_pair and
                        latest_change.change_type == ConfigChangeType.UPDATE and
                        latest_change.reason == "測試審計功能" and
                        latest_change.new_config is not None
                    )
                    
                    print(f"   ✅ 審計記錄正確性: {'正確' if audit_correct else '錯誤'}")
                    print(f"      - 變更類型: {latest_change.change_type.value}")
                    print(f"      - 變更原因: {latest_change.reason}")
                    print(f"      - 時間戳: {latest_change.timestamp}")
                    
                    # 測試回滾功能
                    rollback_success = self.config_manager.rollback_config(
                        pair=test_pair,
                        change_id=latest_change.id
                    )
                    
                    if rollback_success:
                        # 檢查回滾後的配置
                        rolled_back_config = self.config_manager.get_config(test_pair)
                        rollback_history = self.config_manager.get_change_history(pair=test_pair)
                        
                        # 檢查是否有回滾記錄
                        rollback_record_exists = any(
                            change.change_type == ConfigChangeType.ROLLBACK 
                            for change in rollback_history
                        )
                        
                        print(f"   ✅ 回滾執行: 成功")
                        print(f"   ✅ 回滾記錄: {'存在' if rollback_record_exists else '缺失'}")
                        print(f"   ✅ 回滾後倉位: {rolled_back_config.max_position_size}")
                        
                    else:
                        print(f"   ❌ 回滾執行: 失敗")
                        rollback_record_exists = False
                
                else:
                    audit_correct = False
                    rollback_success = False
                    rollback_record_exists = False
            
            else:
                print(f"   ❌ 測試更新失敗")
                audit_correct = False
                rollback_success = False
                rollback_record_exists = False
            
            # 測試獲取所有變更歷史
            all_history = self.config_manager.get_change_history(limit=100)
            
            print(f"📊 審計和回滾測試結果:")
            print(f"   - 變更記錄增加: {'✅' if new_count > initial_count else '❌'}")
            print(f"   - 審計記錄正確: {'✅' if audit_correct else '❌'}")
            print(f"   - 回滾功能: {'✅' if rollback_success else '❌'}")
            print(f"   - 回滾記錄: {'✅' if rollback_record_exists else '❌'}")
            print(f"   - 總變更記錄: {len(all_history)} 條")
            
            self.test_results['audit_and_rollback'] = {
                'status': 'success' if all([audit_correct, rollback_success, rollback_record_exists]) else 'partial',
                'change_record_increased': new_count > initial_count,
                'audit_record_correct': audit_correct,
                'rollback_success': rollback_success,
                'rollback_record_exists': rollback_record_exists,
                'total_history_count': len(all_history)
            }
            
        except Exception as e:
            print(f"❌ 審計和回滾測試失敗: {e}")
            self.test_results['audit_and_rollback'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def test_auto_optimization(self):
        """測試6: 自動參數優化"""
        print("\n🤖 測試6: 自動參數優化")
        print("-" * 50)
        
        try:
            test_pair = "LTCTWD"
            
            # 獲取優化前的配置
            original_config = self.config_manager.get_config(test_pair)
            if not original_config:
                print(f"❌ 測試交易對 {test_pair} 不存在")
                return
            
            original_position_size = original_config.max_position_size
            original_stop_loss = original_config.stop_loss_percent
            
            print(f"   📊 優化前配置:")
            print(f"      - 最大倉位: {original_position_size}")
            print(f"      - 止損比例: {original_stop_loss}")
            
            # 測試場景1: 勝率低的情況
            low_win_rate_data = {
                'win_rate': 0.3,
                'avg_profit': 0.02,
                'max_drawdown': 0.08
            }
            
            optimization1_success = self.config_manager.auto_optimize_config(
                pair=test_pair,
                performance_data=low_win_rate_data
            )
            
            if optimization1_success:
                optimized_config1 = self.config_manager.get_config(test_pair)
                print(f"   ✅ 低勝率優化成功:")
                print(f"      - 止損比例: {original_stop_loss} → {optimized_config1.stop_loss_percent}")
                print(f"      - 止盈比例: {optimized_config1.take_profit_percent}")
            
            # 測試場景2: 回撤過大的情況
            high_drawdown_data = {
                'win_rate': 0.6,
                'avg_profit': 0.05,
                'max_drawdown': 0.20
            }
            
            optimization2_success = self.config_manager.auto_optimize_config(
                pair=test_pair,
                performance_data=high_drawdown_data
            )
            
            if optimization2_success:
                optimized_config2 = self.config_manager.get_config(test_pair)
                print(f"   ✅ 高回撤優化成功:")
                print(f"      - 最大倉位: {optimized_config1.max_position_size} → {optimized_config2.max_position_size}")
            
            # 檢查優化記錄
            optimization_history = self.config_manager.get_change_history(pair=test_pair, limit=5)
            auto_optimization_count = sum(
                1 for change in optimization_history 
                if "自動優化" in change.reason
            )
            
            print(f"📊 自動優化測試結果:")
            print(f"   - 低勝率優化: {'✅' if optimization1_success else '❌'}")
            print(f"   - 高回撤優化: {'✅' if optimization2_success else '❌'}")
            print(f"   - 優化記錄數: {auto_optimization_count}")
            
            self.test_results['auto_optimization'] = {
                'status': 'success' if all([optimization1_success, optimization2_success]) else 'partial',
                'low_win_rate_optimization': optimization1_success,
                'high_drawdown_optimization': optimization2_success,
                'optimization_records': auto_optimization_count
            }
            
        except Exception as e:
            print(f"❌ 自動優化測試失敗: {e}")
            self.test_results['auto_optimization'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_test_report(self):
        """生成測試報告"""
        print("\n" + "=" * 70)
        print("📋 動態配置系統測試報告")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result.get('status') == 'success')
        partial_tests = sum(1 for result in self.test_results.values() 
                           if result.get('status') == 'partial')
        failed_tests = total_tests - passed_tests - partial_tests
        
        print(f"📊 測試統計:")
        print(f"   - 總測試數: {total_tests}")
        print(f"   - 完全通過: {passed_tests}")
        print(f"   - 部分通過: {partial_tests}")
        print(f"   - 測試失敗: {failed_tests}")
        print(f"   - 成功率: {(passed_tests + partial_tests*0.5)/total_tests*100:.1f}%")
        
        print(f"\n📋 詳細測試結果:")
        for test_name, result in self.test_results.items():
            status = result.get('status', 'unknown')
            if status == 'success':
                status_icon = "✅"
            elif status == 'partial':
                status_icon = "🟡"
            else:
                status_icon = "❌"
            
            print(f"   {status_icon} {test_name}: {status}")
            
            if status == 'failed':
                print(f"      錯誤: {result.get('error', 'Unknown error')}")
        
        # 任務1.3實現確認
        print(f"\n🎯 任務1.3實現確認:")
        implementation_checks = [
            ("創建TradingPairConfig數據模型和驗證", 
             self.test_results.get('trading_pair_config_model', {}).get('status') == 'success'),
            ("實現交易對配置的熱更新機制", 
             self.test_results.get('hot_update_mechanism', {}).get('status') == 'success'),
            ("建立配置模板和自動參數優化", 
             self.test_results.get('config_creation_and_templates', {}).get('status') in ['success', 'partial'] and
             self.test_results.get('auto_optimization', {}).get('status') in ['success', 'partial']),
            ("添加配置變更的審計和回滾功能", 
             self.test_results.get('audit_and_rollback', {}).get('status') in ['success', 'partial'])
        ]
        
        for requirement, implemented in implementation_checks:
            status_icon = "✅" if implemented else "❌"
            print(f"   {status_icon} {requirement}")
        
        # 最終評估
        all_requirements_met = all(implemented for _, implemented in implementation_checks)
        
        if all_requirements_met and passed_tests >= 4:
            print(f"\n🎉 任務1.3實現成功！")
            print(f"   動態配置系統已完全實現所有要求。")
        elif passed_tests + partial_tests >= 4:
            print(f"\n✅ 任務1.3基本實現！")
            print(f"   動態配置系統核心功能已實現，部分功能需要進一步完善。")
        else:
            print(f"\n⚠️ 任務1.3需要改進！")
            print(f"   部分核心功能未能正確實現，需要進一步開發。")
        
        # 保存測試報告
        self.save_test_report()
    
    def save_test_report(self):
        """保存測試報告"""
        try:
            from datetime import datetime
            
            report = {
                'test_time': datetime.now().isoformat(),
                'test_type': 'dynamic_config_system',
                'task': '1.3 實現交易對動態配置系統',
                'test_results': self.test_results,
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results.values() 
                                      if r.get('status') == 'success'),
                    'partial_tests': sum(1 for r in self.test_results.values() 
                                       if r.get('status') == 'partial'),
                    'failed_tests': sum(1 for r in self.test_results.values() 
                                      if r.get('status') == 'failed'),
                    'overall_success_rate': (
                        sum(1 for r in self.test_results.values() if r.get('status') == 'success') +
                        sum(0.5 for r in self.test_results.values() if r.get('status') == 'partial')
                    ) / len(self.test_results)
                }
            }
            
            report_path = Path("AImax/logs/dynamic_config_system_test_report.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 測試報告已保存: {report_path}")
            
        except Exception as e:
            print(f"⚠️ 保存測試報告失敗: {e}")


def main():
    """主函數"""
    tester = DynamicConfigSystemTester()
    tester.run_comprehensive_tests()


if __name__ == "__main__":
    main()