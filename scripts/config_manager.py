#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易對配置管理工具 - 提供命令行界面管理動態配置
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.multi_pair_max_client import create_multi_pair_client
from src.data.trading_pair_manager import create_trading_pair_manager
from src.data.multi_pair_data_manager import create_multi_pair_data_manager
from src.data.dynamic_config_system import create_dynamic_config_system

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.max_client = None
        self.pair_manager = None
        self.data_manager = None
        self.config_system = None
    
    async def initialize(self):
        """初始化系統組件"""
        print("📦 初始化系統組件...")
        self.max_client = create_multi_pair_client()
        self.pair_manager = create_trading_pair_manager()
        self.data_manager = create_multi_pair_data_manager()
        self.config_system = create_dynamic_config_system(
            self.pair_manager, self.max_client, self.data_manager
        )
        print("✅ 系統組件初始化完成")
    
    def show_menu(self):
        """顯示主菜單"""
        print("\n" + "="*50)
        print("🔧 AImax 交易對配置管理工具")
        print("="*50)
        print("1. 查看所有交易對配置")
        print("2. 查看單個交易對配置")
        print("3. 更新交易對配置")
        print("4. 應用配置模板")
        print("5. 查看配置變更歷史")
        print("6. 驗證配置")
        print("7. 系統狀態")
        print("8. 自動優化配置")
        print("0. 退出")
        print("="*50)
    
    def show_all_configs(self):
        """顯示所有交易對配置"""
        print("\n📊 所有交易對配置:")
        print("-" * 80)
        print(f"{'交易對':<10} {'風險權重':<10} {'API限流':<10} {'超時':<8} {'重試':<8} {'狀態':<8}")
        print("-" * 80)
        
        for pair, config in self.pair_manager.pair_configs.items():
            status = "啟用" if config.enabled else "禁用"
            print(f"{pair:<10} {config.risk_weight:<10.3f} {config.api_rate_limit:<10.3f} "
                  f"{config.timeout:<8} {config.max_retries:<8} {status:<8}")
    
    def show_single_config(self, pair: str):
        """顯示單個交易對配置"""
        if pair not in self.pair_manager.pair_configs:
            print(f"❌ 交易對 {pair} 不存在")
            return
        
        config = self.pair_manager.pair_configs[pair]
        print(f"\n📋 {pair} 詳細配置:")
        print("-" * 40)
        print(f"交易對: {config.pair}")
        print(f"最小訂單大小: {config.min_order_size}")
        print(f"最大倉位大小: {config.max_position_size}")
        print(f"風險權重: {config.risk_weight}")
        print(f"API限流間隔: {config.api_rate_limit}秒")
        print(f"最大重試次數: {config.max_retries}")
        print(f"超時時間: {config.timeout}秒")
        print(f"精度: {config.precision}")
        print(f"最小名義價值: {config.min_notional}")
        print(f"狀態: {'啟用' if config.enabled else '禁用'}")
    
    async def update_config(self, pair: str, updates: Dict[str, Any]):
        """更新交易對配置"""
        if pair not in self.pair_manager.pair_configs:
            print(f"❌ 交易對 {pair} 不存在")
            return
        
        print(f"\n🔄 更新 {pair} 配置...")
        result = await self.config_system.apply_hot_update(
            pair, updates, user='config_manager', reason='手動配置更新'
        )
        
        if result.success:
            print("✅ 配置更新成功!")
            print(f"應用的變更: {result.changes_applied}")
            if result.warnings:
                print(f"⚠️ 警告: {result.warnings}")
        else:
            print("❌ 配置更新失敗!")
            print(f"錯誤: {result.errors}")
    
    def apply_template(self, pair: str, template_name: str):
        """應用配置模板"""
        if pair not in self.pair_manager.pair_configs:
            print(f"❌ 交易對 {pair} 不存在")
            return
        
        print(f"\n📋 為 {pair} 應用 {template_name} 模板...")
        success = self.config_system.apply_config_template(pair, template_name)
        
        if success:
            print("✅ 模板應用成功!")
        else:
            print("❌ 模板應用失敗!")
    
    def show_change_history(self, pair: str = None, limit: int = 10):
        """顯示配置變更歷史"""
        print(f"\n📜 配置變更歷史 (最近{limit}條):")
        print("-" * 100)
        print(f"{'時間':<20} {'交易對':<10} {'類型':<10} {'字段':<15} {'變更':<30}")
        print("-" * 100)
        
        history = self.config_system.get_config_change_history(pair, limit)
        
        for event in history:
            timestamp = event['timestamp'][:19].replace('T', ' ')
            change_type = event['change_type']
            field_name = event.get('field_name', 'N/A')
            
            if event['old_value'] is not None and event['new_value'] is not None:
                change_desc = f"{event['old_value']} -> {event['new_value']}"
            else:
                change_desc = str(event['new_value'])
            
            change_desc = change_desc[:28] + "..." if len(change_desc) > 30 else change_desc
            
            print(f"{timestamp:<20} {event['pair']:<10} {change_type:<10} "
                  f"{field_name:<15} {change_desc:<30}")
    
    def validate_config(self, pair: str):
        """驗證配置"""
        if pair not in self.pair_manager.pair_configs:
            print(f"❌ 交易對 {pair} 不存在")
            return
        
        config = self.pair_manager.pair_configs[pair]
        is_valid, errors, warnings = self.config_system.validate_config(pair, config)
        
        print(f"\n✅ {pair} 配置驗證結果:")
        print(f"驗證狀態: {'通過' if is_valid else '失敗'}")
        
        if errors:
            print("❌ 錯誤:")
            for error in errors:
                print(f"   - {error}")
        
        if warnings:
            print("⚠️ 警告:")
            for warning in warnings:
                print(f"   - {warning}")
        
        if is_valid and not warnings:
            print("🎉 配置完全正確!")
    
    def show_system_status(self):
        """顯示系統狀態"""
        status = self.config_system.get_system_status()
        
        print("\n💊 系統狀態:")
        print("-" * 40)
        print(f"熱更新: {'啟用' if status['hot_update_enabled'] else '禁用'}")
        print(f"自動優化: {'啟用' if status['auto_optimization_enabled'] else '禁用'}")
        print(f"優化間隔: {status['optimization_interval']}秒")
        print(f"交易對總數: {status['total_pairs']}")
        print(f"驗證規則: {status['validation_rules_count']}個")
        print(f"優化規則: {status['optimization_rules_count']}個")
        print(f"配置模板: {status['config_templates_count']}個")
        print(f"變更記錄: {status['change_history_count']}條")
    
    async def auto_optimize(self):
        """執行自動優化"""
        print("\n🔧 執行自動優化...")
        
        # 獲取模擬市場數據進行優化
        mock_market_data = {}
        for pair in self.pair_manager.pair_configs:
            mock_market_data[pair] = {
                'volatility': 0.03,
                'volume_ratio': 1.2,
                'api_latency': 2.0,
                'price_trend_slope': 0.05
            }
        
        result = await self.config_system.auto_optimize_configurations(mock_market_data)
        
        print(f"優化狀態: {result.get('status', 'completed')}")
        
        if 'optimized_pairs' in result:
            print(f"優化的交易對: {len(result['optimized_pairs'])}")
            for opt in result['optimized_pairs']:
                print(f"  {opt['pair']}: {opt['changes']}")
        
        if 'errors' in result and result['errors']:
            print("❌ 優化錯誤:")
            for error in result['errors']:
                print(f"  - {error}")
    
    def show_available_templates(self):
        """顯示可用的配置模板"""
        templates_file = Path("AImax/configs/dynamic/config_templates.json")
        
        if templates_file.exists():
            with open(templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            
            print("\n📋 可用的配置模板:")
            print("-" * 60)
            for name, template in templates.items():
                desc = template.get('description', '無描述')
                print(f"{name:<15} - {desc}")
        else:
            print("❌ 配置模板文件不存在")
    
    async def run(self):
        """運行配置管理器"""
        await self.initialize()
        
        try:
            while True:
                self.show_menu()
                choice = input("\n請選擇操作 (0-8): ").strip()
                
                if choice == '0':
                    print("👋 退出配置管理工具")
                    break
                elif choice == '1':
                    self.show_all_configs()
                elif choice == '2':
                    pair = input("請輸入交易對名稱 (如 BTCTWD): ").strip().upper()
                    self.show_single_config(pair)
                elif choice == '3':
                    pair = input("請輸入交易對名稱: ").strip().upper()
                    print("可更新的字段: risk_weight, api_rate_limit, timeout, max_retries")
                    field = input("請輸入要更新的字段: ").strip()
                    value_str = input("請輸入新值: ").strip()
                    
                    try:
                        # 嘗試轉換為適當的類型
                        if field in ['timeout', 'max_retries']:
                            value = int(value_str)
                        else:
                            value = float(value_str)
                        
                        await self.update_config(pair, {field: value})
                    except ValueError:
                        print("❌ 無效的數值格式")
                elif choice == '4':
                    self.show_available_templates()
                    pair = input("請輸入交易對名稱: ").strip().upper()
                    template = input("請輸入模板名稱: ").strip()
                    self.apply_template(pair, template)
                elif choice == '5':
                    pair = input("請輸入交易對名稱 (留空查看全部): ").strip().upper()
                    pair = pair if pair else None
                    limit = input("請輸入顯示條數 (默認10): ").strip()
                    limit = int(limit) if limit.isdigit() else 10
                    self.show_change_history(pair, limit)
                elif choice == '6':
                    pair = input("請輸入交易對名稱: ").strip().upper()
                    self.validate_config(pair)
                elif choice == '7':
                    self.show_system_status()
                elif choice == '8':
                    await self.auto_optimize()
                else:
                    print("❌ 無效的選擇，請重新輸入")
                
                input("\n按 Enter 繼續...")
        
        except KeyboardInterrupt:
            print("\n⚠️ 用戶中斷操作")
        except Exception as e:
            print(f"❌ 運行錯誤: {e}")
        finally:
            # 清理資源
            try:
                await self.max_client.close()
                await self.data_manager.close()
            except Exception as e:
                print(f"❌ 清理資源失敗: {e}")

async def main():
    """主函數"""
    manager = ConfigManager()
    await manager.run()

if __name__ == "__main__":
    asyncio.run(main())