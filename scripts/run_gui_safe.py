#!/usr/bin/env python3
"""
AImax GUI安全啟動腳本 - 帶超時保護和錯誤恢復
"""
import sys
import os
import logging
import signal
import threading
import time
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 全局變量
app_running = True
startup_timeout = 60  # 60秒啟動超時

def signal_handler(signum, frame):
    """信號處理器"""
    global app_running
    print("\n⏹️ 收到中斷信號，正在安全關閉...")
    app_running = False
    sys.exit(0)

def timeout_handler():
    """超時處理器"""
    global app_running
    time.sleep(startup_timeout)
    if app_running:
        print(f"\n⏰ 啟動超時 ({startup_timeout}秒)，可能存在問題")
        print("💡 建議檢查:")
        print("   1. 系統資源是否充足")
        print("   2. PyQt6是否正確安裝")
        print("   3. 監控線程是否卡住")
        app_running = False
        os._exit(1)

def setup_logging():
    """設置日誌"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 創建日誌格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件處理器
    file_handler = logging.FileHandler(
        log_dir / 'gui_safe.log', 
        encoding='utf-8',
        mode='w'  # 每次啟動清空日誌
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 配置根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def check_dependencies():
    """檢查依賴"""
    print("🔍 檢查依賴包...")
    missing_deps = []
    
    try:
        import PyQt6
        print("✅ PyQt6 已安裝")
    except ImportError:
        missing_deps.append("PyQt6")
        print("❌ PyQt6 未安裝")
    
    try:
        import psutil
        print("✅ psutil 已安裝")
    except ImportError:
        missing_deps.append("psutil")
        print("❌ psutil 未安裝")
    
    if missing_deps:
        print("\n❌ 缺少以下依賴包:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n請運行以下命令安裝:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    print("✅ 所有依賴包檢查通過")
    return True

def test_basic_imports():
    """測試基本導入"""
    print("\n🧪 測試基本模塊導入...")
    
    try:
        from src.gui.component_manager import ComponentManager
        from src.gui.error_handler import ErrorHandler
        from src.gui.state_manager import StateManager
        print("✅ 核心GUI組件導入成功")
        
        from src.gui.monitoring_dashboard import MonitoringDashboard
        print("✅ 監控儀表板導入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 模塊導入失敗: {e}")
        return False

def create_safe_gui():
    """創建安全的GUI應用程序"""
    print("\n🚀 創建安全GUI應用程序...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # 創建應用程序
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("✅ PyQt6應用程序創建成功")
        
        # 導入主應用程序
        from src.gui.main_application import ModernAITradingGUI
        
        # 創建主窗口
        main_window = ModernAITradingGUI()
        print("✅ 主窗口創建成功")
        
        # 設置安全關閉定時器
        safety_timer = QTimer()
        safety_timer.setSingleShot(True)
        safety_timer.timeout.connect(lambda: (
            print("⏰ 安全定時器觸發，檢查應用程序狀態..."),
            app.processEvents()
        ))
        safety_timer.start(5000)  # 5秒後檢查
        
        # 初始化應用程序（帶超時保護）
        print("🔄 初始化應用程序組件...")
        
        init_success = False
        try:
            # 使用線程初始化，避免阻塞
            def init_worker():
                nonlocal init_success
                try:
                    init_success = main_window.initialize_application()
                except Exception as e:
                    print(f"❌ 初始化過程中發生錯誤: {e}")
                    init_success = False
            
            init_thread = threading.Thread(target=init_worker, daemon=True)
            init_thread.start()
            
            # 等待初始化完成或超時
            start_time = time.time()
            while init_thread.is_alive() and time.time() - start_time < 30:
                app.processEvents()
                time.sleep(0.1)
            
            if init_thread.is_alive():
                print("⚠️ 初始化超時，但繼續運行...")
                init_success = True  # 允許繼續運行
            
        except Exception as e:
            print(f"❌ 初始化失敗: {e}")
            init_success = False
        
        if init_success:
            print("✅ 應用程序初始化完成")
            
            # 顯示主窗口
            main_window.show()
            main_window.raise_()
            main_window.activateWindow()
            
            print("🖥️ GUI界面已顯示")
            print("💡 使用說明:")
            print("   - 點擊 '🚀 開始監控' 啟動實時監控")
            print("   - 使用 Ctrl+C 或關閉窗口退出")
            print("   - 查看日誌: AImax/logs/gui_safe.log")
            
            # 運行事件循環
            return app.exec()
        else:
            print("❌ 應用程序初始化失敗")
            return 1
            
    except Exception as e:
        print(f"❌ 創建GUI應用程序失敗: {e}")
        return 1

def run_text_mode():
    """運行文本模式"""
    print("\n📝 運行文本模式監控...")
    
    try:
        from src.gui.monitoring_dashboard import SystemMonitorThread
        
        # 創建監控線程
        monitor = SystemMonitorThread()
        monitor.initialize_components()
        
        print("✅ 文本模式監控已啟動")
        print("💡 按 Ctrl+C 退出")
        
        # 手動運行監控循環
        while app_running:
            try:
                # 收集並顯示數據
                performance_data = monitor._collect_performance_data()
                if performance_data:
                    system = performance_data.get("system", {})
                    print(f"🔄 [{time.strftime('%H:%M:%S')}] "
                          f"CPU: {system.get('cpu_percent', 0):.1f}%, "
                          f"內存: {system.get('memory_percent', 0):.1f}%, "
                          f"磁盤: {system.get('disk_percent', 0):.1f}%")
                
                time.sleep(5)  # 5秒更新一次
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 監控數據收集失敗: {e}")
                time.sleep(1)
        
        print("✅ 文本模式監控已停止")
        return 0
        
    except Exception as e:
        print(f"❌ 文本模式運行失敗: {e}")
        return 1

def main():
    """主函數"""
    global app_running
    
    print("🚀 AImax GUI 安全啟動器")
    print("=" * 50)
    print(f"⏰ 啟動超時設置: {startup_timeout} 秒")
    print("💡 按 Ctrl+C 可隨時中斷")
    print("=" * 50)
    
    # 設置信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 啟動超時處理器
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()
    
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("🚀 AImax GUI 安全啟動器開始運行")
    
    try:
        # 檢查依賴
        if not check_dependencies():
            return 1
        
        # 測試基本導入
        if not test_basic_imports():
            return 1
        
        # 檢查是否有PyQt6
        try:
            import PyQt6
            print("\n🖥️ 嘗試啟動圖形界面...")
            return create_safe_gui()
        except ImportError:
            print("\n📝 PyQt6不可用，切換到文本模式...")
            return run_text_mode()
            
    except KeyboardInterrupt:
        logger.info("⏹️ 用戶中斷啟動")
        print("\n⏹️ 啟動被用戶中斷")
        return 0
    except Exception as e:
        logger.error(f"❌ 啟動過程中發生異常: {e}")
        print(f"\n❌ 啟動失敗: {e}")
        return 1
    finally:
        app_running = False

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ 程序被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序異常退出: {e}")
        sys.exit(1)