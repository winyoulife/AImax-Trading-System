#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 一鍵部署和配置腳本
自動化部署AImax智能交易系統到GitHub Pages
"""

import os
import sys
import json
import subprocess
import shutil
import hashlib
import getpass
from datetime import datetime
from pathlib import Path

class AIMaxDeployer:
    def __init__(self):
        self.project_name = "AImax-Trading-System"
        self.current_dir = Path.cwd()
        self.config = {}
        self.deployment_log = []
        
    def log(self, message, level="INFO"):
        """記錄部署日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)
        
    def check_prerequisites(self):
        """檢查部署前置條件"""
        self.log("🔍 檢查部署前置條件...")
        
        # 檢查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            self.log("❌ Python版本需要3.8或更高", "ERROR")
            return False
        self.log(f"✅ Python版本: {python_version.major}.{python_version.minor}")
        
        # 檢查Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✅ Git已安裝: {result.stdout.strip()}")
            else:
                self.log("❌ Git未安裝或無法訪問", "ERROR")
                return False
        except FileNotFoundError:
            self.log("❌ Git未安裝", "ERROR")
            return False
        
        # 檢查網路連接
        try:
            import urllib.request
            urllib.request.urlopen('https://github.com', timeout=10)
            self.log("✅ 網路連接正常")
        except Exception as e:
            self.log(f"❌ 網路連接失敗: {str(e)}", "ERROR")
            return False
        
        return True
    
    def interactive_config(self):
        """互動式配置嚮導"""
        self.log("🎯 開始互動式配置嚮導...")
        
        print("\n" + "="*60)
        print("🤖 歡迎使用 AImax 智能平衡交易系統部署嚮導 (83.3%勝率)")
        print("="*60)
        
        # GitHub配置
        print("\n📂 GitHub倉庫配置:")
        self.config['github_username'] = input("請輸入您的GitHub用戶名: ").strip()
        
        default_repo = f"{self.config['github_username']}-AImax-Trading"
        repo_name = input(f"請輸入倉庫名稱 (預設: {default_repo}): ").strip()
        self.config['repo_name'] = repo_name if repo_name else default_repo
        
        # 認證配置
        print("\n🔐 安全認證配置:")
        print("設置您的專屬登入帳號密碼")
        
        self.config['login_username'] = input("請輸入登入帳號 (預設: admin): ").strip() or "admin"
        
        while True:
            password = getpass.getpass("請輸入登入密碼: ")
            confirm_password = getpass.getpass("請確認密碼: ")
            if password == confirm_password and len(password) >= 6:
                self.config['login_password'] = password
                self.config['login_password_hash'] = hashlib.sha256(password.encode()).hexdigest()
                break
            else:
                print("❌ 密碼不匹配或長度不足6位，請重新輸入")
        
        # 交易配置
        print("\n💰 交易系統配置:")
        self.config['enable_trading'] = input("是否啟用真實交易 (y/N): ").lower().startswith('y')
        
        if self.config['enable_trading']:
            print("⚠️  真實交易需要配置交易所API密鑰")
            print("   請在部署完成後到GitHub Secrets中配置")
        
        # Telegram通知配置
        print("\n📱 Telegram通知配置:")
        enable_telegram = input("是否啟用Telegram通知 (y/N): ").lower().startswith('y')
        self.config['enable_telegram'] = enable_telegram
        
        if enable_telegram:
            print("📱 Telegram配置將在部署後進行")
            print("   請準備好您的Bot Token和Chat ID")
        
        # 部署模式
        print("\n🚀 部署模式選擇:")
        print("1. 完整部署 (推薦) - 包含所有功能")
        print("2. 基礎部署 - 僅包含核心功能")
        print("3. 開發模式 - 包含測試和調試功能")
        
        while True:
            mode_choice = input("請選擇部署模式 (1-3): ").strip()
            if mode_choice in ['1', '2', '3']:
                mode_map = {'1': 'full', '2': 'basic', '3': 'development'}
                self.config['deployment_mode'] = mode_map[mode_choice]
                break
            else:
                print("❌ 請輸入有效選項 (1-3)")
        
        # 確認配置
        print("\n📋 配置摘要:")
        print(f"   GitHub用戶: {self.config['github_username']}")
        print(f"   倉庫名稱: {self.config['repo_name']}")
        print(f"   登入帳號: {self.config['login_username']}")
        print(f"   真實交易: {'啟用' if self.config['enable_trading'] else '禁用'}")
        print(f"   Telegram: {'啟用' if self.config['enable_telegram'] else '禁用'}")
        print(f"   部署模式: {self.config['deployment_mode']}")
        
        confirm = input("\n確認以上配置並開始部署? (y/N): ").lower().startswith('y')
        if not confirm:
            self.log("❌ 用戶取消部署", "INFO")
            return False
        
        return True
    
    def create_project_structure(self):
        """創建項目結構"""
        self.log("📁 創建項目結構...")
        
        # 創建新的項目目錄
        project_dir = self.current_dir / self.config['repo_name']
        if project_dir.exists():
            self.log(f"⚠️  目錄 {project_dir} 已存在", "WARNING")
            overwrite = input("是否覆蓋現有目錄? (y/N): ").lower().startswith('y')
            if overwrite:
                shutil.rmtree(project_dir)
                self.log("🗑️  已刪除現有目錄")
            else:
                self.log("❌ 用戶取消覆蓋", "ERROR")
                return False
        
        # 複製項目文件
        try:
            shutil.copytree(self.current_dir, project_dir, 
                          ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.env'))
            self.log(f"✅ 項目結構創建完成: {project_dir}")
            self.project_dir = project_dir
            return True
        except Exception as e:
            self.log(f"❌ 創建項目結構失敗: {str(e)}", "ERROR")
            return False
    
    def customize_configuration(self):
        """自定義配置文件"""
        self.log("⚙️  自定義配置文件...")
        
        try:
            # 更新登入配置
            login_files = [
                self.project_dir / "static" / "secure-login-fixed.html",
                self.project_dir / "web_app.py"
            ]
            
            for file_path in login_files:
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 替換預設帳號密碼
                    content = content.replace('lovejk1314', self.config['login_username'])
                    content = content.replace('898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae', 
                                            self.config['login_password_hash'])
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.log(f"✅ 更新配置: {file_path.name}")
            
            # 創建部署配置文件
            deploy_config = {
                'project_name': self.config['repo_name'],
                'github_username': self.config['github_username'],
                'deployment_mode': self.config['deployment_mode'],
                'enable_trading': self.config['enable_trading'],
                'enable_telegram': self.config['enable_telegram'],
                'login_username': self.config['login_username'],
                'deployed_at': datetime.now().isoformat(),
                'version': 'v1.0-smart-balanced',
                'strategy': 'smart_balanced_83.3%_winrate'
            }
            
            config_file = self.project_dir / "aimax_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(deploy_config, f, indent=2, ensure_ascii=False)
            
            self.log("✅ 部署配置文件創建完成")
            return True
            
        except Exception as e:
            self.log(f"❌ 自定義配置失敗: {str(e)}", "ERROR")
            return False
    
    def initialize_git_repository(self):
        """初始化Git倉庫"""
        self.log("📦 初始化Git倉庫...")
        
        try:
            os.chdir(self.project_dir)
            
            # 初始化Git倉庫
            subprocess.run(['git', 'init'], check=True, capture_output=True)
            self.log("✅ Git倉庫初始化完成")
            
            # 添加所有文件
            subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
            self.log("✅ 文件添加到Git")
            
            # 創建初始提交
            commit_message = f"🚀 初始化 AImax 智能平衡交易系統 v1.0-smart-balanced (83.3%勝率) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True)
            self.log("✅ 初始提交完成")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Git操作失敗: {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Git初始化失敗: {str(e)}", "ERROR")
            return False
    
    def create_github_repository(self):
        """創建GitHub倉庫"""
        self.log("🌐 創建GitHub倉庫...")
        
        print(f"\n📋 請手動在GitHub上創建倉庫:")
        print(f"   1. 訪問: https://github.com/new")
        print(f"   2. 倉庫名稱: {self.config['repo_name']}")
        print(f"   3. 設為私有倉庫 (推薦)")
        print(f"   4. 不要初始化README、.gitignore或LICENSE")
        print(f"   5. 創建倉庫後，複製倉庫URL")
        
        repo_url = input("\n請輸入GitHub倉庫URL: ").strip()
        if not repo_url:
            self.log("❌ 未提供倉庫URL", "ERROR")
            return False
        
        try:
            # 添加遠程倉庫
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True, capture_output=True)
            self.log("✅ 遠程倉庫添加完成")
            
            # 推送到GitHub
            subprocess.run(['git', 'branch', '-M', 'main'], check=True, capture_output=True)
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], check=True, capture_output=True)
            self.log("✅ 代碼推送到GitHub完成")
            
            self.config['repo_url'] = repo_url
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ GitHub倉庫操作失敗: {str(e)}", "ERROR")
            return False
    
    def setup_github_pages(self):
        """設置GitHub Pages"""
        self.log("📄 設置GitHub Pages...")
        
        repo_name = self.config['repo_name']
        github_username = self.config['github_username']
        
        print(f"\n📋 請手動設置GitHub Pages:")
        print(f"   1. 訪問: https://github.com/{github_username}/{repo_name}/settings/pages")
        print(f"   2. Source: Deploy from a branch")
        print(f"   3. Branch: main")
        print(f"   4. Folder: / (root)")
        print(f"   5. 點擊Save")
        
        input("\n設置完成後按Enter繼續...")
        
        pages_url = f"https://{github_username}.github.io/{repo_name}/"
        self.config['pages_url'] = pages_url
        
        self.log(f"✅ GitHub Pages URL: {pages_url}")
        return True
    
    def create_secrets_guide(self):
        """創建Secrets配置指南"""
        self.log("🔐 創建Secrets配置指南...")
        
        secrets_guide = f"""
# AImax GitHub Secrets 配置指南

## 必需的Secrets配置

訪問: https://github.com/{self.config['github_username']}/{self.config['repo_name']}/settings/secrets/actions

### 基礎配置
- `ADMIN_USERNAME`: {self.config['login_username']}
- `ADMIN_PASSWORD_HASH`: {self.config['login_password_hash']}

### 交易配置 (如果啟用真實交易)
- `MAX_API_KEY`: 您的MAX交易所API密鑰
- `MAX_API_SECRET`: 您的MAX交易所API密鑰密碼

### Telegram通知 (如果啟用)
- `TELEGRAM_BOT_TOKEN`: 您的Telegram Bot Token
- `TELEGRAM_CHAT_ID`: 您的Telegram Chat ID

## 配置步驟
1. 點擊 "New repository secret"
2. 輸入Name和Value
3. 點擊 "Add secret"
4. 重複以上步驟添加所有必需的secrets

## 安全提醒
- 請勿在代碼中硬編碼任何敏感信息
- 定期更換API密鑰和密碼
- 確保倉庫設為私有
"""
        
        guide_file = self.project_dir / "SECRETS_SETUP_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(secrets_guide)
        
        self.log("✅ Secrets配置指南創建完成")
        return True
    
    def generate_deployment_report(self):
        """生成部署報告"""
        self.log("📊 生成部署報告...")
        
        report = f"""
# AImax 智能平衡交易系統部署報告

## 部署信息
- 部署時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 項目名稱: {self.config['repo_name']}
- GitHub用戶: {self.config['github_username']}
- 部署模式: {self.config['deployment_mode']}
- 策略版本: v1.0-smart-balanced
- 驗證勝率: 83.3%

## 訪問信息
- 網站地址: {self.config.get('pages_url', 'GitHub Pages設置中')}
- 登入帳號: {self.config['login_username']}
- 登入密碼: [已設置]

## 功能狀態
- 真實交易: {'✅ 啟用' if self.config['enable_trading'] else '❌ 禁用'}
- Telegram通知: {'✅ 啟用' if self.config['enable_telegram'] else '❌ 禁用'}
- GitHub Pages: ✅ 已配置
- 安全認證: ✅ 已配置

## 下一步操作
1. 等待GitHub Actions完成首次部署 (約2-3分鐘)
2. 訪問網站地址測試登入功能
3. 如啟用交易功能，請配置GitHub Secrets
4. 如啟用Telegram，請配置Bot Token

## 部署日誌
"""
        
        for log_entry in self.deployment_log:
            report += f"{log_entry}\n"
        
        report_file = self.project_dir / "DEPLOYMENT_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.log("✅ 部署報告生成完成")
        return True
    
    def deploy(self):
        """執行完整部署流程"""
        self.log("🚀 開始AImax智能交易系統部署...")
        
        try:
            # 檢查前置條件
            if not self.check_prerequisites():
                return False
            
            # 互動式配置
            if not self.interactive_config():
                return False
            
            # 創建項目結構
            if not self.create_project_structure():
                return False
            
            # 自定義配置
            if not self.customize_configuration():
                return False
            
            # 初始化Git倉庫
            if not self.initialize_git_repository():
                return False
            
            # 創建GitHub倉庫
            if not self.create_github_repository():
                return False
            
            # 設置GitHub Pages
            if not self.setup_github_pages():
                return False
            
            # 創建配置指南
            if not self.create_secrets_guide():
                return False
            
            # 生成部署報告
            if not self.generate_deployment_report():
                return False
            
            # 部署成功
            self.log("🎉 AImax智能交易系統部署完成！")
            
            print("\n" + "="*60)
            print("🎉 部署成功！")
            print("="*60)
            print(f"📁 項目目錄: {self.project_dir}")
            print(f"🌐 網站地址: {self.config.get('pages_url', '設置中...')}")
            print(f"🔐 登入帳號: {self.config['login_username']}")
            print(f"📋 查看詳細報告: {self.project_dir}/DEPLOYMENT_REPORT.md")
            print(f"🔐 配置指南: {self.project_dir}/SECRETS_SETUP_GUIDE.md")
            print("\n⏳ 請等待2-3分鐘讓GitHub Actions完成首次部署")
            
            return True
            
        except Exception as e:
            self.log(f"❌ 部署失敗: {str(e)}", "ERROR")
            return False

def main():
    """主函數"""
    print("🤖 AImax 智能平衡交易系統 - 一鍵部署工具 v1.0-smart-balanced (83.3%勝率)")
    print("="*60)
    
    deployer = AIMaxDeployer()
    success = deployer.deploy()
    
    if success:
        print("\n✅ 部署完成！歡迎使用AImax智能交易系統！")
        sys.exit(0)
    else:
        print("\n❌ 部署失敗！請檢查錯誤信息並重試。")
        sys.exit(1)

if __name__ == "__main__":
    main()