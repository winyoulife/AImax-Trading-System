#!/usr/bin/env python3
"""
AImax 文檔驗證腳本
驗證技術文檔的完整性和正確性
"""

import os
import sys
import json
from pathlib import Path

def validate_documentation():
    """驗證文檔完整性"""
    print("🔍 開始驗證AImax技術文檔...")
    
    # 文檔目錄
    docs_dir = Path("AImax/docs")
    
    # 必需的文檔文件
    required_docs = [
        "README.md",
        "SYSTEM_ARCHITECTURE.md", 
        "API_DOCUMENTATION.md",
        "CONFIGURATION_GUIDE.md",
        "DEPLOYMENT_GUIDE.md",
        "TROUBLESHOOTING_GUIDE.md"
    ]
    
    # 檢查文檔文件是否存在
    missing_docs = []
    existing_docs = []
    
    for doc in required_docs:
        doc_path = docs_dir / doc
        if doc_path.exists():
            existing_docs.append(doc)
            print(f"✅ {doc} - 存在")
        else:
            missing_docs.append(doc)
            print(f"❌ {doc} - 缺失")
    
    # 檢查文檔內容
    content_issues = []
    
    for doc in existing_docs:
        doc_path = docs_dir / doc
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 基本內容檢查
            if len(content) < 1000:
                content_issues.append(f"{doc} - 內容過短")
            
            # 檢查必要的標題
            if doc == "README.md":
                required_sections = ["文檔概述", "文檔目錄", "快速導航"]
            elif doc == "SYSTEM_ARCHITECTURE.md":
                required_sections = ["系統概述", "系統架構", "數據流架構"]
            elif doc == "API_DOCUMENTATION.md":
                required_sections = ["API概述", "認證機制", "系統狀態API"]
            elif doc == "CONFIGURATION_GUIDE.md":
                required_sections = ["配置概述", "主系統配置", "AI模型配置"]
            elif doc == "DEPLOYMENT_GUIDE.md":
                required_sections = ["部署概述", "系統要求", "環境準備"]
            elif doc == "TROUBLESHOOTING_GUIDE.md":
                required_sections = ["故障排除概述", "緊急故障處理", "常見問題診斷"]
            else:
                required_sections = []
            
            for section in required_sections:
                if section not in content:
                    content_issues.append(f"{doc} - 缺少章節: {section}")
                    
        except Exception as e:
            content_issues.append(f"{doc} - 讀取錯誤: {str(e)}")
    
    # 生成驗證報告
    print("\n📊 文檔驗證報告")
    print("=" * 50)
    print(f"總文檔數量: {len(required_docs)}")
    print(f"存在文檔: {len(existing_docs)}")
    print(f"缺失文檔: {len(missing_docs)}")
    print(f"內容問題: {len(content_issues)}")
    
    if missing_docs:
        print("\n❌ 缺失的文檔:")
        for doc in missing_docs:
            print(f"  - {doc}")
    
    if content_issues:
        print("\n⚠️  內容問題:")
        for issue in content_issues:
            print(f"  - {issue}")
    
    # 檢查文檔大小
    print("\n📏 文檔大小統計:")
    total_size = 0
    for doc in existing_docs:
        doc_path = docs_dir / doc
        size = doc_path.stat().st_size
        total_size += size
        print(f"  {doc}: {size:,} bytes")
    
    print(f"\n總大小: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    
    # 驗證結果
    if not missing_docs and not content_issues:
        print("\n✅ 文檔驗證通過！所有必需文檔都存在且內容完整。")
        return True
    else:
        print("\n❌ 文檔驗證失敗！請修復上述問題。")
        return False

def generate_doc_summary():
    """生成文檔摘要"""
    print("\n📋 生成文檔摘要...")
    
    docs_dir = Path("AImax/docs")
    summary = {
        "documentation_summary": {
            "generated_at": "2025-01-27T10:00:00Z",
            "total_documents": 0,
            "total_size_bytes": 0,
            "documents": []
        }
    }
    
    if docs_dir.exists():
        for doc_file in docs_dir.glob("*.md"):
            size = doc_file.stat().st_size
            summary["documentation_summary"]["documents"].append({
                "name": doc_file.name,
                "size_bytes": size,
                "size_kb": round(size/1024, 1)
            })
            summary["documentation_summary"]["total_size_bytes"] += size
        
        summary["documentation_summary"]["total_documents"] = len(summary["documentation_summary"]["documents"])
        summary["documentation_summary"]["total_size_kb"] = round(summary["documentation_summary"]["total_size_bytes"]/1024, 1)
    
    # 保存摘要
    summary_file = docs_dir / "documentation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 文檔摘要已保存到: {summary_file}")
    return summary

def main():
    """主函數"""
    print("🚀 AImax 文檔驗證工具")
    print("=" * 50)
    
    # 驗證文檔
    validation_passed = validate_documentation()
    
    # 生成摘要
    summary = generate_doc_summary()
    
    # 輸出結果
    if validation_passed:
        print("\n🎉 文檔驗證完成！技術文檔已準備就緒。")
        sys.exit(0)
    else:
        print("\n⚠️  文檔驗證發現問題，請檢查並修復。")
        sys.exit(1)

if __name__ == "__main__":
    main()