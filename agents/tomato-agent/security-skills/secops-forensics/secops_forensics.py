#!/usr/bin/env python3
"""
secops_forensics.py — 安全取证与事件分析
审计日志分析、IOC 检测、入侵时间线重构

用法:
    python3 secops_forensics.py analyze         # 完整取证分析
    python3 secops_forensics.py timeline        # 时间线重建
    python3 secops_forensics.py ioc-scan        # IOC 扫描
    python3 secops_forensics.py check-log <f>   # 检查日志文件
    python3 secops_forensics.py health-check    # 快速健康检查
    python3 secops_forensics.py report          # JSON 报告
"""

import json
import logging
import os
import platform
import re
import socket
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("secops_forensics")

OPENCLAW_DIR = os.path.expanduser("~/.openclaw")
LOG_SOURCES = {
    "openclaw_logs": os.path.join(OPENCLAW_DIR, "logs"),
    "cron_jobs": os.path.join(OPENCLAW_DIR, "cron"),
    "hermes": os.path.join(OPENCLAW_DIR, "workspace", "hermes"),
}


# ─── 数据模型 ───

@dataclass
class ForensicEvent:
    timestamp: str
    source: str
    event_type: str
    severity: str
    title: str
    description: str
    evidence: str
    recommendation: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ForensicReport:
    hostname: str
    platform: str
    generated_at: str = ""
    events: List[dict] = field(default_factory=list)
    timeline: List[dict] = field(default_factory=list)
    risk_score: int = 0
    risk_level: str = "SAFE"
    summary: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def add_event(self, event: ForensicEvent):
        self.events.append(event.to_dict())

    def add_timeline_item(self, timestamp: str, title: str, severity: str):
        self.timeline.append({
            "timestamp": timestamp,
            "title": title,
            "severity": severity,
        })

    def finalize(self):
        weights = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 7, "LOW": 2}
        raw = sum(weights.get(e["severity"], 0) for e in self.events)
        self.risk_score = min(raw, 100)
        if self.risk_score >= 50: self.risk_level = "CRITICAL"
        elif self.risk_score >= 25: self.risk_level = "HIGH"
        elif self.risk_score >= 10: self.risk_level = "MEDIUM"
        else: self.risk_level = "SAFE"
        self.summary = {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "events": len(self.events),
            "timeline_items": len(self.timeline),
        }

    def text_report(self) -> str:
        lines = [
            f"{'='*56}",
            f"  SecOps Forensics — 安全取证报告",
            f"{'='*56}",
            f"  主机: {self.hostname} ({self.platform})",
            f"  时间: {self.generated_at[:19]}",
            f"  风险评分: {self.risk_score}/100 [{self.risk_level}]",
            f"  发现事件: {len(self.events)}",
            f"  时间线项: {len(self.timeline)}",
        ]

        if self.timeline:
            lines.append(f"\n{'─'*56}")
            lines.append("  入侵时间线")
            lines.append(f"{'─'*56}")
            for item in sorted(self.timeline, key=lambda x: x["timestamp"]):
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(item["severity"], "⚪")
                lines.append(f"  {icon} [{item['timestamp'][:19]}] {item['title']}")

        if self.events:
            lines.append(f"\n{'─'*56}")
            lines.append("  事件详情")
            lines.append(f"{'─'*56}")
            for e in self.events[:20]:
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(e["severity"], "⚪")
                lines.append(f"\n  {icon} [{e['severity']:>8}] {e['title']}")
                lines.append(f"     {e['description']}")
                lines.append(f"     📍 {e['evidence']}")
                if e["recommendation"]:
                    lines.append(f"     💡 {e['recommendation']}")

        lines.append(f"\n{'='*56}")
        return "\n".join(lines)


# ─── 取证分析器 ───

class ForensicsAnalyzer:
    def __init__(self):
        self.report = ForensicReport(
            hostname=socket.gethostname(),
            platform=f"{platform.system()} {platform.release()}",
        )

    def analyze_all(self) -> ForensicReport:
        """完整安全取证分析"""
        logger.info("🔍 SecOps Forensics — 安全取证分析\n")
        self._audit_openclaw_config()
        self._check_cron_integrity()
        self._scan_processes()
        self._scan_network_connections()
        self._check_persistence()
        self._check_suid_changes()
        self._create_timeline()
        self.report.finalize()
        logger.info("\n" + self.report.text_report())
        return self.report

    def ioc_scan(self) -> dict:
        """IOC 检测"""
        logger.info("🕵️ SecOps Forensics — IOC 扫描\n")
        iocs = {
            "suspicious_processes": [],
            "unknown_ports": [],
            "suid_files": [],
            "new_executables": [],
            "persistence_mechanisms": [],
        }

        # 异常进程
        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["ps", "aux", "--sort=-%cpu"],
                    capture_output=True, text=True, timeout=10,
                )
                for line in result.stdout.strip().split("\n")[1:]:
                    parts = line.split()
                    if len(parts) < 11: continue
                    cpu = float(parts[2])
                    mem = float(parts[3])
                    proc_name = parts[10]
                    pid = parts[1]
                    # 高 CPU/内存 + 非典型后台进程名
                    if cpu > 80.0 and not any(k in proc_name.lower()
                        for k in ["kernel", "launchd", "wifi", "WindowServer", "mds", "mdworker"]):
                        iocs["suspicious_processes"].append({
                            "pid": pid, "name": proc_name, "cpu": cpu, "mem": mem
                        })
            # 查找 minerd/cryptonight 等挖矿进程
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.strip().split("\n"):
                if any(k in line.lower() for k in ["minerd", "cryptonight", "xmrig", "cpuminer"]):
                    iocs["suspicious_processes"].append({
                        "name": line[:80],
                        "detail": "疑似挖矿进程",
                    })
        except Exception:
            pass

        # 非常规监听端口
        try:
            result = subprocess.run(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                capture_output=True, text=True, timeout=10,
            )
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 9:
                    addr = parts[8]
                    proc = parts[0]
                    if ":" in addr:
                        port_str = addr.split(":")[-1]
                        try:
                            port = int(port_str)
                            if port not in (22, 80, 443, 8000, 3000, 8080, 8443, 5353, 12345):
                                iocs["unknown_ports"].append(f"{proc}:{addr}")
                        except ValueError:
                            pass
        except Exception:
            pass

        # SUID 文件检查
        try:
            result = subprocess.run(
                ["find", "/", "-perm", "-4000", "-type", "f", "-maxdepth", "5"],
                capture_output=True, text=True, timeout=10,
            )
            suid_list = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line and not any(line.startswith(p) for p in
                    ["/usr", "/bin", "/sbin", "/System", "/Library"]):
                    suid_list.append(line)
            if suid_list:
                for f in suid_list[:10]:
                    iocs["suid_files"].append(f)
        except Exception:
            pass

        # 输出结果
        for category, items in iocs.items():
            if items:
                logger.info(f"  ⚠️  {category}: {len(items)} 项")
                for item in items[:5]:
                    if isinstance(item, dict):
                        logger.info(f"     • {item.get('name', str(item))}")
                    else:
                        logger.info(f"     • {item}")
            else:
                logger.info(f"  ✅ {category}: 无异常")

        # 打分
        ioc_score = (
            len(iocs["suspicious_processes"]) * 15
            + len(iocs["unknown_ports"]) * 10
            + len(iocs["suid_files"]) * 5
        )
        iocs["risk_score"] = min(ioc_score, 100)
        iocs["scanned_at"] = datetime.now(timezone.utc).isoformat()

        return iocs

    def _audit_openclaw_config(self):
        """审计 OpenClaw 配置"""
        logger.info("📁 审计 OpenClaw 配置...")

        for name, path_str in LOG_SOURCES.items():
            path = Path(path_str)
            if path.exists():
                logger.info(f"  ✅ {name}: 存在")
            else:
                logger.info(f"  ℹ️  {name}: 不存在 (非必须)")

        # 检查 cron 配置是否被篡改
        cron_dir = Path(LOG_SOURCES["cron_jobs"])
        if cron_dir.exists():
            for f in cron_dir.iterdir():
                if f.suffix in (".json", ".yaml", ".yml"):
                    try:
                        with open(f, "r") as fh:
                            content = fh.read()
                        # 检测非预期的 cron 任务
                        suspicious_keywords = [
                            "rm", "shutdown", "reboot", "curl.*|bash",
                            "wget.*-O", "chmod.*777", "sudo.*-S"
                        ]
                        for kw in suspicious_keywords:
                            if re.search(kw, content):
                                self.report.add_event(ForensicEvent(
                                    timestamp=datetime.now(timezone.utc).isoformat(),
                                    source=f.name, event_type="cron_abuse",
                                    severity="HIGH",
                                    title="可疑 CRON 任务",
                                    description=f"发现可疑关键词 '{kw}'",
                                    evidence=f.name,
                                    recommendation="审核该 CRON 任务是否合理",
                                ))
                                self.report.add_timeline_item(
                                    datetime.now(timezone.utc).isoformat(),
                                    f"发现可疑 CRON 任务: {f.name}", "HIGH"
                                )
                    except Exception:
                        pass

    def _check_cron_integrity(self):
        """检查计划任务完整性"""
        logger.info("⏰ 检查计划任务完整性...")

        try:
            if platform.system() == "Darwin":
                # macOS: 检查 launchd 服务
                result = subprocess.run(
                    ["launchctl", "list"],
                    capture_output=True, text=True, timeout=10,
                )
                suspicious_launchd = []
                for line in result.stdout.strip().split("\n"):
                    if any(k in line.lower() for k in ["reverse", "shell", "backdoor"]):
                        suspicious_launchd.append(line)

                if suspicious_launchd:
                    for s in suspicious_launchd:
                        self.report.add_event(ForensicEvent(
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            source="launchctl", event_type="persistence",
                            severity="CRITICAL",
                            title="可疑 launchd 服务",
                            description=f"发现可疑名称的 launchd 服务",
                            evidence=s[:80],
                        ))

            # 检查用户 crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True, text=True, timeout=5,
            )
            if result.stdout.strip():
                content = result.stdout
                malicious_cron = []
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    if any(kw in line.lower() for kw in [
                        "curl", "wget", "bash -c", "rm -rf", "base64 -d"
                    ]):
                        malicious_cron.append(line)
                if malicious_cron:
                    self.report.add_event(ForensicEvent(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        source="crontab", event_type="persistence",
                        severity="CRITICAL", title="用户 crontab 含恶意命令",
                        description=f"发现 {len(malicious_cron)} 条可疑 crontab 条目",
                        evidence="\n".join(malicious_cron[:3]),
                        recommendation="立即清理可疑 crontab 条目",
                    ))
        except Exception:
            pass

    def _scan_processes(self):
        """扫描异常进程"""
        logger.info("🔄 扫描异常进程...")

        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=10,
            )

            # 检查已知恶意进程名
            malicious_names = ["minerd", "xmrig", "cpuminer", "cryptonight",
                              "backdoor", "shell_bot", "reverse_shell"]
            for line in result.stdout.strip().split("\n"):
                for mname in malicious_names:
                    if mname in line.lower():
                        self.report.add_event(ForensicEvent(
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            source="ps aux", event_type="malware_process",
                            severity="CRITICAL",
                            title=f"疑似恶意进程: {mname}",
                            description=f"发现已知恶意进程名称 '{mname}'",
                            evidence=line[:100],
                            recommendation=f"立即杀毒: kill -9 $(pgrep {mname})",
                        ))

            # 检查隐藏进程（大括号会被shell解释，跳过）
        except Exception:
            pass

    def _scan_network_connections(self):
        """扫描网络连接"""
        logger.info("🌐 扫描网络连接...")

        try:
            if platform.system() == "Darwin":
                result = subprocess.run(
                    ["lsof", "-nP", "-iTCP", "-sTCP:ESTABLISHED"],
                    capture_output=True, text=True, timeout=10,
                )
                suspicious_conns = []
                for line in result.stdout.strip().split("\n")[1:]:
                    parts = line.split()
                    if len(parts) >= 9:
                        foreign = parts[8]
                        proc = parts[0]
                        # 检测连接到已知恶意 IP 段
                        if any(fs in foreign for fs in ["185.", "45.", "5.", "94."]):
                            suspicious_conns.append(f"{proc}: {foreign}")
                        # 检测非常规端口出站连接
                        if ":" in foreign:
                            fhost, fport = foreign.rsplit(":", 1)
                            try:
                                port_num = int(fport)
                                if port_num in (4444, 5555, 6666, 8888, 9999, 31337, 6667):
                                    suspicious_conns.append(f"{proc}:{foreign}")
                            except ValueError:
                                pass

                if suspicious_conns:
                    for conn in suspicious_conns[:5]:
                        self.report.add_event(ForensicEvent(
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            source="lsof", event_type="suspicious_connection",
                            severity="HIGH",
                            title="可疑网络连接",
                            description=f"连接到可疑端口/IP",
                            evidence=conn,
                            recommendation="使用 netstat 或 tcpdump 进一步分析",
                        ))
        except Exception:
            pass

    def _check_persistence(self):
        """检查持久化机制"""
        logger.info("💾 检查持久化机制...")

        # macOS launch agents
        launch_agents = Path.home() / "Library" / "LaunchAgents"
        if launch_agents.exists():
            for f in launch_agents.iterdir():
                if f.suffix == ".plist":
                    try:
                        content = f.read_text(errors="ignore")
                        if any(k in content.lower() for k in ["bash", "python", "curl", "wget"]):
                            self.report.add_event(ForensicEvent(
                                timestamp=datetime.now(timezone.utc).isoformat(),
                                source=str(f), event_type="persistence",
                                severity="HIGH",
                                title="LaunchAgent 含代码执行",
                                description="用户 LaunchAgent 包含脚本执行",
                                evidence=f.name,
                                recommendation="审核该 LaunchAgent 的合理性",
                            ))
                    except Exception:
                        pass

    def _check_suid_changes(self):
        """检查 SUID 文件变更"""
        logger.info("🔐 检查 SUID 文件...")

        try:
            result = subprocess.run(
                ["find", "/", "-perm", "-4000", "-type", "f", "-maxdepth", "3"],
                capture_output=True, text=True, timeout=10,
            )
            unusual_suid = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                basename = os.path.basename(line)
                known_suid = ["sudo", "su", "passwd", "login", "newgrp",
                             "ping", "ping6", "traceroute", "traceroute6",
                             "at", "crontab", "ps", "ssh-agent"]
                if basename not in known_suid:
                    unusual_suid.append(line)

            if unusual_suid:
                for f in unusual_suid[:5]:
                    self.report.add_event(ForensicEvent(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        source="find", event_type="suid_abuse",
                        severity="MEDIUM",
                        title="非标准 SUID 文件",
                        description=f"发现非系统标准的 SUID 文件",
                        evidence=f,
                        recommendation="审计该文件是否为预期设置",
                    ))
        except Exception:
            pass

    def _create_timeline(self):
        """创建时间线"""
        # 已经通过 add_event 过程中添加了时间线项
        # 这里对已有时间线按时间排序
        self.report.timeline.sort(key=lambda x: x["timestamp"])

    def health_check(self) -> dict:
        """快速健康检查"""
        logger.info("🏥 SecOps Forensics — 快速健康检查\n")

        checks = {
            "host_info": {
                "hostname": socket.gethostname(),
                "platform": f"{platform.system()} {platform.release()}",
                "time": datetime.now(timezone.utc).isoformat(),
            },
            "checks": {},
            "status": "OK",
        }

        # 1. 磁盘空间
        try:
            result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True, text=True, timeout=5,
            )
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                used_percent = parts[4] if len(parts) >= 5 else "?"
                checks["checks"]["disk_usage"] = f"{used_percent}"
                if int(used_percent.replace("%", "")) > 90:
                    checks["status"] = "WARN"
        except Exception:
            checks["checks"]["disk_usage"] = "unknown"

        # 2. 运行时间
        try:
            result = subprocess.run(
                ["uptime"],
                capture_output=True, text=True, timeout=5,
            )
            checks["checks"]["uptime"] = result.stdout.strip()[:80]
        except Exception:
            pass

        # 3. 最后登录
        try:
            result = subprocess.run(
                ["last", "-1"],
                capture_output=True, text=True, timeout=5,
            )
            checks["checks"]["last_login"] = result.stdout.strip()[:80]
        except Exception:
            pass

        # 4. SSH 认证日志
        try:
            ssh_log = "/var/log/system.log"
            if Path(ssh_log).exists():
                result = subprocess.run(
                    ["tail", "-20", ssh_log],
                    capture_output=True, text=True, timeout=5,
                )
                failed_logins = len(re.findall(
                    r"Failed\s+password|Invalid\s+user", result.stdout, re.IGNORECASE
                ))
                checks["checks"]["failed_ssh_24h"] = failed_logins
                if failed_logins > 10:
                    checks["status"] = "WARN"
        except Exception:
            pass

        logger.info(f"  状态: {checks['status']}")
        logger.info(f"  检查项: {len(checks['checks'])}")
        return checks


# ─── CLI ───

def main():
    analyzer = ForensicsAnalyzer()

    if len(sys.argv) < 2:
        print("用法: python3 secops_forensics.py <command>")
        print("命令: analyze | timeline | ioc-scan | check-log <file> | health-check | report")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "analyze":
        analyzer.analyze_all()

    elif cmd == "timeline":
        report = analyzer.analyze_all()
        print(f"\n{'='*56}")
        print(f"  📊 入侵时间线")
        print(f"{'='*56}")
        if report.timeline:
            for item in sorted(report.timeline, key=lambda x: x["timestamp"]):
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(item["severity"], "⚪")
                print(f"  {icon} [{item['timestamp'][:19]}] {item['title']}")
        else:
            print(f"   ✅ 未发现异常事件")
        print(f"{'='*56}\n")

    elif cmd == "ioc-scan":
        iocs = analyzer.ioc_scan()
        print(json.dumps(iocs, indent=2, ensure_ascii=False))

    elif cmd == "check-log":
        if len(sys.argv) < 3:
            print("用法: secops_forensics.py check-log <文件路径>")
            sys.exit(1)
        filepath = sys.argv[2]
        if not os.path.isfile(filepath):
            print(f"文件不存在: {filepath}")
            sys.exit(1)
        logger.info(f"📖 检查日志文件: {filepath}")
        try:
            result = subprocess.run(["tail", "-100", filepath], capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split("\n")

            # 简单异常检测
            anomaly_count = 0
            for line in lines:
                if any(k in line.lower() for k in ["error", "fail", "denied", "invalid"]):
                    anomaly_count += 1

            print(f"  总行数(最后100行): {len(lines)}")
            print(f"  异常行数: {anomaly_count}")
            if anomaly_count > 20:
                print(f"  ⚠️  异常比例过高")
            else:
                print(f"  ✅ 日志状态正常")
        except Exception as e:
            print(f"  ❌ 读取失败: {e}")

    elif cmd == "health-check":
        analyzer.health_check()

    elif cmd == "report":
        report = analyzer.analyze_all()
        print(json.dumps({
            "report": {
                "hostname": report.hostname,
                "platform": report.platform,
                "generated_at": report.generated_at,
                "summary": report.summary,
            },
            "events": report.events,
            "timeline": report.timeline,
        }, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
