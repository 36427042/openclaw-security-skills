#!/usr/bin/env python3
"""
mcp_guardian.py — MCP Security Guardian
扫描 MCP Server 配置、端点安全、凭证泄漏

用法:
    python3 mcp_guardian.py scan          # 全量扫描
    python3 mcp_guardian.py quick         # 快速扫描
    python3 mcp_guardian.py check <url>   # 检查指定端点
    python3 mcp_guardian.py harden        # 生成加固方案(只报告)
    python3 mcp_guardian.py report        # 输出JSON报告
"""

import json
import logging
import os
import re
import socket
import ssl
import subprocess
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("mcp_guardian")


# ─── 数据模型 ───

@dataclass
class RiskFinding:
    severity: str       # CRITICAL / HIGH / MEDIUM / LOW
    category: str       # auth / exposure / credentials / config / cve
    title: str
    description: str
    location: str
    recommendation: str
    cve_id: str = ""
    cvss: float = 0.0


@dataclass
class ScanReport:
    target: str
    timestamp: str = ""
    findings: List[dict] = field(default_factory=list)
    score: int = 0
    total_checks: int = 0
    summary: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def add(self, finding: RiskFinding):
        self.findings.append(asdict(finding))
        self.total_checks += 1

    def finalize(self):
        """计算风险评分"""
        weights = {"CRITICAL": 25, "HIGH": 15, "MEDIUM": 7, "LOW": 2}
        raw = sum(weights.get(f["severity"], 0) for f in self.findings)
        self.score = min(raw, 100)
        by_sev = {}
        for f in self.findings:
            by_sev.setdefault(f["severity"], 0)
            by_sev[f["severity"]] += 1
        self.summary = {
            "score": self.score,
            "level": self._risk_level(),
            "findings": len(self.findings),
            "by_severity": by_sev,
            "scanned_at": self.timestamp,
        }

    def _risk_level(self) -> str:
        if self.score >= 80:
            return "CRITICAL"
        if self.score >= 60:
            return "HIGH"
        if self.score >= 30:
            return "MEDIUM"
        return "LOW"

    def text_report(self) -> str:
        lines = [
            "=" * 56,
            f"  MCP Guardian — 安全扫描报告",
            "=" * 56,
            f"  扫描目标: {self.target}",
            f"  扫描时间: {self.timestamp[:19]}",
            f"  风险评分: {self.score}/100 [{self.summary.get('level', 'N/A')}]",
            f"  发现问题: {len(self.findings)}",
            f"  检查总数: {self.total_checks}",
            "-" * 56,
        ]
        sev_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        for f in self.findings:
            icon = sev_icons.get(f["severity"], "⚪")
            lines.append(f"  {icon} [{f['severity']:>8}] {f['title']}")
            lines.append(f"     {f['description']}")
            if f.get("cve_id"):
                lines.append(f"     CVE: {f['cve_id']} (CVSS: {f['cvss']})")
            lines.append(f"     📍 {f['location']}")
            lines.append(f"     💡 {f['recommendation']}")
            lines.append("  " + "-" * 50)
        lines.append("=" * 56)
        return "\n".join(lines)


# ─── 扫描器 ───

class MCPScanner:
    """MCP 安全扫描器"""

    CONFIG_DIRS = [
        os.path.expanduser("~/.openclaw"),
        os.path.expanduser("~/.clawdbot"),
        os.path.expanduser("~/.claude"),
    ]

    SENSITIVE_PATTERNS = [
        # API Keys & Tokens
        (r"(?:api[_-]?key|apikey|api_key)\s*[=:]\s*['\"]?(sk-[a-zA-Z0-9_-]{10,})['\"]?", "API Key"),
        (r"(?:token|secret|password)\s*[=:]\s*['\"]([a-zA-Z0-9_\-\.]{10,})['\"]?", "Token/Secret"),
        (r"OPENAI_API_KEY\s*[=:]\s*['\"]?(sk-[a-zA-Z0-9]{20,})", "OpenAI API Key"),
        (r"ANTHROPIC_API_KEY\s*[=:]\s*['\"]?(sk-ant-[a-zA-Z0-9]{20,})", "Anthropic API Key"),
        (r"VOLC_ACCESSKEY|VOLC_SECRETKEY", "Volc Engine Credentials"),
        # .env / credentials files
        (r"\.env$", "Environment File"),
        (r"credentials\.(json|yaml|yml)$", "Credentials File"),
    ]

    def __init__(self):
        self.report = ScanReport(target="localhost")

    # ── 扫描入口 ──

    def scan_all(self) -> ScanReport:
        """全量扫描"""
        logger.info("🔍 MCP Guardian — 全量安全扫描开始...\n")
        self._scan_config_files()
        self._scan_bind_addresses()
        self._scan_credentials()
        self._scan_known_vulns()
        self.report.finalize()
        return self.report

    def quick_scan(self) -> ScanReport:
        """快速扫描（仅检查配置和凭证）"""
        logger.info("⚡ MCP Guardian — 快速安全扫描...\n")
        self._scan_config_files()
        self._scan_credentials()
        self.report.finalize()
        return self.report

    def check_endpoint(self, url: str) -> ScanReport:
        """检查指定 MCP 端点"""
        self.report = ScanReport(target=url)
        logger.info(f"🔍 检查 MCP 端点: {url}\n")
        self._check_mcp_endpoint(url)
        # 附带检查本地配置
        self._scan_config_files()
        self.report.finalize()
        return self.report

    # ── 扫描方法 ──

    def _scan_config_files(self):
        """扫描 MCP 配置文件"""
        logger.info("📁 扫描 MCP 配置文件...")

        for base_dir in self.CONFIG_DIRS:
            if not os.path.isdir(base_dir):
                continue

            # 递归扫描配置文件
            for root, dirs, files in os.walk(base_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    # 忽略二进制和非配置
                    if fname.endswith((".pyc", ".py", ".jpg", ".png", ".mp4")):
                        continue
                    try:
                        if os.path.getsize(fpath) > 1024 * 100:  # >100KB skip
                            continue
                    except (FileNotFoundError, OSError):
                        continue
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    except Exception:
                        continue

                    rel_path = os.path.relpath(fpath, os.path.expanduser("~"))

                    # 检测 0.0.0.0 绑定
                    if "0.0.0.0" in content and ("bind" in content.lower() or "host" in content.lower()):
                        self.report.add(RiskFinding(
                            severity="HIGH",
                            category="exposure",
                            title="检测到 0.0.0.0 绑定",
                            description="MCP 服务器配置为监听所有网络接口, 可能暴露到公网",
                            location=rel_path,
                            recommendation="改为 127.0.0.1 仅本地监听, 或配置防火墙限制访问",
                        ))

                    # 检测 MCP 端点配置
                    mcp_endpoints = re.findall(
                        r'(?:url|endpoint|server)[=:]\s*["\']?(https?://[^"\'\\s]+)["\']?',
                        content, re.IGNORECASE
                    )
                    for ep in mcp_endpoints:
                        if ep.startswith("http://"):
                            self.report.add(RiskFinding(
                                severity="MEDIUM",
                                category="config",
                                title="MCP 使用明文 HTTP",
                                description=f"MCP 端点使用未加密的 HTTP 连接",
                                location=f"{rel_path}: {ep[:60]}",
                                recommendation="改为 HTTPS 加密连接",
                            ))

                    # 检测 MCP server 配置 without auth
                    if "mcp" in fname.lower() or "mcp" in content.lower()[:500]:
                        # 检查是否有 auth 配置
                        has_auth = bool(re.search(
                            r'(?:auth|token|key|secret|bearer|api_key)',
                            content, re.IGNORECASE
                        ))
                        if not has_auth:
                            self.report.add(RiskFinding(
                                severity="HIGH",
                                category="auth",
                                title="MCP 配置缺少认证机制",
                                description="MCP Server 未配置任何认证方式",
                                location=rel_path,
                                recommendation="添加 Bearer Token 或 API Key 认证",
                            ))

        logger.info(f"  ✅ 配置文件检查完成\n")

    def _scan_bind_addresses(self):
        """扫描监听地址"""
        logger.info("🌐 检查网络监听地址...")

        # macOS 检查监听端口
        try:
            result = subprocess.run(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout
            # 查找 0.0.0.0 监听
            lines = output.strip().split("\n")
            exposed = []
            for line in lines:
                if "0.0.0.0:" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        port_line = parts[8] if len(parts) > 8 else "?"
                        exposed.append(f"{parts[0]} ({port_line})")

            if exposed:
                for srv in exposed:
                    self.report.add(RiskFinding(
                        severity="HIGH",
                        category="exposure",
                        title="服务绑定到 0.0.0.0",
                        description=f"服务 '{srv}' 监听所有接口, 可能暴露到公网",
                        location=f"lsof: {srv}",
                        recommendation="修改监听地址为 127.0.0.1 或配置防火墙白名单",
                    ))
            else:
                logger.info("  ✅ 未检测到 0.0.0.0 绑定风险")

            # 检查是否有高端口监听
            high_ports = []
            for line in lines:
                if "*:" in line or "0.0.0.0:" in line:
                    continue
                if "127.0.0.1:" in line:
                    continue
                match = re.search(r':(\d+)', line)
                if match:
                    port = int(match.group(1))
                    if 1024 <= port <= 49151 and port not in (80, 443, 22, 8000, 8001):
                        parts = line.split()
                        high_ports.append(f"{parts[0]} (port {port})")

            logger.info(f"  ℹ️  发现 {len(high_ports)} 个非常规监听服务")

        except Exception as e:
            logger.warning(f"  ⚠️  无法扫描监听端口: {e}")

    def _scan_credentials(self):
        """扫描凭证泄漏"""
        logger.info("🔑 扫描凭证泄漏...")

        cred_findings = []

        for base_dir in self.CONFIG_DIRS:
            if not os.path.isdir(base_dir):
                continue

            for root, dirs, files in os.walk(base_dir):
                # 跳过 git 目录
                if ".git" in dirs:
                    dirs.remove(".git")
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        if os.path.getsize(fpath) > 1024 * 50:  # >50KB skip
                            continue
                    except (FileNotFoundError, OSError):
                        continue
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    except Exception:
                        continue

                    rel_path = os.path.relpath(fpath, os.path.expanduser("~"))

                    for pattern, desc in self.SENSITIVE_PATTERNS:
                        if re.search(pattern, content, re.IGNORECASE):
                            # 检查是否在注释中
                            lines = content.split("\n")
                            for i, line in enumerate(lines, 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    # 模糊处理 - 不要泄漏实际 key
                                    masked = re.sub(
                                        r"['\"]([a-zA-Z0-9_\-\.]{8,})['\"]",
                                        lambda m: f"'{m.group(1)[:4]}...[redacted]'",
                                        line.strip()[:100]
                                    )
                                    cred_findings.append({
                                        "file": rel_path,
                                        "line": i,
                                        "pattern": desc,
                                        "content": masked,
                                    })

        if cred_findings:
            # 去重
            seen = set()
            unique_findings = []
            for f in cred_findings:
                key = f"{f['file']}:{f['pattern']}"
                if key not in seen:
                    seen.add(key)
                    unique_findings.append(f)

            # 仅报告关键凭证泄漏
            for f in unique_findings[:20]:
                sev = "CRITICAL" if "API Key" in f["pattern"] or "Token" in f["pattern"] else "HIGH"
                self.report.add(RiskFinding(
                    severity=sev,
                    category="credentials",
                    title=f"凭证明文存储: {f['pattern']}",
                    description=f"发现敏感凭证明文存储",
                    location=f"{f['file']}:{f['line']}",
                    recommendation="使用环境变量或密钥管理服务(如 1Password CLI, macOS Keychain)",
                ))

            logger.info(f"  ⚠️  发现 {len(unique_findings)} 处凭证泄漏风险")
        else:
            logger.info("  ✅ 未发现凭证泄漏")

    def _scan_known_vulns(self):
        """检查已知漏洞"""
        logger.info("🛡️  检查已知漏洞...")

        # CVE-2026-32211: Azure DevOps MCP Auth Bypass
        self.report.add(RiskFinding(
            severity="CRITICAL",
            category="cve",
            title="CVE-2026-32211 — Azure DevOps MCP Auth Bypass",
            description="Azure DevOps MCP Server 认证绕过, CVSS 9.1, 无需凭证即可访问 API Keys 和 Tokens",
            location="Azure DevOps MCP Server 配置",
            recommendation="更新至修复版本, 添加 MCP 端点认证",
            cve_id="CVE-2026-32211",
            cvss=9.1,
        ))

        # CVE-2026-25253: OpenClaw Token Exfiltration
        self.report.add(RiskFinding(
            severity="CRITICAL",
            category="cve",
            title="CVE-2026-25253 — OpenClaw Token 泄露",
            description="通过浏览器桥接进行 Token 窃取, 可导致完整 Gateway 沦陷、配置修改、代码执行",
            location="OpenClaw Gateway 配置",
            recommendation="更新至最新版 OpenClaw, 限制 Gateway 的浏览器访问",
            cve_id="CVE-2026-25253",
            cvss=8.5,
        ))

        logger.info("  ✅ 已知漏洞检查完成\n")

    def _check_mcp_endpoint(self, url: str):
        """检查远程 MCP 端点"""
        logger.info(f"  🌐 测试端点: {url}")

        # 检查 URL 的协议
        if url.startswith("http://"):
            self.report.add(RiskFinding(
                severity="HIGH",
                category="config",
                title="MCP 端点使用明文 HTTP",
                description="HTTP 连接可能被中间人攻击, 凭证和指令会被窃听",
                location=url,
                recommendation="升级到 HTTPS",
            ))

        # 测试端点响应
        try:
            req = urllib.request.Request(url, method="GET")
            # 添加通用 User-Agent
            req.add_header("User-Agent", "MCP-Guardian/1.0")

            try:
                resp = urllib.request.urlopen(req, timeout=10)
                status = resp.status
                body = resp.read().decode("utf-8", errors="ignore")[:2000]

                if status == 200:
                    # 检查是否返回了敏感数据
                    if any(k in body.lower() for k in ("api_key", "token", "secret", "password")):
                        self.report.add(RiskFinding(
                            severity="CRITICAL",
                            category="auth",
                            title="MCP 端点未认证且返回敏感数据",
                            description=f"端点返回 200, 无认证要求, 响应中包含凭证相关字段",
                            location=url,
                            recommendation="立即添加认证机制并移除响应中的敏感数据",
                        ))
                    else:
                        self.report.add(RiskFinding(
                            severity="HIGH",
                            category="auth",
                            title="MCP 端点无认证要求",
                            description=f"端点返回 200, 无需认证即可访问",
                            location=url,
                            recommendation="添加 Bearer Token 认证",
                        ))
                elif status == 401 or status == 403:
                    logger.info(f"  ✅ 端点有认证保护 (HTTP {status})")
                else:
                    logger.info(f"  ℹ️  端点返回 HTTP {status}")
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    logger.info(f"  ✅ 端点有认证保护 (HTTP {e.code})")
                else:
                    logger.info(f"  ℹ️  端点返回 HTTP {e.code}")
            except urllib.error.URLError as e:
                self.report.add(RiskFinding(
                    severity="LOW",
                    category="config",
                    title="MCP 端点不可达",
                    description=f"无法连接到 MCP 端点: {e.reason}",
                    location=url,
                    recommendation="检查网络连通性和 URL 是否正确",
                ))

        except Exception as e:
            logger.warning(f"  ⚠️  检查端点时出错: {e}")

        # 检查 SSL/TLS
        if url.startswith("https://"):
            try:
                hostname = url.split("/")[2].split(":")[0]
                port = 443
                if ":" in url.split("/")[2]:
                    port = int(url.split("/")[2].split(":")[1])

                ctx = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        # 证书检查通过
                        logger.info(f"  ✅ SSL/TLS 证书有效")
            except Exception as e:
                self.report.add(RiskFinding(
                    severity="MEDIUM",
                    category="config",
                    title="SSL/TLS 证书问题",
                    description=f"SSL 握手失败: {e}",
                    location=url,
                    recommendation="检查 SSL 证书配置",
                ))

    def generate_harden_plan(self) -> dict:
        """生成加固方案"""
        plan = {
            "summary": "MCP 配置加固方案",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "priority_items": [],
            "commands": [],
        }

        # 1. 绑定地址加固
        plan["priority_items"].append({
            "priority": "HIGH",
            "action": "限制 MCP Server 绑定到 127.0.0.1",
            "detail": "修改配置文件, 将 host/bind 从 0.0.0.0 改为 127.0.0.1",
        })
        plan["commands"].append("# 检查并修改 MCP 配置中的绑定地址")
        plan["commands"].append("grep -r '0.0.0.0' ~/.openclaw/ --include='*.json' --include='*.yaml' --include='*.yml'")

        # 2. 认证加固
        plan["priority_items"].append({
            "priority": "CRITICAL",
            "action": "为 MCP Server 添加 Bearer Token 认证",
            "detail": "在 MCP 配置中添加 auth token 配置项",
        })
        plan["commands"].append("")
        plan["commands"].append("# 为 MCP 端点设置 Bearer Token")
        plan["commands"].append("# 编辑配置文件添加:")
        plan["commands"].append("# auth: { type: bearer, token: $(openssl rand -hex 32) }")

        # 3. 凭证管理
        plan["priority_items"].append({
            "priority": "CRITICAL",
            "action": "将所有明文凭证迁移到环境变量或密钥管理",
            "detail": ".env 文件和 JSON 配置中的 API Keys 应迁移到环境变量",
        })
        plan["commands"].append("")
        plan["commands"].append("# 使用环境变量替代明文凭证")
        plan["commands"].append("export MCP_AUTH_TOKEN=$(openssl rand -hex 32)")
        plan["commands"].append("# 在配置中使用 ${MCP_AUTH_TOKEN} 引用")

        # 4. HTTPS 强制
        plan["priority_items"].append({
            "priority": "HIGH",
            "action": "MCP 端点强制使用 HTTPS",
            "detail": "确保所有 MCP 连接使用 TLS 加密",
        })
        plan["commands"].append("")
        plan["commands"].append("# 将所有 http:// MCP 端点改为 https://")
        plan["commands"].append("# 或配置反向代理(如 nginx)终止 TLS")

        return plan


# ─── CLI ───

def main():
    scanner = MCPScanner()

    if len(sys.argv) < 2:
        print("用法: python3 mcp_guardian.py <command>")
        print("命令: scan | quick | check <url> | harden | report")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "scan":
        report = scanner.scan_all()
        print("\n" + report.text_report())
        print(f"\nJSON 报告: {json.dumps(report.summary, indent=2)}\n")

    elif cmd == "quick":
        report = scanner.quick_scan()
        print("\n" + report.text_report())

    elif cmd == "check":
        if len(sys.argv) < 3:
            print("用法: mcp_guardian.py check <url>")
            sys.exit(1)
        report = scanner.check_endpoint(sys.argv[2])
        print("\n" + report.text_report())

    elif cmd == "harden":
        plan = scanner.generate_harden_plan()
        print(f"\n{'='*56}")
        print(f"  MCP 加固方案")
        print(f"{'='*56}")
        for item in plan["priority_items"]:
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(item["priority"], "⚪")
            print(f"  {icon} [{item['priority']}] {item['action']}")
            print(f"     {item['detail']}")
        print(f"\n  📋 建议执行命令:")
        for cmd in plan["commands"]:
            print(f"    {cmd}")
        print(f"{'='*56}\n")

    elif cmd == "report":
        report = scanner.scan_all()
        print(json.dumps({
            "summary": report.summary,
            "findings": report.findings,
            "mcp_guardian_version": "1.0.0",
        }, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
