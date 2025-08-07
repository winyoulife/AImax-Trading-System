#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 雲端更新管理器
標準化的雲端部署和更新流程
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path

class CloudUpdateManager:
    """雲端更新管理器"""
    
    def __init__(self):
        self.config_file = "config/cloud_update_config.json"
        self.backup_dir = "backups/cloud_updates"
        self.static_dir = "static"
        self.main_dashboard = "smart-balanced-dashboard.html"
        self.load_config()
    
    def load_config(self):
        """載入配置"""
        default_config = {
            "main_dashboard_file": "smart-balanced-dashboard.html",
            "backup_enabled": True,
            "auto_version_increment": True,
            "target_files": [
                "smart-balanced-dashboard.html",
                "smart-balanced-dashboard-static.html"
            ],
            "version_format": "v{major}.{minor}-{tag}",
            "current_version": {"major": 2, "minor": 2, "tag": "realtime"}
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def create_backup(self):
        """創建備份"""
        if not self.config["backup_enabled"]:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, timestamp)
        os.makedirs(backup_path, exist_ok=True)
        
        # 備份所有目標文件
        for file in self.config["target_files"]:
            src = os.path.join(self.static_dir, file)
            if os.path.exists(src):
                dst = os.path.join(backup_path, file)
                shutil.copy2(src, dst)
                print(f"✅ 備份: {file}")
        
        return backup_path
    
    def increment_version(self):
        """自動增加版本號"""
        if self.config["auto_version_increment"]:
            self.config["current_version"]["minor"] += 1
            self.save_config()
    
    def get_version_string(self):
        """獲取版本字符串"""
        v = self.config["current_version"]
        return self.config["version_format"].format(
            major=v["major"], 
            minor=v["minor"], 
            tag=v["tag"]
        )
    
    def update_dashboard_content(self, updates):
        """更新儀表板內容"""
        main_file = os.path.join(self.static_dir, self.main_dashboard)
        
        if not os.path.exists(main_file):
            print(f"❌ 主文件不存在: {main_file}")
            return False
        
        # 讀取文件
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 應用更新
        for old_text, new_text in updates.items():
            if old_text in content:
                content = content.replace(old_text, new_text)
                print(f"✅ 更新: {old_text[:50]}... → {new_text[:50]}...")
            else:
                print(f"⚠️ 未找到: {old_text[:50]}...")
        
        # 更新版本信息
        version = self.get_version_string()
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")
        
        # 更新版本標識
        import re
        version_pattern = r'版本: v[\d\.]+-\w+ \| 更新時間: [\d/]+ [\d:]+'
        new_version = f'版本: {version} | 更新時間: {timestamp}'
        content = re.sub(version_pattern, new_version, content)
        
        # 寫入文件
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    
    def sync_all_files(self):
        """同步所有目標文件"""
        main_file = os.path.join(self.static_dir, self.main_dashboard)
        
        if not os.path.exists(main_file):
            print(f"❌ 主文件不存在: {main_file}")
            return False
        
        # 複製到所有目標文件
        for target_file in self.config["target_files"]:
            if target_file != self.main_dashboard:
                target_path = os.path.join(self.static_dir, target_file)
                shutil.copy2(main_file, target_path)
                print(f"✅ 同步: {target_file}")
        
        return True
    
    def deploy_to_cloud(self):
        """部署到雲端"""
        print("🚀 開始部署到雲端...")
        
        # Git 操作
        os.system("git add .")
        
        version = self.get_version_string()
        commit_msg = f"🔄 自動更新 {version} - {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        os.system(f'git commit -m "{commit_msg}"')
        os.system("git push origin main")
        
        print("✅ 部署完成")
    
    def full_update(self, updates=None):
        """完整更新流程"""
        print("🔄 開始完整更新流程")
        print("=" * 60)
        
        # 1. 創建備份
        backup_path = self.create_backup()
        if backup_path:
            print(f"📦 備份創建: {backup_path}")
        
        # 2. 增加版本號
        self.increment_version()
        version = self.get_version_string()
        print(f"📅 版本更新: {version}")
        
        # 3. 更新內容
        if updates:
            success = self.update_dashboard_content(updates)
            if not success:
                print("❌ 內容更新失敗")
                return False
        
        # 4. 同步所有文件
        self.sync_all_files()
        
        # 5. 部署到雲端
        self.deploy_to_cloud()
        
        print("=" * 60)
        print(f"🎉 更新完成！版本: {version}")
        print(f"🌐 請等待2-3分鐘後訪問頁面查看更新")
        
        return True

def main():
    """主函數"""
    manager = CloudUpdateManager()
    
    print("🔧 AImax 雲端更新管理器")
    print("=" * 60)
    
    # 示例更新
    updates = {
        # 可以在這裡添加需要更新的內容
        # "舊內容": "新內容"
    }
    
    # 執行完整更新
    manager.full_update(updates)

if __name__ == "__main__":
    main()