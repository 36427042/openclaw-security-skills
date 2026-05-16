#!/usr/bin/env python3
"""
hermes_enhanced.py — Hermes增强包装器
调用hermes_engine.py执行全伙伴并行任务并输出飞书友好报告

用法：
  python3 hermes_enhanced.py                    # 全部并行执行
  python3 hermes_enhanced.py --workflow full    # 全链路工作流
  python3 hermes_enhanced.py --status           # 仅状态报告
  python3 hermes_enhanced.py --all              # 全部伙伴并行
"""
import subprocess, sys, os, json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(SCRIPT_DIR, "hermes_engine.py")

def run_hermes(args: list) -> dict:
    """调用Hermes引擎并返回结果"""
    cmd = [sys.executable, ENGINE] + args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "⏰ 超时(>600s)",
            "returncode": -1,
        }

def generate_status_report() -> str:
    """生成状态报告（不执行脚本，只检查）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"🤖 Hermes 状态报告",
        f"时间: {now}",
        "",
        "📦 注册工具:",
    ]

    # 检查引擎状态
    status_result = run_hermes(["status"])
    if status_result["returncode"] == 0:
        for line in status_result["stdout"].split("\n"):
            if line.strip():
                lines.append(f"  {line}")

    # 检查DeerFlow
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://localhost:8001/api/agents", timeout=5)
        data = json.loads(resp.read())
        agents = [a["name"] for a in data.get("agents", [])]
        lines.append(f"\n🏭 DeerFlow Agents ({len(agents)}个):")
        for a in agents:
            lines.append(f"  ✅ {a}")
    except Exception as e:
        lines.append(f"\n⚠️ DeerFlow: {e}")

    return "\n".join(lines)

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else ["run", "--all"]

    if "--status" in args:
        report = generate_status_report()
        print(report)
        print("\n📨 报告已生成")
        return

    print(f"🤖 Hermes Enhanced v3.0")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📡 调用: {ENGINE} {' '.join(args)}")
    print("")

    result = run_hermes(args)

    # 输出stdout
    if result["stdout"]:
        print(result["stdout"])
    if result["stderr"]:
        print(f"⚠️ {result['stderr'][:500]}")

    print(f"\n📊 返回码: {result['returncode']}")

if __name__ == "__main__":
    main()
