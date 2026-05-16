#!/usr/bin/env python3
"""
instance_lockdown.py — OpenClaw 实例安全加固器
检测 Gateway 配置安全问题、网络暴露、Token 风险

用法:
    python3 instance_lockdown.py audit          # 全面审计
    python3 instance_lockdown.py network-scan   # 网络扫描
    python3 instance_lockdown.py harden         # 生成加固方案
    python3 instance_lockdown.py quick          # 快速检查
    python3 instance_lockdown.py report         # JSON 报告
"""

import json
import logging
import os
import platform
import re
import socket
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("instance_lockdown")

OPENCLAW_DIR = os.path.expanduser("~/.openclaw")
OPENCLAW_CONFIG = os.path.join(OPENCLAW_DIR, "config.yaml")
OPENCLAW_GATEWAY_CONFIG = os.path.join(OPENCLAW_DIR, "gateway", "config.yaml")


# ─── 数据模型 ───

@dataclass
class Finding:
    severity: str
    category: str
    title: str
    description: str
    location: str
    recommendation: str

    def to_dict(self):
        return asdict(self)


@dataclass
class InstanceReport:
    hostname: str
    platform: str
    timestamp: str = ""
    findings: List[dict] = field(default_factory=list)
    score: int = 0
    check_count: int = 0
    summary: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def add(self, finding: Finding):
        self.findings.append(finding.to_dict())
        self.check_count += 1

    def finalize(self):
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
            "checks": self.check_count,
            "by_severity": by_sev,
            "scanned_at": self.timestamp,
        }

    def _risk_level(self) -> str:
        if self.score >= 60: return "CRITICAL"
        if self.score >= 30: return "HIGH"
        if self.score >= 10: return "MEDIUM"
        return "LOW"

    def text_report(self) -> str:
        lines = [
            "=" * 56,
            f"  Instance Lockdown — 实例安全审计报告",
            "=" * 56,
            f"  主机: {self.hostname} ({self.platform})",
            f"  时间: {self.timestamp[:19]}",
            f"  风险评分: {self.score}/100 [{self.summary.get('level', 'N/A')}]",
            f"  发现问题: {len(self.findings)}/{self.check_count}",
            "-" * 56,
        ]
        sev_icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        for f in self.findings:
            icon = sev_icons.get(f["severity"], "⚪")
            lines.append(f"\n  {icon} [{f['severity']:>8}] {f['title']}")
            lines.append(f"     {f['description']}")
            lines.append(f"     📍 {f['location']}")
            lines.append(f"     💡 {f['recommendation']}")
        lines.append(f"\n{'='*56}")
        return "\n".join(lines)


# ─── 扫描器 ───

class InstanceScanner:
    def __init__(self):
        self.report = InstanceReport(
            hostname=socket.gethostname(),
            platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
        )

    # ─── 审计方法 ───

    def audit_all(self) -> InstanceReport:
        logger.info(f"🔍 Instance Lockdown — 全面安全审计\n")
        self._check_gateway_config()
        self._check_network_exposure()
        self._check_firewall()
        self._check_token_security()
        self._check_openclaw_version()
        self._check_cves()
        self.report.finalize()
        logger.info("\n" + self.report.text_report())
        return self.report

    def quick_audit(self) -> InstanceReport:
        logger.info("⚡ 快速安全检查...\n")
        self._check_gateway_config()
        self._check_token_security()
        self._check_cves()
        self.report.finalize()
        logger.info("\n" + self.report.text_report())
        return self.report

    def network_scan(self) -> InstanceReport:
        logger.info("🌐 网络暴露检测...\n")
        self._check_network_exposure()
        self._check_firewall()
        self._check_gateway_config()
        self.report.finalize()
        logger.info("\n" + self.report.text_report())
        return self.report

    # ─── 检查项目 ───

    def _check_gateway_config(self):
        """检查 Gateway 配置"""
        logger.info("📁 检查 Gateway 配置...")

        config_paths = [OPENCLAW_GATEWAY_CONFIG, OPENCLAW_CONFIG]
        config_found = False

        for cfg_path in config_paths:
            if not os.path.isfile(cfg_path):
                continue
            config_found = True
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            rel = os.path.relpath(cfg_path, os.path.expanduser("~"))

            # 检测 bind=0.0.0.0
            if re.search(r"bind\s*[=:]\s*['\"]?0\.0\.0\.0['\"]?", content):
                self.report.add(Finding(
                    severity="CRITICAL", category="exposure",
                    title="Gateway 绑定到 0.0.0.0",
                    description="Gateway 监听所有网络接口，实例可被公网访问",
                    location=rel,
                    recommendation="将 bind 改为 127.0.0.1 或配置防火墙白名单",
                ))

            # 检测 bind=0.0.0.0:PORT
            if re.search(r"bind\s*[=:]\s*['\"]?0\.0\.0\.0:\d+['\"]?", content):
                self.report.add(Finding(
                    severity="CRITICAL", category="exposure",
                    title="Gateway 绑定到 0.0.0.0 + 端口",
                    description="Gateway 绑定所有接口的指定端口，可通过 IP:Port 访问",
                    location=rel,
                    recommendation="改为 127.0.0.1:PORT 仅本地监听",
                ))

            # 检测是否有 auth 配置
            has_auth = bool(re.search(r"auth|token|password|secret", content, re.IGNORECASE))
            if not has_auth:
                self.report.add(Finding(
                    severity="HIGH", category="auth",
                    title="Gateway 未配置认证",
                    description="Gateway 没有认证配置，任何人可访问控制",
                    location=rel,
                    recommendation="在 config.yaml 中添加 auth 配置",
                ))

            # 检查是否配置 SSL
            has_https = bool(re.search(r"https|cert|tls|ssl", content, re.IGNORECASE))
            if not has_https:
                self.report.add(Finding(
                    severity="MEDIUM", category="config",
                    title="Gateway 未使用 HTTPS",
                    description="Gateway 通信未加密，可能被窃听",
                    location=rel,
                    recommendation="配置 SSL/TLS 证书启用 HTTPS",
                ))

            # 检查默认端口
            if re.search(r"bind\s*[=:]\s*['\"]?(?:\d+\.)*:\s*(?:8000|3000)", content):
                self.report.add(Finding(
                    severity="LOW", category="config",
                    title="使用默认 Gateway 端口",
                    description="使用 8000/3000 等默认端口，易被批量扫描",
                    location=rel,
                    recommendation="使用非常规端口 (如 18723)",
                ))

        if not config_found:
            self.report.add(Finding(
                severity="MEDIUM", category="config",
                title="Gateway 配置文件未找到",
                description="未找到 OpenClaw Gateway 配置",
                location="~/.openclaw/gateway/config.yaml",
                recommendation="创建 Gateway 配置并启用安全设置",
            ))

        logger.info("  ✅ Gateway 配置检查完成\n")

    def _check_network_exposure(self):
        """检查网络暴露面"""
        logger.info("🌐 检查网络暴露面...")

        try:
            # macOS: lsof 检查监听端口
            result = subprocess.run(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                capture_output=True, text=True, timeout=10,
            )
            lines = result.stdout.strip().split("\n")[1:]  # skip header

            openclaw_ports = []
            exposed = []
            for line in lines:
                parts = line.split()
                if len(parts) < 9:
                    continue
                addr = parts[8]
                proc = parts[0]

                # 检查是否包含 openclaw/node
                if "openclaw" in proc.lower() or "node" in proc.lower():
                    openclaw_ports.append(addr)
                    if addr.startswith("*:") or addr.startswith("0.0.0.0:"):
                        port = addr.split(":")[-1]
                        exposed.append(f"{proc}:{addr}")

            if exposed:
                for e in exposed:
                    self.report.add(Finding(
                        severity="HIGH", category="exposure",
                        title="OpenClaw 服务暴露到公网",
                        description=f"服务 {e} 绑定到所有接口",
                        location=f"lsof: {e}",
                        recommendation="绑定到 127.0.0.1",
                    ))

            logger.info(f"  ℹ️  共 {len(openclaw_ports)} 个 OpenClaw 相关监听端口")
            if not exposed:
                logger.info("  ✅ 未检测到公网暴露")

        except Exception as e:
            logger.warning(f"  ⚠️  网络扫描失败: {e}")

        # 检查外部 IP
        try:
            result = subprocess.run(
                ["curl", "-s", "https://ifconfig.me/ip"],
                capture_output=True, text=True, timeout=10,
            )
            public_ip = result.stdout.strip()
            if public_ip:
                logger.info(f"  📡 公网 IP: {public_ip}")
                # 检查是否有服务在公网 IP 上
                try:
                    for port in [8000, 3000, 8080]:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((public_ip, port))
                        sock.close()
                        if result == 0:
                            self.report.add(Finding(
                                severity="CRITICAL", category="exposure",
                                title=f"公网端口 {port} 开放",
                                description=f"公网 IP {public_ip}:{port} 可连接",
                                location=f"{public_ip}:{port}",
                                recommendation="关闭端口或添加防火墙白名单",
                            ))
                except Exception:
                    pass
        except Exception:
            logger.info("  ℹ️  无法获取公网 IP")

    def _check_firewall(self):
        """检查防火墙状态"""
        logger.info("🔥 检查防火墙状态...")

        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
                    capture_output=True, text=True, timeout=5,
                )
                output = result.stdout.strip()
                if "enabled" in output.lower():
                    logger.info("  ✅ macOS 防火墙已启用")
                else:
                    self.report.add(Finding(
                        severity="HIGH", category="config",
                        title="macOS 防火墙未启用",
                        description="macOS 内置防火墙关闭，所有端口暴露",
                        location="System Settings → Network → Firewall",
                        recommendation="启用 macOS 防火墙",
                    ))
            except Exception:
                logger.info("  ℹ️  无法检查防火墙状态")
        else:
            try:
                subprocess.run(["which", "ufw"], check=True, capture_output=True)
                result = subprocess.run(
                    ["sudo", "ufw", "status"],
                    capture_output=True, text=True, timeout=5,
                )
                if "active" in result.stdout:
                    logger.info("  ✅ UFW 防火墙已启用")
                else:
                    self.report.add(Finding(
                        severity="HIGH", category="config",
                        title="UFW 防火墙未启用",
                        description="UFW 未激活",
                        location="ufw status",
                        recommendation="启用 UFW: sudo ufw enable",
                    ))
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("  ℹ️  未安装 UFW (非必选)")

    def _check_token_security(self):
        """检查 Token 安全性"""
        logger.info("🔑 检查 Token 安全性...")

        # 检查 .env 中的 OpenClaw Token
        env_path = os.path.join(OPENCLAW_DIR, ".env")
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 检查 OPENCLAW_TOKEN
                if "OPENCLAW_TOKEN" in content:
                    self.report.add(Finding(
                        severity="HIGH", category="credentials",
                        title="OpenClaw Token 存储在 .env",
                        description="Token 在 .env 文文件中明文存储",
                        location="~/.openclaw/.env",
                        recommendation="使用加密存储或密钥管理服务",
                    ))

                # 检查是否有其他 key
                keys_in_env = re.findall(r'(?:TOKEN|KEY|SECRET|PASSWORD)\s*=\s*(\S+)', content)
                if keys_in_env:
                    for k in keys_in_env[:5]:
                        if len(k) > 8:
                            self.report.add(Finding(
                                severity="MEDIUM", category="credentials",
                                title="凭证明文存储",
                                description=f"在 .env 中发现凭证明文",
                                location="~/.openclaw/.env",
                                recommendation="使用 1Password CLI / macOS Keychain",
                            ))
            except Exception:
                pass

        # 检查 config.yaml 中的 token
        for cfg_path in [OPENCLAW_GATEWAY_CONFIG, OPENCLAW_CONFIG]:
            if os.path.isfile(cfg_path):
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if re.search(r"token\s*:\s*['\"]?[a-zA-Z0-9_-]{8,}['\"]?", content):
                        self.report.add(Finding(
                            severity="HIGH", category="credentials",
                            title="Gateway Token 明文存储",
                            description=f"Token 在 {os.path.basename(cfg_path)} 中明文保存",
                            location=f"~/.openclaw/{os.path.basename(cfg_path)}",
                            recommendation="使用环境变量引用: token=${OPENCLAW_TOKEN}",
                        ))
                except Exception:
                    pass

        # 检查 macOS Keychain 是否已使用
        try:
            result = subprocess.run(
                ["security", "find-internet-password", "-s", "openclaw"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                logger.info("  ✅ macOS Keychain 中有 OpenClaw 凭据")
            else:
                logger.info("  ℹ️  macOS Keychain 未发现 OpenClaw 凭据")
        except Exception:
            pass

    def _check_openclaw_version(self):
        """检查 OpenClaw 版本"""
        logger.info("📊 检查 OpenClaw 版本...")

        try:
            result = subprocess.run(
                ["openclaw", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            version = result.stdout.strip() or result.stderr.strip()
            logger.info(f"  ℹ️  OpenClaw 版本: {version}")
        except Exception:
            logger.info("  ℹ️  无法获取 OpenClaw 版本")

    def _check_cves(self):
        """检查已知漏洞"""
        logger.info("🛡️  检查已知漏洞...")

        # CVE-2026-25253: OpenClaw Token Exfiltration
        self.report.add(Finding(
            severity="CRITICAL", category="cve",
            title="CVE-2026-25253 — Token 泄露风险",
            description="通过浏览器桥接可窃取 Gateway Token, 攻击者凭此可完全控制 Agent",
            location="浏览器桥接配置",
            recommendation="1. 升级 OpenClaw 至修补版本\n2. 限制浏览器桥接访问来源\n3. 启用 Gateway 认证",
        ))

    def generate_harden_script(self) -> dict:
        """生成加固脚本"""
        lines = [
            "#!/bin/bash",
            "# OpenClaw Instance Lockdown — 一键加固脚本",
            f"# 生成时间: {datetime.now(timezone.utc).isoformat()}",
            "",
            "echo '🔐 OpenClaw Instance Lockdown — 开始加固...'",
            "",
            "# 1. Gateway 配置加固",
            "echo '📁 1. 加固 Gateway 配置...'",
            "CONFIG=\"$HOME/.openclaw/gateway/config.yaml\"",
            "if [ -f \"$CONFIG\" ]; then",
            "  # 确保 bind 为 127.0.0.1",
            "  if grep -q '0.0.0.0' \"$CONFIG\"; then",
            "    sed -i '' 's/0.0.0.0/127.0.0.1/g' \"$CONFIG\"",
            "    echo '   ✅ 绑定地址已改为 127.0.0.1'",
            "  fi",
            "fi",
            "",
            "# 2. 防火墙设置 (macOS)",
            "echo '🔥 2. 配置防火墙...'",
            "sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on 2>/dev/null &&",
            "  echo '   ✅ macOS 防火墙已启用' ||",
            "  echo '   ⚠️ 防火墙启用失败 (需要手动设置)'",
            "",
            "# 3. Token 迁移到环境变量",
            "echo '🔑 3. 检查 Token 存储...'",
            "if [ -f \"$HOME/.openclaw/.env\" ]; then",
            "  echo '   ⚠️  .env 文件已存在，请手动迁移 Token 到环境变量'",
            "fi",
            "",
            "# 4. 非默认端口",
            "echo '🌐 4. 建议使用非默认 Gateway 端口'",
            "echo '   💡 推荐: bind=127.0.0.1:18723'",
            "",
            "# 5. 日志审计",
            "echo '📝 5. 启用日志审计...'",
            "if [ -f \"$CONFIG\" ]; then",
            "  # 检查是否已有日志配置",
            "  if ! grep -q 'log.*level' \"$CONFIG\" 2>/dev/null; then",
            "    echo '   ℹ️  请在 config.yaml 中添加:'",
            "    echo '   log:'",
            "    echo '     level: info'",
            "    echo '     file: ~/.openclaw/gateway/audit.log'",
            "  fi",
            "fi",
            "",
            "echo ''",
            "echo '✅ 加固完成! 建议重启 Gateway: openclaw gateway restart'",
            "echo '📋 剩余问题请查看: openclaw run instance-lockdown audit'",
        ]
        return {
            "script": "\n".join(lines),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commands": [
                "# 保存脚本到文件",
                "instance-lockdown harden > ~/lockdown.sh && chmod +x ~/lockdown.sh",
                "# 检查后再执行",
                "cat ~/lockdown.sh",
                "# 执行加固",
                "bash ~/lockdown.sh",
            ]
        }


# ─── CLI ───

def main():
    scanner = InstanceScanner()

    if len(sys.argv) < 2:
        print("用法: python3 instance_lockdown.py <command>")
        print("命令: audit | network-scan | quick | harden | report")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "audit":
        scanner.audit_all()

    elif cmd == "network-scan":
        scanner.network_scan()

    elif cmd == "quick":
        scanner.quick_audit()

    elif cmd == "harden":
        plan = scanner.generate_harden_script()
        print(plan["script"])

    elif cmd == "report":
        r = scanner.audit_all()
        print(json.dumps({
            "hostname": r.hostname,
            "platform": r.platform,
            "timestamp": r.timestamp,
            "summary": r.summary,
            "findings": r.findings,
        }, indent=2, ensure_ascii=False))

    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
