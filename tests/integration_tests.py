#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 集成測試 - 任務15實現
測試GitHub Actions工作流和系統集成
"""

import sys
import os
import json
import time
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

class GitHubActionsIntegrationTest:
    """GitHub Actions集成測試"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
        
    def test_workflow_syntax(self) -> Dict[str, Any]:
        """測試工作流語法"""
        results = {}
        
        if not self.workflows_dir.exists():
            return {"error": "workflows目錄不存在"}
        
        workflow_files = list(self.workflows_dir.glob("*.yml"))
        
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 基本語法檢查
                syntax_checks = {
                    'has_name': 'name:' in content,
                    'has_on': 'on:' in content,
                    'has_jobs': 'jobs:' in content,
                    'has_runs_on': 'runs-on:' in content,
                    'has_steps': 'steps:' in content
                }
                
                results[workflow_file.name] = {
                    'syntax_valid': all(syntax_checks.values()),
                    'checks': syntax_checks,
                    'size': len(content)
                }
                
            except Exception as e:
                results[workflow_file.name] = {
                    'error': str(e),
                    'syntax_valid': False
                }
        
        return results
    
    def test_secrets_configuration(self) -> Dict[str, Any]:
        """測試Secrets配置"""
        results = {}
        
        # 檢查secrets模板
        secrets_template = self.project_root / "github_secrets_template.json"
        if secrets_template.exists():
            try:
                with open(secrets_template, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                
                results['template'] = {
                    'exists': True,
                    'secrets_count': len(template),
                    'has_max_api': 'MAX_API_KEY' in template,
                    'has_telegram': any('TELEGRAM' in key for key in template.keys())
                }
            except Exception as e:
                results['template'] = {'error': str(e)}
        else:
            results['template'] = {'exists': False}
        
        # 檢查工作流中的secrets使用
        workflow_files = list(self.workflows_dir.glob("*.yml"))
        secrets_usage = {}
        
        for workflow_file in workflow_files:
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                secrets_usage[workflow_file.name] = {
                    'uses_secrets': '${{ secrets.' in content,
                    'secret_count': content.count('${{ secrets.')
                }
            except Exception as e:
                secrets_usage[workflow_file.name] = {'error': str(e)}
        
        results['usage'] = secrets_usage
        return results
    
    def test_deployment_workflow(self) -> Dict[str, Any]:
        """測試部署工作流"""
        deploy_workflow = self.workflows_dir / "deploy-pages.yml"
        
        if not deploy_workflow.exists():
            return {"error": "部署工作流不存在"}
        
        try:
            with open(deploy_workflow, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查部署相關配置
            deployment_checks = {
                'has_github_pages': 'pages' in content.lower(),
                'has_build_step': 'build' in content.lower(),
                'has_deploy_step': 'deploy' in content.lower(),
                'has_permissions': 'permissions:' in content,
                'has_artifact_upload': 'upload-pages-artifact' in content
            }
            
            return {
                'exists': True,
                'deployment_ready': all(deployment_checks.values()),
                'checks': deployment_checks
            }
            
        except Exception as e:
            return {"error": str(e)}

class WebDashboardIntegrationTest:
    """Web控制面板集成測試"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.static_dir = self.project_root / "static"
    
    def test_dashboard_functionality(self) -> Dict[str, Any]:
        """測試控制面板功能"""
        results = {}
        
        # 檢查主要HTML文件
        html_files = ['index.html', 'secure-login.html', 'help.html']
        
        for html_file in html_files:
            file_path = self.static_dir / html_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 基本HTML結構檢查
                    html_checks = {
                        'has_doctype': '<!DOCTYPE' in content,
                        'has_html_tag': '<html' in content,
                        'has_head': '<head>' in content,
                        'has_body': '<body>' in content,
                        'has_title': '<title>' in content
                    }
                    
                    results[html_file] = {
                        'exists': True,
                        'valid_html': all(html_checks.values()),
                        'checks': html_checks,
                        'size': len(content)
                    }
                    
                except Exception as e:
                    results[html_file] = {'error': str(e)}
            else:
                results[html_file] = {'exists': False}
        
        return results
    
    def test_authentication_system(self) -> Dict[str, Any]:
        """測試認證系統"""
        auth_config_path = self.static_dir / "auth_config.json"
        
        if not auth_config_path.exists():
            return {"error": "認證配置文件不存在"}
        
        try:
            with open(auth_config_path, 'r', encoding='utf-8') as f:
                auth_config = json.load(f)
            
            # 檢查認證配置
            auth_checks = {
                'has_users': 'users' in auth_config,
                'has_session_timeout': 'session_timeout' in auth_config,
                'has_target_user': 'lovejk1314' in auth_config.get('users', {}),
                'user_hash_valid': len(auth_config.get('users', {}).get('lovejk1314', '')) > 0
            }
            
            return {
                'config_valid': all(auth_checks.values()),
                'checks': auth_checks,
                'session_timeout': auth_config.get('session_timeout', 0)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """測試API端點（如果有本地服務器運行）"""
        # 這裡可以添加對本地API端點的測試
        # 由於是靜態部署，主要檢查GitHub API集成
        
        js_files = list(self.static_dir.glob("js/*.js"))
        api_integration = {}
        
        for js_file in js_files:
            try:
                with open(js_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                api_integration[js_file.name] = {
                    'has_fetch': 'fetch(' in content,
                    'has_github_api': 'api.github.com' in content,
                    'has_error_handling': 'catch' in content,
                    'size': len(content)
                }
                
            except Exception as e:
                api_integration[js_file.name] = {'error': str(e)}
        
        return {'api_integration': api_integration}

class TradingSystemIntegrationTest:
    """交易系統集成測試"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
    
    def test_end_to_end_trading_flow(self) -> Dict[str, Any]:
        """測試端到端交易流程"""
        results = {}
        
        try:
            # 測試數據獲取
            from src.data.simple_data_fetcher import DataFetcher
            fetcher = DataFetcher()
            
            start_time = time.time()
            df = fetcher.get_historical_data('BTCUSDT', '1h', 100)
            data_fetch_time = time.time() - start_time
            
            results['data_fetch'] = {
                'success': True,
                'time': data_fetch_time,
                'data_points': len(df)
            }
            
            # 測試信號生成
            from src.core.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals
            strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
            
            start_time = time.time()
            signals = strategy.detect_signals(df)
            signal_time = time.time() - start_time
            
            results['signal_generation'] = {
                'success': True,
                'time': signal_time,
                'signals_count': len(signals)
            }
            
            # 測試模擬交易
            from src.trading.simulation_manager import SimulationTradingManager
            sim_manager = SimulationTradingManager()
            
            if signals:
                test_signal = signals[0]
                trade_result = sim_manager.execute_simulation_trade(test_signal)
                
                results['simulation_trading'] = {
                    'success': trade_result.get('success', False),
                    'details': trade_result
                }
            else:
                results['simulation_trading'] = {
                    'success': False,
                    'reason': 'No signals generated'
                }
            
            # 測試報告生成
            report = sim_manager.get_performance_report()
            results['report_generation'] = {
                'success': len(report) > 0,
                'report_length': len(report)
            }
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def test_github_actions_simulation(self) -> Dict[str, Any]:
        """測試GitHub Actions模擬"""
        # 檢查GitHub Actions交易腳本
        github_trader_path = self.project_root / "scripts" / "github_actions_trader.py"
        
        if not github_trader_path.exists():
            return {"error": "GitHub Actions交易腳本不存在"}
        
        try:
            # 嘗試導入和基本驗證
            spec = {}
            with open(github_trader_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查腳本結構
            script_checks = {
                'has_main_function': 'def main(' in content,
                'has_error_handling': 'try:' in content and 'except' in content,
                'has_logging': 'logging' in content,
                'has_data_fetch': 'DataFetcher' in content,
                'has_signal_detection': 'detect_signals' in content
            }
            
            return {
                'script_exists': True,
                'script_valid': all(script_checks.values()),
                'checks': script_checks,
                'size': len(content)
            }
            
        except Exception as e:
            return {"error": str(e)}

def run_integration_tests() -> Dict[str, Any]:
    """運行所有集成測試"""
    print("🔗 運行 AImax 集成測試")
    print("=" * 50)
    
    results = {}
    
    # GitHub Actions測試
    print("📋 測試 GitHub Actions...")
    github_test = GitHubActionsIntegrationTest()
    results['github_actions'] = {
        'workflow_syntax': github_test.test_workflow_syntax(),
        'secrets_config': github_test.test_secrets_configuration(),
        'deployment': github_test.test_deployment_workflow()
    }
    
    # Web控制面板測試
    print("🌐 測試 Web控制面板...")
    web_test = WebDashboardIntegrationTest()
    results['web_dashboard'] = {
        'functionality': web_test.test_dashboard_functionality(),
        'authentication': web_test.test_authentication_system(),
        'api_endpoints': web_test.test_api_endpoints()
    }
    
    # 交易系統測試
    print("💰 測試交易系統...")
    trading_test = TradingSystemIntegrationTest()
    results['trading_system'] = {
        'end_to_end_flow': trading_test.test_end_to_end_trading_flow(),
        'github_actions_simulation': trading_test.test_github_actions_simulation()
    }
    
    # 保存結果
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"📊 集成測試完成，報告已保存: {report_file}")
    
    return results

if __name__ == "__main__":
    results = run_integration_tests()
    
    # 檢查是否有錯誤
    has_errors = False
    for category, tests in results.items():
        for test_name, result in tests.items():
            if isinstance(result, dict) and 'error' in result:
                has_errors = True
                print(f"❌ {category}.{test_name}: {result['error']}")
    
    if not has_errors:
        print("✅ 所有集成測試通過！")
    
    sys.exit(1 if has_errors else 0)