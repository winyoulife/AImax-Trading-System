#!/usr/bin/env python3
"""
AImax GUI啟動腳本
"""
import sys
import os
import logging
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """設置日誌"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'gui.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """檢查依賴"""
    missing_deps = []
    
    try:
        import PyQt6
    except ImportError:
        missing_deps.append("PyQt6")
    
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    if missing_deps:
        print("❌ 缺少以下依賴包:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n請運行以下命令安裝:")
        print(f"pip install {' '.join(missing_deps)}")
        return False
    
    return True

def main():
    """主函數"""
    print("🚀 啟動 AImax GUI系統...")
    
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 檢查依賴
    if not check_dependencies():
        sys.exit(1)
    
    try:
        # 導入並運行GUI
        from src.gui.main_application import main as gui_main
        gui_main()
        
    except KeyboardInterrupt:
        logger.info("⏹️ 用戶中斷")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 啟動GUI失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()