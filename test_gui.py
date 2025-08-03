#!/usr/bin/env python3
"""
測試多時框回測GUI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from scripts.multi_timeframe_macd_backtest_gui_v2 import MultiTimeframeMACDBacktestGUI

def main():
    """測試GUI"""
    try:
        print("啟動多時間框架MACD回測分析器...")
        app = MultiTimeframeMACDBacktestGUI()
        app.run()
    except Exception as e:
        print(f"GUI測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()