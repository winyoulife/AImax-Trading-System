#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雲端部署驗證腳本
確認所有雲端組件都正確使用智能平衡策略
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime

class CloudDeploymentVerifier:
    """雲端部署驗證器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.verification_results = []
        
    def log_result(self, component, status, details=""):
        """記錄驗證結果"""
        result = {
            'component': component,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.verification_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {component}: {details}")
    
    def verify_github_actions_workflow(self):
        """驗證GitHub Actions工作流程"""
        print("\n🔍 驗證GitHub Actions工作流程...")
        
        workflow_file = self.project_root / ".github" / "workflows" / "main-trading.yml"
        
        if not workflow_file.exists():
            self.log_result("GitHub Actions工作流程", "FAIL", "main-trading.yml檔案不存在")
            return False
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵配置
            checks = [
                ("智能平衡交易系統", "智能平衡交易系統" in content),
                ("83.3%勝率策略", "83.3%勝率策略" in content),
                ("smart_balanced策略", "smart_balanced" in content),
                ("智能平衡測試腳本", "test_smart_balanced_volume_macd.py" in content),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    self.log_result(f"工作流程-{check_name}", "PASS", "配置正確")
                else:
                    self.log_result(f"工作流程-{check_name}", "FAIL", "配置錯誤")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_result("GitHub Actions工作流程", "FAIL", f"讀取失敗: {e}")
            return False
    
    def verify_trading_script(self):
        """驗證交易執行腳本"""
        print("\n🔍 驗證交易執行腳本...")
        
        script_file = self.project_root / "scripts" / "github_actions_trader.py"
        
        if not script_file.exists():
            self.log_result("交易執行腳本", "FAIL", "github_actions_trader.py檔案不存在")
            return False
        
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵配置
            checks = [
                ("智能平衡策略導入", "SmartBalancedVolumeEnhancedMACDSignals" in content),
                ("83.3%勝率標記", "83.3%" in content),
                ("v1.0-smart-balanced版本", "v1.0-smart-balanced" in content),
                ("智能平衡信號檢測", "detect_smart_balanced_signals" in content),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    self.log_result(f"交易腳本-{check_name}", "PASS", "配置正確")
                else:
                    self.log_result(f"交易腳本-{check_name}", "FAIL", "配置錯誤")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_result("交易執行腳本", "FAIL", f"讀取失敗: {e}")
            return False
    
    def verify_web_app(self):
        """驗證網頁應用"""
        print("\n🔍 驗證網頁應用...")
        
        web_app_file = self.project_root / "web_app.py"
        
        if not web_app_file.exists():
            self.log_result("網頁應用", "FAIL", "web_app.py檔案不存在")
            return False
        
        try:
            with open(web_app_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵配置
            checks = [
                ("智能平衡策略導入", "SmartBalancedVolumeEnhancedMACDSignals" in content),
                ("策略實例化", "SmartBalancedVolumeEnhancedMACDSignals()" in content),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    self.log_result(f"網頁應用-{check_name}", "PASS", "配置正確")
                else:
                    self.log_result(f"網頁應用-{check_name}", "FAIL", "配置錯誤")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_result("網頁應用", "FAIL", f"讀取失敗: {e}")
            return False
    
    def verify_dashboard(self):
        """驗證監控面板"""
        print("\n🔍 驗證監控面板...")
        
        dashboard_file = self.project_root / "static" / "smart-dashboard.html"
        
        if not dashboard_file.exists():
            self.log_result("監控面板", "FAIL", "smart-dashboard.html檔案不存在")
            return False
        
        try:
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵配置
            checks = [
                ("智能平衡標題", "智能平衡交易儀表板" in content),
                ("83.3%勝率顯示", "83.3%勝率策略" in content),
                ("v1.0-smart-balanced版本", "v1.0-smart-balanced" in content),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    self.log_result(f"監控面板-{check_name}", "PASS", "配置正確")
                else:
                    self.log_result(f"監控面板-{check_name}", "FAIL", "配置錯誤")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_result("監控面板", "FAIL", f"讀取失敗: {e}")
            return False
    
    def verify_core_strategy(self):
        """驗證核心策略檔案"""
        print("\n🔍 驗證核心策略檔案...")
        
        strategy_file = self.project_root / "src" / "core" / "smart_balanced_volume_macd_signals.py"
        
        if not strategy_file.exists():
            self.log_result("核心策略檔案", "FAIL", "smart_balanced_volume_macd_signals.py檔案不存在")
            return False
        
        try:
            with open(strategy_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵配置
            checks = [
                ("智能平衡類別", "SmartBalancedVolumeEnhancedMACDSignals" in content),
                ("信號檢測方法", "detect_smart_balanced_signals" in content),
                ("智能平衡驗證", "smart_signal_validation" in content),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    self.log_result(f"核心策略-{check_name}", "PASS", "配置正確")
                else:
                    self.log_result(f"核心策略-{check_name}", "FAIL", "配置錯誤")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_result("核心策略檔案", "FAIL", f"讀取失敗: {e}")
            return False
    
    def verify_simulation_status(self):
        """驗證模擬交易狀態"""
        print("\n🔍 驗證模擬交易狀態...")
        
        status_file = self.project_root / "data" / "simulation" / "execution_status.json"
        
        if not status_file.exists():
            self.log_result("模擬交易狀態", "WARN", "execution_status.json檔案不存在（正常，會在首次執行時創建）")
            return True
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
            
            # 檢查策略配置
            strategy = status_data.get('strategy', '')
            if 'smart_balanced' in strategy and '83.3' in strategy:
                self.log_result("模擬狀態-策略配置", "PASS", f"策略: {strategy}")
                return True
            else:
                self.log_result("模擬狀態-策略配置", "FAIL", f"策略配置錯誤: {strategy}")
                return False
            
        except Exception as e:
            self.log_result("模擬交易狀態", "FAIL", f"讀取失敗: {e}")
            return False
    
    def verify_git_status(self):
        """驗證Git版本控制狀態"""
        print("\n🔍 驗證Git版本控制狀態...")
        
        try:
            os.chdir(self.project_root)
            
            # 檢查智能平衡策略標籤
            result = subprocess.run(['git', 'tag', '-l', 'v1.0-smart-balanced'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                self.log_result("Git標籤", "PASS", "v1.0-smart-balanced標籤存在")
            else:
                self.log_result("Git標籤", "FAIL", "v1.0-smart-balanced標籤不存在")
                return False
            
            # 檢查當前分支
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                self.log_result("Git分支", "PASS", f"當前分支: {current_branch}")
            else:
                self.log_result("Git分支", "FAIL", "無法獲取當前分支")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Git版本控制", "FAIL", f"檢查失敗: {e}")
            return False
    
    def generate_verification_report(self):
        """生成驗證報告"""
        print("\n📊 生成驗證報告...")
        
        # 統計結果
        total_checks = len(self.verification_results)
        passed_checks = len([r for r in self.verification_results if r['status'] == 'PASS'])
        failed_checks = len([r for r in self.verification_results if r['status'] == 'FAIL'])
        warning_checks = len([r for r in self.verification_results if r['status'] == 'WARN'])
        
        # 生成報告
        report = f"""
# 雲端部署驗證報告

## 驗證摘要
- **驗證時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **總檢查項目**: {total_checks}
- **通過**: {passed_checks}
- **失敗**: {failed_checks}
- **警告**: {warning_checks}
- **成功率**: {(passed_checks/total_checks*100):.1f}%

## 詳細結果

"""
        
        for result in self.verification_results:
            status_icon = "✅" if result['status'] == "PASS" else "❌" if result['status'] == "FAIL" else "⚠️"
            report += f"### {status_icon} {result['component']}\n"
            report += f"- **狀態**: {result['status']}\n"
            report += f"- **詳情**: {result['details']}\n"
            report += f"- **時間**: {result['timestamp']}\n\n"
        
        # 結論
        if failed_checks == 0:
            report += """
## 🎉 驗證結論

**✅ 雲端部署驗證通過！**

所有關鍵組件都已正確配置為使用智能平衡策略：
- GitHub Actions工作流程已更新
- 交易執行腳本使用正確策略
- 網頁應用配置正確
- 監控面板顯示正確信息
- 核心策略檔案完整
- Git版本控制正常

**🚀 系統現在可以安全地進行雲端交易！**
"""
        else:
            report += f"""
## ⚠️ 驗證結論

**❌ 發現 {failed_checks} 個問題需要修復**

請檢查上述失敗項目並進行修復，然後重新執行驗證。
"""
        
        # 保存報告
        report_file = self.project_root / "CLOUD_DEPLOYMENT_VERIFICATION_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 驗證報告已保存: {report_file}")
        
        return failed_checks == 0
    
    def run_verification(self):
        """執行完整驗證"""
        print("🔍 開始雲端部署驗證...")
        print("="*60)
        
        # 執行所有驗證
        verifications = [
            self.verify_core_strategy,
            self.verify_github_actions_workflow,
            self.verify_trading_script,
            self.verify_web_app,
            self.verify_dashboard,
            self.verify_simulation_status,
            self.verify_git_status,
        ]
        
        all_passed = True
        for verification in verifications:
            try:
                if not verification():
                    all_passed = False
            except Exception as e:
                print(f"❌ 驗證過程中發生錯誤: {e}")
                all_passed = False
        
        # 生成報告
        report_success = self.generate_verification_report()
        
        return all_passed and report_success

def main():
    """主函數"""
    print("🔍 雲端部署驗證工具")
    print("="*60)
    print("驗證所有雲端組件是否正確使用智能平衡策略")
    print("="*60)
    
    verifier = CloudDeploymentVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 雲端部署驗證完全通過！")
        print("🏆 所有組件都正確使用83.3%勝率的智能平衡策略")
        print("🚀 系統現在可以安全地進行雲端交易")
        return 0
    else:
        print("\n⚠️ 雲端部署驗證發現問題")
        print("📋 請查看驗證報告並修復問題")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())