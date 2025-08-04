#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 雲端部署腳本
用於在雲端服務器上快速部署交易系統
"""

import os
import sys
import subprocess
import json
from datetime import datetime

class CloudDeployer:
    """雲端部署器"""
    
    def __init__(self):
        self.project_name = "AImax-Trading-System"
        self.web_port = 5000
        
    def show_banner(self):
        """顯示部署橫幅"""
        print("=" * 60)
        print("🚀 AImax 智能交易系統 - 雲端部署工具")
        print("=" * 60)
        print("📅 部署時間:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("🌐 目標環境: 雲端服務器")
        print("🔒 安全等級: 私有部署")
        print("=" * 60)
        print()
    
    def check_system(self):
        """檢查系統環境"""
        print("🔍 檢查系統環境...")
        
        # 檢查Python版本
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            print(f"❌ Python版本過舊: {python_version.major}.{python_version.minor}")
            return False
        
        # 檢查Git
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Git 已安裝")
            else:
                print("❌ Git 未安裝")
                return False
        except FileNotFoundError:
            print("❌ Git 未安裝")
            return False
        
        # 檢查網路連接
        try:
            import requests
            response = requests.get('https://api.github.com', timeout=10)
            if response.status_code == 200:
                print("✅ 網路連接正常")
            else:
                print("⚠️ 網路連接異常")
        except:
            print("⚠️ 無法檢查網路連接")
        
        return True
    
    def install_dependencies(self):
        """安裝依賴"""
        print("\n📦 安裝系統依賴...")
        
        try:
            # 升級pip
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            print("✅ pip 已升級")
            
            # 安裝requirements
            if os.path.exists('requirements.txt'):
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                             check=True, capture_output=True)
                print("✅ Python依賴已安裝")
            else:
                print("⚠️ requirements.txt 不存在")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 依賴安裝失敗: {e}")
            return False
    
    def setup_config(self):
        """設置配置"""
        print("\n⚙️ 設置系統配置...")
        
        # 創建必要目錄
        directories = ['logs', 'data', 'templates', 'static']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ 目錄已創建: {directory}")
        
        # 檢查配置文件
        config_files = [
            'config/trading_system.json',
            'config/risk_management.json',
            'config/telegram_config.py'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"✅ 配置文件存在: {config_file}")
            else:
                print(f"⚠️ 配置文件缺失: {config_file}")
        
        return True
    
    def create_startup_script(self):
        """創建啟動腳本"""
        print("\n📝 創建啟動腳本...")
        
        # 創建systemd服務文件（Linux）
        service_content = f"""[Unit]
Description=AImax Trading System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={os.getcwd()}
Environment=PATH={os.environ.get('PATH')}
ExecStart={sys.executable} start_web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        with open('aimax-trading.service', 'w') as f:
            f.write(service_content)
        
        print("✅ systemd服務文件已創建: aimax-trading.service")
        
        # 創建啟動腳本
        startup_script = """#!/bin/bash
# AImax 交易系統啟動腳本

echo "🚀 啟動 AImax 交易系統..."

# 檢查Python環境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安裝"
    exit 1
fi

# 進入項目目錄
cd "$(dirname "$0")"

# 啟動Web服務器
python3 start_web_server.py

echo "✅ AImax 交易系統已啟動"
"""
        
        with open('start_aimax.sh', 'w') as f:
            f.write(startup_script)
        
        # 設置執行權限
        os.chmod('start_aimax.sh', 0o755)
        print("✅ 啟動腳本已創建: start_aimax.sh")
        
        return True
    
    def show_deployment_info(self):
        """顯示部署資訊"""
        print("\n" + "=" * 60)
        print("🎉 AImax 交易系統部署完成！")
        print("=" * 60)
        
        print("\n📱 Web控制面板:")
        print(f"   本地訪問: http://localhost:{self.web_port}")
        print(f"   遠程訪問: http://[服務器IP]:{self.web_port}")
        
        print("\n🔐 專屬登入資訊:")
        print("   帳號: lovejk1314")
        print("   密碼: Ichen5978")
        
        print("\n🚀 啟動方式:")
        print("   方式1: python start_web_server.py")
        print("   方式2: ./start_aimax.sh")
        print("   方式3: systemctl start aimax-trading (需要安裝服務)")
        
        print("\n⚠️ 重要提醒:")
        print("   • 已設置專屬密碼，如需修改: python change_password.py")
        print("   • 配置防火牆規則限制訪問")
        print("   • 設置SSL證書（生產環境）")
        print("   • 定期備份交易數據")
        
        print("\n🛠️ 系統管理:")
        print("   • 查看日誌: tail -f logs/*.log")
        print("   • 停止服務: Ctrl+C 或 systemctl stop aimax-trading")
        print("   • 重啟服務: systemctl restart aimax-trading")
        
        print("\n📞 技術支援:")
        print("   • 檢查系統狀態: python scripts/emergency_stop.py --status")
        print("   • 緊急停止: python scripts/emergency_stop.py")
        
        print("\n" + "=" * 60)
    
    def deploy(self):
        """執行部署"""
        self.show_banner()
        
        # 檢查系統
        if not self.check_system():
            print("❌ 系統檢查失敗，部署中止")
            return False
        
        # 安裝依賴
        if not self.install_dependencies():
            print("❌ 依賴安裝失敗，部署中止")
            return False
        
        # 設置配置
        if not self.setup_config():
            print("❌ 配置設置失敗，部署中止")
            return False
        
        # 創建啟動腳本
        if not self.create_startup_script():
            print("❌ 啟動腳本創建失敗，部署中止")
            return False
        
        # 顯示部署資訊
        self.show_deployment_info()
        
        return True

def main():
    """主函數"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("AImax 雲端部署工具")
        print()
        print("用法:")
        print("  python deploy_cloud.py        # 執行部署")
        print("  python deploy_cloud.py --help # 顯示幫助")
        print()
        print("功能:")
        print("  • 自動檢查系統環境")
        print("  • 安裝必要依賴")
        print("  • 設置系統配置")
        print("  • 創建啟動腳本")
        print("  • 生成服務文件")
        return 0
    
    deployer = CloudDeployer()
    
    try:
        if deployer.deploy():
            print("\n✅ 部署成功完成！")
            return 0
        else:
            print("\n❌ 部署失敗！")
            return 1
    except KeyboardInterrupt:
        print("\n\n🛑 部署已取消")
        return 0
    except Exception as e:
        print(f"\n❌ 部署過程中發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())