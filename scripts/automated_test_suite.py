#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對系統自動化測試套件 - 任務8.3實現
創建完整的自動化測試流程
"""

import sys
import os
import json
import time
import subprocess
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging
from pathlib import Path

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """測試結果數據結構"""
    test_name: str
    status: str  # PASSED, FAILED, SKIPPED
    duration: float
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TestSuite:
    """測試套件數據結構"""
    name: str
    description: str
    test_files: List[str]
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # 5分鐘超時
    critical: bool = False  # 是否為關鍵測試

class AutomatedTestRunner:
    """自動化測試運行器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.test_results: List[TestResult] = []
        self.test_suites: Dict[str, TestSuite] = {}
        self.setup_test_suites()
        
    def setup_test_suites(self):
        """設置測試套件"""
        try:
            # 1. 核心功能測試套件
            self.test_suites["core"] = TestSuite(
                name="核心功能測試",
                description="測試系統核心功能和組件",
                test_files=[
                    "AImax/scripts/test_strategy_control.py",
                    "AImax/scripts/test_multi_pair_monitor.py",
                    "AImax/scripts/test_realtime_monitoring.py"
                ],
                critical=True,
                timeout=180
            )
            
            # 2. 系統整合測試套件
            self.test_suites["integration"] = TestSuite(
                name="系統整合測試",
                description="測試系統組件間的整合",
                test_files=[
                    "AImax/scripts/run_multi_pair_integration_test.py"
                ],
                dependencies=["core"],
                critical=True,
                timeout=300
            )
            
            # 3. 性能測試套件
            self.test_suites["performance"] = TestSuite(
                name="性能測試",
                description="測試系統性能和資源使用",
                test_files=[
                    "AImax/scripts/test_system_performance_optimization.py"
                ],
                dependencies=["core"],
                timeout=240
            )
            
            # 4. AI系統測試套件
            self.test_suites["ai"] = TestSuite(
                name="AI系統測試",
                description="測試AI協作和決策系統",
                test_files=[
                    "AImax/scripts/test_enhanced_ai_system.py",
                    "AImax/scripts/test_five_ai_simple.py"
                ],
                timeout=300
            )
            
            # 5. 數據系統測試套件
            self.test_suites["data"] = TestSuite(
                name="數據系統測試",
                description="測試數據管理和處理系統",
                test_files=[
                    "AImax/scripts/test_multi_pair_data_system.py",
                    "AImax/scripts/validate_historical_data.py"
                ],
                timeout=180
            )
            
            logger.info(f"✅ 設置了 {len(self.test_suites)} 個測試套件")
            
        except Exception as e:
            logger.error(f"❌ 測試套件設置失敗: {e}")
    
    def run_test_file(self, test_file: str, timeout: int = 300) -> TestResult:
        """運行單個測試文件"""
        test_name = Path(test_file).stem
        start_time = time.time()
        
        try:
            logger.info(f"🧪 運行測試: {test_name}")
            
            # 檢查測試文件是否存在
            test_path = self.project_root / test_file
            if not test_path.exists():
                return TestResult(
                    test_name=test_name,
                    status="SKIPPED",
                    duration=0,
                    error_message=f"測試文件不存在: {test_file}"
                )
            
            # 運行測試
            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return TestResult(
                    test_name=test_name,
                    status="PASSED",
                    duration=duration,
                    details={
                        "stdout": result.stdout[-1000:] if result.stdout else "",  # 最後1000字符
                        "stderr": result.stderr[-500:] if result.stderr else ""
                    }
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status="FAILED",
                    duration=duration,
                    error_message=f"退出碼: {result.returncode}",
                    details={
                        "stdout": result.stdout[-1000:] if result.stdout else "",
                        "stderr": result.stderr[-500:] if result.stderr else ""
                    }
                )
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status="FAILED",
                duration=duration,
                error_message=f"測試超時 ({timeout}秒)"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                test_name=test_name,
                status="FAILED",
                duration=duration,
                error_message=f"測試執行錯誤: {e}"
            )
    
    def run_test_suite(self, suite_name: str) -> List[TestResult]:
        """運行測試套件"""
        if suite_name not in self.test_suites:
            logger.error(f"❌ 測試套件不存在: {suite_name}")
            return []
        
        suite = self.test_suites[suite_name]
        logger.info(f"🚀 開始運行測試套件: {suite.name}")
        
        suite_results = []
        
        for test_file in suite.test_files:
            result = self.run_test_file(test_file, suite.timeout)
            suite_results.append(result)
            self.test_results.append(result)
            
            # 如果是關鍵測試且失敗，記錄警告
            if suite.critical and result.status == "FAILED":
                logger.warning(f"⚠️ 關鍵測試失敗: {result.test_name}")
        
        # 統計套件結果
        passed = sum(1 for r in suite_results if r.status == "PASSED")
        failed = sum(1 for r in suite_results if r.status == "FAILED")
        skipped = sum(1 for r in suite_results if r.status == "SKIPPED")
        
        logger.info(f"📊 套件 {suite.name} 完成: {passed} 通過, {failed} 失敗, {skipped} 跳過")
        
        return suite_results
    
    def run_all_tests(self, parallel: bool = False) -> Dict[str, Any]:
        """運行所有測試"""
        logger.info("🚀 開始運行完整測試套件")
        start_time = time.time()
        
        # 按依賴順序運行測試套件
        execution_order = self._get_execution_order()
        
        all_results = {}
        
        for suite_name in execution_order:
            suite_results = self.run_test_suite(suite_name)
            all_results[suite_name] = suite_results
            
            # 檢查關鍵測試是否失敗
            suite = self.test_suites[suite_name]
            if suite.critical:
                failed_critical = [r for r in suite_results if r.status == "FAILED"]
                if failed_critical:
                    logger.error(f"❌ 關鍵測試套件 {suite.name} 有失敗項目，考慮停止後續測試")
        
        total_duration = time.time() - start_time
        
        # 生成測試報告
        report = self._generate_test_report(all_results, total_duration)
        
        logger.info(f"✅ 所有測試完成，總耗時: {total_duration:.2f}秒")
        
        return report
    
    def _get_execution_order(self) -> List[str]:
        """獲取測試套件執行順序（考慮依賴關係）"""
        order = []
        visited = set()
        
        def visit(suite_name: str):
            if suite_name in visited:
                return
            
            visited.add(suite_name)
            suite = self.test_suites[suite_name]
            
            # 先處理依賴
            for dep in suite.dependencies:
                if dep in self.test_suites:
                    visit(dep)
            
            order.append(suite_name)
        
        # 訪問所有套件
        for suite_name in self.test_suites:
            visit(suite_name)
        
        return order
    
    def _generate_test_report(self, all_results: Dict[str, List[TestResult]], total_duration: float) -> Dict[str, Any]:
        """生成測試報告"""
        try:
            # 統計總體結果
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r.status == "PASSED")
            failed_tests = sum(1 for r in self.test_results if r.status == "FAILED")
            skipped_tests = sum(1 for r in self.test_results if r.status == "SKIPPED")
            
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # 按套件統計
            suite_stats = {}
            for suite_name, results in all_results.items():
                suite_stats[suite_name] = {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.status == "PASSED"),
                    "failed": sum(1 for r in results if r.status == "FAILED"),
                    "skipped": sum(1 for r in results if r.status == "SKIPPED"),
                    "duration": sum(r.duration for r in results),
                    "critical": self.test_suites[suite_name].critical
                }
            
            # 失敗測試詳情
            failed_tests_details = [
                {
                    "test_name": r.test_name,
                    "error_message": r.error_message,
                    "duration": r.duration
                }
                for r in self.test_results if r.status == "FAILED"
            ]
            
            report = {
                "test_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "total_duration": total_duration,
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "skipped_tests": skipped_tests,
                    "success_rate": success_rate
                },
                "suite_statistics": suite_stats,
                "failed_tests": failed_tests_details,
                "test_details": [
                    {
                        "test_name": r.test_name,
                        "status": r.status,
                        "duration": r.duration,
                        "timestamp": r.timestamp.isoformat()
                    }
                    for r in self.test_results
                ],
                "recommendations": self._generate_recommendations(suite_stats, failed_tests_details)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 測試報告生成失敗: {e}")
            return {"error": f"報告生成失敗: {e}"}
    
    def _generate_recommendations(self, suite_stats: Dict, failed_tests: List) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        # 檢查關鍵測試失敗
        critical_failures = []
        for suite_name, stats in suite_stats.items():
            if stats["critical"] and stats["failed"] > 0:
                critical_failures.append(suite_name)
        
        if critical_failures:
            recommendations.append(f"關鍵測試套件失敗: {', '.join(critical_failures)}，需要優先修復")
        
        # 檢查成功率
        total_tests = sum(stats["total"] for stats in suite_stats.values())
        total_passed = sum(stats["passed"] for stats in suite_stats.values())
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate < 80:
            recommendations.append(f"整體成功率 {success_rate:.1f}% 偏低，建議檢查失敗測試")
        elif success_rate < 95:
            recommendations.append(f"成功率 {success_rate:.1f}% 良好，但仍有改進空間")
        else:
            recommendations.append("測試成功率優秀，系統狀態良好")
        
        # 檢查性能問題
        slow_tests = [r for r in self.test_results if r.duration > 60]  # 超過1分鐘
        if slow_tests:
            recommendations.append(f"發現 {len(slow_tests)} 個慢速測試，建議優化性能")
        
        return recommendations

class ContinuousIntegration:
    """持續集成系統"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.test_runner = AutomatedTestRunner(project_root)
        
    def create_ci_config(self):
        """創建CI配置文件"""
        try:
            # 創建GitHub Actions配置
            github_actions_config = """name: AImax Multi-Pair Trading System CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run automated tests
      run: |
        python AImax/scripts/automated_test_suite.py
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: AImax/logs/test_reports/
"""
            
            # 創建.github/workflows目錄
            workflows_dir = self.project_root / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            
            # 寫入配置文件
            with open(workflows_dir / "ci.yml", "w", encoding="utf-8") as f:
                f.write(github_actions_config)
            
            logger.info("✅ GitHub Actions CI配置已創建")
            
            # 創建本地CI腳本
            local_ci_script = """#!/bin/bash
# 本地持續集成腳本

echo "🚀 開始本地CI流程"

# 檢查Python環境
python --version

# 安裝依賴
echo "📦 安裝依賴..."
pip install -r requirements.txt

# 運行測試
echo "🧪 運行自動化測試..."
python AImax/scripts/automated_test_suite.py

# 檢查測試結果
if [ $? -eq 0 ]; then
    echo "✅ 所有測試通過"
else
    echo "❌ 測試失敗"
    exit 1
fi

echo "🎉 本地CI流程完成"
"""
            
            with open(self.project_root / "run_ci.sh", "w", encoding="utf-8") as f:
                f.write(local_ci_script)
            
            # 設置執行權限（在Unix系統上）
            try:
                os.chmod(self.project_root / "run_ci.sh", 0o755)
            except:
                pass
            
            logger.info("✅ 本地CI腳本已創建")
            
        except Exception as e:
            logger.error(f"❌ CI配置創建失敗: {e}")
    
    def run_ci_pipeline(self) -> Dict[str, Any]:
        """運行CI流程"""
        logger.info("🚀 開始CI流程")
        
        try:
            # 1. 環境檢查
            env_check = self._check_environment()
            if not env_check["success"]:
                return {"success": False, "error": "環境檢查失敗", "details": env_check}
            
            # 2. 運行測試
            test_results = self.test_runner.run_all_tests()
            
            # 3. 分析結果
            success_rate = test_results.get("test_summary", {}).get("success_rate", 0)
            ci_success = success_rate >= 80  # 80%以上成功率視為CI通過
            
            # 4. 生成CI報告
            ci_report = {
                "success": ci_success,
                "timestamp": datetime.now().isoformat(),
                "environment": env_check,
                "test_results": test_results,
                "ci_status": "PASSED" if ci_success else "FAILED",
                "recommendations": test_results.get("recommendations", [])
            }
            
            # 5. 保存CI報告
            self._save_ci_report(ci_report)
            
            logger.info(f"{'✅' if ci_success else '❌'} CI流程完成: {ci_report['ci_status']}")
            
            return ci_report
            
        except Exception as e:
            logger.error(f"❌ CI流程執行失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_environment(self) -> Dict[str, Any]:
        """檢查環境"""
        try:
            checks = {}
            
            # Python版本檢查
            python_version = sys.version_info
            checks["python_version"] = {
                "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                "valid": python_version >= (3, 8)
            }
            
            # 依賴檢查
            required_modules = ["pandas", "numpy", "psutil", "aiohttp"]
            missing_modules = []
            
            for module in required_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            checks["dependencies"] = {
                "missing": missing_modules,
                "valid": len(missing_modules) == 0
            }
            
            # 項目結構檢查
            required_dirs = ["AImax/src", "AImax/scripts", "AImax/logs"]
            missing_dirs = []
            
            for dir_path in required_dirs:
                if not (self.project_root / dir_path).exists():
                    missing_dirs.append(dir_path)
            
            checks["project_structure"] = {
                "missing_dirs": missing_dirs,
                "valid": len(missing_dirs) == 0
            }
            
            # 整體檢查結果
            all_valid = all(check["valid"] for check in checks.values())
            
            return {
                "success": all_valid,
                "checks": checks,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_ci_report(self, report: Dict[str, Any]):
        """保存CI報告"""
        try:
            reports_dir = self.project_root / "AImax" / "logs" / "ci_reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_dir / f"ci_report_{timestamp}.json"
            
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"📄 CI報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ CI報告保存失敗: {e}")

def main():
    """主函數"""
    print("🚀 AImax 自動化測試套件")
    print("=" * 50)
    
    try:
        # 創建測試運行器
        test_runner = AutomatedTestRunner()
        
        # 運行所有測試
        results = test_runner.run_all_tests()
        
        # 顯示結果
        summary = results.get("test_summary", {})
        print(f"\n📊 測試結果總結:")
        print(f"總測試數: {summary.get('total_tests', 0)}")
        print(f"通過: {summary.get('passed_tests', 0)}")
        print(f"失敗: {summary.get('failed_tests', 0)}")
        print(f"跳過: {summary.get('skipped_tests', 0)}")
        print(f"成功率: {summary.get('success_rate', 0):.1f}%")
        print(f"總耗時: {summary.get('total_duration', 0):.2f}秒")
        
        # 保存測試報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path("AImax/logs/test_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"automated_test_report_{timestamp}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 詳細報告已保存: {report_file}")
        
        # 返回成功狀態
        success_rate = summary.get('success_rate', 0)
        return 0 if success_rate >= 80 else 1
        
    except Exception as e:
        print(f"❌ 測試套件執行失敗: {e}")
        return 1

if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    exit_code = main()
    sys.exit(exit_code)