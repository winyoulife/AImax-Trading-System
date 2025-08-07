#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新所有檔案使用智能平衡策略
確保沒有任何檔案還在使用舊的終極優化策略
"""

import os
import re
from pathlib import Path

class SmartBalancedUpdater:
    """智能平衡策略批量更新器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.updated_files = []
        self.replacements = [
            # 策略類別替換
            (r'from src\.core\.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals',
             'from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals'),
            
            (r'from src\.core\.ultimate_optimized_volume_macd_signals import UltimateOptimizedVolumeEnhancedMACDSignals',
             'from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals'),
            
            (r'UltimateOptimizedVolumeEnhancedMACDSignals\(\)',
             'SmartBalancedVolumeEnhancedMACDSignals()'),
            
            # 方法名稱替換
            (r'\.detect_signals\(',
             '.detect_smart_balanced_signals('),
            
            (r'\.detect_ultimate_optimized_signals\(',
             '.detect_smart_balanced_signals('),
            
            # 策略名稱替換
            (r"'smart_balanced_83.3_percent'",
             "'smart_balanced_83.3_percent'"),
            
            (r"'smart_balanced_83.3%_winrate'",
             "'smart_balanced_83.3%_winrate'"),
            
            (r"'smart_balanced'",
             "'smart_balanced'"),
            
            (r'"smart_balanced_83.3_percent"',
             '"smart_balanced_83.3_percent"'),
            
            (r'"smart_balanced_83.3%_winrate"',
             '"smart_balanced_83.3%_winrate"'),
            
            (r'"smart_balanced"',
             '"smart_balanced"'),
            
            # 配置檔案中的策略名稱
            (r'"src\.core\.clean_ultimate_signals"',
             '"src.core.smart_balanced_volume_macd_signals"'),
        ]
    
    def should_skip_file(self, file_path):
        """檢查是否應該跳過此檔案"""
        skip_patterns = [
            '.git/',
            '__pycache__/',
            '.pyc',
            'node_modules/',
            '.md',  # 跳過文檔檔案
            'ultimate_optimized_volume_macd_signals.py',  # 保留原始檔案作為參考
            'test_ultimate_optimized_strategy.py',  # 保留測試檔案
            'CORE_STRATEGY_BACKUP.py',  # 保留備份檔案
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def update_file(self, file_path):
        """更新單個檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            updated = False
            
            # 應用所有替換規則
            for pattern, replacement in self.replacements:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    updated = True
            
            # 如果有更新，寫回檔案
            if updated:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.updated_files.append(str(file_path))
                print(f"✅ 已更新: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 更新失敗 {file_path}: {e}")
            return False
    
    def scan_and_update(self):
        """掃描並更新所有檔案"""
        print("🔍 掃描項目檔案...")
        
        # 掃描所有Python檔案
        python_files = list(self.project_root.rglob("*.py"))
        
        # 掃描所有JavaScript檔案
        js_files = list(self.project_root.rglob("*.js"))
        
        # 掃描所有HTML檔案
        html_files = list(self.project_root.rglob("*.html"))
        
        # 掃描所有YAML檔案
        yaml_files = list(self.project_root.rglob("*.yml"))
        yaml_files.extend(list(self.project_root.rglob("*.yaml")))
        
        # 掃描所有JSON檔案
        json_files = list(self.project_root.rglob("*.json"))
        
        all_files = python_files + js_files + html_files + yaml_files + json_files
        
        print(f"📁 找到 {len(all_files)} 個檔案")
        
        updated_count = 0
        for file_path in all_files:
            if self.should_skip_file(file_path):
                continue
            
            if self.update_file(file_path):
                updated_count += 1
        
        print(f"\n🎉 更新完成！共更新了 {updated_count} 個檔案")
        
        if self.updated_files:
            print("\n📋 已更新的檔案列表:")
            for file_path in self.updated_files:
                print(f"   - {file_path}")
        
        return updated_count > 0
    
    def verify_updates(self):
        """驗證更新結果"""
        print("\n🔍 驗證更新結果...")
        
        # 檢查是否還有舊的策略引用
        old_patterns = [
            'clean_ultimate_signals',
            'smart_balanced_83.3_percent',
            'smart_balanced_83.3%_winrate',
        ]
        
        issues_found = []
        
        for pattern in old_patterns:
            print(f"   檢查模式: {pattern}")
            
            # 搜尋所有檔案
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file() and not self.should_skip_file(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if pattern in content:
                                issues_found.append((str(file_path), pattern))
                    except:
                        continue
        
        if issues_found:
            print("\n⚠️ 發現未更新的檔案:")
            for file_path, pattern in issues_found:
                print(f"   - {file_path}: {pattern}")
            return False
        else:
            print("\n✅ 所有檔案都已正確更新為智能平衡策略！")
            return True

def main():
    """主函數"""
    print("🔄 智能平衡策略批量更新工具")
    print("="*60)
    print("確保所有檔案都使用83.3%勝率的智能平衡策略")
    print("="*60)
    
    updater = SmartBalancedUpdater()
    
    # 執行更新
    success = updater.scan_and_update()
    
    if success:
        # 驗證更新結果
        verification_success = updater.verify_updates()
        
        if verification_success:
            print("\n🎉 所有檔案已成功更新為智能平衡策略！")
            print("🏆 現在所有雲端部署都將使用83.3%勝率策略")
            return 0
        else:
            print("\n⚠️ 部分檔案可能需要手動檢查")
            return 1
    else:
        print("\n📝 沒有檔案需要更新")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())