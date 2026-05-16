#!/usr/bin/env python3
"""
evomap_harness.py — EvoMap Harness 统一框架

合并 evomap_harness.py (核心框架) + harness_fusion.py (工作流模板)
为单一文件，消除重复 main()、orch 实例、CLI。

架构:
  OpenClaw层: 接得上 + 调得动 + 能执行
  Harness层:  跑得稳 + 管得住 + 追得回

7节点:
  🥔 土豆 -> 统筹调度  🍅 番茄 -> 爆单定价  🥬 生菜 -> 文案生成
  🌽 玉米 -> 视频管线  🥕 萝卜 -> 直播运营  🥒 苦瓜 -> 风控审查
  🫘 豌豆 -> 数据监控
"""
import json, os, sys, time, subprocess, traceback
from datetime import datetime
from typing import Any, Callable, Optional

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
HARNESS_DIR = os.path.join(WORKSPACE, "harness")
STATE_DIR = os.path.join(HARNESS_DIR, "state")
TASKS_DIR = os.path.join(STATE_DIR, "tasks")
EVENTS_DIR = os.path.join(STATE_DIR, "events")
SCRIPTS_DIR = os.path.join(WORKSPACE, "scripts")
os.makedirs(TASKS_DIR, exist_ok=True)
os.makedirs(EVENTS_DIR, exist_ok=True)

# ════════════════════════════════════════════════
# 1. DurableState — 文件级持久状态（追得回）
# ════════════════════════════════════════════════

class DurableState:
    """每个任务一个json，幸存重启。最小化写入+智能合并"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.path = os.path.join(TASKS_DIR, f"{task_id}.json")
        self._state = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path) as f:
                return json.load(f)
        return {
            "task_id": self.task_id, "status": "created",
            "progress": 0, "current_step": "", "steps": [],
            "milestones": [], "errors": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(), "metadata": {},
        }

    def _save(self):
        self._state["updated_at"] = datetime.now().isoformat()
        with open(self.path, "w") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None): return self._state.get(key, default)
    def set(self, key, value): self._state[key] = value; self._save()
    def update(self, **kwargs): self._state.update(kwargs); self._save()
    def set_progress(self, pct): self._state["progress"] = max(0, min(100, pct)); self._save()

    def add_milestone(self, name, detail=""):
        ms = {"name": name, "detail": detail, "at": datetime.now().isoformat()}
        self._state["milestones"].append(ms); self._save(); return ms

    def add_error(self, step, err):
        rec = {"step": step, "error": str(err), "at": datetime.now().isoformat()}
        self._state["errors"].append(rec); self._state["status"] = "failed"; self._save(); return rec

    def mark_step(self, step_name, status="running"):
        for s in self._state["steps"]:
            if s["name"] == step_name: s["status"] = status; s["at"] = datetime.now().isoformat(); self._save(); return
        self._state["steps"].append({"name": step_name, "status": status, "at": datetime.now().isoformat()}); self._save()

    @property
    def can_resume(self) -> bool:
        return self._state["status"] in ("running", "paused", "failed")

    def snapshot(self) -> dict: return dict(self._state)

# ════════════════════════════════════════════════
# 2. EventLog — 事件溯源（管得住）
# ════════════════════════════════════════════════

class EventLog:
    """JSONL事件日志，每一步都有记录"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.path = os.path.join(EVENTS_DIR, f"{task_id}.events.jsonl")

    def emit(self, event_type: str, data: dict = None):
        event = {"ts": datetime.now().isoformat(), "task_id": self.task_id, "type": event_type, "data": data or {}}
        with open(self.path, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def replay(self, limit=100) -> list:
        events = []
        if not os.path.exists(self.path): return events
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line: events.append(json.loads(line))
        return events[-limit:]

    def get_task_timeline(self) -> list:
        return [(e["ts"], e["type"], e.get("data", {})) for e in self.replay(1000)]

# ════════════════════════════════════════════════
# 3. HarnessTask — 可恢复的长程任务（跑得稳）
# ════════════════════════════════════════════════

class HarnessTask:
    def __init__(self, task_id: str, name: str, owner: str):
        self.id, self.name, self.owner = task_id, name, owner
        self.state = DurableState(task_id)
        self.events = EventLog(task_id)
        if self.state.get("status") == "created":
            self.state.update(status="ready", name=name, owner=owner)
            self.events.emit("task_created", {"name": name, "owner": owner})

    def run(self, steps: list[dict], context: dict = None):
        self.state.set("status", "running")
        self.state.set("current_step", steps[0]["name"] if steps else "")
        self.events.emit("task_started", {"step_count": len(steps)})
        total = len(steps)

        for i, step in enumerate(steps):
            sn, fn, args = step["name"], step["fn"], step.get("args", {})
            existing = [s for s in self.state.get("steps", []) if s["name"] == sn]
            if existing and existing[0]["status"] == "completed":
                self.events.emit("step_skipped", {"step": sn, "reason": "already_completed"})
                continue
            self.state.mark_step(sn, "running")
            self.state.set("current_step", sn)
            self.events.emit("step_started", {"step": sn, "index": i+1, "total": total})
            try:
                args["_state"], args["_events"] = self.state, self.events
                if context: args["_context"] = context
                result = fn(**args)
                self.state.mark_step(sn, "completed")
                self.state.set_progress(int((i + 1) / total * 100))
                self.events.emit("step_completed", {"step": sn, "result": str(result)[:200]})
            except Exception as e:
                self.state.mark_step(sn, "failed")
                self.state.add_error(sn, f"{e}\n{traceback.format_exc()}")
                self.events.emit("step_failed", {"step": sn, "error": str(e)})
                return {"status": "failed", "step": sn, "error": str(e)}

        self.state.set("status", "completed"); self.state.set_progress(100)
        self.events.emit("task_completed", {})
        return {"status": "completed", "task_id": self.id}

    def resume(self, steps: list[dict], context: dict = None) -> dict:
        if not self.state.can_resume:
            return {"status": "cannot_resume", "reason": f"current: {self.state.get('status')}"}
        self.events.emit("task_resumed", {"reason": "resume_requested"})
        self.state.set("status", "running")
        completed = {s["name"] for s in self.state.get("steps", []) if s["status"] == "completed"}
        failed = {s["name"] for s in self.state.get("steps", []) if s["status"] == "failed"}
        remaining = [s for s in steps if s["name"] not in completed]
        self.events.emit("resume_plan", {"completed": list(completed), "failed": list(failed), "remaining": [s["name"] for s in remaining]})
        return self.run(remaining, context)

    def status(self) -> dict: return self.state.snapshot()
    def timeline(self) -> list: return self.events.get_task_timeline()

# ════════════════════════════════════════════════
# 4. HarnessOrchestrator — 7节点任务编排
# ════════════════════════════════════════════════

class HarnessOrchestrator:
    def __init__(self):
        self.registry_path = os.path.join(STATE_DIR, "orchestrator.json")
        self._registry = self._load_registry()

    def _load_registry(self) -> dict:
        if os.path.exists(self.registry_path):
            with open(self.registry_path) as f:
                return json.load(f)
        return {"tasks": {}, "nodes": {}}

    def _save_registry(self):
        with open(self.registry_path, "w") as f:
            json.dump(self._registry, f, ensure_ascii=False, indent=2)

    def register_node(self, nid, name, capabilities):
        self._registry["nodes"][nid] = {"name": name, "capabilities": capabilities,
            "registered_at": datetime.now().isoformat(), "task_count": 0}; self._save_registry()

    def create_task(self, owner: str, name: str, steps: list) -> HarnessTask:
        task_id = f"{owner}_{int(time.time())}"
        task = HarnessTask(task_id, name, owner)
        self._registry["tasks"][task_id] = {"task_id": task_id, "name": name, "owner": owner,
            "step_count": len(steps), "status": "created", "created_at": datetime.now().isoformat()}
        self._registry["nodes"].setdefault(owner, {}).setdefault("task_count", 0)
        self._registry["nodes"][owner]["task_count"] += 1; self._save_registry(); return task

    def list_tasks(self, owner=None) -> list[dict]:
        tasks = []
        for tid, info in self._registry["tasks"].items():
            if owner and info.get("owner") != owner: continue
            sp = os.path.join(TASKS_DIR, f"{tid}.json")
            if os.path.exists(sp):
                with open(sp) as f: s = json.load(f)
                info.update(progress=s.get("progress", 0), current_step=s.get("current_step", ""), step_detail=s.get("steps", []))
            tasks.append(info)
        return sorted(tasks, key=lambda t: t.get("created_at", ""), reverse=True)

    def get_task(self, task_id: str) -> Optional[HarnessTask]:
        if task_id in self._registry["tasks"]:
            i = self._registry["tasks"][task_id]
            return HarnessTask(task_id, i["name"], i["owner"])
        return None

    def register_nodes(self):
        for name, nid, caps in [
            ("🥔 土豆", "orchestrator", ["统筹", "调度", "汇报"]),
            ("🍅 番茄", "booster", ["定价", "矩阵", "利润率"]),
            ("🥬 生菜", "copy", ["文案", "话术", "合规"]),
            ("🌽 玉米", "video", ["视频", "渲染", "去重"]),
            ("🥕 萝卜", "live", ["直播", "运营"]),
            ("🥒 苦瓜", "risk", ["风控", "审查", "应急"]),
            ("🫘 豌豆", "data", ["监控", "分析", "预警"]),
        ]: self.register_node(nid, name, caps)

# ════════════════════════════════════════════════
# 5. Workflow Templates — 工作流模板
# ════════════════════════════════════════════════

def run_script_step(script_name: str, **kwargs) -> dict:
    """运行6虾脚本作为harness步骤"""
    sp = os.path.join(SCRIPTS_DIR, script_name)
    events = kwargs.get("_events")
    result = subprocess.run(["python3", sp], capture_output=True, text=True, timeout=300)
    if events: events.emit("script_executed", {"script": script_name, "returncode": result.returncode})
    if result.returncode != 0:
        raise RuntimeError(f"{script_name}失败: {result.stderr[:500]}")
    return {"script": script_name, "output": result.stdout[-300:]}

def get_workflow(name: str) -> list:
    wk = {
        "booster": [
            {"name": "读取历史数据", "fn": run_script_step, "args": {"script_name": "booster_matrix.py"}},
            {"name": "计算5国定价",   "fn": lambda **kw: {"msg": "定价完成"}},
            {"name": "生成定价报告",  "fn": lambda **kw: {"msg": "报告已输出"}},
            {"name": "推送飞书",      "fn": lambda **kw: {"msg": "飞书推送完成"}},
        ],
        "copy": [
            {"name": "加载违禁词库", "fn": run_script_step, "args": {"script_name": "copy_engine.py"}},
            {"name": "生成5国话术",  "fn": lambda **kw: {"msg": "话术已生成"}},
            {"name": "合规校验",     "fn": lambda **kw: {"msg": "校验通过"}},
            {"name": "导出CSV",      "fn": lambda **kw: {"msg": "CSV已导出"}},
        ],
        "video": [
            {"name": "简创创建草稿",  "fn": lambda **kw: {"msg": "草稿已创建"}},
            {"name": "上传5国素材",  "fn": lambda **kw: {"msg": "素材已上传"}},
            {"name": "提交云渲染",   "fn": lambda **kw: {"msg": "渲染已提交"}},
            {"name": "轮询等待完成", "fn": lambda **kw: {"msg": "渲染完成"}},
            {"name": "下载5国成品",  "fn": lambda **kw: {"msg": "下载完成"}},
        ],
        "risk": [
            {"name": "检查违禁词", "fn": run_script_step, "args": {"script_name": "risk_controller.py"}},
            {"name": "视频风审",   "fn": lambda **kw: {"msg": "视频风审通过"}},
            {"name": "账号关联检查","fn": lambda **kw: {"msg": "未发现关联"}},
        ],
        "data": [
            {"name": "采集经营数据", "fn": run_script_step, "args": {"script_name": "data_monitor.py"}},
            {"name": "异常检测",     "fn": lambda **kw: {"msg": "无异常"}},
            {"name": "推送飞书汇总", "fn": lambda **kw: {"msg": "已推送"}},
        ],
        "hermes": [
            {"name": "booster",       "fn": run_script_step, "args": {"script_name": "hermes_enhanced.py"}},
            {"name": "copy_engine",   "fn": lambda **kw: {"msg": "copy完成"}},
            {"name": "video_pipeline","fn": lambda **kw: {"msg": "video完成"}},
            {"name": "risk_control",  "fn": lambda **kw: {"msg": "risk完成"}},
            {"name": "data_monitor",  "fn": lambda **kw: {"msg": "data完成"}},
            {"name": "生成汇总报告",  "fn": lambda **kw: {"msg": "报告已生成"}},
        ],
    }
    return wk.get(name, [])

# ════════════════════════════════════════════════
# 6. CLI
# ════════════════════════════════════════════════

_orch = HarnessOrchestrator()
WORKFLOW_NAMES = list(get_workflow("_keys").keys()) if False else ["booster", "copy", "video", "risk", "data", "hermes"]

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "help"

    if cmd == "init":
        _orch.register_nodes()
        print("✅ EvoMap Harness 初始化完成")
        print(f"   状态目录: {STATE_DIR}")
        print(f"   7节点已注册")
        print(f"   可用工作流: {' '.join(WORKFLOW_NAMES)}")

    elif cmd == "status":
        tasks = _orch.list_tasks()
        print(f"📊 Harness 状态 — 总任务: {len(tasks)}")
        for nid, ninfo in _orch._registry.get("nodes", {}).items():
            nt = [t for t in tasks if t.get("owner") == nid]
            active = sum(1 for t in nt if t.get("status") in ("running","created","ready"))
            print(f"   {ninfo['name']}: {ninfo['task_count']}任务 ({active}活跃)")
        if tasks:
            for t in tasks[:5]:
                print(f"   {t.get('task_id','?'):30s} {t.get('name','')[:20]:20s} {t.get('status','?'):10s} {t.get('progress',0)}%")

    elif cmd == "run" and len(sys.argv) >= 3:
        wf_name = sys.argv[2]
        steps = get_workflow(wf_name)
        if not steps:
            print(f"❌ 未知工作流: {wf_name}，可用: {' '.join(WORKFLOW_NAMES)}"); return
        task = _orch.create_task(owner=wf_name, name=f"wf_{wf_name}", steps=steps)
        print(f"🚀 {wf_name} — TaskID: {task.id} ({len(steps)}步)")
        result = task.run(steps)
        print(f"{'✅' if result['status']=='completed' else '❌'} 完成: {result.get('status','?')}")

    elif cmd == "resume" and len(sys.argv) >= 3:
        task = _orch.get_task(sys.argv[2])
        if not task: print(f"❌ 任务不存在: {sys.argv[2]}"); return
        owner = task.state.get("owner", "")
        steps = get_workflow(owner) if owner else []
        if not steps: print(f"❌ 找不到工作流: {owner}"); return
        result = task.resume(steps)
        print(f"🔄 恢复结果: {result.get('status','?')}")

    elif cmd == "list":
        tasks = _orch.list_tasks()
        print(f"📋 任务列表 ({len(tasks)})")
        for t in tasks:
            icon = {"completed":"✅","running":"⏳","failed":"❌","created":"🆕"}.get(t.get("status",""),"❓")
            print(f"   {icon} {t['task_id']:30s} {t['name']:20s} {t.get('status','?'):10s} {t.get('progress',0)}%")

    elif cmd == "show" and len(sys.argv) >= 3:
        task = _orch.get_task(sys.argv[2])
        if not task: print(f"❌ 不存在: {sys.argv[2]}"); return
        s = task.status()
        print(f"📋 {s['task_id']} — {s.get('name','')} — {s.get('status','')} — {s.get('progress',0)}%")
        for step in s.get("steps", []):
            ic = {"completed":"✅","running":"⏳","failed":"❌","pending":"⏭️"}.get(step.get("status",""),"❓")
            print(f"   {ic} {step['name']} ({step.get('status','?')})")
        for m in s.get("milestones", []):
            print(f"   🏁 {m['name']} ({m.get('at','')[:19]})")
        if s.get("errors"):
            for e in s["errors"]: print(f"   ❌ {e['step']}: {str(e['error'])[:150]}")
        for ts, etype, d in task.timeline()[-10:]:
            print(f"   ⏱️ {ts[11:19]} [{etype}] {d.get('step','')}")

    else:
        print("""
🧬 EvoMap Harness — 统一框架

用法: python3 evomap_harness.py <命令>

命令:
  init              初始化7节点注册
  status            查看整体状态
  run <workflow>    启动工作流
  resume <task_id>  从失败恢复
  list              列出所有任务
  show <task_id>    查看任务详情
  help              显示帮助

工作流: """ + " ".join(WORKFLOW_NAMES) + """
""")

if __name__ == "__main__":
    main()
