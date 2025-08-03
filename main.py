#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax AI交易系統 v2.0 - 統一入口點
提供完整的GUI啟動流程，包含依賴檢查、錯誤處理和進度顯示
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class MainApplication:
    """主應用程式類別 - 管理整個啟動流程"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
        self.startup_time = time.time()
        
    def show_banner(self):
        """顯示啟動橫幅"""
        print("=" * 60)
        print("🚀 AImax AI交易系統 v2.0")
        print("=" * 60)
        print("✨ 全新GUI修復版本")
        print("🤖 5AI協作智能交易")
        print("📊 實時狀態監控")
        print("🛡️ 完整錯誤恢復")
        print("=" * 60)
        print()
    
    def check_python_version(self) -> bool:
        """檢查Python版本"""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
                return True
            else:
                print(f"❌ Python版本過舊: {version.major}.{version.minor}.{version.micro}")
                print("   需要Python 3.8或更高版本")
                return False
        except Exception as e:
            print(f"❌ 檢查Python版本失敗: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """檢查系統依賴"""
        print("🔍 檢查系統依賴...")
        
        try:
            from src.gui.dependency_checker import DependencyChecker
            
            checker = DependencyChecker()
            results = checker.check_all_dependencies()
            
            if results['overall_status']:
                print("✅ 所有依賴檢查通過")
                return True
            else:
                print("❌ 依賴檢查失敗")
                print("\n" + checker.generate_installation_guide(results))
                return False
                
        except ImportError:
            # 如果依賴檢查器不可用，進行基本檢查
            return self._basic_dependency_check()
        except Exception as e:
            print(f"❌ 依賴檢查過程中發生錯誤: {e}")
            return self._basic_dependency_check()
    
    def _basic_dependency_check(self) -> bool:
        """基本依賴檢查"""
        print("⚠️ 使用基本依賴檢查...")
        
        missing_deps = []
        
        # 檢查PyQt6
        try:
            import PyQt6
            print("✅ PyQt6 已安裝")
        except ImportError:
            missing_deps.append("PyQt6")
            print("❌ PyQt6 未安裝")
        
        # 檢查其他基本依賴
        basic_deps = ['json', 'datetime', 'pathlib', 'threading']
        for dep in basic_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
                print(f"❌ {dep} 未安裝")
        
        if missing_deps:
            print("\n🔧 安裝指引:")
            print("pip install PyQt6")
            return False
        
        return True
    
    def show_startup_progress(self):
        """顯示啟動進度"""
        print("🚀 正在啟動AImax系統...")
        
        steps = [
            "初始化應用程式...",
            "載入GUI組件...",
            "連接AI系統...",
            "啟動狀態監控...",
            "準備用戶界面..."
        ]
        
        for i, step in enumerate(steps, 1):
            print(f"[{i}/{len(steps)}] {step}")
            time.sleep(0.3)  # 模擬載入時間
        
        print("✅ 系統啟動完成！")
        print()
    
    def launch_gui(self) -> bool:
        """啟動GUI系統"""
        try:
            print("🖥️ 啟動GUI系統...")
            
            # 導入GUI啟動器和啟動優化器
            from src.gui.simple_gui_launcher import SimpleGUILauncher
            from src.gui.startup_optimizer import StartupOptimizer
            
            # 創建並配置啟動優化器
            optimizer = StartupOptimizer()
            optimizer.configure_optimization(
                parallel_loading=True,
                lazy_loading=True,
                resource_preloading=True,
                target_time=3.0
            )
            
            # 設置優化器回調
            def on_optimization_progress(phase, progress):
                print(f"⚡ 優化進度: {phase} ({progress:.0f}%)")
            
            def on_optimization_completed(report):
                timing = report['timing']
                performance = report['performance']
                print(f"✅ 啟動優化完成！")
                print(f"   總時間: {timing['total_time']:.2f}s")
                print(f"   效率分數: {performance['efficiency_score']:.1f}%")
                if performance['target_met']:
                    print("   🎯 達成啟動時間目標")
            
            # 連接優化器信號
            optimizer.optimization_progress.connect(on_optimization_progress)
            optimizer.optimization_completed.connect(on_optimization_completed)
            
            # 執行啟動優化
            print("⚡ 執行啟動優化...")
            optimizer.optimize_startup()
            
            # 創建GUI啟動器
            launcher = SimpleGUILauncher()
            
            # 設置回調函數
            def on_gui_ready(main_window):
                self.main_window = main_window
                elapsed_time = time.time() - self.startup_time
                print(f"✅ GUI啟動成功！(耗時 {elapsed_time:.1f} 秒)")
                print("📝 使用提示:")
                print("   • 左側面板顯示AI和交易狀態")
                print("   • 右側面板顯示系統日誌")
                print("   • 菜單欄提供完整功能")
                print("   • 可通過工具菜單查看系統診斷")
                print()
            
            def on_launch_failed(error_message):
                print(f"❌ GUI啟動失敗: {error_message}")
                self._show_troubleshooting()
                return False
            
            # 連接信號
            launcher.gui_ready.connect(on_gui_ready)
            launcher.launch_failed.connect(on_launch_failed)
            
            # 啟動GUI
            if launcher.launch_gui():
                # 運行應用程式
                exit_code = launcher.app.exec()
                
                # 清理資源
                launcher.cleanup()
                
                return exit_code == 0
            else:
                print("❌ 無法啟動GUI")
                return False
                
        except ImportError as e:
            print(f"❌ 導入GUI模組失敗: {e}")
            print("請確保所有GUI組件都已正確安裝")
            return False
        except Exception as e:
            print(f"❌ GUI啟動過程中發生錯誤: {e}")
            self._show_troubleshooting()
            return False
    
    def _show_troubleshooting(self):
        """顯示故障排除資訊"""
        print("\n🔧 故障排除指引:")
        print("1. 確保Python版本 >= 3.8")
        print("2. 安裝必要依賴: pip install PyQt6")
        print("3. 檢查AI系統文件是否完整")
        print("4. 查看系統日誌獲取詳細錯誤資訊")
        print("5. 重新啟動系統或聯繫技術支援")
        print()
    
    def run(self) -> int:
        """運行主應用程式"""
        try:
            # 顯示啟動橫幅
            self.show_banner()
            
            # 檢查Python版本
            if not self.check_python_version():
                return 1
            
            # 檢查依賴
            if not self.check_dependencies():
                return 1
            
            # 顯示啟動進度
            self.show_startup_progress()
            
            # 啟動GUI
            if self.launch_gui():
                print("👋 感謝使用AImax AI交易系統！")
                return 0
            else:
                return 1
                
        except KeyboardInterrupt:
            print("\n⚠️ 用戶中斷啟動")
            print("👋 感謝使用AImax AI交易系統！")
            return 0
        except Exception as e:
            print(f"❌ 系統啟動失敗: {e}")
            self._show_troubleshooting()
            return 1


def show_help():
    """顯示幫助資訊"""
    print("AImax AI交易系統 v2.0 - 使用說明")
    print()
    print("用法:")
    print("  python main.py          # 啟動GUI系統")
    print("  python main.py --help   # 顯示此幫助")
    print()
    print("功能特色:")
    print("  • 5AI協作智能交易")
    print("  • 實時狀態監控")
    print("  • 完整錯誤恢復")
    print("  • 現代化GUI界面")
    print("  • 多種交易策略")
    print()
    print("系統要求:")
    print("  • Python 3.8+")
    print("  • PyQt6")
    print("  • 8GB+ RAM")
    print()
    print("更多資訊請查看 README.md")


def main():
    """主入口函數"""
    # 檢查命令行參數
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            show_help()
            return 0
        elif sys.argv[1] in ['--version', '-v']:
            print("AImax AI交易系統 v2.0")
            return 0
        else:
            print(f"未知參數: {sys.argv[1]}")
            print("使用 --help 查看幫助")
            return 1
    
    # 創建並運行主應用程式
    app = MainApplication()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())