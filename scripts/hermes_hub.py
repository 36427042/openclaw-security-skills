#!/usr/bin/env python3
"""
hermes_hub.py — Hermes融合接口（6伙伴统一导入入口）
替代subprocess调用，直接import调用，快10-50倍

用法：
  from hermes_hub import Hub
  hub = Hub()
  result = hub.run("booster")   # 调用番茄🍅选品
  result = hub.run("copy")      # 调用生菜🥬文案
  result = hub.run_all()        # 全部并行
  result = hub.run_workflow("market_check")  # 按工作流
"""
import sys, os, json, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

SCRIPTS_DIR = os.path.expanduser("~/.openclaw/workspace/scripts")
sys.path.insert(0, SCRIPTS_DIR)

# ═══════════════════════════════════════════
#  伙伴配置（与hermes_engine.py同步）
# ═══════════════════════════════════════════
PARTNER_CONFIGS = {
    "booster": {"name": "🍅番茄·选品", "script": "booster_matrix.py", "timeout": 60},
    "copy":    {"name": "🥬生菜·文案", "script": "copy_engine.py", "timeout": 60},
    "video":   {"name": "🌽玉米·视频", "script": "video_pipeline_v2.py", "timeout": 600},
    "tts":     {"name": "🥕萝卜·配音", "script": None, "timeout": 30},      # API调用，无独立脚本
    "risk":    {"name": "🥒苦瓜·风控", "script": "risk_controller.py", "timeout": 30},
    "data":    {"name": "🫘豌豆·数据", "script": "data_monitor.py", "timeout": 30},
}

WORKFLOWS = {
    "full_pipeline":     {"subtasks": ["booster", "copy", "video", "risk", "data"]},
    "content_pipeline":  {"subtasks": ["copy", "tts", "video", "risk"]},
    "market_check":      {"subtasks": ["booster", "data", "risk"]},
}

MAX_WORKERS = 4


class Hub:
    """统一融合接口"""

    def __init__(self):
        self._modules = {}  # key: 已导入的模块缓存
        self._cache = {}    # 结果缓存

    # ─── 模块懒加载 ───

    def _import(self, key: str):
        """按需导入伙伴模块"""
        if key in self._modules:
            return self._modules[key]

        cfg = PARTNER_CONFIGS.get(key)
        if not cfg or not cfg["script"]:
            return None

        script_path = os.path.join(SCRIPTS_DIR, cfg["script"])
        if not os.path.exists(script_path):
            return None

        try:
            # 动态导入模块
            import importlib
            mod_name = cfg["script"].replace(".py", "")
            mod = importlib.import_module(mod_name)
            self._modules[key] = mod
            return mod
        except Exception as e:
            return None

    # ─── 统一执行接口 ───

    def run(self, key: str, parallel_context: bool = False) -> Dict[str, Any]:
        """执行单个伙伴任务"""
        cfg = PARTNER_CONFIGS.get(key)
        if not cfg:
            return {"status": "error", "error": f"未知伙伴: {key}"}

        start = time.time()

        # 并行执行时用subprocess（stdout隔离），串行时直接import（快）
        if parallel_context:
            return self._run_subprocess(key)

        mod = self._import(key)

        if mod and hasattr(mod, "main"):
            # ✅ 直接导入调用（快，同步stdout捕获）
            import io
            import contextlib
            try:
                output_capture = io.StringIO()
                with contextlib.redirect_stdout(output_capture):
                    mod.main()
                output = output_capture.getvalue()

                return {
                    "partner": key,
                    "name": cfg["name"],
                    "status": "ok",
                    "duration": round(time.time() - start, 2),
                    "output": output,
                }
            except Exception as e:
                return {
                    "partner": key,
                    "name": cfg["name"],
                    "status": "error",
                    "duration": round(time.time() - start, 2),
                    "error": str(e),
                }
        else:
            return self._run_subprocess(key)

    def _run_subprocess(self, key: str) -> Dict[str, Any]:
        """subprocess fallback（模块加载失败时使用）"""
        import subprocess
        cfg = PARTNER_CONFIGS.get(key)
        if not cfg or not cfg["script"]:
            return {"partner": key, "name": cfg.get("name", "?"), "status": "skipped", "reason": "无脚本"}

        script_path = os.path.join(SCRIPTS_DIR, cfg["script"])
        if not os.path.exists(script_path):
            return {"partner": key, "name": cfg["name"], "status": "skipped", "reason": f"脚本不存在"}

        start = time.time()
        try:
            proc = subprocess.run(["python3", script_path],
                                  capture_output=True, text=True, timeout=cfg["timeout"])
            return {
                "partner": key, "name": cfg["name"],
                "status": "ok" if proc.returncode == 0 else "error",
                "duration": round(time.time() - start, 2),
                "stdout": proc.stdout, "stderr": proc.stderr,
                "error": proc.stderr[-300:] if proc.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            return {"partner": key, "name": cfg["name"], "status": "timeout", "duration": cfg["timeout"]}
        except Exception as e:
            return {"partner": key, "name": cfg["name"], "status": "crash", "error": str(e)}

    # ─── 批量执行 ───

    def run_all(self, parallel: bool = True) -> List[Dict[str, Any]]:
        """全部6伙伴并行执行"""
        keys = list(PARTNER_CONFIGS.keys())
        return self.run_batch(keys, parallel=parallel)

    def run_batch(self, keys: List[str], parallel: bool = True) -> List[Dict[str, Any]]:
        """批量执行指定伙伴"""
        results = []
        if parallel and len(keys) > 1:
            # 并行模式：用subprocess（stdout自然隔离，线程安全）
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
                futures = {exe.submit(self.run, k, True): k for k in keys}
                for future in as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        results.append({"status": "error", "error": str(e), "duration": 0})
        else:
            # 串行模式：直接import（快10-50倍）
            for k in keys:
                results.append(self.run(k, False))
        return results

    def run_workflow(self, name: str, parallel: bool = True) -> Dict[str, Any]:
        """按预定义工作流执行"""
        wf = WORKFLOWS.get(name)
        if not wf:
            return {"status": "error", "error": f"未知工作流: {name}"}

        start = time.time()
        results = self.run_batch(wf["subtasks"], parallel=parallel)

        ok = sum(1 for r in results if r.get("status") == "ok")
        fail = len(results) - ok

        return {
            "workflow": name,
            "subtasks": wf["subtasks"],
            "results": results,
            "summary": f"✅ {ok}/{len(results)} 成功 | ❌ {fail} 失败 | ⏱ {round(time.time() - start, 1)}s",
            "duration": round(time.time() - start, 1),
        }

    # ─── 缓存 ───

    def cached_run(self, key: str, ttl: int = 60) -> Dict[str, Any]:
        """带缓存的执行（TTL秒内返回缓存）"""
        now = time.time()
        if key in self._cache and (now - self._cache[key].get("_ts", 0)) < ttl:
            return self._cache[key].copy()
        result = self.run(key)
        result["_ts"] = now
        self._cache[key] = result
        return result

    def clear_cache(self):
        self._cache.clear()

    # ─── 状态 ───

    def status(self) -> Dict[str, Any]:
        """状态报告"""
        modules_loaded = 0
        modules_fail = 0
        for key in PARTNER_CONFIGS:
            mod = self._import(key)
            if mod:
                modules_loaded += 1
            else:
                modules_fail += 1

        return {
            "hub": "Hermes融合接口 v1.0",
            "partners": len(PARTNER_CONFIGS),
            "workflows": list(WORKFLOWS.keys()),
            "modules_loaded": modules_loaded,
            "modules_fallback_subprocess": modules_fail,
            "cache_size": len(self._cache),
        }


# ═══════════════════════════════════════════
#  CLI入口
# ═══════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes融合接口")
    parser.add_argument("action", nargs="?", default="status",
                        choices=["status", "run", "all", "workflow"])
    parser.add_argument("--partner", "-p", default=None)
    parser.add_argument("--workflow", "-w", default=None)
    parser.add_argument("--serial", action="store_true", help="串行执行")
    args = parser.parse_args()

    hub = Hub()

    if args.action == "status" or (args.action == "run" and not args.partner):
        print(json.dumps(hub.status(), indent=2, ensure_ascii=False))

    elif args.action == "run" and args.partner:
        result = hub.run(args.partner)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.action == "all":
        results = hub.run_all(parallel=not args.serial)
        ok = sum(1 for r in results if r.get("status") == "ok")
        print(f"🏁 {ok}/{len(results)} 成功")
        for r in results:
            icon = '✅' if r.get('status')=='ok' else '❌'
            out_len = len(r.get('output','')) if r.get('output') else len(r.get('stdout',''))
            print(f"  {icon} {r.get('name','?')} ({r.get('duration',0):.1f}s, {out_len}字符)")

    elif args.action == "workflow" and args.workflow:
        result = hub.run_workflow(args.workflow, parallel=not args.serial)
        print(result.get("summary", ""))
        for r in result.get("results", []):
            icon = '✅' if r.get('status')=='ok' else '❌'
            out_len = len(r.get('output','')) if r.get('output') else len(r.get('stdout',''))
            print(f"  {icon} {r.get('name','?')} ({r.get('duration',0):.2f}s, {out_len}字符)")
