#!/usr/bin/env python3
"""
skill_defender.py — Skill Runtime Defender
扫描已安装 Skills 的恶意模式、供应链攻击检测、权限越界

用法:
    python3 skill_defender.py scan         # 全量扫描
    python3 skill_defender.py check <name> # 检查指定Skill
    python3 skill_defender.py watch        # 持续监控(one-shot)
    python3 skill_defender.py report       # JSON报告
"""

import ast
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("skill_defender")

SKILLS_DIR = os.path.expanduser("~/.openclaw/skills")
OPENCLAW_SKILLS_DIR = Path("/opt/homebrew/Cellar/node@22/22.22.2_2/lib/node_modules/openclaw/skills")


# ─── 红牌规则 ───

RED_FLAGS = [
    # CRITICAL — 直接危险
    {"id": "RF-001", "pattern": r"\beval\s*\(", "severity": "CRITICAL",
     "title": "eval() 调用", "desc": "任意代码执行风险", "fix": "使用 ast.literal_eval 或无 eval 的方案"},
    {"id": "RF-002", "pattern": r"\bexec\s*\(", "severity": "CRITICAL",
     "title": "exec() 调用", "desc": "任意代码执行风险", "fix": "移除 exec 调用"},
    {"id": "RF-003", "pattern": r"os\.system\s*\(", "severity": "CRITICAL",
     "title": "os.system() 系统命令", "desc": "系统命令注入风险", "fix": "改用 subprocess.run(['cmd', ...])"},
    {"id": "RF-004", "pattern": r"subprocess\.(?:call|Popen|run)\s*\([^)]*shell\s*=\s*True", "severity": "CRITICAL",
     "title": "subprocess(shell=True)", "desc": "Shell 命令注入风险", "fix": "使用列表参数: subprocess.run(['ls', '-la'])"},
    {"id": "RF-005", "pattern": r"rm\s+-rf\s+[/*]", "severity": "CRITICAL",
     "title": "危险 rm -rf", "desc": "破坏性文件删除", "fix": "禁止通配删除，指定具体路径"},
    {"id": "RF-006", "pattern": r"__import__\s*\(", "severity": "HIGH",
     "title": "__import__() 动态导入", "desc": "动态导入可能加载恶意模块", "fix": "静态 import 替代"},
    {"id": "RF-007", "pattern": r"compile\s*\([^)]*['\"]", "severity": "HIGH",
     "title": "compile() 动态编译", "desc": "字符串编译为代码对象", "fix": "避免从用户输入编译代码"},
    {"id": "RF-008", "pattern": r"pty\.spawn", "severity": "HIGH",
     "title": "pty.spawn PTY 提权", "desc": "PTY 生成可能存在提权风险", "fix": "使用 subprocess.run 替代"},

    # HIGH — 严重风险
    {"id": "RF-009", "pattern": r"curl\s+(?:-s|-k)?\s*(?:\d{1,3}\.){3}\d{1,3}", "severity": "HIGH",
     "title": "curl 连接 IP 地址", "desc": "直接连接 IP 地址的可疑网络请求", "fix": "使用域名并验证 SSL 证书"},
    {"id": "RF-010", "pattern": r"wget\s+(?:-q)?\s*(?:\d{1,3}\.){3}\d{1,3}", "severity": "HIGH",
     "title": "wget 连接 IP 地址", "desc": "直接连接 IP 地址的下载请求", "fix": "使用域名并验证 SSL"},
    {"id": "RF-011", "pattern": r"base64\.(?:b64decode|decode)\s*\([^)]*input|requests?|user|data", "severity": "HIGH",
     "title": "base64 decode 外部输入", "desc": "对输入进行 base64 解码可能隐藏恶意负载", "fix": "避免对用户输入做 base64 解码"},
    {"id": "RF-012", "pattern": r"os\.environ(?:\.get|\[)?\s*['\"]?(?:AWS|GCP|AZURE|OPENAI|ANTHROPIC|VOLC)", "severity": "HIGH",
     "title": "读取云服务凭证环境变量", "desc": "读取 AI/云服务 API Key", "fix": "限制环境变量读取范围"},
    {"id": "RF-013", "pattern": r"(?:sudo|su)\s", "severity": "HIGH",
     "title": "提权操作 (sudo/su)", "desc": "请求超级用户权限", "fix": "避免使用 sudo，采用最小权限原则"},

    # MEDIUM — 需要注意
    {"id": "RF-014", "pattern": r"requests\.(?:post|put|delete|patch)\s*\(", "severity": "MEDIUM",
     "title": "HTTP 数据外发请求", "desc": "向外发送数据可能涉及数据泄漏", "fix": "审查目标 URL 是否受信任"},
    {"id": "RF-015", "pattern": r"urllib\.(?:request|urlopen|Request)", "severity": "MEDIUM",
     "title": "urllib 网络请求", "desc": "通过网络请求发送/获取数据", "fix": "限制网络请求到受信任端点"},
    {"id": "RF-016", "pattern": r"socket\.(?:connect|send|sendall)", "severity": "MEDIUM",
     "title": "socket 自定义连接", "desc": "自定义网络连接可能绕过 HTTP 监控", "fix": "使用 requests/httpx 等标准库"},
    {"id": "RF-017", "pattern": r"chmod\s+777", "severity": "MEDIUM",
     "title": "权限 777", "desc": "文件/目录设为所有人可读写执行", "fix": "使用最小必要权限 (如 644, 755)"},
    {"id": "RF-018", "pattern": r"open\(['\"](/dev/|/proc/|/sys/)", "severity": "MEDIUM",
     "title": "访问系统设备文件", "desc": "访问 /dev/*, /proc/*, /sys/* 设备文件", "fix": "非必要不直接访问设备文件"},

    # LOW — 建议
    {"id": "RF-019", "pattern": r"password|secret|credential|token|api_key", "severity": "LOW",
     "title": "涉及凭证关键词", "desc": "脚本中包含凭证相关关键词，需确认用途", "fix": "使用环境变量或密钥管理"},
    {"id": "RF-020", "pattern": r"tempfile\.(?:mkstemp|mkdtemp|TemporaryFile)", "severity": "LOW",
     "title": "临时文件操作", "desc": "创建临时文件需确保清理", "fix": "使用 with tempfile.TemporaryDirectory() 自动清理"},
    {"id": "RF-021", "pattern": r"crontab|launchctl|systemctl\s+enable", "severity": "MEDIUM",
     "title": "持久化机制", "desc": "设置定时任务或系统服务开机自启", "fix": "审查持久化需求的必要性"},
    {"id": "RF-022", "pattern": r"requests?\.get\(['\"](?:http://|ftp://)", "severity": "LOW",
     "title": "非 HTTPS 网络请求", "desc": "使用未加密的 HTTP/FTP 请求", "fix": "改用 HTTPS"},
]


# ─── 数据模型 ───

@dataclass
class Finding:
    rule_id: str
    severity: str
    title: str
    desc: str
    location: str
    code_snippet: str
    fix: str


@dataclass
class SkillReport:
    name: str
    path: str
    files: int
    lines: int
    findings: List[dict] = field(default_factory=list)
    score: int = 0
    risk_level: str = "LOW"
    permissions: dict = field(default_factory=dict)

    @property
    def has_critical(self) -> bool:
        return any(f["severity"] == "CRITICAL" for f in self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f["severity"] == "CRITICAL")

    def calc_score(self):
        weights = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 5, "LOW": 2}
        raw = sum(weights.get(f["severity"], 0) for f in self.findings)
        self.score = min(raw, 100)
        if self.score >= 60:
            self.risk_level = "CRITICAL"
        elif self.score >= 30:
            self.risk_level = "HIGH"
        elif self.score >= 10:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "LOW"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "files": self.files,
            "lines": self.lines,
            "findings": self.findings,
            "score": self.score,
            "risk_level": self.risk_level,
            "permissions": self.permissions,
        }


# ─── 扫描器 ───

class SkillDefender:
    """Skill 安全扫描器"""

    def scan_all(self) -> List[SkillReport]:
        """全量扫描所有安装的 Skills"""
        logger.info("🛡️ Skill Defender — 全量安全扫描\n")
        logger.info(f"📁 扫描路径: {SKILLS_DIR}\n")

        if not os.path.isdir(SKILLS_DIR):
            logger.error(f"Skills 目录不存在: {SKILLS_DIR}")
            return []

        reports = []
        for skill_name in sorted(os.listdir(SKILLS_DIR)):
            skill_path = os.path.join(SKILLS_DIR, skill_name)
            if not os.path.isdir(skill_path):
                continue
            report = self._scan_skill(skill_name, skill_path)
            reports.append(report)

        self._print_summary(reports)
        return reports

    def check_skill(self, skill_name: str) -> Optional[SkillReport]:
        """检查指定 Skill"""
        skill_path = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_path):
            logger.error(f"Skill '{skill_name}' 不存在")
            return None
        report = self._scan_skill(skill_name, skill_path)
        self._print_single(report)
        return report

    def _scan_skill(self, name: str, path: str) -> SkillReport:
        """扫描单个 Skill"""
        logger.info(f"  🔍 {name}...")

        # 收集所有文件
        files = []
        for root, dirs, fnames in os.walk(path):
            # 跳过 __pycache__
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
            for fn in fnames:
                fpath = os.path.join(root, fn)
                ext = os.path.splitext(fn)[1].lower()
                if ext in (".py", ".sh", ".md", ".yaml", ".yml", ".json", ".js", ".ts"):
                    if os.path.exists(fpath):
                        files.append({"name": fn, "path": fpath, "ext": ext})

        total_lines = 0
        findings_list = []

        for f in files:
            try:
                with open(f["path"], "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                lines = content.split("\n")
                total_lines += len(lines)

                for flag in RED_FLAGS:
                    for i, line in enumerate(lines, 1):
                        if re.search(flag["pattern"], line):
                            snippet = line.strip()[:100]
                            findings_list.append(Finding(
                                rule_id=flag["id"],
                                severity=flag["severity"],
                                title=flag["title"],
                                desc=flag["desc"],
                                location=f"{f['name']}:{i}",
                                code_snippet=snippet,
                                fix=flag["fix"],
                            ))

            except Exception as e:
                logger.warning(f"    跳过 {f['name']}: {e}")

        # 权限分析
        perms = self._analyze_permissions(files)

        report = SkillReport(
            name=name,
            path=path,
            files=len(files),
            lines=total_lines,
            findings=[asdict(f) for f in findings_list],
            permissions=perms,
        )
        report.calc_score()

        # 输出摘要
        if report.findings:
            by_sev = {}
            for f in report.findings:
                by_sev.setdefault(f["severity"], 0)
                by_sev[f["severity"]] += 1
            sev_str = ", ".join(f"{k}:{v}" for k, v in sorted(by_sev.items()))
            logger.info(f"    ⚠️  发现 {len(report.findings)} 个问题 ({sev_str}) 评分: {report.score}/100 [{report.risk_level}]")
        else:
            logger.info(f"    ✅ 未发现问题 评分: 0/100 [SAFE]")

        return report

    def _analyze_permissions(self, files: List[dict]) -> dict:
        """分析 Skill 需要的权限"""
        reads = set()
        writes = set()
        networks = set()
        commands = set()

        for f in files:
            try:
                with open(f["path"], "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
            except Exception:
                continue

            # 文件读操作
            read_patterns = [
                r"open\(['\"](~?/[\w/.]+)['\"]",
                r"Path\(['\"](~?/[\w/.]+)['\"]",
                r"os\.path\.exists\(['\"](~?/[\w/.]+)['\"]",
            ]
            for pat in read_patterns:
                for m in re.finditer(pat, content):
                    path = m.group(1)
                    if "ssh" in path: reads.add("~/.ssh")
                    elif "aws" in path: reads.add("~/.aws")
                    elif "config" in path: reads.add("~/.config")
                    elif "openclaw" in path: reads.add("~/.openclaw")
                    else: reads.add(path[:50])

            # 网络操作
            net_patterns = [
                r"requests\.(?:get|post|put|delete)\s*\(['\"](https?://[^'\"]+)",
                r"urlopen\(['\"](https?://[^'\"]+)",
                r"curl\s+['\"]?(https?://[^'\"]+)",
            ]
            for pat in net_patterns:
                for m in re.finditer(pat, content):
                    networks.add(m.group(1)[:60])

            # 系统命令
            cmd_patterns = [
                r"subprocess\.run\(['\"]([^'\"]+)",
                r"os\.system\(['\"]([^'\"]+)",
            ]
            for pat in cmd_patterns:
                for m in re.finditer(pat, content):
                    commands.add(m.group(1)[:60])

        return {
            "reads": sorted(reads),
            "writes": sorted(writes),
            "networks": sorted(networks),
            "commands": sorted(commands),
        }

    def _print_summary(self, reports: List[SkillReport]):
        """打印汇总"""
        print(f"\n{'='*56}")
        print(f"  Skill Defender — 扫描汇总")
        print(f"{'='*56}")
        print(f"  扫描 Skills: {len(reports)}")

        critical = [r for r in reports if r.has_critical]
        high = [r for r in reports if r.risk_level == "HIGH"]
        safe = [r for r in reports if r.risk_level == "LOW"]

        if critical:
            print(f"\n  🔴 CRITICAL Skills ({len(critical)}):")
            for r in critical:
                print(f"    • {r.name}: {r.critical_count} 个关键问题")

        if high:
            print(f"\n  🟠 HIGH Risk Skills ({len(high)}):")
            for r in high:
                print(f"    • {r.name}: 评分 {r.score}/100")

        print(f"\n  🟢 SAFE Skills: {len(safe)}/{len(reports)}")
        print(f"{'='*56}\n")

        avg_score = sum(r.score for r in reports) / len(reports) if reports else 0
        print(f"  整体安全评分: {avg_score:.0f}/100")
        print(f"  总发现问题: {sum(len(r.findings) for r in reports)}")
        print(f"  总代码行数: {sum(r.lines for r in reports)}\n")

    def _print_single(self, report: SkillReport):
        """打印单个 Skill 的详细报告"""
        print(f"\n{'='*56}")
        print(f"  🛡️  {report.name}")
        print(f"{'='*56}")
        print(f"  文件数: {report.files}")
        print(f"  代码行: {report.lines}")
        print(f"  风险评分: {report.score}/100 [{report.risk_level}]")
        print(f"  发现问题: {len(report.findings)}")
        if report.findings:
            print()
            for f in report.findings:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(f["severity"], "⚪")
                print(f"  {icon} [{f['severity']:>8}] {f['title']}")
                print(f"    📍 {f['location']}")
                print(f"    📝 {f['code_snippet']}")
                print(f"    💡 {f['fix']}")
                print()
        print(f"{'='*56}\n")

    def generate_fix_plan(self) -> dict:
        """生成修复方案"""
        reports = self.scan_all()
        fix_plan = {
            "summary": "Skill Defender — 自动修复方案",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "critical_items": [],
            "high_items": [],
            "commands": [],
        }

        for r in reports:
            if r.has_critical:
                for f in r.findings:
                    if f["severity"] == "CRITICAL":
                        fix_plan["critical_items"].append({
                            "skill": r.name,
                            "finding": f["title"],
                            "location": f["location"],
                            "fix": f["fix"],
                        })
            elif r.risk_level == "HIGH":
                for f in r.findings:
                    if f["severity"] == "HIGH":
                        fix_plan["high_items"].append({
                            "skill": r.name,
                            "finding": f["title"],
                            "location": f["location"],
                        })

        fix_plan["commands"].append("# 1. 查看需要修复的 Skills")
        fix_plan["commands"].append("openclaw run skill-defender scan")
        fix_plan["commands"].append("")
        fix_plan["commands"].append("# 2. 逐一检查高风险的 Skill")
        fix_plan["commands"].append("openclaw run skill-defender check <skill-name>")
        fix_plan["commands"].append("")
        fix_plan["commands"].append("# 3. 对包含 eval/exec/os.system 的 Skill 优先处理")
        fix_plan["commands"].append("grep -rnE 'eval|exec|os\\.system' ~/.openclaw/skills/ --include='*.py'")

        return fix_plan

    def get_watch_rules(self) -> dict:
        """生成运行时监控规则（用于 Hermes watch 集成）"""
        return {
            "skill_watch_rules": [
                {
                    "name": "skill_network_exfil",
                    "pattern": "Skill 发起外部 HTTP 请求",
                    "severity": "high",
                    "action": "记录并告警",
                },
                {
                    "name": "skill_credential_access",
                    "pattern": "Skill 读取 ~/.ssh, ~/.aws, 凭证文件",
                    "severity": "critical",
                    "action": "立即阻止并告警",
                },
                {
                    "name": "skill_shell_exec",
                    "pattern": "Skill 执行系统命令",
                    "severity": "high",
                    "action": "记录命令内容并告警",
                },
                {
                    "name": "skill_file_modify",
                    "pattern": "Skill 修改用户文件",
                    "severity": "medium",
                    "action": "记录修改的路径",
                },
            ]
        }


# ─── CLI ───

def main():
    defender = SkillDefender()

    if len(sys.argv) < 2:
        print("用法: python3 skill_defender.py <command>")
        print("命令: scan | check <name> | fix | watch | report")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "scan":
        defender.scan_all()

    elif cmd == "check":
        if len(sys.argv) < 3:
            print("用法: skill_defender.py check <skill-name>")
            sys.exit(1)
        defender.check_skill(sys.argv[2])

    elif cmd == "fix":
        plan = defender.generate_fix_plan()
        print(f"\n{'='*56}")
        print(f"  🔧 Skill Defender — 修复方案")
        print(f"{'='*56}")
        if plan["critical_items"]:
            print(f"\n  🔴 关键问题 ({len(plan['critical_items'])}):")
            for item in plan["critical_items"]:
                print(f"    • [{item['skill']}] {item['finding']} @ {item['location']}")
                print(f"      💡 {item['fix']}")
        if plan["high_items"]:
            print(f"\n  🟠 高危问题 ({len(plan['high_items'])}):")
            for item in plan["high_items"]:
                print(f"    • [{item['skill']}] {item['finding']} @ {item['location']}")
        print(f"\n  📋 建议执行:")
        for cmd in plan["commands"]:
            print(f"    {cmd}")
        print(f"{'='*56}\n")

    elif cmd == "watch":
        rules = defender.get_watch_rules()
        print(json.dumps(rules, indent=2, ensure_ascii=False))

    elif cmd == "report":
        reports = defender.scan_all()
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_skills": len(reports),
            "skills": [r.to_dict() for r in reports],
            "summary": {
                "critical": sum(1 for r in reports if r.has_critical),
                "high": sum(1 for r in reports if r.risk_level == "HIGH"),
                "medium": sum(1 for r in reports if r.risk_level == "MEDIUM"),
                "safe": sum(1 for r in reports if r.risk_level == "LOW"),
                "total_findings": sum(len(r.findings) for r in reports),
                "avg_score": round(sum(r.score for r in reports) / len(reports), 1) if reports else 0,
            },
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
