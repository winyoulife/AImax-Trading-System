#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復所有儀表板標題和策略顯示
確保所有用戶看到的都是智能平衡策略
"""

import os
import re
from pathlib import Path

class DashboardTitleFixer:
    """儀表板標題修復器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.fixed_files = []
        
        # 定義所有需要替換的模式
        self.replacements = [
            # 標題替換
            (r'終極智能交易儀表板', '智能平衡交易儀表板'),
            (r'終極智能交易系統', '智能平衡交易系統'),
            
            # 勝率替換
            (r'85%勝率策略', '83.3%勝率策略'),
            (r'85%勝率', '83.3%勝率'),
            
            # 系統描述替換
            (r'高頻智能交易系統', '智能平衡交易系統'),
            (r'高頻交易系統', '智能平衡交易系統'),
            
            # 策略名稱替換
            (r'Clean Ultimate 85%勝率策略', '智能平衡 83.3%勝率策略'),
            (r'Clean Ultimate策略', '智能平衡策略'),
            
            # 版本替換
            (r'AImax v3\.0', 'AImax v1.0-smart-balanced'),
            (r'終極智能交易儀表板 v3\.0', '智能平衡交易儀表板 v1.0'),
        ]
    
    def should_skip_file(self, file_path):
        """檢查是否應該跳過此檔案"""
        skip_patterns = [
            '.git/',
            '__pycache__/',
            '.pyc',
            'node_modules/',
            'ultimate_optimized_volume_macd_signals.py',  # 保留原始檔案
            'test_ultimate_optimized_strategy.py',  # 保留測試檔案
            'CORE_STRATEGY_BACKUP.py',  # 保留備份檔案
            'fix_all_dashboard_titles.py',  # 跳過自己
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def fix_file(self, file_path):
        """修復單個檔案"""
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
                self.fixed_files.append(str(file_path))
                print(f"✅ 已修復: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 修復失敗 {file_path}: {e}")
            return False
    
    def scan_and_fix(self):
        """掃描並修復所有檔案"""
        print("🔍 掃描需要修復的檔案...")
        
        # 掃描所有相關檔案類型
        file_patterns = ["*.html", "*.py", "*.js", "*.yml", "*.yaml", "*.md"]
        all_files = []
        
        for pattern in file_patterns:
            all_files.extend(list(self.project_root.rglob(pattern)))
        
        print(f"📁 找到 {len(all_files)} 個檔案")
        
        fixed_count = 0
        for file_path in all_files:
            if self.should_skip_file(file_path):
                continue
            
            if self.fix_file(file_path):
                fixed_count += 1
        
        print(f"\n🎉 修復完成！共修復了 {fixed_count} 個檔案")
        
        if self.fixed_files:
            print("\n📋 已修復的檔案列表:")
            for file_path in self.fixed_files:
                print(f"   - {file_path}")
        
        return fixed_count > 0
    
    def verify_fixes(self):
        """驗證修復結果"""
        print("\n🔍 驗證修復結果...")
        
        # 檢查是否還有舊的標題
        old_patterns = [
            '終極智能交易儀表板',
            '85%勝率策略',
            '高頻智能交易系統',
        ]
        
        issues_found = []
        
        for pattern in old_patterns:
            print(f"   檢查模式: {pattern}")
            
            # 搜尋HTML檔案（最重要的用戶界面檔案）
            html_files = list(self.project_root.rglob("*.html"))
            
            for file_path in html_files:
                if self.should_skip_file(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern in content:
                            issues_found.append((str(file_path), pattern))
                except:
                    continue
        
        if issues_found:
            print("\n⚠️ 發現未修復的檔案:")
            for file_path, pattern in issues_found:
                print(f"   - {file_path}: {pattern}")
            return False
        else:
            print("\n✅ 所有用戶界面檔案都已正確更新！")
            return True

def main():
    """主函數"""
    print("🔧 儀表板標題和策略顯示修復工具")
    print("="*60)
    print("確保所有用戶看到的都是智能平衡策略 (83.3%勝率)")
    print("="*60)
    
    fixer = DashboardTitleFixer()
    
    # 執行修復
    success = fixer.scan_and_fix()
    
    if success:
        # 驗證修復結果
        verification_success = fixer.verify_fixes()
        
        if verification_success:
            print("\n🎉 所有用戶界面已成功更新！")
            print("🏆 用戶現在將看到智能平衡策略 (83.3%勝率)")
            print("🚀 請推送到GitHub以更新雲端部署")
            return 0
        else:
            print("\n⚠️ 部分檔案可能需要手動檢查")
            return 1
    else:
        print("\n📝 沒有檔案需要修復")
        return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())