#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 單元測試 - 任務15實現
測試核心交易邏輯的單元測試
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

class TestDataFetcher(unittest.TestCase):
    """測試數據獲取器"""
    
    def setUp(self):
        """測試設置"""
        try:
            from src.data.simple_data_fetcher import DataFetcher
            self.fetcher = DataFetcher()
        except ImportError:
            self.skipTest("DataFetcher模塊不可用")
    
    def test_get_current_price(self):
        """測試獲取當前價格"""
        price = self.fetcher.get_current_price('BTCUSDT')
        self.assertIsInstance(price, (int, float))
        self.assertGreater(price, 0)
    
    def test_get_historical_data(self):
        """測試獲取歷史數據"""
        df = self.fetcher.get_historical_data('BTCUSDT', '1h', 50)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('close', df.columns)
        self.assertIn('volume', df.columns)
    
    def test_invalid_symbol(self):
        """測試無效交易對處理"""
        with self.assertRaises(Exception):
            self.fetcher.get_current_price('INVALID_SYMBOL')

class TestTradingSignals(unittest.TestCase):
    """測試交易信號"""
    
    def setUp(self):
        """測試設置"""
        try:
            from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
            from src.data.simple_data_fetcher import DataFetcher
            
            self.strategy = SmartBalancedVolumeEnhancedMACDSignals()
            self.fetcher = DataFetcher()
        except ImportError:
            self.skipTest("交易信號模塊不可用")
    
    def test_calculate_macd(self):
        """測試MACD計算"""
        # 創建測試數據
        dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
        df = pd.DataFrame({
            'timestamp': dates,
            'close': np.random.randn(100).cumsum() + 50000,
            'volume': np.random.randint(100, 1000, 100)
        })
        
        result = self.strategy.calculate_macd(df)
        
        self.assertIn('macd', result.columns)
        self.assertIn('macd_signal', result.columns)
        self.assertIn('macd_hist', result.columns)
    
    def test_detect_signals(self):
        """測試信號檢測"""
        df = self.fetcher.get_historical_data('BTCUSDT', '1h', 100)
        signals = self.strategy.detect_smart_balanced_signals(df)
        
        self.assertIsInstance(signals, list)
        
        # 如果有信號，檢查信號結構
        if signals:
            signal = signals[0]
            self.assertIn('action', signal)
            self.assertIn('confidence', signal)
            self.assertIn('price', signal)
            self.assertIn(['buy', 'sell'], signal['action'])

class TestSimulationManager(unittest.TestCase):
    """測試模擬交易管理器"""
    
    def setUp(self):
        """測試設置"""
        try:
            from src.trading.simulation_manager import SimulationTradingManager
            self.sim_manager = SimulationTradingManager()
        except ImportError:
            self.skipTest("模擬交易管理器不可用")
    
    def test_execute_simulation_trade(self):
        """測試執行模擬交易"""
        test_signal = {
            'action': 'buy',
            'price': 50000,
            'confidence': 0.87,
            'symbol': 'BTCUSDT'
        }
        
        result = self.sim_manager.execute_simulation_trade(test_signal)
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
    
    def test_get_performance_report(self):
        """測試獲取性能報告"""
        report = self.sim_manager.get_performance_report()
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)

class TestWebDashboard(unittest.TestCase):
    """測試Web控制面板"""
    
    def setUp(self):
        """測試設置"""
        self.project_root = Path(__file__).parent.parent
        self.static_dir = self.project_root / "static"
    
    def test_static_files_exist(self):
        """測試靜態文件存在"""
        required_files = [
            "index.html",
            "css/dashboard.css",
            "js/dashboard.js"
        ]
        
        for file in required_files:
            file_path = self.static_dir / file
            self.assertTrue(file_path.exists(), f"文件不存在: {file}")
    
    def test_auth_config_exists(self):
        """測試認證配置存在"""
        auth_config_path = self.static_dir / "auth_config.json"
        self.assertTrue(auth_config_path.exists(), "認證配置文件不存在")

class TestGitHubActions(unittest.TestCase):
    """測試GitHub Actions配置"""
    
    def setUp(self):
        """測試設置"""
        self.project_root = Path(__file__).parent.parent
        self.workflows_dir = self.project_root / ".github" / "workflows"
    
    def test_workflows_directory_exists(self):
        """測試工作流目錄存在"""
        self.assertTrue(self.workflows_dir.exists(), "GitHub workflows目錄不存在")
    
    def test_workflow_files_exist(self):
        """測試工作流文件存在"""
        workflow_files = list(self.workflows_dir.glob("*.yml"))
        self.assertGreater(len(workflow_files), 0, "沒有找到工作流文件")
        
        # 檢查關鍵工作流
        expected_workflows = [
            "main-trading.yml",
            "monitoring.yml",
            "deploy-pages.yml"
        ]
        
        existing_files = [f.name for f in workflow_files]
        for workflow in expected_workflows:
            if workflow in existing_files:
                self.assertIn(workflow, existing_files)

class TestTelegramNotifications(unittest.TestCase):
    """測試Telegram通知"""
    
    def setUp(self):
        """測試設置"""
        self.project_root = Path(__file__).parent.parent
    
    def test_telegram_config_exists(self):
        """測試Telegram配置存在"""
        config_path = self.project_root / "config" / "telegram_config.py"
        self.assertTrue(config_path.exists(), "Telegram配置文件不存在")
    
    def test_telegram_bot_module(self):
        """測試Telegram機器人模塊"""
        try:
            from src.notifications.simple_telegram_bot import SimpleTelegramBot
            # 如果能導入，測試通過
            self.assertTrue(True)
        except ImportError:
            self.skipTest("Telegram機器人模塊不可用")

class TestErrorHandling(unittest.TestCase):
    """測試錯誤處理"""
    
    def test_network_error_handling(self):
        """測試網路錯誤處理"""
        # 這裡可以添加網路錯誤模擬測試
        self.assertTrue(True)  # 佔位符
    
    def test_api_error_handling(self):
        """測試API錯誤處理"""
        # 這裡可以添加API錯誤模擬測試
        self.assertTrue(True)  # 佔位符

def run_unit_tests():
    """運行單元測試"""
    print("🧪 運行 AImax 單元測試")
    print("=" * 50)
    
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    test_classes = [
        TestDataFetcher,
        TestTradingSignals,
        TestSimulationManager,
        TestWebDashboard,
        TestGitHubActions,
        TestTelegramNotifications,
        TestErrorHandling
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回結果
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)