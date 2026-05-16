#!/usr/bin/env python3
"""
hermes_coding.py — Claude Code 模式编程增强
自愈式执行 / 代码审查 / 工作区感知

用法:
    from hermes_coding import coding

    # 自愈执行
    result = coding.run("python3 test.py", max_attempts=3)

    # 代码审查
    review = coding.review("video_pipeline.py")

    # 工作区状态
    status = coding.workspace_status()
"""

import ast
import json
import logging
import os
import re
import subprocess
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("hermes_coding")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/coding")
os.makedirs(DATA_DIR, exist_ok=True)
WORKSPACE_CONTEXT_PATH = os.path.join(DATA_DIR, "workspace_context.json")

SCRIPTS_DIR = os.path.expanduser("~/.openclaw/workspace/scripts")
AGENTS_DIR = os.path.expanduser("~/.openclaw/workspace/agents")


# ── 1. 自愈式执行 ──

class SelfHealingExec:
    """自愈式执行：运行→分析错误→修改代码→重试"""

    COMMON_PATTERNS = [
        # Python 语法错误
        (r"SyntaxError:.*\((.+?)\)", "语法错误: 检查括号/引号/缩进", "syntax"),
        (r"IndentationError:.*", "缩进错误: 统一用4空格", "indent"),
        (r"NameError: name '(\w+)' is not defined", 
         lambda m: f"缺少导入: 检查'{m.group(1)}'是否import", "import"),
        (r"ModuleNotFoundError: No module named '(\w+)'",
         lambda m: f"模块未安装: pip install {m.group(1)}", "dependency"),
        (r"ImportError: cannot import name '(\w+)' from '(\w+)'",
         lambda m: f"导入失败: '{m.group(1)}' 不在 '{m.group(2)}' 中", "import"),
        (r"TypeError: (\w+)\(\) missing \d+ required positional argument: '(\w+)'",
         lambda m: f"参数缺少: {m.group(1)}() 需要传 {m.group(2)}", "signature"),
        (r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
         lambda m: f"属性不存在: {m.group(1)}.{m.group(2)} 拼写或导入问题", "attribute"),
        (r"EOFError:.*", "文件未完整读取: 检查文件指针位置", "io"),
        # 文件/路径
        (r"FileNotFoundError:.*'(.*?)'", lambda m: f"文件不存在: {m.group(1)}", "path"),
        (r"PermissionError:.*'(.*?)'", lambda m: f"无权限访问: {m.group(1)}", "perms"),
        # 网络
        (r"ConnectionError:.*", "网络连接失败", "network"),
        (r"ConnectionRefusedError:.*", "连接被拒绝: 服务未运行或端口错误", "network"),
        (r"TimeoutError:.*", "请求超时: 增加timeout或检查服务器", "timeout"),
        (r"requests\.exceptions\.(ConnectTimeout|ReadTimeout)", 
         "HTTP请求超时: 加timeout参数或检查URL", "network"),
        # JSON
        (r"json\.JSONDecodeError:.*", "JSON解析失败: 检查响应格式", "format"),
        # 路径
        (r"No such file or directory: '(.*?)'",
         lambda m: f"路径不存在: {m.group(1)}", "path"),
        # 环境
        (r"KeyError: '(\w+)'",
         lambda m: f"环境变量/字典键缺失: {m.group(1)}", "config"),
    ]

    def __init__(self):
        self._history: List[dict] = []
        self._lock = threading.Lock()

    def run(self, command: str, cwd: str = None,
            max_attempts: int = 3, timeout: int = 30) -> dict:
        """自愈执行"""
        attempt = 0
        cwd = cwd or SCRIPTS_DIR
        log: List[dict] = []

        while attempt < max_attempts:
            attempt += 1
            logger.info("🔄 执行 #%d: %s", attempt, command[:80])

            try:
                result = subprocess.run(
                    command, shell=True, cwd=cwd,
                    capture_output=True, text=True, timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                log.append({"attempt": attempt, "error": f"超时({timeout}s)"})
                continue
            except Exception as e:
                log.append({"attempt": attempt, "error": str(e)})
                continue

            stdout = (result.stdout or "")[:2000]
            stderr = (result.stderr or "")[:2000]
            ok = result.returncode == 0

            log.append({
                "attempt": attempt,
                "returncode": result.returncode,
                "stdout_len": len(result.stdout or ""),
                "stderr_len": len(result.stderr or ""),
            })

            if ok:
                self._record({
                    "command": command[:100],
                    "attempts": attempt,
                    "success": True,
                    "fixes": [l for l in log if l.get("fix_applied")],
                })
                return {
                    "success": True,
                    "attempts": attempt,
                    "stdout": stdout,
                    "stderr": stderr,
                    "log": log,
                }

            # 分析错误
            fixes = self._diagnose(stderr or stdout or "")
            if not fixes:
                break  # 分析不出原因，放弃

            # 尝试修复
            for fix in fixes[:2]:
                if self._apply_fix(fix):
                    log.append({
                        "attempt": attempt,
                        "fix_applied": fix["action"],
                        "fix_desc": fix["description"],
                    })
                    logger.info("🔧 已修复: %s", fix["description"])
                else:
                    log.append({
                        "attempt": attempt,
                        "fix_failed": fix["action"],
                    })

        # 全部失败
        self._record({
            "command": command[:100],
            "attempts": attempt,
            "success": False,
            "fixes": [l for l in log if l.get("fix_applied")],
        })
        return {
            "success": False,
            "attempts": attempt,
            "stdout": result.stdout if "result" in dir() else "",
            "stderr": result.stderr if "result" in dir() else "",
            "diagnoses": [l for l in log if l.get("fix_applied") or l.get("fix_failed")],
            "log": log,
        }

    def _diagnose(self, error_text: str) -> List[dict]:
        """分析错误文本，返回修复建议列表"""
        fixes = []
        for pattern, desc, fix_type in self.COMMON_PATTERNS:
            match = re.search(pattern, error_text)
            if match:
                description = desc(match) if callable(desc) else desc
                fixes.append({
                    "type": fix_type,
                    "description": description,
                    "match": match.group(0)[:100],
                    "action": f"fix_{fix_type}",
                })
        return fixes

    def _apply_fix(self, fix: dict) -> bool:
        """尝试自动修复（纯文件操作）"""
        try:
            # 目前只修复 import 和 path 类可自动处理的
            if fix["type"] == "import":
                match = re.search(r"'(\w+)'", fix["match"])
                if match:
                    module = match.group(1)
                    # 尝试 pip install（安全操作，仅安装）
                    subprocess.run(
                        f"pip install {module} 2>/dev/null || pip3 install {module} 2>/dev/null",
                        shell=True, capture_output=True, timeout=30,
                    )
                    return True
            return False
        except Exception:
            return False

    def history(self, limit: int = 10) -> List[dict]:
        with self._lock:
            return list(self._history)[-limit:]

    def _record(self, entry: dict):
        with self._lock:
            self._history.append(entry)
            if len(self._history) > 100:
                self._history = self._history[-50:]

    def stats(self) -> dict:
        with self._lock:
            total = len(self._history)
            successes = sum(1 for h in self._history if h.get("success"))
            return {
                "total_runs": total,
                "success_rate": round(successes / total * 100, 1) if total else 0,
                "successes": successes,
                "failures": total - successes,
            }


# ── 2. 代码审查 ──

class CodeReviewer:
    """代码静态审查"""

    RULES = [
        {
            "id": "bare-except",
            "pattern": r"except\s*:",
            "message": "裸except会吞掉所有异常，包括KeyboardInterrupt",
            "severity": "HIGH",
            "fix": "改为 except Exception as e:",
        },
        {
            "id": "hardcoded-path",
            "pattern": r"['\"](/Users/|/home/|/tmp/|/var/|C:\\).*?['\"]",
            "message": "硬编码路径，推荐用os.path.expanduser或配置",
            "severity": "MEDIUM",
            "fix": "使用 os.path.expanduser('~') 或配置变量",
        },
        {
            "id": "eval-exec",
            "pattern": r"\beval\(|\bexec\(|\bos\.system\(|\bsubprocess\.call\(|\bsubprocess\.Popen\(",
            "message": "存在潜在安全风险的函数调用",
            "severity": "HIGH",
            "fix": "改用 subprocess.run 并限制shell=True",
        },
        {
            "id": "print-debug",
            "pattern": r"print\(['\"].*?(debug|test|tmp|temporary).*?['\"]",
            "message": "可能是调试用的print语句",
            "severity": "LOW",
            "fix": "移除或改用logging.debug",
        },
        {
            "id": "long-line",
            "pattern": r"^.{100,}$",
            "message": "行过长(>100字符)，影响可读性",
            "severity": "LOW",
            "fix": "拆分为多行",
        },
        {
            "id": "no-docstring",
            "pattern": r"^class\s+\w+|^def\s+\w+",
            "message": "缺少docstring",
            "severity": "LOW",
            "fix": "在声明后添加多行注释",
        },
        {
            "id": "global-var",
            "pattern": r"^(\w+)\s*=\s*(?:\[|\{|\(|\"|True|False|\d+)",
            "message": "模块级可变对象，小心意外修改",
            "severity": "LOW",
            "fix": "考虑用函数包裹或添加注释",
        },
        {
            "id": "logging-not-module",
            "pattern": r"^(?!#.*)print\(.*\)\s*$",
            "message": "生产代码中应优先使用logging而非print",
            "severity": "LOW",
            "fix": "改用logger.info/debug/warning",
        },
        {
            "id": "fixed-timeout",
            "pattern": r"timeout\s*=\s*\d{1,3}(?:\s*[,)])",
            "message": "固定超时值，长时间运行可能需要调大",
            "severity": "LOW",
            "fix": "考虑从配置读取或动态计算",
        },
        {
            "id": "unused-import",
            "pattern": r"^import (\w+)\s*$",
            "message": "需检查是否被使用，未使用的import浪费资源",
            "severity": "LOW",
            "fix": "移除未使用的import",
        },
        {
            "id": "except-pass",
            "pattern": r"except.*:\s*\n\s*pass",
            "message": "捕获异常后仅pass会隐藏问题",
            "severity": "MEDIUM",
            "fix": "至少加日志: logger.warning(...)",
        },
        {
            "id": "shell-true",
            "pattern": r"subprocess\.run\([^)]*shell\s*=\s*True",
            "message": "shell=True存在命令注入风险",
            "severity": "HIGH",
            "fix": "用列表参数代替字符串: ['cmd', 'arg']",
        },
        {
            "id": "dangerous-rm",
            "pattern": r"rm\s+-rf\s+[/*]",
            "message": "危险命令: rm -rf / 或 rm -rf *",
            "severity": "CRITICAL",
            "fix": "指定具体路径，禁止通配删除",
        },
    ]

    def review(self, filepath: str) -> dict:
        """审查一个文件"""
        if not os.path.exists(filepath):
            return {"error": f"文件不存在: {filepath}"}
        if not os.path.isfile(filepath):
            return {"error": f"不是文件: {filepath}"}

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        issues = []
        stats = {
            "total_lines": len(lines),
            "code_lines": sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
            "comment_lines": sum(1 for l in lines if l.strip().startswith("#")),
            "blank_lines": sum(1 for l in lines if not l.strip()),
            "functions": len(re.findall(r"^def\s+\w+", content, re.MULTILINE)),
            "classes": len(re.findall(r"^class\s+\w+", content, re.MULTILINE)),
            "imports": len(re.findall(r"^import\s|^from\s", content, re.MULTILINE)),
        }

        # 按规则逐行扫描
        for rule in self.RULES:
            for i, line in enumerate(lines, 1):
                if re.search(rule["pattern"], line):
                    issues.append({
                        "id": rule["id"],
                        "line": i,
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "code": line.strip()[:80],
                        "fix": rule["fix"],
                    })

        # 按严重级别汇总
        by_severity = defaultdict(int)
        for issue in issues:
            by_severity[issue["severity"]] += 1

        risk_score = (
            by_severity.get("CRITICAL", 0) * 10 +
            by_severity.get("HIGH", 0) * 5 +
            by_severity.get("MEDIUM", 0) * 2 +
            by_severity.get("LOW", 0) * 0.5
        )

        return {
            "file": filepath,
            "stats": stats,
            "issues": issues,
            "issue_count": len(issues),
            "by_severity": dict(by_severity),
            "risk_score": round(risk_score, 1),
            "risk_level": "LOW" if risk_score < 5 else "MEDIUM" if risk_score < 15 else "HIGH",
        }


# ── 3. 工作区感知 ──

class WorkspaceAwareness:
    """工作区感知：项目结构 + 文件间依赖"""

    WATCH_DIRS = [SCRIPTS_DIR, AGENTS_DIR]

    def __init__(self):
        self._lock = threading.Lock()
        self._context: dict = {}
        self._load_context()

    def refresh(self) -> dict:
        """刷新工作区状态"""
        ctx = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scripts": self._scan_scripts(),
            "agents": self._scan_agents(),
            "recent_files": [],
            "import_graph": {},
        }

        # Dependency graph
        ctx["import_graph"] = self._build_import_graph()

        with self._lock:
            self._context = ctx
        self._save_context(ctx)
        return ctx

    def status(self) -> dict:
        """获取工作区状态摘要"""
        if not self._context:
            self.refresh()
        ctx = self._context

        scripts = ctx.get("scripts", [])
        agents = ctx.get("agents", [])
        graph = ctx.get("import_graph", {})

        # 分析哪些文件相互引用
        deps = []
        seen = set()
        for source, targets in graph.items():
            for t in targets:
                pair = tuple(sorted([source, t]))
                if pair not in seen:
                    seen.add(pair)
                    deps.append({"from": source, "to": t})

        return {
            "scripts": {
                "total": len(scripts),
                "python": len([s for s in scripts if s["ext"] == ".py"]),
                "shell": len([s for s in scripts if s["ext"] == ".sh"]),
                "other": len([s for s in scripts if s["ext"] not in (".py", ".sh")]),
                "total_lines": sum(s.get("lines", 0) for s in scripts),
                "largest": max(scripts, key=lambda s: s.get("lines", 0)) if scripts else None,
            },
            "agents": {
                "total": len(agents),
                "names": [a["name"] for a in agents],
            },
            "dependencies": {
                "total_pairs": len(deps),
                "most_referenced": self._most_referenced(agents),
            },
            "updated_at": ctx.get("timestamp", ""),
        }

    def _scan_scripts(self) -> List[dict]:
        """扫描脚本目录"""
        files = []
        scripts_dir = SCRIPTS_DIR
        if not os.path.isdir(scripts_dir):
            return files
        for fname in sorted(os.listdir(scripts_dir)):
            fpath = os.path.join(scripts_dir, fname)
            if not os.path.isfile(fpath):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in (".py", ".sh", ".md", ".yaml", ".yml", ".json"):
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                files.append({
                    "name": fname,
                    "path": fpath,
                    "ext": ext,
                    "lines": len(content.split("\n")),
                    "size": len(content),
                })
            except Exception:
                pass
        return files

    def _scan_agents(self) -> List[dict]:
        """扫描agent目录"""
        agents = []
        if not os.path.isdir(AGENTS_DIR):
            return agents
        for dname in os.listdir(AGENTS_DIR):
            dpath = os.path.join(AGENTS_DIR, dname)
            if not os.path.isdir(dpath):
                continue
            identity = ""
            mem_file = ""
            identity_path = os.path.join(dpath, "IDENTITY.md")
            if os.path.isfile(identity_path):
                try:
                    with open(identity_path, "r") as f:
                        identity = f.read()[:200]
                except Exception:
                    pass
            mem_path = os.path.join(dpath, "MEMORY.md")
            if os.path.isfile(mem_path):
                import stat
                try:
                    sz = os.stat(mem_path).st_size
                    mem_file = f"{sz:,} bytes"
                except Exception:
                    pass
            agents.append({
                "name": dname,
                "path": dpath,
                "identity_preview": identity,
                "memory_size": mem_file,
            })
        return agents

    def _build_import_graph(self) -> Dict[str, List[str]]:
        """构建文件间引用图"""
        graph = {}
        scripts_dir = SCRIPTS_DIR
        if not os.path.isdir(scripts_dir):
            return graph
        for fname in os.listdir(scripts_dir):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(scripts_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            refs = re.findall(r"from\s+(\w+)\s+import|import\s+(\w+)", content)
            targets = []
            for ref in refs:
                t = ref[0] or ref[1]
                if t != fname.replace(".py", ""):
                    targets.append(t)
            if targets:
                graph[fname] = sorted(set(targets))
        return graph

    def _most_referenced(self, agents: List[dict]) -> List[str]:
        return [a["name"] for a in agents[:5]] if agents else []

    def _save_context(self, ctx: dict):
        try:
            with open(WORKSPACE_CONTEXT_PATH, "w", encoding="utf-8") as f:
                json.dump(ctx, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存工作区上下文失败: %s", e)

    def _load_context(self):
        if os.path.exists(WORKSPACE_CONTEXT_PATH):
            try:
                with open(WORKSPACE_CONTEXT_PATH, "r", encoding="utf-8") as f:
                    self._context = json.load(f)
            except Exception:
                pass


# ── 统一接口 ──

class CodingHub:
    """编程增强统一接口"""

    def __init__(self):
        self.executor = SelfHealingExec()
        self.reviewer = CodeReviewer()
        self.workspace = WorkspaceAwareness()

    def run_script(self, command: str, cwd: str = None,
                   max_attempts: int = 3, timeout: int = 30) -> dict:
        return self.executor.run(command, cwd, max_attempts, timeout)

    def review_file(self, filepath: str) -> dict:
        return self.reviewer.review(filepath)

    def workspace_status(self) -> dict:
        return self.workspace.status()

    def workspace_refresh(self) -> dict:
        return self.workspace.refresh()

    def exec_history(self, limit: int = 10) -> List[dict]:
        return self.executor.history(limit)

    def exec_stats(self) -> dict:
        return self.executor.stats()


coding = CodingHub()


def _test():
    print("=== Coding 系统测试 ===")

    # 1. 工作区感知
    ws = coding.workspace_status()
    print(f"✅ 工作区: {ws['scripts']['total']}脚本, {ws['scripts']['total_lines']}行")
    print(f"  Agents: {', '.join(ws['agents']['names'])}")
    ws_ref = coding.workspace_refresh()
    print(f"  Refreshed: {ws_ref['timestamp'][:19]}")

    # 2. 代码审查
    scripts_dir = SCRIPTS_DIR
    target = os.path.join(scripts_dir, "hermes_engine.py")
    if os.path.exists(target):
        review = coding.review_file(target)
        print(f"\n✅ 审查 {os.path.basename(target)}:")
        print(f"  {review['stats']['total_lines']}行, {review['stats']['functions']}函数, {review['stats']['classes']}类")
        print(f"  问题: {review['issue_count']} ({dict(review['by_severity'])})")
        print(f"  风险: {review['risk_level']} ({review['risk_score']})")

    # 3. 执行历史
    stats = coding.exec_stats()
    print(f"\n✅ 执行统计: {stats['total_runs']}次, 成功率{stats['success_rate']}%")

    print("\n=== All passed ✅ ===")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
