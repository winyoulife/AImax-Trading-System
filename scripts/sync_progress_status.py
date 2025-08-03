#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進度狀態同步工具 - 同步tasks.md和進度日誌的狀態
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def parse_tasks_file(tasks_file_path: str) -> Dict[str, bool]:
    """解析tasks.md文件，提取任務狀態"""
    tasks_status = {}
    
    if not Path(tasks_file_path).exists():
        return tasks_status
    
    with open(tasks_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配任務行
    task_pattern = r'^- \[([ x])\] (.+)$'
    matches = re.findall(task_pattern, content, re.MULTILINE)
    
    for status_char, task_name in matches:
        is_completed = status_char == 'x'
        tasks_status[task_name.strip()] = is_completed
    
    return tasks_status

def generate_progress_summary(all_specs_status: Dict[str, Dict[str, bool]]) -> str:
    """生成進度摘要"""
    summary_lines = [
        "# 📊 AImax 任務進度同步報告",
        f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    total_tasks = 0
    completed_tasks = 0
    
    for spec_name, tasks in all_specs_status.items():
        spec_total = len(tasks)
        spec_completed = sum(tasks.values())
        total_tasks += spec_total
        completed_tasks += spec_completed
        
        completion_rate = (spec_completed / spec_total * 100) if spec_total > 0 else 0
        
        summary_lines.extend([
            f"## {spec_name}",
            f"- 總任務數: {spec_total}",
            f"- 已完成: {spec_completed}",
            f"- 完成率: {completion_rate:.1f}%",
            ""
        ])
        
        # 列出已完成的任務
        completed_task_names = [name for name, completed in tasks.items() if completed]
        if completed_task_names:
            summary_lines.append("### ✅ 已完成任務:")
            for task_name in completed_task_names:
                summary_lines.append(f"- {task_name}")
            summary_lines.append("")
        
        # 列出未完成的任務
        pending_task_names = [name for name, completed in tasks.items() if not completed]
        if pending_task_names:
            summary_lines.append("### ⏳ 待完成任務:")
            for task_name in pending_task_names[:5]:  # 只顯示前5個
                summary_lines.append(f"- {task_name}")
            if len(pending_task_names) > 5:
                summary_lines.append(f"- ... 還有 {len(pending_task_names) - 5} 個任務")
            summary_lines.append("")
    
    # 總體統計
    overall_completion = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    summary_lines.extend([
        "## 📈 總體進度",
        f"- 總任務數: {total_tasks}",
        f"- 已完成: {completed_tasks}",
        f"- 整體完成率: {overall_completion:.1f}%",
        ""
    ])
    
    return "\n".join(summary_lines)

def main():
    """主函數"""
    print("🔄 開始同步任務進度狀態...")
    
    # 定義所有spec文件路徑
    spec_files = {
        "AI交易系統核心": ".kiro/specs/ai-trading-system/tasks.md",
        "多交易對系統": ".kiro/specs/multi-pair-trading-system/tasks.md",
        "Ollama AI系統": ".kiro/specs/ollama-ai-trading-system/tasks.md",
        "GUI系統改進": ".kiro/specs/gui-system-improvement/tasks.md",
        "回測系統": ".kiro/specs/real-backtest-system/tasks.md",
        "圖表顯示修復": ".kiro/specs/chart-display-fix/tasks.md"
    }
    
    all_specs_status = {}
    
    # 解析所有spec文件
    for spec_name, file_path in spec_files.items():
        if Path(file_path).exists():
            tasks_status = parse_tasks_file(file_path)
            if tasks_status:  # 只包含有任務的spec
                all_specs_status[spec_name] = tasks_status
                print(f"✅ 已解析 {spec_name}: {len(tasks_status)} 個任務")
        else:
            print(f"⚠️ 文件不存在: {file_path}")
    
    # 生成進度摘要
    progress_summary = generate_progress_summary(all_specs_status)
    
    # 保存進度摘要
    output_path = "AImax/reports/task_progress_sync.md"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(progress_summary)
    
    print(f"📄 進度同步報告已生成: {output_path}")
    
    # 顯示摘要統計
    total_specs = len(all_specs_status)
    total_tasks = sum(len(tasks) for tasks in all_specs_status.values())
    total_completed = sum(sum(tasks.values()) for tasks in all_specs_status.values())
    overall_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0
    
    print("\n📊 同步完成統計:")
    print(f"   規格文檔數: {total_specs}")
    print(f"   總任務數: {total_tasks}")
    print(f"   已完成: {total_completed}")
    print(f"   整體完成率: {overall_rate:.1f}%")

if __name__ == "__main__":
    main()