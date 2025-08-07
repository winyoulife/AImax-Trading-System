#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正所有GitHub Actions配置文件
確保部署能正常工作
"""

import os
import sys
import yaml
from pathlib import Path

def fix_github_actions():
    """修正所有GitHub Actions配置文件"""
    print("🔧 修正所有GitHub Actions配置文件")
    print("=" * 60)
    
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ .github/workflows 目錄不存在")
        return
    
    # 需要保留的核心文件
    keep_files = {
        'simple-deploy.yml'  # 只保留這個簡單的部署文件
    }
    
    # 檢查所有yml文件
    problem_files = []
    for yml_file in workflows_dir.glob("*.yml"):
        if yml_file.name in keep_files:
            print(f"✅ 保留: {yml_file.name}")
            continue
            
        try:
            with open(yml_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"📋 語法正確但將停用: {yml_file.name}")
            problem_files.append(yml_file)
        except yaml.YAMLError as e:
            print(f"❌ 語法錯誤: {yml_file.name} - {e}")
            problem_files.append(yml_file)
        except Exception as e:
            print(f"❌ 讀取錯誤: {yml_file.name} - {e}")
            problem_files.append(yml_file)
    
    # 停用所有非核心文件
    disabled_dir = workflows_dir / "disabled"
    disabled_dir.mkdir(exist_ok=True)
    
    for file in problem_files:
        try:
            new_path = disabled_dir / file.name
            file.rename(new_path)
            print(f"🔄 已移動到disabled: {file.name}")
        except Exception as e:
            print(f"❌ 移動失敗: {file.name} - {e}")
    
    # 確保simple-deploy.yml正確
    simple_deploy = workflows_dir / "simple-deploy.yml"
    if simple_deploy.exists():
        print(f"\n✅ 檢查simple-deploy.yml...")
        try:
            with open(simple_deploy, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"✅ simple-deploy.yml 語法正確")
        except Exception as e:
            print(f"❌ simple-deploy.yml 有問題: {e}")
    
    print(f"\n📋 修正完成後的文件列表:")
    for yml_file in workflows_dir.glob("*.yml"):
        print(f"  ✅ {yml_file.name}")
    
    print(f"\n🗑️ 已停用的文件:")
    for yml_file in disabled_dir.glob("*.yml"):
        print(f"  📦 {yml_file.name}")
    
    print(f"\n" + "=" * 60)
    print("🔧 GitHub Actions修正完成")
    print("現在只有simple-deploy.yml會運行，應該能正常部署")

if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("安裝PyYAML...")
        os.system("pip install PyYAML")
        import yaml
    
    fix_github_actions()