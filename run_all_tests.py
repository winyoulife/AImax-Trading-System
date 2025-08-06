#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 完整測試套件運行器 - 任務15實現
運行所有測試並生成綜合報告
"""

import sys
import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加項目路徑
sys.path.append(str(Path(__file__).parent))

def run_test_suite(test_name: str, test_module: str) -> Dict[str, Any]:
    """運行單個測試套件"""
    print(f"\n🧪 運行 {test_name}...")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        # 動態導入測試模塊
        if test_module == "unit_tests":
            from tests.unit_tests import run_unit_tests
            success = run_unit_tests()
            
        elif test_module == "integration_tests":
            from tests.integration_tests import run_integration_tests
            result = run_integration_tests()
            success = not any('error' in str(v) for v in result.values())
            
        elif test_module == "e2e_tests":
            from tests.e2e_tests import main as run_e2e_tests
            exit_code = run_e2e_tests()
            success = exit_code == 0
            
        elif test_module == "simulation_tests":
            from tests.simulation_tests import run_simulation_tests
            result = run_simulation_tests()
            success = result['summary']['success_rate'] >= 80
            
        elif test_module == "comprehensive_tests":
            from tests.test_runner import main as run_comprehensive_tests
            exit_code = run_comprehensive_tests()
            success = exit_code == 0
            
        else:
            raise ValueError(f"未知的測試模塊: {test_module}")
        
        duration = time.time() - start_time
        
        return {
            'test_name': test_name,
            'module': test_module,
            'status': 'PASSED' if success else 'FAILED',
            'duration': duration,
            'success': success
        }
        
    except Exception as e:
        duration = time.time() - start_time
        
        return {
            'test_name': test_name,
            'module': test_module,
            'status': 'ERROR',
            'duration': duration,
            'success': False,
            'error': str(e)
        }

def generate_comprehensive_report(test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成綜合測試報告"""
    total_tests = len(test_results)
    passed_tests = len([r for r in test_results if r['success']])
    failed_tests = len([r for r in test_results if not r['success']])
    
    total_duration = sum(r['duration'] for r in test_results)
    
    # 計算成功率
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # 生成詳細報告
    report = {
        'test_suite': 'AImax_Complete_Test_Suite',
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_test_suites': total_tests,
            'passed_suites': passed_tests,
            'failed_suites': failed_tests,
            'success_rate': success_rate,
            'total_duration': total_duration,
            'overall_status': 'PASSED' if success_rate >= 80 else 'FAILED'
        },
        'test_results': test_results,
        'recommendations': []
    }
    
    # 添加建議
    if success_rate < 100:
        report['recommendations'].append("部分測試失敗，建議檢查失敗的測試套件")
    
    if success_rate < 80:
        report['recommendations'].append("成功率低於80%，建議進行系統檢查和修復")
    
    if total_duration > 300:  # 5分鐘
        report['recommendations'].append("測試執行時間較長，建議優化測試性能")
    
    return report

def save_report(report: Dict[str, Any]) -> Path:
    """保存測試報告"""
    project_root = Path(__file__).parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # JSON報告
    json_report_file = reports_dir / f"complete_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # HTML報告
    html_report_file = reports_dir / f"complete_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    html_content = generate_html_report(report)
    with open(html_report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return json_report_file

def generate_html_report(report: Dict[str, Any]) -> str:
    """生成HTML格式的測試報告"""
    summary = report['summary']
    
    # 狀態顏色
    status_color = "#28a745" if summary['overall_status'] == 'PASSED' else "#dc3545"
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AImax 完整測試報告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .status {{ font-size: 24px; font-weight: bold; color: {status_color}; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .test-results {{ margin-bottom: 30px; }}
        .test-item {{ background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #ddd; }}
        .test-passed {{ border-left-color: #28a745; }}
        .test-failed {{ border-left-color: #dc3545; }}
        .test-error {{ border-left-color: #ffc107; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 5px; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: {status_color}; transition: width 0.3s ease; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 AImax 完整測試報告</h1>
            <div class="status">{summary['overall_status']}</div>
            <p>生成時間: {report['timestamp']}</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <div class="metric-value">{summary['total_test_suites']}</div>
                <div class="metric-label">總測試套件</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['passed_suites']}</div>
                <div class="metric-label">通過套件</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['failed_suites']}</div>
                <div class="metric-label">失敗套件</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['success_rate']:.1f}%</div>
                <div class="metric-label">成功率</div>
            </div>
            <div class="metric">
                <div class="metric-value">{summary['total_duration']:.1f}s</div>
                <div class="metric-label">總耗時</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {summary['success_rate']:.1f}%"></div>
        </div>
        
        <div class="test-results">
            <h2>📋 測試結果詳情</h2>
    """
    
    for result in report['test_results']:
        status_class = {
            'PASSED': 'test-passed',
            'FAILED': 'test-failed',
            'ERROR': 'test-error'
        }.get(result['status'], 'test-item')
        
        error_info = f"<p><strong>錯誤:</strong> {result.get('error', '')}</p>" if 'error' in result else ""
        
        html += f"""
            <div class="test-item {status_class}">
                <h3>{result['test_name']} - {result['status']}</h3>
                <p><strong>模塊:</strong> {result['module']}</p>
                <p><strong>耗時:</strong> {result['duration']:.2f}秒</p>
                {error_info}
            </div>
        """
    
    html += """
        </div>
    """
    
    if report['recommendations']:
        html += """
        <div class="recommendations">
            <h2>💡 建議</h2>
            <ul>
        """
        for rec in report['recommendations']:
            html += f"<li>{rec}</li>"
        
        html += """
            </ul>
        </div>
        """
    
    html += """
    </div>
</body>
</html>
    """
    
    return html

def main():
    """主函數"""
    print("🚀 AImax 完整測試套件")
    print("=" * 60)
    print("正在運行所有測試套件...")
    
    start_time = time.time()
    
    # 定義測試套件
    test_suites = [
        ("單元測試", "unit_tests"),
        ("集成測試", "integration_tests"),
        ("端到端測試", "e2e_tests"),
        ("模擬交易測試", "simulation_tests"),
        ("綜合測試", "comprehensive_tests")
    ]
    
    # 運行所有測試
    test_results = []
    
    for test_name, test_module in test_suites:
        result = run_test_suite(test_name, test_module)
        test_results.append(result)
        
        # 顯示即時結果
        status_emoji = "✅" if result['success'] else "❌"
        print(f"{status_emoji} {test_name}: {result['status']} ({result['duration']:.2f}s)")
    
    # 生成綜合報告
    total_time = time.time() - start_time
    report = generate_comprehensive_report(test_results)
    report['summary']['total_execution_time'] = total_time
    
    # 保存報告
    report_file = save_report(report)
    
    # 顯示最終結果
    print("\n" + "=" * 60)
    print("🎯 測試套件執行完成")
    print("=" * 60)
    
    summary = report['summary']
    print(f"📊 總結:")
    print(f"   測試套件數: {summary['total_test_suites']}")
    print(f"   通過: {summary['passed_suites']} ✅")
    print(f"   失敗: {summary['failed_suites']} ❌")
    print(f"   成功率: {summary['success_rate']:.1f}%")
    print(f"   總耗時: {summary['total_duration']:.2f}秒")
    print(f"   整體狀態: {summary['overall_status']}")
    
    print(f"\n📄 報告已保存: {report_file}")
    
    # 顯示建議
    if report['recommendations']:
        print(f"\n💡 建議:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
    
    # 返回適當的退出碼
    return 0 if summary['success_rate'] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())