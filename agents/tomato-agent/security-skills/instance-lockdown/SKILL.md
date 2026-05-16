---
name: instance-lockdown
description: "OpenClaw 实例安全加固器 — 检测并修复 Gateway 配置中的安全薄弱环节。检查绑定地址、认证配置、Token 加密、防火墙规则、浏览器桥接暴露面。解决 40,000+ 公网暴露实例的威胁。"
---

# Instance Lockdown — OpenClaw 实例安全加固器 🔐

## 威胁背景

Wiz Research 2026年3月识别出 40,000+ 公网暴露的 OpenClaw 实例，其中 12,000+ 完全没有认证保护。攻击者可以：
- 通过未保护的 Gateway 控制 AI Agent
- 注入恶意指令到 Agent 工作流
- 窃取 OpenClaw 凭证接管身份验证（CVE-2026-25253）

## 可检测的不安全配置

| 配置问题 | 风险级别 | 影响 |
|---------|---------|------|
| `bind=0.0.0.0` | 🔴 CRITICAL | 实例暴露到公网 |
| 无认证 Gateway | 🔴 CRITICAL | 任意访问控制 Agent |
| Token 明文存储 | 🔴 HIGH | 凭证窃取 |
| 浏览器桥接未限制 | 🟠 HIGH | Token 泄露 (CVE-2026-25253) |
| 无防火墙 | 🟠 HIGH | 端口暴露 |
| 默认端口 | 🟡 MEDIUM | 易被批量扫描 |
| 无日志审计 | 🟡 MEDIUM | 入侵无法追溯 |
| 未加密通信 | 🟠 HIGH | 中间人攻击 |

## 功能

1. **Gateway 配置审计** — 分析 `~/.openclaw/config.yaml` 安全设置
2. **网络暴露检测** — 扫描监听地址、开放端口、防火墙状态
3. **认证检查** — 检测 Gateway 是否配置了认证
4. **Token 安全评估** — 检查 Token 存储和加密方式
5. **CVE 检查** — 检测已知漏洞（CVE-2026-25253）
6. **一键加固** — 生成加固脚本

## 用法

```bash
# 全面审计实例安全
openclaw run instance-lockdown audit

# 网络暴露扫描
openclaw run instance-lockdown network-scan

# 生成加固脚本
openclaw run instance-lockdown harden

# 快速检查
openclaw run instance-lockdown quick

# JSON 报表
openclaw run instance-lockdown report
```

## 集成

```python
from hermes_skills import skill_registry

skill_registry.skillify(
    "OpenClaw实例安全巡检",
    "每日安全检查 OpenClaw Gateway 安全配置",
    steps=["bittergourd", "pea"],
    tags=["安全", "实例", "巡检"],
)
```

CRON 定时巡检：

```bash
openclaw cron add --name "instance-lockdown:daily-audit" \
  --schedule "0 5 * * *" \
  --command "openclaw run instance-lockdown quick"
```
