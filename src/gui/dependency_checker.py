#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依賴檢查器 - 檢查GUI啟動所需的依賴項目
確保系統能夠正常啟動GUI界面
"""

import sys
import importlib
import subprocess
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DependencyInfo:
    """依賴項目資訊"""
    name: str
    required_version: Optional[str] = None
    install_command: Optional[str] = None
    description: str = ""
    is_critical: bool = True


class DependencyChecker:
    """依賴檢查器類別"""
    
    def __init__(self):
        self.required_dependencies = [
            DependencyInfo(
                name="PyQt6",
                required_version="6.0.0",
                install_command="pip install PyQt6",
                description="GUI框架",
                is_critical=True
            ),
            DependencyInfo(
                name="asyncio",
                description="異步處理支援",
                is_critical=True
            ),
            DependencyInfo(
                name="threading",
                description="多線程支援",
                is_critical=True
            ),
            DependencyInfo(
                name="json",
                description="JSON處理",
                is_critical=True
            ),
            DependencyInfo(
                name="datetime",
                description="時間處理",
                is_critical=True
            ),
            DependencyInfo(
                name="pathlib",
                description="路徑處理",
                is_critical=True
            )
        ]
        
        self.check_results = {}
        self.missing_dependencies = []
        self.installation_commands = []
    
    def check_python_version(self) -> Tuple[bool, str]:
        """檢查Python版本"""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                return True, f"Python {version.major}.{version.minor}.{version.micro}"
            else:
                return False, f"Python版本過舊: {version.major}.{version.minor}.{version.micro} (需要3.8+)"
        except Exception as e:
            return False, f"無法檢查Python版本: {str(e)}"
    
    def check_single_dependency(self, dep: DependencyInfo) -> Tuple[bool, str]:
        """檢查單個依賴項目"""
        try:
            # 嘗試導入模組
            module = importlib.import_module(dep.name)
            
            # 檢查版本（如果需要）
            if dep.required_version and hasattr(module, '__version__'):
                installed_version = module.__version__
                # 簡單版本比較（實際應用中可能需要更複雜的版本比較）
                if self._compare_versions(installed_version, dep.required_version):
                    return True, f"{dep.name} {installed_version} ✓"
                else:
                    return False, f"{dep.name} 版本不符: {installed_version} (需要 {dep.required_version}+)"
            else:
                return True, f"{dep.name} ✓"
                
        except ImportError:
            return False, f"{dep.name} 未安裝"
        except Exception as e:
            return False, f"{dep.name} 檢查失敗: {str(e)}"
    
    def _compare_versions(self, installed: str, required: str) -> bool:
        """簡單版本比較"""
        try:
            installed_parts = [int(x) for x in installed.split('.')]
            required_parts = [int(x) for x in required.split('.')]
            
            # 補齊長度
            max_len = max(len(installed_parts), len(required_parts))
            installed_parts.extend([0] * (max_len - len(installed_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))
            
            return installed_parts >= required_parts
        except:
            return True  # 如果版本比較失敗，假設版本正確
    
    def check_ai_system_dependencies(self) -> Tuple[bool, List[str]]:
        """檢查AI系統依賴"""
        ai_modules = [
            "src.ai.enhanced_ai_manager",
            "src.trading.trade_executor", 
            "src.trading.risk_manager",
            "src.core.trading_system_integrator"
        ]
        
        results = []
        all_available = True
        
        for module_path in ai_modules:
            try:
                # 檢查文件是否存在
                file_path = Path(module_path.replace('.', '/') + '.py')
                if file_path.exists():
                    results.append(f"{module_path} ✓")
                else:
                    results.append(f"{module_path} ❌ (文件不存在)")
                    all_available = False
            except Exception as e:
                results.append(f"{module_path} ❌ ({str(e)})")
                all_available = False
        
        return all_available, results
    
    def check_all_dependencies(self) -> Dict[str, any]:
        """檢查所有依賴項目"""
        results = {
            'python_version': {'status': False, 'message': ''},
            'gui_dependencies': {},
            'ai_system': {'status': False, 'details': []},
            'missing_critical': [],
            'installation_commands': [],
            'overall_status': False
        }
        
        # 檢查Python版本
        python_ok, python_msg = self.check_python_version()
        results['python_version'] = {'status': python_ok, 'message': python_msg}
        
        # 檢查GUI依賴
        missing_critical = []
        for dep in self.required_dependencies:
            dep_ok, dep_msg = self.check_single_dependency(dep)
            results['gui_dependencies'][dep.name] = {
                'status': dep_ok,
                'message': dep_msg,
                'is_critical': dep.is_critical
            }
            
            if not dep_ok and dep.is_critical:
                missing_critical.append(dep.name)
                if dep.install_command:
                    results['installation_commands'].append(dep.install_command)
        
        # 檢查AI系統
        ai_ok, ai_details = self.check_ai_system_dependencies()
        results['ai_system'] = {'status': ai_ok, 'details': ai_details}
        
        results['missing_critical'] = missing_critical
        
        # 整體狀態
        results['overall_status'] = (
            python_ok and 
            len(missing_critical) == 0 and 
            ai_ok
        )
        
        return results
    
    def generate_installation_guide(self, check_results: Dict) -> str:
        """生成安裝指引"""
        guide = []
        guide.append("=== AImax GUI 依賴安裝指引 ===\n")
        
        if not check_results['python_version']['status']:
            guide.append("❌ Python版本問題:")
            guide.append(f"   {check_results['python_version']['message']}")
            guide.append("   請升級到Python 3.8或更高版本\n")
        
        if check_results['missing_critical']:
            guide.append("❌ 缺少關鍵依賴:")
            for dep_name in check_results['missing_critical']:
                dep_info = check_results['gui_dependencies'][dep_name]
                guide.append(f"   - {dep_name}: {dep_info['message']}")
            guide.append("")
            
            if check_results['installation_commands']:
                guide.append("🔧 安裝命令:")
                for cmd in check_results['installation_commands']:
                    guide.append(f"   {cmd}")
                guide.append("")
        
        if not check_results['ai_system']['status']:
            guide.append("❌ AI系統模組問題:")
            for detail in check_results['ai_system']['details']:
                if '❌' in detail:
                    guide.append(f"   {detail}")
            guide.append("   請確保AI系統模組文件存在\n")
        
        if check_results['overall_status']:
            guide.append("✅ 所有依賴檢查通過！系統可以正常啟動。")
        else:
            guide.append("⚠️  請解決上述問題後重新啟動系統。")
        
        return "\n".join(guide)
    
    def quick_check(self) -> bool:
        """快速檢查是否可以啟動GUI"""
        try:
            import PyQt6
            return True
        except ImportError:
            return False


if __name__ == "__main__":
    # 測試依賴檢查器
    checker = DependencyChecker()
    results = checker.check_all_dependencies()
    
    print("=== 依賴檢查結果 ===")
    print(f"Python版本: {results['python_version']['message']}")
    print(f"整體狀態: {'✅ 通過' if results['overall_status'] else '❌ 失敗'}")
    
    if not results['overall_status']:
        print("\n" + checker.generate_installation_guide(results))