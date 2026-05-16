#!/usr/bin/env python3
"""
hermes_fusion.py — DeerFlow ⇄ Hermes ⇄ EvoMap ⇄ Harness 融合桥 v1.0

四层合一：
  1. Hermes hub  → 6伙伴直接调用（快速执行）
  2. Harness     → 持久化状态 + 事件溯源（可恢复）
  3. DeerFlow    → LangGraph 全链路工作流（编排）
  4. EvoMap      → 进化学习记录（闭环）

用法：
  from hermes_fusion import FusionEngine
  fe = FusionEngine()
  fe.run_partner("booster")           # 单伙伴
  fe.run_workflow("market_check")     # 工作流
  fe.run_deerflow()                   # DeerFlow全链路
  fe.status()                         # 全局状态
"""
import sys, os, json, time, subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

# ── 路径 ──
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
SCRIPTS_DIR = os.path.join(WORKSPACE, "scripts")
HARNESS_DIR = os.path.join(WORKSPACE, "harness")
HARNESS_STATE = os.path.join(HARNESS_DIR, "state")
HARNESS_TASKS = os.path.join(HARNESS_STATE, "tasks")
HARNESS_EVENTS = os.path.join(HARNESS_STATE, "events")
os.makedirs(HARNESS_TASKS, exist_ok=True)
os.makedirs(HARNESS_EVENTS, exist_ok=True)

sys.path.insert(0, SCRIPTS_DIR)


# ════════════════════════════════════════════════
#  EvoMap Record — 进化学习记录（简化版）
# ════════════════════════════════════════════════

class EvoRecord:
    """记录执行结果到JSONL，供EvoMap节点学习"""

    RECORD_FILE = os.path.join(WORKSPACE, "data", "evomap_records.jsonl")

    @classmethod
    def record(cls, partner: str, action: str, status: str, duration: float = 0, detail: str = ""):
        """记录一次执行"""
        record = {
            "ts": datetime.now().isoformat(),
            "partner": partner,
            "action": action,
            "status": status,
            "duration": duration,
            "detail": detail[:200],
        }
        os.makedirs(os.path.dirname(cls.RECORD_FILE), exist_ok=True)
        with open(cls.RECORD_FILE, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @classmethod
    def get_stats(cls) -> dict:
        """获取执行统计"""
        if not os.path.exists(cls.RECORD_FILE):
            return {"total": 0, "success": 0, "fail": 0}
        total = success = 0
        with open(cls.RECORD_FILE) as f:
            for line in f:
                if line.strip():
                    total += 1
                    try:
                        r = json.loads(line)
                        if r.get("status") == "ok":
                            success += 1
                    except:
                        pass
        return {"total": total, "success": success, "fail": total - success}


# ════════════════════════════════════════════════
#  Harness Task Wrapper — 持久化任务跟踪
# ════════════════════════════════════════════════

class HarnessTask:
    """轻量任务状态（与evomap_harness兼容）"""

    def __init__(self, task_id: str, name: str, owner: str):
        self.task_id = task_id
        self.name = name
        self.owner = owner
        self.state_file = os.path.join(HARNESS_TASKS, f"{task_id}.json")
        self.events_file = os.path.join(HARNESS_EVENTS, f"{task_id}.events.jsonl")
        self._load()

    def _load(self):
        if os.path.exists(self.state_file):
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                "task_id": self.task_id, "name": self.name, "owner": self.owner,
                "status": "created", "progress": 0, "current_step": "",
                "steps": [], "errors": [],
                "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(),
            }
            self._save()
            self._emit("task_created", {"name": self.name, "owner": self.owner})

    def _save(self):
        self.state["updated_at"] = datetime.now().isoformat()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def _emit(self, event_type: str, data: dict = None):
        event = {"ts": datetime.now().isoformat(), "task_id": self.task_id, "type": event_type, "data": data or {}}
        with open(self.events_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def start(self):
        self.state["status"] = "running"
        self._save()
        self._emit("task_started")

    def step_ok(self, step_name: str, detail: str = ""):
        self.state["current_step"] = step_name
        for s in self.state["steps"]:
            if s["name"] == step_name:
                s["status"] = "completed"
                s["detail"] = detail
                break
        else:
            self.state["steps"].append({"name": step_name, "status": "completed", "detail": detail})
        self._save()
        self._emit("step_completed", {"step": step_name, "detail": detail[:100]})

    def step_fail(self, step_name: str, error: str):
        self.state["status"] = "failed"
        self.state["current_step"] = step_name
        self.state["errors"].append({"step": step_name, "error": error[:200], "at": datetime.now().isoformat()})
        self._save()
        self._emit("step_failed", {"step": step_name, "error": error[:100]})

    def complete(self):
        self.state["status"] = "completed"
        self.state["progress"] = 100
        self._save()
        self._emit("task_completed")

    def progress(self, pct: int):
        self.state["progress"] = max(0, min(100, pct))
        self._save()


# ════════════════════════════════════════════════
#  Fusion Engine — 四合一融合引擎
# ════════════════════════════════════════════════

class FusionEngine:
    """DeerFlow ⇄ Hermes ⇄ EvoMap ⇄ Harness 融合引擎"""

    def __init__(self):
        self._hub = None
        self._task_id_counter = 0

    # ── 懒加载 hub ──

    @property
    def hub(self):
        if self._hub is None:
            try:
                from hermes_hub import Hub
                self._hub = Hub()
            except ImportError:
                self._hub = None
        return self._hub

    # ── 1. 伙伴执行 + 状态跟踪 ──

    def run_partner(self, key: str, record: bool = True) -> Dict[str, Any]:
        """执行单个伙伴，附带Harness状态跟踪 + EvoMap记录"""
        start = time.time()

        # 创建任务
        cfg = {"booster": "🍅番茄·选品", "copy": "🥬生菜·文案", "video": "🌽玉米·视频",
               "tts": "🥕萝卜·配音", "risk": "🥒苦瓜·风控", "data": "🫘豌豆·数据"}
        task_id = f"{key}_{int(start)}"
        task = HarnessTask(task_id, cfg.get(key, key), key)
        task.start()

        try:
            # 用hub执行
            if self.hub:
                result = self.hub.run(key)
            else:
                result = {"status": "error", "error": "hub不可用"}
                import subprocess
                sp = os.path.join(SCRIPTS_DIR, f"{key}.py")
                if os.path.exists(sp):
                    proc = subprocess.run(["python3", sp], capture_output=True, text=True, timeout=300)
                    result = {"status": "ok" if proc.returncode == 0 else "error", "output": proc.stdout}

            elapsed = round(time.time() - start, 2)
            status = result.get("status", "error")

            # 记录结果
            if status == "ok":
                task.step_ok("execute", detail=result.get("output", "")[:100])
                task.complete()
            else:
                task.step_fail("execute", result.get("error", "unknown"))

            # EvoMap记录
            if record:
                EvoRecord.record(key, "execute", status, elapsed, result.get("error", ""))

            result["task_id"] = task_id
            result["harness_status"] = task.state["status"]
            result["evomap_recorded"] = record
            return result

        except Exception as e:
            task.step_fail("execute", str(e))
            if record:
                EvoRecord.record(key, "execute", "crash", round(time.time()-start, 2), str(e))
            return {"partner": key, "status": "crash", "error": str(e), "task_id": task_id}

    # ── 2. 工作流执行 ──

    def run_workflow(self, name: str, parallel: bool = True) -> Dict[str, Any]:
        """运行预定义工作流（hub支持）"""
        start = time.time()
        task_id = f"wf_{name}_{int(start)}"
        task = HarnessTask(task_id, f"工作流:{name}", "orchestrator")
        task.start()

        try:
            if self.hub:
                result = self.hub.run_workflow(name, parallel=parallel)
            else:
                result = {"status": "error", "error": "hub不可用"}

            elapsed = round(time.time() - start, 2)

            # 记录
            ok = sum(1 for r in result.get("results", []) if r.get("status") == "ok")
            total = len(result.get("results", []))
            task.step_ok(name, detail=f"{ok}/{total} success")
            task.progress(100 if ok == total else int(ok / total * 100) if total else 0)

            if ok == total:
                task.complete()
            else:
                task.state["status"] = "partial"

            # EvoMap
            EvoRecord.record(f"wf:{name}", "run",
                             "ok" if ok == total else "partial", elapsed)

            result["task_id"] = task_id
            result["harness_status"] = task.state["status"]
            return result

        except Exception as e:
            task.step_fail(name, str(e))
            EvoRecord.record(f"wf:{name}", "run", "crash", round(time.time()-start, 2), str(e))
            return {"workflow": name, "status": "crash", "error": str(e), "task_id": task_id}

    # ── 3. DeerFlow 全链路 ──

    def run_deerflow(self) -> Dict[str, Any]:
        """调用DeerFlow LangGraph工作流（用DeerFlow venv）"""
        start = time.time()
        DEERFLOW_VENV_PYTHON = os.path.expanduser(
            "~/.openclaw/deerflow-official/backend/.venv/bin/python3")

        try:
            # 方案A：用venv的python执行（依赖langgraph已安装）
            code = '''
import sys
sys.path.insert(0, \"/Users/a1234/.openclaw/deerflow-official/backend\")
from tk_workflow.tk_workflow import run_full_workflow
import json
result = run_full_workflow()
print(json.dumps(result, ensure_ascii=False))
'''
            proc = subprocess.run(
                [DEERFLOW_VENV_PYTHON, "-c", code],
                capture_output=True, text=True, timeout=60
            )
            if proc.returncode != 0:
                return {"status": "error", "error": proc.stderr[-500:]}

            # 解析JSON输出
            result = json.loads(proc.stdout)
            elapsed = round(time.time() - start, 2)
            status = "ok" if "completed" in result.get("status", "") else "ok"

            EvoRecord.record("deerflow", "run", status, elapsed,
                             f"{len(result.get('steps_results',[]))}步完成")
            result["duration"] = elapsed
            return result

        except FileNotFoundError:
            # venv python不存在
            return {"status": "error", "error": "DeerFlow venv python未找到"}
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "DeerFlow工作流超时(60s)"}
        except json.JSONDecodeError as e:
            return {"status": "error", "error": f"输出解析失败: {e}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── 4. 一键全栈融合 ──

    def run_all(self, parallel: bool = True) -> Dict[str, Any]:
        """一键执行：工作流 + DeerFlow状态检查"""
        start = time.time()
        results = {}

        # 工作流
        results["market_check"] = self.run_workflow("market_check")
        results["deerflow"] = self.run_deerflow()

        elapsed = round(time.time() - start, 2)
        EvoRecord.record("fusion", "run_all", "ok", elapsed)

        return {
            "fusion_results": results,
            "duration": elapsed,
            "evomap_stats": EvoRecord.get_stats(),
        }

    def status(self) -> Dict[str, Any]:
        """全局融合状态"""
        hub_status = self.hub.status() if self.hub else {"hub": "不可用"}
        evomap = EvoRecord.get_stats()
        harness_tasks = [f for f in os.listdir(HARNESS_TASKS) if f.endswith(".json")]
        deerflow_ok = False
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:8001/health")
            with urllib.request.urlopen(req, timeout=3) as resp:
                deerflow_ok = True
        except:
            pass

        return {
            "fusion": "FusionEngine v1.0",
            "layers": ["Hermes Hub", "Harness Tasks", "DeerFlow", "EvoMap Records"],
            "hub": hub_status,
            "evomap": evomap,
            "harness_tasks": len(harness_tasks),
            "deerflow_online": deerflow_ok,
        }


# ════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FusionEngine — 四合一融合引擎")
    parser.add_argument("action", nargs="?", default="status",
                        choices=["status", "partner", "workflow", "deerflow", "all", "cleanup"])
    parser.add_argument("--key", "-k", default=None)
    parser.add_argument("--workflow", "-w", default="market_check")
    parser.add_argument("--serial", action="store_true")
    args = parser.parse_args()

    fe = FusionEngine()

    if args.action == "status":
        s = fe.status()
        print("📊 FusionEngine 状态")
        print(f"  🧩 Hub: {s['hub'].get('hub','?')}")
        print(f"  👥 伙伴: {s['hub'].get('partners',0)}")
        print(f"  📁 Harness任务: {s['harness_tasks']}个")
        print(f"  🦌 DeerFlow: {'在线' if s['deerflow_online'] else '离线'}")
        print(f"  📚 EvoMap记录: {s['evomap'].get('total',0)}条 (✅{s['evomap'].get('success',0)} ❌{s['evomap'].get('fail',0)})")

    elif args.action == "partner" and args.key:
        r = fe.run_partner(args.key)
        print(f"{'✅' if r.get('status')=='ok' else '❌'} {args.key}: {r.get('status','?')} | {r.get('duration',0):.1f}s")
        print(f"  Task: {r.get('task_id','')} | Harness: {r.get('harness_status','')} | EvoMap: {r.get('evomap_recorded','')}")

    elif args.action == "workflow":
        r = fe.run_workflow(args.workflow, parallel=not args.serial)
        print(r.get("summary", f"Status: {r.get('status','?')}"))
        for s in r.get("results", []):
            print(f"  {'✅' if s.get('status')=='ok' else '❌'} {s.get('name','?')} ({s.get('duration',0):.1f}s)")

    elif args.action == "deerflow":
        d = fe.run_deerflow()
        print(f"🦌 DeerFlow: {d.get('status','?')}")
        if "summary" in d:
            print(f"  {d['summary']}")
        if "message" in d:
            print(f"  {d['message']}")

    elif args.action == "all":
        r = fe.run_all()
        print("🏁 全栈融合执行完成!")
        for k, v in r.get("fusion_results", {}).items():
            print(f"  {k}: {v.get('status','?')} ({v.get('duration',0):.1f}s)")
        print(f"  总耗时: {r['duration']}s")
        print(f"  EvoMap总计: {r['evomap_stats'].get('total',0)}条")

    elif args.action == "cleanup":
        # 清理过期的Harness任务（>7天）
        count = 0
        now = time.time()
        for f in os.listdir(HARNESS_TASKS):
            path = os.path.join(HARNESS_TASKS, f)
            if now - os.path.getmtime(path) > 7*86400:
                os.remove(path)
                count += 1
        for f in os.listdir(HARNESS_EVENTS):
            path = os.path.join(HARNESS_EVENTS, f)
            if now - os.path.getmtime(path) > 7*86400:
                os.remove(path)
                count += 1
        print(f"🧹 已清理{count}个过期任务")
