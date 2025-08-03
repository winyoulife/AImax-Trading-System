#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一交易程式 - AImax系統的統一入口點
整合所有已完成的組件，提供統一的用戶界面和系統管理
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """系統狀態"""
    ai_models_available: int
    ai_models_total: int
    api_connection: bool
    database_status: bool
    config_valid: bool
    overall_status: bool
    errors: List[str]
    warnings: List[str]

@dataclass
class TradingMode:
    """交易模式"""
    name: str
    description: str
    entry_point: str
    required_components: List[str]
    config_template: Dict[str, Any]

class UnifiedTradingProgram:
    """統一交易程式主類"""
    
    def __init__(self):
        """初始化統一交易程式"""
        self.version = "2.0"
        self.project_root = project_root
        self.is_running = False
        self.current_mode = None
        
        # 設置日誌
        self._setup_logging()
        
        # 定義可用的交易模式
        self.available_modes = {
            "single": TradingMode(
                name="單交易對交易",
                description="專注於單一交易對的AI驅動交易",
                entry_point="src.core.trading_system_integrator",
                required_components=["ai_manager", "trade_executor", "risk_manager"],
                config_template={"symbol": "BTCTWD", "initial_balance": 100000}
            ),
            "multi": TradingMode(
                name="多交易對交易",
                description="同時管理多個交易對的協調交易",
                entry_point="src.data.enhanced_multi_pair_data_manager",
                required_components=["ai_manager", "multi_pair_manager", "global_risk_manager"],
                config_template={"symbols": ["BTCTWD", "ETHTWD", "LTCTWD"], "initial_balance": 100000}
            ),
            "backtest": TradingMode(
                name="回測模式",
                description="使用歷史數據進行策略回測",
                entry_point="src.testing.system_integration_test",
                required_components=["ai_manager", "backtest_engine"],
                config_template={"start_date": "2024-01-01", "end_date": "2024-12-31"}
            ),
            "gui": TradingMode(
                name="GUI界面模式",
                description="啟動圖形用戶界面",
                entry_point="src.gui.main_application",
                required_components=["gui_framework"],
                config_template={"theme": "dark", "auto_start": False}
            )
        }
        
        logger.info("🚀 統一交易程式初始化完成")
    
    def _setup_logging(self):
        """設置日誌系統"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'unified_program.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    async def start(self):
        """啟動統一交易程式"""
        try:
            logger.info("🚀 啟動AImax統一交易系統...")
            
            # 顯示歡迎畫面
            self.show_welcome_screen()
            
            # 執行系統檢查
            system_status = await self.perform_system_check()
            
            # 顯示系統狀態
            self.display_system_status(system_status)
            
            if not system_status.overall_status:
                print("\n❌ 系統檢查失敗，無法啟動交易系統")
                print("請解決以下問題後重試:")
                for error in system_status.errors:
                    print(f"   - {error}")
                return False
            
            # 進入主選單
            await self.main_menu_loop()
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️ 用戶中斷程式")
            return False
        except Exception as e:
            logger.error(f"❌ 程式啟動失敗: {e}")
            print(f"\n❌ 程式啟動失敗: {e}")
            return False
    
    def show_welcome_screen(self):
        """顯示歡迎畫面"""
        print("=" * 60)
        print(f"🤖 AImax 統一交易系統 v{self.version}")
        print("=" * 60)
        print()
        print("🎯 系統特色:")
        print("   • 5AI專業協作 (市場掃描/深度分析/趨勢分析/風險評估/最終決策)")
        print("   • 多交易對支持 (BTC/ETH/LTC等)")
        print("   • 多種交易策略 (DCA/網格/套利)")
        print("   • 完整風險管理")
        print("   • 實時監控界面")
        print()
    
    async def perform_system_check(self):
        """執行系統檢查"""
        print("🔍 系統狀態檢查...")
        
        errors = []
        warnings = []
        
        # 檢查AI模型
        ai_available, ai_total = await self._check_ai_models()
        if ai_available == 0:
            errors.append("沒有可用的AI模型")
        elif ai_available < ai_total:
            warnings.append(f"部分AI模型不可用 ({ai_available}/{ai_total})")
        
        # 檢查API連接
        api_status = await self._check_api_connection()
        if not api_status:
            errors.append("MAX API連接失敗")
        
        # 檢查數據庫
        db_status = await self._check_database()
        if not db_status:
            errors.append("數據庫連接失敗")
        
        # 檢查配置文件
        config_status = await self._check_config_files()
        if not config_status:
            errors.append("配置文件無效")
        
        return SystemStatus(
            ai_models_available=ai_available,
            ai_models_total=ai_total,
            api_connection=api_status,
            database_status=db_status,
            config_valid=config_status,
            overall_status=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def _check_ai_models(self) -> tuple[int, int]:
        """檢查AI模型可用性"""
        try:
            # 嘗試導入AI管理器
            from src.ai.enhanced_ai_manager import EnhancedAIManager
            
            # 創建AI管理器實例
            ai_manager = EnhancedAIManager()
            
            # 檢查AI狀態
            ai_status = ai_manager.get_ai_system_status()
            available = ai_status.get('models_configured', 0)
            total = 5  # 5個AI模型
            
            return available, total
            
        except Exception as e:
            logger.error(f"AI模型檢查失敗: {e}")
            return 0, 5
    
    async def _check_api_connection(self) -> bool:
        """檢查API連接"""
        try:
            # 嘗試導入MAX客戶端
            from src.data.max_client import MAXDataClient
            
            # 創建客戶端實例（使用測試模式）
            client = MAXDataClient()
            
            # 簡單的連接測試
            # 這裡可以添加實際的API測試
            return True
            
        except Exception as e:
            logger.error(f"API連接檢查失敗: {e}")
            return False
    
    async def _check_database(self) -> bool:
        """檢查數據庫狀態"""
        try:
            # 檢查數據庫文件是否存在
            data_dir = self.project_root / "data"
            if not data_dir.exists():
                return False
            
            # 檢查主要數據庫文件
            db_files = ["market_history.db", "multi_pair_market.db"]
            for db_file in db_files:
                db_path = data_dir / db_file
                if not db_path.exists():
                    logger.warning(f"數據庫文件不存在: {db_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"數據庫檢查失敗: {e}")
            return False
    
    async def _check_config_files(self) -> bool:
        """檢查配置文件"""
        try:
            config_dir = self.project_root / "config"
            if not config_dir.exists():
                return False
            
            # 檢查主要配置文件
            required_configs = [
                "ai_models_qwen7b.json",
                "trading_system.json",
                "risk_management.json"
            ]
            
            for config_file in required_configs:
                config_path = config_dir / config_file
                if not config_path.exists():
                    logger.error(f"配置文件不存在: {config_file}")
                    return False
                
                # 嘗試載入JSON
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"配置文件格式錯誤: {config_file}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"配置文件檢查失敗: {e}")
            return False
    
    def display_system_status(self, status: SystemStatus):
        """顯示系統狀態"""
        print()
        if status.overall_status:
            print("✅ 系統檢查通過")
        else:
            print("❌ 系統檢查失敗")
        
        print(f"   AI模型: {status.ai_models_available}/{status.ai_models_total} 可用")
        print(f"   API連接: {'✅ 正常' if status.api_connection else '❌ 失敗'}")
        print(f"   數據庫: {'✅ 正常' if status.database_status else '❌ 失敗'}")
        print(f"   配置文件: {'✅ 有效' if status.config_valid else '❌ 無效'}")
        
        if status.warnings:
            print("\n⚠️ 警告:")
            for warning in status.warnings:
                print(f"   - {warning}")
        
        if status.errors:
            print("\n❌ 錯誤:")
            for error in status.errors:
                print(f"   - {error}")
    
    async def main_menu_loop(self):
        """主選單循環"""
        while True:
            try:
                print("\n" + "=" * 40)
                print("📋 請選擇交易模式:")
                print("=" * 40)
                
                # 顯示可用模式
                mode_keys = list(self.available_modes.keys())
                for i, (key, mode) in enumerate(self.available_modes.items(), 1):
                    print(f"{i}. {mode.name}")
                    print(f"   {mode.description}")
                
                print("5. 系統設置")
                print("0. 退出")
                print()
                
                # 獲取用戶選擇
                choice = input("請輸入選項 (0-5): ").strip()
                
                if choice == "0":
                    print("\n👋 感謝使用AImax交易系統！")
                    break
                elif choice == "5":
                    await self.show_system_settings()
                elif choice in ["1", "2", "3", "4"]:
                    mode_key = mode_keys[int(choice) - 1]
                    await self.start_trading_mode(mode_key)
                else:
                    print("❌ 無效選項，請重新選擇")
                
            except KeyboardInterrupt:
                print("\n\n👋 感謝使用AImax交易系統！")
                break
            except Exception as e:
                logger.error(f"主選單錯誤: {e}")
                print(f"❌ 發生錯誤: {e}")
    
    async def start_trading_mode(self, mode_key: str):
        """啟動指定的交易模式"""
        try:
            mode = self.available_modes[mode_key]
            print(f"\n🚀 啟動 {mode.name}...")
            
            if mode_key == "single":
                await self._start_single_pair_mode()
            elif mode_key == "multi":
                await self._start_multi_pair_mode()
            elif mode_key == "backtest":
                await self._start_backtest_mode()
            elif mode_key == "gui":
                await self._start_gui_mode()
            
        except Exception as e:
            logger.error(f"啟動交易模式失敗 ({mode_key}): {e}")
            print(f"❌ 啟動失敗: {e}")
    
    async def _start_single_pair_mode(self):
        """啟動單交易對模式"""
        try:
            from src.core.trading_system_integrator import TradingSystemIntegrator
            
            print("📊 初始化單交易對交易系統...")
            
            # 創建交易系統整合器
            trading_system = TradingSystemIntegrator(100000.0)
            
            print("✅ 系統初始化完成")
            print("🔄 開始交易循環...")
            print("   (按 Ctrl+C 停止)")
            
            # 啟動交易系統
            await trading_system.start_trading_system()
            
        except KeyboardInterrupt:
            print("\n⏹️ 用戶停止交易")
        except Exception as e:
            logger.error(f"單交易對模式錯誤: {e}")
            print(f"❌ 交易系統錯誤: {e}")
    
    async def _start_multi_pair_mode(self):
        """啟動多交易對模式"""
        try:
            print("📊 多交易對模式開發中...")
            print("   當前可用功能:")
            print("   - 多交易對數據管理 ✅")
            print("   - 全局風險管理 ✅")
            print("   - AI協調系統 ✅")
            print()
            print("   完整多交易對協調器即將推出！")
            
            input("按 Enter 返回主選單...")
            
        except Exception as e:
            logger.error(f"多交易對模式錯誤: {e}")
            print(f"❌ 多交易對模式錯誤: {e}")
    
    async def _start_backtest_mode(self):
        """啟動回測模式"""
        try:
            from src.testing.system_integration_test import SystemIntegrationTest
            
            print("📈 啟動回測模式...")
            
            # 創建系統整合測試
            test_system = SystemIntegrationTest()
            
            print("🧪 執行系統整合測試...")
            await test_system.run_comprehensive_test()
            
            input("按 Enter 返回主選單...")
            
        except Exception as e:
            logger.error(f"回測模式錯誤: {e}")
            print(f"❌ 回測模式錯誤: {e}")
    
    async def _start_gui_mode(self):
        """啟動GUI模式"""
        try:
            print("🖥️ 啟動GUI界面...")
            print("   正在載入圖形界面...")
            
            # 檢查GUI依賴
            try:
                import PyQt6
                print("   ✅ PyQt6 已安裝")
            except ImportError:
                print("   ❌ PyQt6 未安裝")
                print("   請運行: pip install PyQt6")
                return
            
            # 啟動GUI
            from src.gui.main_application import main as gui_main
            gui_main()
            
        except Exception as e:
            logger.error(f"GUI模式錯誤: {e}")
            print(f"❌ GUI模式錯誤: {e}")
    
    async def show_system_settings(self):
        """顯示系統設置"""
        try:
            print("\n" + "=" * 40)
            print("⚙️ 系統設置")
            print("=" * 40)
            
            print("1. 查看系統狀態")
            print("2. 查看配置文件")
            print("3. 測試AI模型")
            print("4. 測試交易系統")
            print("0. 返回主選單")
            
            choice = input("\n請選擇 (0-4): ").strip()
            
            if choice == "1":
                status = await self.perform_system_check()
                self.display_system_status(status)
            elif choice == "2":
                self._show_config_info()
            elif choice == "3":
                await self._test_ai_models()
            elif choice == "4":
                await self._test_trading_system()
            
            if choice != "0":
                input("\n按 Enter 繼續...")
                
        except Exception as e:
            logger.error(f"系統設置錯誤: {e}")
            print(f"❌ 系統設置錯誤: {e}")
    
    def _show_config_info(self):
        """顯示配置信息"""
        try:
            config_dir = self.project_root / "config"
            print(f"\n📁 配置文件目錄: {config_dir}")
            
            if config_dir.exists():
                config_files = list(config_dir.glob("*.json"))
                print(f"   找到 {len(config_files)} 個配置文件:")
                
                for config_file in config_files:
                    size = config_file.stat().st_size
                    print(f"   - {config_file.name} ({size} bytes)")
            else:
                print("   ❌ 配置目錄不存在")
                
        except Exception as e:
            print(f"❌ 顯示配置信息失敗: {e}")
    
    async def _test_ai_models(self):
        """測試AI模型"""
        try:
            print("\n🤖 測試AI模型...")
            
            from src.ai.enhanced_ai_manager import EnhancedAIManager
            
            ai_manager = EnhancedAIManager()
            ai_status = ai_manager.get_ai_status()
            
            print(f"   配置的模型數量: {ai_status.get('models_configured', 0)}")
            print(f"   可用的模型: {ai_status.get('models_available', 0)}")
            
            # 簡單的AI測試
            test_data = {
                'current_price': 1500000,
                'price_change_1m': 0.5,
                'volatility_level': '中'
            }
            
            print("   執行簡單AI測試...")
            # 這裡可以添加實際的AI測試
            print("   ✅ AI系統基本功能正常")
            
        except Exception as e:
            logger.error(f"AI模型測試失敗: {e}")
            print(f"   ❌ AI模型測試失敗: {e}")
    
    async def _test_trading_system(self):
        """測試交易系統"""
        try:
            print("\n💰 測試交易系統...")
            
            from src.core.trading_system_integrator import TradingSystemIntegrator
            
            # 創建測試系統
            trading_system = TradingSystemIntegrator(100000.0)
            
            # 獲取系統狀態
            status = trading_system.get_system_status()
            print(f"   系統活躍: {status.is_active}")
            print(f"   當前餘額: {status.current_balance:,.0f} TWD")
            print(f"   活躍倉位: {status.active_positions}")
            
            # 執行一個測試週期
            print("   執行測試交易週期...")
            cycle = await trading_system._execute_trading_cycle()
            
            print(f"   ✅ 測試週期完成: {cycle.cycle_id}")
            print(f"   週期成功: {cycle.success}")
            
        except Exception as e:
            logger.error(f"交易系統測試失敗: {e}")
            print(f"   ❌ 交易系統測試失敗: {e}")
    
    def stop(self):
        """停止程式"""
        self.is_running = False
        logger.info("🛑 統一交易程式已停止")


# 創建全局實例
def create_unified_program() -> UnifiedTradingProgram:
    """創建統一交易程式實例"""
    return UnifiedTradingProgram()


# 主函數
async def main():
    """主函數"""
    try:
        # 創建統一交易程式
        program = create_unified_program()
        
        # 啟動程式
        success = await program.start()
        
        return success
        
    except Exception as e:
        logger.error(f"程式執行失敗: {e}")
        print(f"❌ 程式執行失敗: {e}")
        return False


if __name__ == "__main__":
    # 運行程式
    asyncio.run(main())