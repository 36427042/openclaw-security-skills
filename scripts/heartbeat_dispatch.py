#!/usr/bin/env python3
"""
心跳自动派活机制 v1.0
读取task_board.md → 识别可执行TASK → 自动分派
"""
import os, re, time, subprocess, json
from datetime import datetime

TASK_BOARD = os.path.expanduser("~/.openclaw/workspace/agents/tomato-agent/task_board.md")
MEMORY = os.path.expanduser("~/.openclaw/workspace/agents/tomato-agent/memory")

def parse_task_board():
    """解析任务看板"""
    if not os.path.exists(TASK_BOARD):
        return {"pending": [], "in_progress": [], "done": []}
    
    with open(TASK_BOARD) as f:
        content = f.read()
    
    tasks = {"pending": [], "in_progress": [], "done": []}
    
    # 找到所有任务行 (格式: | XX | 任务名 | 状态 | ...)
    for line in content.split('\n'):
        match = re.match(r'\|\s*([A-Z]+\d+|[A-Z]+)\s*\|\s*(.+?)\s*\|\s*(✅|⏳|🔄|📝|🟡|🔴)\s*\|', line)
        if match:
            task_id, name, status = match.groups()
            status_map = {
                "✅": "done", "⏳": "pending", "🔄": "in_progress",
                "📝": "pending", "🟡": "pending", "🔴": "blocked"
            }
            cat = status_map.get(status, "pending")
            tasks[cat].append({"id": task_id.strip(), "name": name.strip(), "status": status})
    
    return tasks

def log_dispatch(tasks):
    """记录派活日志"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(MEMORY, f"dispatch_{today}.md")
    
    now = datetime.now().strftime("%H:%M")
    lines = [f"## ⏰ {now} 心跳派活\n"]
    lines.append(f"| 状态 | 数量 |")
    lines.append(f"|:---|:---:|")
    lines.append(f"| ✅ 已完成 | {len(tasks['done'])} |")
    lines.append(f"| 🔄 进行中 | {len(tasks['in_progress'])} |")
    lines.append(f"| ⏳ 待执行 | {len(tasks['pending'])} |")
    lines.append(f"| 🔴 阻塞 | {sum(1 for t in tasks['pending'] if t['status']=='🔴')} |")
    
    pending = [t for t in tasks['pending'] if t['status'] in ('⏳', '📝')]
    if pending:
        lines.append(f"\n### 可立即执行 ({len(pending)}项)")
        for t in pending[:10]:
            lines.append(f"- [ ] {t['id']}: {t['name']}")
    
    with open(log_file, "w") as f:
        f.write("\n".join(lines))
    
    return len(pending)

if __name__ == "__main__":
    tasks = parse_task_board()
    pending = log_dispatch(tasks)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❤️ 派活: {len(tasks['done'])}完/{len(tasks['in_progress'])}进/{pending}待")
