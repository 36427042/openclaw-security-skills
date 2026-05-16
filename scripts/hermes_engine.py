#!/usr/bin/env python3
"""
hermes_engine.py — Hermes 任务分派引擎 v3.0
融合DeerFlow原版设计：并行调度 + 自注册工具 + TaskDelegator分拆 + EvoMap闭环

架构:
  DeerFlow (LangGraph编排)
    ↓ 拆解后的子任务
  Hermes TaskDelegator
    ↓ ThreadPoolExecutor 并行
  6伙伴 + 土豆 并行执行
    ↓ 聚合结果
  EvoMap 学习闭环

用法:
  python3 hermes_engine.py --help
  python3 hermes_engine.py run --task "完整上架"         # 自动拆解+并行
  python3 hermes_engine.py run --subtasks '["选品","文案"]'  # 手动指定子任务
  python3 hermes_engine.py run --partner booster            # 单伙伴
  python3 hermes_engine.py list-tools                       # 列出已注册工具
  python3 hermes_engine.py status                           # 运行状态
  python3 hermes_engine.py evolve                           # 运行EvoMap进化
"""

import json, os, subprocess, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, Callable, Any

# ═══════════════════════════════════════════
#  增强模块（v3.1+，纯新增，零侵入）
# ═══════════════════════════════════════════
# hermes_retry   — 指数退避重试（借鉴Claude Code QueryEngine）
# hermes_tools   — 统一工具接口（借鉴Claude Code buildTool）
# hermes_tasks   — 任务生命周期管理（借鉴Claude Code Task System）
# hermes_messages— 伙伴间通信（借鉴Claude Code SendMessageTool）
# hermes_skills  — Skill技能系统（借鉴Claude Code skillify）
# hermes_tasks  — 任务生命周期管理（借鉴Claude Code Task System）
_UPGRADE_AVAILABLE = True
try:
    import hermes_retry
    from hermes_retry import retry_call, retry_video_api, MaxRetriesError, RetryConfig
    _HAS_RETRY = True
except ImportError:
    _HAS_RETRY = False
try:
    import hermes_tools as _ht
    from hermes_tools import build_tool, registry as tool_registry
    _HAS_TOOLS = True
except ImportError:
    _HAS_TOOLS = False
try:
    import hermes_tasks
    from hermes_tasks import task_manager, task_runner
    _HAS_TASKS = True
except ImportError:
    _HAS_TASKS = False
try:
    from hermes_messages import messenger
    _HAS_MSG = True
except ImportError:
    _HAS_MSG = False
try:
    from hermes_skills import skill_registry
    _HAS_SKILLS = True
except ImportError:
    _HAS_SKILLS = False
try:
    from hermes_perms import perms
    _HAS_PERMS = True
except ImportError:
    _HAS_PERMS = False
try:
    from hermes_tokens import tracker
    _HAS_TOKENS = True
except ImportError:
    _HAS_TOKENS = False
try:
    from hermes_memory_extract import extractor, auto_extract
    _HAS_MEMORY = True
except ImportError:
    _HAS_MEMORY = False
try:
    from hermes_flags import flags
    _HAS_FLAGS = True
except ImportError:
    _HAS_FLAGS = False
try:
    from hermes_routing import router
    _HAS_ROUTING = True
except ImportError:
    _HAS_ROUTING = False
try:
    from hermes_compact import compactor
    _HAS_COMPACT = True
except ImportError:
    _HAS_COMPACT = False
try:
    from hermes_watch import watcher
    _HAS_WATCH = True
except ImportError:
    _HAS_WATCH = False
try:
    from hermes_coding import coding
    _HAS_CODING = True
except ImportError:
    _HAS_CODING = False

# ── 路径 ──
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
SCRIPTS_DIR = os.path.join(WORKSPACE, "scripts")
STATE_DIR = os.path.join(WORKSPACE, "data", "hermes")
LOG_DIR = os.path.join(STATE_DIR, "logs")
LEARN_DIR = os.path.join(STATE_DIR, "learnings")
PIPELINE_DIR = os.path.join(WORKSPACE, "data", "pipeline")
PIPELINE_CONTEXT_FILE = os.path.join(PIPELINE_DIR, "context.json")
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(PIPELINE_DIR, exist_ok=True)
os.makedirs(LEARN_DIR, exist_ok=True)

# ── 自注册工具系统 ──
_TOOLS = {}  # name -> {fn, schema, toolset, availability}

def register_tool(fn=None, *, name: str = None, schema: dict = None,
                  toolset: str = "default", available: bool = True):
    """注册一个工具（自注册系统，import即注册）
    用法:
      @register_tool                    # 无参数装饰器
      @register_tool(name="name")       # 带参数装饰器
      register_tool(fn, name="xxx")      # 直接函数式
      register_tool(fn)                  # 直接函数式（用函数名）
    """
    if fn is not None and callable(fn):
        # 直接函数式或裸装饰器
        nm = name if name else fn.__name__
        _TOOLS[nm] = {
            "fn": fn,
            "schema": schema or {"description": fn.__doc__ or ""},
            "toolset": toolset,
            "available": available,
            "registered_at": datetime.now().isoformat(),
        }
        return fn

    # 参数化装饰器 @register_tool(name="xxx")
    def decorator(fn):
        nm = name if name else fn.__name__
        _TOOLS[nm] = {
            "fn": fn,
            "schema": schema or {"description": fn.__doc__ or ""},
            "toolset": toolset,
            "available": available,
            "registered_at": datetime.now().isoformat(),
        }
        return fn
    return decorator

def list_tools(toolset: str = None) -> list:
    """列出已注册工具"""
    tools = _TOOLS
    if toolset:
        tools = {k: v for k, v in tools.items() if v["toolset"] == toolset}
    return [{"name": k, "toolset": v["toolset"],
             "desc": v["schema"].get("description", "")[:60]} for k, v in tools.items()]

def safe_dispatch(name: str, **kwargs) -> dict:
    """安全执行工具（v3.1+ 支持重试）"""
    if name not in _TOOLS:
        return {"status": "error", "error": f"工具未注册: {name}"}
    tool = _TOOLS[name]
    if not tool["available"]:
        return {"status": "unavailable", "error": f"工具不可用: {name}"}
    try:
        if _HAS_RETRY and tool.get("retryable", False):
            import asyncio
            result = asyncio.run(retry_video_api(tool["fn"], **kwargs)) if tool.get("timeout", 0) > 10 \
                     else tool["fn"](**kwargs)
        else:
            result = tool["fn"](**kwargs)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "crash", "error": str(e)}

# ═══════════════════════════════════════════
#  v3.1+ 升级功能
# ═══════════════════════════════════════════

def _upgrade_register_partners() -> dict:
    """用新build_tool系统注册伙伴工具（纯新增，不覆盖旧系统）"""
    if not _HAS_TOOLS:
        return {"status": "skipped", "reason": "hermes_tools 不可用"}
    count = 0
    for key, cfg in PARTNER_CONFIGS.items():
        if tool_registry.get(f"partner_{key}"):
            continue
        tool = {
            "booster": {"desc": "5国选品+定价+25店矩阵计算", "tag": "选品"},
            "copy": {"desc": "5国语言CO-STAR话术生成+合规校验", "tag": "文案"},
            "video": {"desc": "5国视频生成+6层去重+素材管理", "tag": "视频"},
            "tts": {"desc": "多引擎TTS配音+直播", "tag": "配音"},
            "risk": {"desc": "风控审查+违禁词检查+应急SOP", "tag": "风控"},
            "data": {"desc": "数据监控+飞书看板+异常检测", "tag": "数据"},
        }.get(key, {})
        @build_tool(
            name=f"partner_{key}",
            description=tool.get("desc", ""),
            input_schema={"properties": {}, "required": []},
            permission_level="notify",
            partner=key,
            tags=[tool.get("tag", "")],
        )
        def _make_partner_func(k=key):
            return _run_script_subprocess(k)
        count += 1
    return {"status": "ok", "registered": count}

def _upgrade_status() -> dict:
    """升级状态报告"""
    return {
        "retry": "✅" if _HAS_RETRY else "❌",
        "tools": "✅" if _HAS_TOOLS and len(tool_registry) > 0 else "❌",
        "tasks": "✅" if _HAS_TASKS else "❌",
        "retry_module": _HAS_RETRY,
        "tools_module": _HAS_TOOLS,
        "tasks_module": _HAS_TASKS,
        "tools_count": len(tool_registry) if _HAS_TOOLS else 0,
        "task_count": len(task_manager) if _HAS_TASKS else 0,
        "upgrade": "🧬 v3.1" if (_HAS_RETRY and _HAS_TOOLS and _HAS_TASKS) else "⚪ v3.0",
    }

# ═══════════════════════════════════════════
#  6伙伴注册为工具 (自注册)
# ═══════════════════════════════════════════

PARTNER_CONFIGS = {
    "booster": {"name": "🍅番茄·选品", "script": "booster_matrix.py", "timeout": 600,
                "keywords": ["选品","定价","爆单","矩阵","pricing","market"]},
    "copy":    {"name": "🥬生菜·文案", "script": "copy_engine.py", "timeout": 120,
                "keywords": ["文案","话术","描述","copy","content","多语言"]},
    "video":   {"name": "🌽玉米·视频", "script": "pipeline_video.py", "timeout": 600,
                "keywords": ["视频","素材","混剪","去重","video","剪辑"]},
    "tts":     {"name": "🥕萝卜·配音", "script": "qwen_tts_engine.py", "timeout": 120,
                "keywords": ["配音","语音","TTS","直播","voice","audio"]},
    "risk":    {"name": "🥒苦瓜·风控", "script": "risk_controller.py", "timeout": 120,
                "keywords": ["风控","审核","安全","合规","违禁词","risk"]},
    "data":    {"name": "🫘豌豆·数据", "script": "data_monitor.py", "timeout": 120,
                "keywords": ["数据","监控","报表","分析","dashboard","监控预警"]},
}

def _run_script_subprocess(partner_key: str, task: str = None, pipeline_context: str = None) -> dict:
    """执行伙伴脚本 — 用subprocess（stdout自然隔离，线程安全）
    v3.2: 支持 --task 传递任务上下文（通过环境变量 HERMES_TASK）"""
    cfg = PARTNER_CONFIGS[partner_key]
    script_path = os.path.join(SCRIPTS_DIR, cfg.get("script", ""))
    start = time.time()
    result = {"partner": partner_key, "name": cfg["name"], "status": "ok"}

    if not os.path.exists(script_path):
        result["status"] = "skipped"
        result["reason"] = f"脚本不存在: {cfg['script']}"
        return result

    # 🔴 v3.2: 传递任务上下文
    cmd = ["python3", script_path]
    env = os.environ.copy()
    if task:
        env["HERMES_TASK"] = task
        task_file = f"/tmp/hermes_task_{partner_key}_{int(time.time())}.txt"
        with open(task_file, 'w') as f:
            f.write(task)
        env["HERMES_TASK_FILE"] = task_file

    # 🔴 v3.3: 串行流水线上下文传递
    piped_file = pipeline_context or PIPELINE_CONTEXT_FILE
    env["PIPELINE_CONTEXT_FILE"] = piped_file
    if not os.path.exists(piped_file):
        with open(piped_file, 'w') as f:
            json.dump({"chain": [], "products": [], "step": 0}, f)

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=cfg["timeout"], env=env)
        result["duration"] = round(time.time() - start, 2)
        # 🔴 v3.3: 读取脚本写回的pipeline context
        try:
            with open(piped_file) as f:
                result["pipeline_context"] = json.load(f)
        except:
            pass
        if proc.returncode != 0:
            result["status"] = "error"
            result["error"] = proc.stderr[-300:]
    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["duration"] = cfg["timeout"]
    except Exception as e:
        result["status"] = "crash"
        result["error"] = str(e)

    result.setdefault("duration", round(time.time() - start, 2))
    return result


def _run_script_via_hub(partner_key: str, pipeline_context: str = None) -> dict:
    """执行伙伴脚本 — 用hub直接import（快10-50倍，仅串行模式下安全）"""
    try:
        from hermes_hub import Hub
        hub = Hub()
        return hub.run(partner_key, pipeline_context=pipeline_context)
    except ImportError:
        return _run_script_subprocess(partner_key, pipeline_context=pipeline_context)

def _register_partners():
    """工厂方式注册6伙伴，避免lambda闭包捕获问题"""
    for key, cfg in PARTNER_CONFIGS.items():
        # 用闭包捕获当前key的值
        def make_tool(k=key):
            return _run_script_subprocess(k)
        register_tool(make_tool, name=f"partner_{key}",
                      schema={"description": f"执行 {cfg['name']} 脚本"},
                      toolset="partners")

_register_partners()

# v3.1+: 自动注册升级工具系统（如可用）
if _HAS_TOOLS:
    _upgrade_register_partners()

@register_tool(name="土豆_调度", toolset="orchestrator")
def 土豆调度(subtasks: list = None, parallel: bool = True) -> dict:
    """土豆统筹：拆解任务并分派给6伙伴"""
    return delegate_tasks(subtasks or list(PARTNER_CONFIGS.keys()), parallel=parallel)

# ═══════════════════════════════════════════
#  TaskDelegator 任务拆解+并行调度
# ═══════════════════════════════════════════

class IterationBudget:
    """迭代预算控制"""
    def __init__(self, total: int = 1000, timeout: int = 600):
        self.total = total
        self.timeout = timeout
        self._used = 0
        self._start = time.time()

    def consume(self, n: int = 1) -> int:
        self._used += n
        return self._used

    @property
    def exhausted(self) -> bool:
        return self._used >= self.total or (time.time() - self._start) > self.timeout

    @property
    def used(self) -> int:
        return self._used

    def reset(self):
        self._used = 0
        self._start = time.time()

class TaskDelegator:
    """任务拆解+并行调度引擎"""

    MAX_CONCURRENT = 4  # 最大并行数
    MAX_DEPTH = 3       # 最大递归深度

    def __init__(self):
        self._execution_log = []
        self._active = {}

    def decompose(self, task_description: str) -> list:
        """将高级任务描述拆解为子任务列表（关键词匹配版）"""
        task_lower = task_description.lower()
        matched = set()

        for key, cfg in PARTNER_CONFIGS.items():
            for kw in cfg["keywords"]:
                if kw in task_lower:
                    matched.add(key)
                    break

        # 如果啥都没匹配，跑全部
        return list(matched) if matched else list(PARTNER_CONFIGS.keys())

    def delegate_tasks(self, subtask_keys: list, parallel: bool = True) -> list:
        """分派并执行子任务（并行/串行）"""
        budget = IterationBudget()
        results = []
        self._execution_log.append({
            "time": datetime.now().isoformat(),
            "subtasks": subtask_keys,
            "parallel": parallel,
        })

        if parallel and len(subtask_keys) > 1:
            # ── ThreadPoolExecutor 并行 ──
            with ThreadPoolExecutor(max_workers=min(self.MAX_CONCURRENT, len(subtask_keys))) as exe:
                futures = {exe.submit(_run_script_subprocess, k): k for k in subtask_keys}
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        results.append({"partner": key, "status": "crash", "error": str(e)})
                    budget.consume()
        else:
            # ── 串行执行（保持依赖顺序 + 🔴 v3.3 pipeline context） ──
            piped_file = PIPELINE_CONTEXT_FILE
            # Reset pipeline context for fresh chain
            init_ctx = {"chain": [], "products": [], "step": 0, "started": datetime.now().isoformat()}
            with open(piped_file, 'w') as f:
                json.dump(init_ctx, f)
            for i, key in enumerate(subtask_keys):
                # 🔴 v3.3: 读回上次脚本可能更新的context
                try:
                    with open(piped_file) as f:
                        prev_ctx = json.load(f)
                    prev_ctx["step"] = i + 1
                    with open(piped_file, 'w') as f:
                        json.dump(prev_ctx, f)
                except:
                    pass
                result = _run_script_subprocess(key, pipeline_context=piped_file)
                results.append(result)
                budget.consume()

        self._log(f"并行调度: {len(subtask_keys)}个子任务, 并行={parallel}, 耗时={sum(r.get('duration',0) for r in results):.1f}s")
        return results

    def decompose_and_execute(self, task: str, subtasks: list = None, parallel: bool = True) -> dict:
        """高级入口：拆解→执行→聚合"""
        if subtasks is None:
            subtasks = self.decompose(task)
        self._log(f"拆解任务「{task[:40]}」→ {len(subtasks)}个子任务: {subtasks}")

        results = self.delegate_tasks(subtasks, parallel=parallel)

        # 聚合
        ok = sum(1 for r in results if r["status"] == "ok")
        fail = sum(1 for r in results if r["status"] in ("error", "timeout", "crash"))
        total_dur = sum(r.get("duration", 0) for r in results)

        # 学习记录
        self._record_learnings(results)

        return {
            "task": task,
            "subtasks": subtasks,
            "results": results,
            "summary": f"✅ {ok}/{len(results)} 成功 | ❌ {fail} 失败 | ⏱ {total_dur:.1f}s",
            "duration": total_dur,
            "parallel": parallel,
        }

    def _log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logfile = os.path.join(LOG_DIR, f"hermes_{datetime.now().strftime('%Y%m%d')}.log")
        entry = f"[{ts}] [DELEGATOR] {msg}"
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
        print(f"  🧩 {entry}")

    def _record_learnings(self, results: list):
        """EvoMap学习：记录失败的伙伴和原因"""
        failed = [r for r in results if r["status"] in ("error", "timeout", "crash")]
        if failed:
            learn_file = os.path.join(LEARN_DIR, "failures.jsonl")
            with open(learn_file, "a", encoding="utf-8") as f:
                for r in failed:
                    record = {
                        "timestamp": datetime.now().isoformat(),
                        "partner": r.get("name", r.get("partner", "?")),
                        "status": r["status"],
                        "error": r.get("error", r.get("reason", "unknown"))[:200],
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

# 全局单例
_delegator = TaskDelegator()
delegate_tasks = _delegator.delegate_tasks

# ═══════════════════════════════════════════
#  语义路由（AI任务→匹配伙伴）
# ═══════════════════════════════════════════

def route_task(task_desc: str) -> list:
    """AI语义分派：根据关键词匹配伙伴"""
    task_lower = task_desc.lower()
    matched = []
    for key, cfg in PARTNER_CONFIGS.items():
        if any(kw in task_lower for kw in cfg["keywords"]):
            matched.append(key)
    return matched if matched else list(PARTNER_CONFIGS.keys())

# ═══════════════════════════════════════════
#  工作流预定义
# ═══════════════════════════════════════════

WORKFLOWS = {
    "full_pipeline": ["booster", "copy", "video", "risk", "data"],
    "content_pipeline": ["copy", "tts", "video", "risk"],
    "market_check": ["booster", "data", "risk"],
}

# ═══════════════════════════════════════════
#  EvoMap 进化引擎（精简版）
# ═══════════════════════════════════════════

def run_evolution():
    """EvoMap进化循环：扫描失败记录 → 发现模式 → 输出优化建议"""
    learn_file = os.path.join(LEARN_DIR, "failures.jsonl")
    if not os.path.exists(learn_file):
        return {"status": "ok", "message": "无失败记录，无需进化"}

    with open(learn_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    if not records:
        return {"status": "ok", "message": "无失败记录，无需进化"}

    recent = records[-20:]
    # 按伙伴分组统计失败次数
    from collections import Counter
    fail_counts = Counter(r.get("partner", "?") for r in recent)

    patterns = []
    for partner, count in fail_counts.most_common(3):
        if count >= 2:
            patterns.append(f"{partner}: 失败{count}次/{len(recent)}次")

    evolved = bool(patterns)
    suggestions = "\n".join(f"  ⚠️ {p}" for p in patterns) if patterns else "  ✅ 无重复失败模式"

    # 存档进化结果
    evolution_file = os.path.join(LEARN_DIR, "evolution.md")
    with open(evolution_file, "a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')} EvoMap进化\n")
        f.write(f"{suggestions}\n")

    return {
        "status": "evolved" if evolved else "clean",
        "records_checked": len(recent),
        "patterns": patterns,
        "suggestions": suggestions,
    }

# ═══════════════════════════════════════════
#  🥔 土豆进度巡检（实时读取task_board+EchoTik+服务状态）
# ═══════════════════════════════════════════

def _print_commander_progress():
    """读取task_board + 实时服务状态，输出土豆当前进展"""
    import subprocess as sp
    
    # 1. 任务看板统计
    task_board = os.path.expanduser("~/.openclaw/workspace/agents/tomato-agent/task_board.md")
    done = inprog = pending = blocked = 0
    if os.path.exists(task_board):
        with open(task_board) as f:
            for line in f:
                if '✅' in line and '|' in line: done += 1
                elif '🔄' in line: inprog += 1
                elif '⏳' in line: pending += 1
                elif '🔴' in line: blocked += 1
        print(f"  📋 任务看板: ✅{done} 🔄{inprog} ⏳{pending} 🔴{blocked}")
    
    # 2. EchoTik 拉取进度
    echotik_log = "/tmp/echotik_full.log"
    if os.path.exists(echotik_log):
        with open(echotik_log) as f:
            lines = f.readlines()
            last_line = lines[-1].strip() if lines else ""
            if "完成" in last_line and "总商品数" in last_line:
                print(f"  📡 EchoTik: ✅ 拉取完成")
            elif "INFO" in last_line:
                # 提取品类/国家，格式: [厨房用品] [PH] [保鲜容器] 第2/10页...
                import re
                m = re.search(r'\[([^\]]+)\]\s*\[([A-Z]{2})\]', last_line)
                if m:
                    print(f"  📡 EchoTik: 🔄 {m.group(1)}/{m.group(2)}")
                else:
                    print(f"  📡 EchoTik: 🔄 运行中")
            else:
                print(f"  📡 EchoTik: 🔄 运行中")
    else:
        # 检查进程
        try:
            result = sp.run(["pgrep", "-f", "echotik_fetcher"], capture_output=True, text=True)
            if result.stdout.strip():
                print(f"  📡 EchoTik: 🔄 进程运行中")
            else:
                print(f"  📡 EchoTik: ⚪ 未启动")
        except:
            print(f"  📡 EchoTik: ⚪ 未启动")
    
    # 3. 服务状态
    services = {
        "AIRI-Male": "http://localhost:5173",
        "7虾面板": "http://localhost:8889",
    }
    svc_status = []
    for name, url in services.items():
        try:
            import urllib.request
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2):
                svc_status.append(f"✅ {name}")
        except:
            svc_status.append(f"❌ {name}")
    print(f"  🌐 服务: {'  '.join(svc_status)}")
    
    # 4. 4个关键伙伴最新产出
    partner_dirs = {
        "🫘 豌豆": "pea-agent",
        "🥬 生菜": "lettuce-agent", 
        "🥒 苦瓜": "bittergourd-agent",
        "🌽 玉米": "corn-agent",
    }
    for name, pdir in partner_dirs.items():
        output_dir = os.path.expanduser(f"~/.openclaw/workspace/agents/{pdir}/output")
        if os.path.isdir(output_dir):
            mds = sorted(
                [f for f in os.listdir(output_dir) if f.endswith('.md')],
                key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
                reverse=True
            )
            if mds:
                newest = mds[0]
                mtime = datetime.fromtimestamp(os.path.getmtime(os.path.join(output_dir, newest)))
                # 检查是否是今天
                is_today = mtime.strftime("%Y-%m-%d") == datetime.now().strftime("%Y-%m-%d")
                tag = "🆕" if is_today else "📦"
                print(f"  {name}: {tag} {newest[:45]}")
            else:
                print(f"  {name}: ⚪ 无产出")
        else:
            print(f"  {name}: ⚪ 无产出")
    
    # 5. EvoMap状态
    evomap_reg = os.path.expanduser("~/.openclaw/workspace/EvoMap/evomap_registry.json")
    if os.path.exists(evomap_reg):
        with open(evomap_reg) as f:
            reg = json.load(f)
        nodes = reg.get("nodes", []) if isinstance(reg, dict) else []
        if isinstance(nodes, list):
            active = sum(1 for n in nodes if isinstance(n, dict) and n.get("status") == "active")
            print(f"  🗺️ EvoMap: {active}/{len(nodes)}节点已注册")
        elif isinstance(nodes, dict):
            active = sum(1 for n in nodes.values() if isinstance(n, dict) and n.get("status") == "active")
            print(f"  🗺️ EvoMap: {active}/{len(nodes)}节点活跃")
    
    # 6. 已解决问题的实时统计（对比失败记录中已修复的）
    failures_file = os.path.join(LEARN_DIR, "failures.jsonl")
    resolved_file = os.path.join(LEARN_DIR, "resolved.jsonl")
    if os.path.exists(failures_file):
        with open(failures_file) as f:
            fail_count = sum(1 for _ in f)
    else:
        fail_count = 0
    if os.path.exists(resolved_file):
        with open(resolved_file) as f:
            resolved_count = sum(1 for _ in f)
    else:
        resolved_count = 0
    
    if fail_count or resolved_count:
        rate = f"{resolved_count/(fail_count+resolved_count)*100:.0f}%" if (fail_count+resolved_count) else "-"
        print(f"  🩺 问题: {fail_count}条 🔴 → {resolved_count}条已解决 🟢 (修复率{rate})")
    else:
        print(f"  🩺 问题: 无历史记录")

# ═══════════════════════════════════════════
#  报告生成 + 飞书推送
# ═══════════════════════════════════════════

def generate_report(result: dict) -> str:
    """生成结构化的执行报告"""
    
    # DeerFlow工作流报告格式
    if "steps" in result and "task" not in result:
        lines = [
            f"🦌 DeerFlow 全链路报告",
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"状态: {result.get('status', 'N/A')}",
            f"步数: {result.get('steps', 0)}步",
            f"错误: {result.get('errors', 0)}个",
            f"{'─'*40}",
        ]
        if result.get("errors", 0) == 0:
            lines.append("✅ 全链路7步全部通过")
        else:
            lines.append(f"⚠️ 有 {result['errors']} 个步骤需要关注")
        return "\n".join(lines)
    
    # Hermes并行任务报告格式
    lines = [
        f"🛡️ HERMES 并行任务报告",
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"任务: {result.get('task', 'N/A')[:50]}",
        f"并行: {'是' if result.get('parallel') else '否'}",
        f"子任务: {len(result.get('results', []))}个",
        f"{'─'*40}",
    ]

    for r in result.get("results", []):
        icon = {"ok": "✅", "error": "❌", "skipped": "⏭️",
                "timeout": "⏰", "crash": "💥"}.get(r["status"], "❓")
        dur = r.get("duration", "?")
        lines.append(f"{icon} {r.get('name', r.get('partner','?'))}: {r['status']} ({dur}s)")

    lines.append(f"{'─'*40}")
    lines.append(f"📊 {result.get('summary', '')}")

    return "\n".join(lines)

# ═══════════════════════════════════════════
#  DeerFlow 工作流集成
# ═══════════════════════════════════════════

DEERFLOW_URL = "http://localhost:8001"

def _run_deerflow_workflow(workflow_name: str = "tk_workflow") -> dict:
    """调用DeerFlow LangGraph工作流
    
    策略（三级fallback）：
    1. 用DeerFlow venv Python → subprocess（最可靠，langgraph已安装）
    2. 直接导入（仅当系统python有langgraph）
    3. DeerFlow REST API
    """
    start = time.time()
    
    # ── 策略1: venv subprocess（首选） ──
    venv_python = os.path.expanduser("~/.openclaw/deerflow-official/backend/.venv/bin/python")
    tk_workflow_dir = os.path.expanduser("~/.openclaw/deerflow-official/backend/tk_workflow")
    
    if os.path.exists(venv_python) and os.path.exists(tk_workflow_dir):
        try:
            result = subprocess.run(
                [venv_python, "-c", f"""
import sys, json
sys.path.insert(0, '{tk_workflow_dir}')
from tk_workflow import run_full_workflow
result = run_full_workflow()
print(json.dumps({{"status": result.get("status","?"), "errors": len(result.get("errors",[])), "steps": result.get("step_index",0)}}))
"""],
                capture_output=True, text=True, timeout=600,
                cwd=tk_workflow_dir
            )
            output = result.stdout.strip()
            print(f"[hermes] DeerFlow venv完成: {output[:200]}")
            workflow_result = json.loads(output) if output else {"status": result.returncode}
            
            # 记录学习：DeerFlow错误记入EvoMap演化库
            if workflow_result.get("errors") and workflow_result["errors"] > 0:
                learn_file = os.path.join(LEARN_DIR, "failures.jsonl")
                os.makedirs(LEARN_DIR, exist_ok=True)
                with open(learn_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "time": datetime.now().isoformat(),
                        "partner": "deerflow",
                        "task": "tk_workflow",
                        "error": f"{workflow_result['errors']} step(s) failed",
                        "context": workflow_result
                    }, ensure_ascii=False) + "\n")
            
            return workflow_result
        except Exception as e:
            print(f"[hermes] DeerFlow venv失败, 尝试直接导入: {e}")
    
    # ── 策略2: 直接导入（fallback） ──
    try:
        sys.path.insert(0, tk_workflow_dir)
        from tk_workflow import run_workflow
        result = run_workflow()
        print(f"[hermes] DeerFlow直接导入完成")
        return result
    except ImportError:
        pass
    
    # ── 策略3: REST API（最后防线） ──
    try:
        import urllib.request
        data = json.dumps({"workflow": workflow_name}).encode()
        req = urllib.request.Request(
            f"{DEERFLOW_URL}/api/workflow/run",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        pass
    
    return {"status": "error", "workflow": workflow_name, "error": "所有调用路径均失败"}

@register_tool(name="deerflow_run", toolset="orchestrator")
def deerflow_run(workflow_name: str = "tk_workflow") -> dict:
    """运行DeerFlow全链路工作流"""
    return _run_deerflow_workflow(workflow_name)

@register_tool(name="deerflow_health", toolset="orchestrator")
def deerflow_health() -> dict:
    """检查DeerFlow服务状态"""
    try:
        import urllib.request
        req = urllib.request.Request(f"{DEERFLOW_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"status": "error", "error": str(e)}

def push_to_feishu(report: str):
    """输出报告（cron delivery会自动推送到飞书）"""
    print(report)
    print("\n📨 报告已输出，cron delivery将推送到飞书")

# ═══════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════

def print_help():
    print("""HERMES 任务分派引擎 v3.0 — 并行调度+自注册工具+EvoMap闭环

用法:
  hermes_engine.py run --task "<描述>"                 # AI拆解+并行执行
  hermes_engine.py run --subtasks '["booster","copy"]' # 手动指定子任务
  hermes_engine.py run --workflow <名称>                # 预定义工作流
  hermes_engine.py run --partner <key>                  # 单伙伴执行
  hermes_engine.py run --all                            # 全部并行跑
  hermes_engine.py run --serial --workflow full_pipeline # 串行模式
  hermes_engine.py list-tools                           # 列出已注册工具
  hermes_engine.py status                               # 运行状态
  hermes_engine.py evolve                               # 运行EvoMap进化
  hermes_engine.py learnings                            # 查看学习记录

工作流:
  full_pipeline     🏭 选品→文案→视频→风控→数据
  content_pipeline  🎬 文案→配音→视频→风控
  market_check      🔍 选品+数据+风控

伙伴:
  booster 🍅  copy 🥬  video 🌽  tts 🥕  risk 🥒  data 🫘

v3.1+ 增强命令:
  upgrade           查看升级模块状态 (--register 注册工具, --tasks 看任务)
  task              任务生命周期管理 (create/list/get/stop)
  message           伙伴间通信 (send/read/team/broadcast)
  skill             Skill技能系统 (create/list/run/skillify)
  perm              权限系统 (rule/check/log)
  token             Token消耗追踪 (stats/list)
  memo              记忆自动提取 (extract/save)
  flag              Feature Flag系统 (on/off/toggle)
  route             自动路由 (send/stats)
  compact           记忆压缩 (analyze/run/stats)
  watch             实时监控 (events/summary/check)
  coding            编程增强 (run/review/workspace)
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]

    if cmd in ("--help", "-h", "help"):
        print_help()

    elif cmd == "list-tools":
        tools = list_tools()
        print(f"📦 已注册工具: {len(tools)}个")
        for t in tools:
            print(f"  🔧 {t['name']} [{t['toolset']}] — {t['desc']}")

    elif cmd == "status":
        print(f"📊 HERMES 融合引擎 v3.1")
        print(f"  🧩 工具: {len(_TOOLS)}个")
        print(f"  👥 伙伴: {len(PARTNER_CONFIGS)}个")
        print(f"  🏭 工作流: {len(WORKFLOWS)}个")
        print(f"  ⚡ 最大并行: {TaskDelegator.MAX_CONCURRENT}个线程")

        # Hub状态
        try:
            from hermes_hub import Hub
            hub = Hub()
            hs = hub.status()
            print(f"  🔄 融合接口: import直调{hs['modules_loaded']}个, subprocess备用{hs['modules_fallback_subprocess']}个")
        except ImportError:
            print(f"  ⚠️ 融合接口: 未加载")

        # DeerFlow状态
        try:
            import urllib.request
            req = urllib.request.Request(f"{DEERFLOW_URL}/health")
            with urllib.request.urlopen(req, timeout=3) as resp:
                df = json.loads(resp.read().decode())
                print(f"  🦌 DeerFlow: 服务中")
        except Exception:
            print(f"  🦌 DeerFlow: 未响应")

        learn_file = os.path.join(LEARN_DIR, "failures.jsonl")
        if os.path.exists(learn_file):
            with open(learn_file) as f:
                count = sum(1 for _ in f)
            print(f"  📚 学习记录: {count}条")

        # ── 🥔 土豆进度巡检 ──
        print(f"\n{'─'*50}")
        print(f"🥔 土豆·统筹 当前进展")
        print(f"{'─'*50}")
        _print_commander_progress()

    elif cmd == "run":
        parallel = "--serial" not in sys.argv

        # --partner <key> — 单伙伴模式（支持 --task 传递任务上下文）
        # 🔴 v3.2: 优先检查 --partner，支持 --partner copy --task "..."
        if "--partner" in sys.argv:
            idx = sys.argv.index("--partner") + 1
            key = sys.argv[idx]
            task_arg = None
            if "--task" in sys.argv:
                tidx = sys.argv.index("--task") + 1
                if tidx < len(sys.argv):
                    task_arg = " ".join(sys.argv[tidx:])
                    if task_arg.startswith("\"") and task_arg.endswith("\""):
                        task_arg = task_arg[1:-1]
            # 🔴 v3.3: 串行pipeline上下文（--partner模式下也传递）
            piped_file = PIPELINE_CONTEXT_FILE
            try:
                from hermes_hub import Hub
                hub = Hub()
                kwargs = {} if task_arg is None else {'task': task_arg}
                r = hub.run(key, pipeline_context=piped_file, **kwargs)
            except ImportError:
                kwargs = {} if task_arg is None else {'task': task_arg}
                r = _run_script_subprocess(key, pipeline_context=piped_file, **kwargs)
            result = {"task": f"partner:{key}", "subtasks": [key],
                      "results": [r], "summary": r["status"],
                      "duration": r.get("duration", 0), "parallel": False}

        # --task "描述" — AI拆解+并行执行（无 --partner 时）
        elif "--task" in sys.argv:
            idx = sys.argv.index("--task") + 1
            task_desc = " ".join(sys.argv[idx:])
            subtasks = _delegator.decompose(task_desc)
            print(f"🤖 拆解「{task_desc[:50]}」→ {', '.join(PARTNER_CONFIGS[k]['name'] for k in subtasks)}")
            result = _delegator.decompose_and_execute(task_desc, subtasks=subtasks, parallel=parallel)

        # --subtasks '["booster","copy"]'
        elif "--subtasks" in sys.argv:
            idx = sys.argv.index("--subtasks") + 1
            subtasks = json.loads(sys.argv[idx])
            result = _delegator.decompose_and_execute("manual", subtasks=subtasks, parallel=parallel)

        # --workflow <名称>
        elif "--workflow" in sys.argv:
            idx = sys.argv.index("--workflow") + 1
            wf_name = sys.argv[idx]

            # DeerFlow全链路走直接调
            if wf_name == "deerflow":
                print(f"🦌 调用DeerFlow全链路工作流...")
                result = _run_deerflow_workflow("tk_workflow")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                subtasks = WORKFLOWS.get(wf_name, list(PARTNER_CONFIGS.keys()))
                print(f"🏭 工作流: {wf_name} → {' → '.join(subtasks)}")
                print(f"  模式: {'并行' if parallel else '串行'}")
                result = _delegator.decompose_and_execute(f"wf:{wf_name}", subtasks=subtasks, parallel=parallel)

        # --all (所有伙伴并行跑)
        elif "--all" in sys.argv:
            print(f"🚀 全部{len(PARTNER_CONFIGS)}个伙伴并行执行!")
            result = _delegator.decompose_and_execute("all", subtasks=list(PARTNER_CONFIGS.keys()))

        else:
            print("❌ 请指定任务类型")
            return

        report = generate_report(result)
        push_to_feishu(report)
        
        # ── EvoMap 进化记录 ──
        try:
            evo_result = run_evolution()
            if evo_result.get("evolved"):
                print(f"\n🧬 EvoMap进化: {evo_result.get('patterns', '无新模式')}")
        except Exception as e:
            pass  # 进化记录失败不阻塞主流程

    elif cmd == "evolve":
        print("♻️ 运行EvoMap进化...")
        result = run_evolution()
        print(f"  状态: {result['status']}")
        print(f"  检查: {result.get('records_checked', 0)}条记录")
        print(f"  模式: {result.get('patterns', []) or '无'}")
        print(result.get("suggestions", ""))

    elif cmd == "learnings":
        learn_file = os.path.join(LEARN_DIR, "failures.jsonl")
        evo_file = os.path.join(LEARN_DIR, "evolution.md")
        if os.path.exists(learn_file):
            with open(learn_file) as f:
                lines = f.readlines()
            print(f"📝 失败记录 ({len(lines)}条):")
            for line in lines[-10:]:
                r = json.loads(line)
                print(f"  [{r['timestamp'][:16]}] {r['partner']}: {r['error'][:60]}")
        if os.path.exists(evo_file):
            print(f"\n📈 进化记录:")
            with open(evo_file) as f:
                print(f.read()[-500:])

    elif cmd == "upgrade":
        """v3.1+ 升级状态检查+注册"""
        print(f"🧬 HERMES v3.1 升级模块")
        print(f"  {'='*40}")
        s = _upgrade_status()
        print(f"  Retry: {s['retry']}     — 指数退避重试")
        print(f"  Tools: {s['tools']}     — 统一工具接口 ({s['tools_count']}个)")
        print(f"  Tasks: {s['tasks']}     — 任务生命周期 ({s['task_count']}个)")
        print(f"  版本: {s['upgrade']}")

        if '--register' in sys.argv and _HAS_TOOLS:
            r = _upgrade_register_partners()
            print(f"\n  注册: {r['status']} (新增{r.get('registered',0)}个)")

        if '--tasks' in sys.argv and _HAS_TASKS:
            tasks = task_manager.list(limit=5)
            print(f"\n  📋 最近任务:")
            for t in tasks:
                print(f"    [{t['status']}] {t['name']} ({t.get('duration_s', '?')}s)")

    elif cmd == "task":
        """任务管理: task create/list/get/stop"""
        if not _HAS_TASKS:
            print("❌ hermes_tasks 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "list"
        if sub == "create" and len(sys.argv) > 3:
            t = task_manager.create(sys.argv[3], partner=sys.argv[4] if len(sys.argv) > 4 else "")
            print(f"✅ 任务创建: {t.id[:8]}... {t.name}")
        elif sub == "list":
            tasks = task_manager.list(limit=10)
            for t in tasks:
                print(f"  [{t['status']:>9}] {t['id'][:8]} {t['name']} ({t.get('partner','?')})")
        elif sub == "get" and len(sys.argv) > 3:
            t = task_manager.get(sys.argv[3])
            print(json.dumps(t, indent=2, ensure_ascii=False) if t else "❌ 未找到")
        elif sub == "stop" and len(sys.argv) > 3:
            t = task_manager.stop(sys.argv[3])
            print(f"✅ 已停止: {t['id'][:8]} {t['name']}" if t else "❌ 未找到")
        else:
            print("用法: task create <名称> [伙伴] | list | get <id> | stop <id>")

    elif cmd == "message":
        """伙伴间通信: message send/read/broadcast/team"""
        if not _HAS_MSG:
            print("❌ hermes_messages 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help" or sub == "--help":
            print("用法:")
            print("  message stats                     # 消息统计")
            print("  message send <from> <to> <主题>     # 发送消息")
            print("  message read <partner>            # 读收件箱")
            print("  message broadcast <from> <主题>    # 全员广播")
            print("  message team <名称> <成员1 成员2>  # 组队")
        elif sub == "stats":
            s = messenger.stats()
            print(f"📊 消息统计: {s['total_messages']}条总, {s['unread']}条未读, {s['teams']}个团队")
            for inbox, cnt in s["inboxes"].items():
                print(f"  {inbox}: {cnt['total']}总 / {cnt['unread']}未读")
        elif sub == "send" and len(sys.argv) > 5:
            m = messenger.send(sys.argv[3], sys.argv[4], sys.argv[5], " ".join(sys.argv[6:]))
            print(f"✅ 已发送: {m['id'][:12]}... {m['subject']}")
        elif sub == "read" and len(sys.argv) > 3:
            msgs = messenger.read(sys.argv[3])
            print(f"📥 {sys.argv[3]}的收件箱 ({len(msgs)}条未读):")
            for m in msgs:
                urgent = "‼️ " if m["urgent"] else ""
                print(f"  {urgent}[{m['id'][:8]}] {m['from']}: {m['subject']} — {m['body'][:60]}")
        elif sub == "broadcast" and len(sys.argv) > 4:
            r = messenger.broadcast(sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
            print(f"✅ 已广播给 {len(r)} 个伙伴")
        elif sub == "team" and len(sys.argv) > 4:
            t = messenger.create_team(sys.argv[3], sys.argv[4:])
            print(f"✅ 团队已创建: {t['name']} ({len(t['members'])}人)")
        else:
            print("❌ 用法: message help")

    elif cmd == "skill":
        """Skill技能系统: skill create/list/run/skillify"""
        if not _HAS_SKILLS:
            print("❌ hermes_skills 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help" or sub == "--help":
            print("用法:")
            print("  skill list [tag]              # 列出Skills")
            print("  skill create <名称> [步骤...]   # 创建Skill")
            print("  skill run <名称>               # 运行Skill")
            print("  skill delete <名称>            # 删除Skill")
            print("  skill skillify <名称> [步骤...] # 从步骤创建")
            print("  skill stats                   # 统计")
        elif sub == "list":
            tag = sys.argv[3] if len(sys.argv) > 3 else None
            skills = skill_registry.list(tag=tag)
            print(f"📋 Skills ({len(skills)}个):")
            for s in skills:
                steps = " → ".join(s["steps"]) if s["steps"] else "(无)"
                print(f"  {s['name']} ({len(s['steps'])}步, {s['run_count']}次): {steps}")
        elif sub == "create" and len(sys.argv) > 4:
            s = skill_registry.create(sys.argv[3], steps=sys.argv[4:])
            print(f"✅ 已创建: {s.name} ({len(s.steps)}步)")
        elif sub == "run" and len(sys.argv) > 3:
            r = skill_registry.run(sys.argv[3])
            if r["status"] == "ready":
                print(f"🏃 {sys.argv[3]} 已就绪 ({r['duration_s']}s): {' → '.join(r['steps'])}")
            else:
                print(f"❌ {r.get('error', '未知错误')}")
        elif sub == "delete" and len(sys.argv) > 3:
            ok = skill_registry.delete(sys.argv[3])
            print(f"✅ 已删除" if ok else "❌ 未找到")
        elif sub == "skillify" and len(sys.argv) > 4:
            name = sys.argv[3]
            s = skill_registry.skillify(name, f'快速自动创建: {name}', steps=sys.argv[4:])
            print(f"✅ skillify: {s.name} ({len(s.steps)}步)")
        elif sub == "stats":
            stats = skill_registry.stats()
            print(f"📊 Skills统计: {stats['total']}个, {stats['total_runs']}次运行")
            for line in stats["skills"]:
                print(f"  {line}")
        else:
            print("❌ 用法: skill help")

    elif cmd == "perm":
        """权限系统: perm rule/check/log"""
        if not _HAS_PERMS:
            print("❌ hermes_perms 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help":
            print("用法:")
            print("  perm rule <pattern> <level>    # 添加规则 (auto/notify/confirm/escalate)")
            print("  perm check <tool> [user]      # 检查权限")
            print("  perm list                     # 列出规则")
            print("  perm log [limit]              # 审计日志")
        elif sub == "list":
            for r in perms.list_rules():
                print(f"  {r['pattern']:25s} → {r['level']:10s} {r.get('description','')}")
        elif sub == "check" and len(sys.argv) > 3:
            r = perms.check(sys.argv[3], user=sys.argv[4] if len(sys.argv) > 4 else "")
            print(f"  {sys.argv[3]} → allowed={r['allowed']} ({r['level']}): {r['reason']}")
        elif sub == "rule" and len(sys.argv) > 4:
            desc = " ".join(sys.argv[5:]) if len(sys.argv) > 5 else ""
            r = perms.rule(sys.argv[3], sys.argv[4], desc)
            print(f"✅ 规则已添加: {r.pattern} → {r.level.value}")
        elif sub == "log":
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            for l in perms.audit_log(limit):
                print(f"  [{l['created_at'][:19]}] {l['action']:>8} {l['user']:10s} {l['tool']:20s} ({l['level']})")
        else:
            print("❌ 用法: perm help")

    elif cmd == "token":
        """Token消耗追踪: token stats/list"""
        if not _HAS_TOKENS:
            print("❌ hermes_tokens 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "stats"
        if sub == "stats":
            s = tracker.stats()
            print(f"📊 Token消耗统计")
            print(f"  总调用: {s['total_calls']}次")
            print(f"  总token: {s['total_tokens']}")
            print(f"  总成本: ¥{s['total_cost']}")
            print(f"  今日: {s['today_calls']}次 / ¥{s['today_cost']}")
            warn = s.get('budget_warn', 200)
            print(f"  预算: {'⚠️ 超' + str(warn) + '元线' if s.get('above_warn') else '✅ 正常'}")
            print(f"  按模型:")
            for m, d in s.get('by_model', {}).items():
                print(f"    {m:25s} {d['calls']:3d}次  {d['tokens']:6d}tokens  ¥{d['cost']:.2f}")
            print(f"  按伙伴:")
            for p, d in s.get('by_partner', {}).items():
                print(f"    {p:15s} {d['calls']:3d}次  {d['tokens']:6d}tokens  ¥{d['cost']:.2f}")
        elif sub == "list":
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            partner = sys.argv[4] if len(sys.argv) > 4 else None
            records = tracker.list(limit=limit, partner=partner)
            print(f"📋 最近 {len(records)} 条记录:")
            for r in records:
                print(f"  [{r['timestamp'][:19]}] {r['model']:25s} {r['total_tokens']:6d}tok  ¥{r['cost']:.2f}  {r.get('partner',''):10s}")
        elif sub == "record":
            # 手动记录一次
            model = sys.argv[3] if len(sys.argv) > 3 else "manual"
            tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 0
            r = tracker.record(model=model, total_tokens=tokens)
            print(f"✅ 已记录: {r['model']} {r['total_tokens']}tok ¥{r['cost']}")
        else:
            print("用法: token stats | list [limit] [partner] | record <model> <tokens>")

    elif cmd == "memo":
        """记忆提取: memo extract/save"""
        if not _HAS_MEMORY:
            print("❌ hermes_memory_extract 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help":
            print("用法:")
            print("  memo extract <文本> [partner]  # 提取记忆事实")
            print("  memo extract-file <文件> [partner] # 从文件提取")
            print("  memo stats                    # 记忆统计")
        elif sub == "extract" and len(sys.argv) > 3:
            text = " ".join(sys.argv[3:])
            partner = sys.argv[4] if len(sys.argv) > 4 else ""
            facts = extractor.extract(text, partner)
            print(f"📝 提取 {len(facts)} 条事实:")
            for f in facts:
                print(f"  [{f.type:18s}] {f.content[:80]}")
        elif sub == "extract-file" and len(sys.argv) > 3:
            filepath = sys.argv[3]
            partner = sys.argv[4] if len(sys.argv) > 4 else "booster"
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                saved = auto_extract(text, partner, f"file:{filepath}")
                print(f"✅ 已提取并保存 {saved} 条到 {partner}")
            else:
                print(f"❌ 文件不存在: {filepath}")
        elif sub == "stats":
            s = extractor.stats()
            print(f"📊 记忆统计: 共 {s['total']} 条")
            for p, c in s.get('by_partner', {}).items():
                print(f"  {p:15s} {c}条")
            for t, c in s.get('by_type', {}).items():
                print(f"  {t:20s} {c}条")
        else:
            print("❌ 用法: memo help")

    elif cmd == "flag":
        """Feature Flag系统: flag on/off/list/check"""
        if not _HAS_FLAGS:
            print("❌ hermes_flags 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help":
            print("用法:")
            print("  flag list [category]    # 列出flags")
            print("  flag on <name> [by]     # 启用")
            print("  flag off <name> [by]    # 禁用")
            print("  flag toggle <name>      # 切换")
            print("  flag check <name>       # 检查是否有效")
            print("  flag stats              # 统计")
            print("")
            print("分类: core / workflow / experimental")
        elif sub == "list":
            cat = sys.argv[3] if len(sys.argv) > 3 else ""
            flist = flags.list(category=cat)
            print(f"📋 Flags ({len(flist)}):")
            for f in flist:
                status = "🟢" if f["enabled"] else "⭕"
                print(f"  {status} {f['name']:25s} {f['category']:15s} {f.get('description','')}")
        elif sub == "on" and len(sys.argv) > 3:
            by = sys.argv[4] if len(sys.argv) > 4 else "CLI"
            ok = flags.on(sys.argv[3], by)
            print(f"✅ {sys.argv[3]} → ON" if ok else f"❌ {sys.argv[3]} 不存在")
        elif sub == "off" and len(sys.argv) > 3:
            by = sys.argv[4] if len(sys.argv) > 4 else "CLI"
            ok = flags.off(sys.argv[3], by)
            print(f"✅ {sys.argv[3]} → OFF" if ok else f"❌ {sys.argv[3]} 不存在")
        elif sub == "toggle" and len(sys.argv) > 3:
            ok = flags.toggle(sys.argv[3])
            state = flags.is_on(sys.argv[3])
            print(f"✅ {sys.argv[3]} → {'ON' if state else 'OFF'}" if ok else f"❌ {sys.argv[3]} 不存在")
        elif sub == "check" and len(sys.argv) > 3:
            state = flags.is_on(sys.argv[3])
            f = flags.get(sys.argv[3])
            status = "🟢有效" if state else "⭕无效"
            print(f"{status} {sys.argv[3]}: enabled={f['enabled'] if f else '?'}")
        elif sub == "stats":
            s = flags.stats()
            print(f"📊 Flag统计: {s['total']}总, {s['enabled']}启用, {s['disabled']}禁用")
            print(f"  分类: {', '.join(s['categories'])}")
            print(f"  实际有效: {s['effective']}/{s['enabled']}")
        else:
            print("❌ 用法: flag help")

    elif cmd == "route":
        """自动路由: route send/stats"""
        if not _HAS_ROUTING:
            print("❌ hermes_routing 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help":
            print("用法:")
            print("  route send <文本>           # 自动路由任务")
            print("  route to <伙伴> <任务>      # 手动指定伙伴")
            print("  route add <关键词> <伙伴...> # 添加自定义路由")
            print("  route history               # 路由历史")
            print("  route stats                 # 路由统计")
        elif sub == "send" and len(sys.argv) > 3:
            text = " ".join(sys.argv[3:])
            r = router.route(text)
            print(f"🧭 {r.intent} (置信度 {r.confidence:.1f})")
            print(f"  目标: {', '.join(r.targets)}")
            if r.matched_keywords:
                print(f"  匹配: {', '.join(r.matched_keywords)}")
        elif sub == "to" and len(sys.argv) > 4:
            result = router.to(sys.argv[3], " ".join(sys.argv[4:]))
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                print(f"✅ 已分配至 {sys.argv[3]}")
        elif sub == "add" and len(sys.argv) > 4:
            router.add_route(sys.argv[3], sys.argv[4:])
            print(f"✅ 自定义路由: '{sys.argv[3]}' → {', '.join(sys.argv[4:])}")
        elif sub == "history":
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            for h in router.history(limit):
                print(f"  [{h['intent']:8s}] {', '.join(h['targets']):20s} ({h['confidence']:.1f}) {h['text'][:40]}")
        elif sub == "stats":
            s = router.stats()
            print(f"📊 路由统计: {s['total_routes']}次路由, {s['custom_routes']}条自定义")
            print(f"  伙伴: {', '.join(s['partners'])}")
            print(f"  复合意图: {s['composite_intents']}个")
        else:
            print("❌ 用法: route help")

    elif cmd == "compact":
        """记忆压缩: compact analyze/run/stats"""
        if not _HAS_COMPACT:
            print("❌ hermes_compact 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help":
            print("用法:")
            print("  compact analyze [伙伴]      # 分析记忆状态")
            print("  compact run [伙伴]           # 执行压缩 (默认dry-run)")
            print("  compact run --apply [伙伴]   # 实际压缩 (会备份)")
            print("  compact stats                # 全部伙伴概况")
        elif sub == "analyze":
            partner = sys.argv[3] if len(sys.argv) > 3 else "tomato"
            r = compactor.analyze(partner)
            if "error" in r:
                print(f"❌ {r['error']}")
            else:
                print(f"📋 {partner} 记忆分析:")
                print(f"  MEMORY.md: {r['mem_file']['size_chars']:,} chars, {r['mem_file']['sections']} sections")
                print(f"  Daily记忆: {r['daily_memory']['files']} files, {r['daily_memory']['total_chars']:,} chars")
                print(f"  重复: {r['duplicates_found']} 对")
                print(f"  总计: {r['total_size']:,} chars")
        elif sub == "run":
            apply = "--apply" in sys.argv
            partner = sys.argv[-1] if sys.argv[-1] not in ("run", "--apply") else "tomato"
            if partner == "tomato" and len(sys.argv) > 3:
                if sys.argv[3] != "--apply":
                    partner = sys.argv[3]
            r = compactor.compact(partner, dry_run=not apply)
            if "error" in r:
                print(f"❌ {r['error']}")
            else:
                mode = "✅ 实际压缩" if not r['dry_run'] else "📋 (dry-run)"
                print(f"{mode} {partner}: {r['original_chars']:,}→{r['new_chars']:,} chars")
                print(f"  回收: {r['removed_chars']:,} chars, {r['removed_lines']} 行")
                print(f"  去重: {r['duplicates_collapsed']} 行")
        elif sub == "stats":
            s = compactor.stats()
            print(f"📊 记忆概况: {s['total_chars']:,} chars（7伙伴）")
            for p, d in s['partners'].items():
                mem = d.get('mem_size', 0) or 0
                print(f"  {p:15s} {mem:>6,} chars, {d['daily_files']} daily")
        else:
            print("❌ 用法: compact help")

    elif cmd == "watch":
        """实时监控: watch events/summary/check"""
        if not _HAS_WATCH:
            print("❌ hermes_watch 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "summary"
        if sub == "help":
            print("用法:")
            print("  watch events [limit] [category]  # 查看事件")
            print("  watch summary [minutes]           # 摘要")
            print("  watch last-error                  # 最近一次错误")
            print("  watch last-hour                   # 最近1小时事件")
            print("  watch stats                       # 统计")
        elif sub == "events":
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            cat = sys.argv[4] if len(sys.argv) > 4 else ""
            for e in watcher.events(limit=limit, category=cat):
                print(f"  {e['severity'][0]} [{e['timestamp'][:19]}] {e['name']:25s} {e['message'][:60]}")
        elif sub == "summary":
            minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 60
            s = watcher.summary(since_minutes=minutes)
            print(f"📊 {minutes}分钟摘要: {s['total_events']}事件")
            print(f"  按级别: {dict(s['by_severity'])}")
            for cat, cnt in s.get('by_category', {}).items():
                print(f"  {cat}: {cnt}")
            if s.get('errors'):
                print(f"  错误列表:")
                for e in s['errors'][-5:]:
                    print(f"    ❌ {e['name']}: {e['message']}")
        elif sub == "last-error":
            e = watcher.last_error()
            print(f"❌ {e['name']}: {e['message']}" if e else "✅ 无错误")
        elif sub == "last-hour":
            for e in watcher.last_hour():
                print(f"  {e['severity'][0]} [{e['timestamp'][:19]}] {e['name']} {e['message'][:60]}")
        elif sub == "stats":
            s = watcher.stats()
            print(f"📊 监控统计: {s['total_events']}条事件")
            print(f"  分类: {', '.join(s['categories'])}")
        else:
            print("❌ 用法: watch help")

    elif cmd == "coding":
        """编程增强: coding run/review/workspace"""
        if not _HAS_CODING:
            print("❌ hermes_coding 未加载")
            return
        sub = sys.argv[2] if len(sys.argv) > 2 else "help"
        if sub == "help":
            print("用法:")
            print("  coding run <命令>            # 自愈式执行")
            print("  coding review <文件>         # 代码审查")
            print("  coding workspace             # 工作区状态")
            print("  coding refresh               # 刷新工作区")
            print("  coding history               # 执行历史")
            print("  coding stats                 # 执行统计")
        elif sub == "run":
            cmd = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            if not cmd:
                print("❌ 请输入命令")
                return
            print(f"🔄 执行: {cmd}")
            r = coding.run_script(cmd)
            if r["success"]:
                print(f"✅ 成功 (第{r['attempts']}次)")
                if r.get("stdout"):
                    print(f"输出:\n{r['stdout'][:500]}")
            else:
                print(f"❌ {r['attempts']}次尝试均失败")
                if r.get("diagnoses"):
                    for d in r["diagnoses"]:
                        print(f"  🔧 {d.get('fix_desc','')}")
                if r.get("stderr"):
                    print(f"错误:\n{r['stderr'][:500]}")
        elif sub == "review":
            path = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            if not path:
                # 默认审查当前目录主文件
                path = "hermes_engine.py"
            r = coding.review_file(path)
            if "error" in r:
                print(f"❌ {r['error']}")
            else:
                s = r["stats"]
                print(f"📋 审查: {os.path.basename(path)}")
                print(f"  {s['total_lines']}行, {s['functions']}函数, {s['classes']}类")
                print(f"  代码{s['code_lines']}行 / 注释{s['comment_lines']}行")
                if r["issues"]:
                    print(f"\n⚠️ {r['issue_count']}个问题, 风险{r['risk_level']}")
                    for sev in ("CRITICAL", "HIGH", "MEDIUM"):
                        items = [i for i in r["issues"] if i["severity"] == sev]
                        if items:
                            prefix = "🔥" if sev == "CRITICAL" else "⚠️" if sev == "HIGH" else "⚡"
                            print(f"\n  {prefix} {sev} ({len(items)}):")
                            for i in items[:5]:
                                print(f"    L{i['line']} {i['code'][:60]}")
                            if len(items) > 5:
                                print(f"    ... 还有{len(items)-5}条")
                else:
                    print("\n✅ 无问题")
        elif sub == "workspace":
            ws = coding.workspace_status()
            s = ws["scripts"]
            print(f"📂 工作区状态:")
            print(f"  {s['total']}脚本 ({s['python']}py, {s['shell']}sh)")
            print(f"  {s['total_lines']:,} 行代码")
            print(f"  Agents: {', '.join(ws['agents']['names'])}")
            if s.get('largest'):
                print(f"  最大文件: {s['largest']['name']} ({s['largest']['lines']}行)")
        elif sub == "refresh":
            ws = coding.workspace_refresh()
            print(f"✅ 工作区已刷新 ({ws['timestamp'][:19]})")
        elif sub == "history":
            limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            for h in coding.exec_history(limit):
                status = "✅" if h.get("success") else "❌"
                print(f"  {status} {h.get('command','')} ({h.get('attempts',0)}次)")
        elif sub == "stats":
            s = coding.exec_stats()
            print(f"📊 执行统计: {s['total_runs']}次, {s['successes']}成功/{s['failures']}失败")
            print(f"  成功率: {s['success_rate']}%")
        else:
            print("❌ 用法: coding help")

    else:
        print(f"❌ 未知命令: {cmd}")
        print_help()

if __name__ == "__main__":
    main()
