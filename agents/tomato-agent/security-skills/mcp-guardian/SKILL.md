---
name: mcp-guardian
description: "MCP (Model Context Protocol) 安全守护者 — 扫描 MCP 服务器端点认证漏洞、权限暴露、未加密连接和已知 CVE。检查 agent 配置中 MCP Server 的安全状态，识别 0.0.0.0 绑定、无认证端点、凭证泄漏等风险。"
---

# MCP Guardian — MCP 安全守护者 🔒

2026 年 AI Agent 安全的核心供应链风险在于 MCP (Model Context Protocol)。Trend Micro 发现 492 个暴露在公网的无认证 MCP 服务器，Azure DevOps MCP 认证绕过漏洞 (CVE-2026-32211, CVSS 9.1)。本 Skill 负责扫描和加固 MCP 相关配置。

## 威胁背景

| 威胁类型 | 实际案例 | 影响 |
|---------|---------|------|
| 无认证暴露 | Trend Micro: 492 servers | API 密钥、Token 可被任意获取 |
| 0.0.0.0 绑定 | 公共 OpenClaw 实例 | 内网服务暴露到公网 |
| MCP 配置投毒 | Claude Code RCE (CVE-2025-59536) | 恶意 MCP 服务器端执行代码 |
| 凭证明文存储 | `~/.clawdbot/.env` 等配置 | Token 被盗取后全网关沦陷 |
| CVE-2026-32211 | Azure DevOps MCP 认证绕过 | CVSS 9.1, 无需凭证访问 |

## 功能

1. **端点扫描** — 扫描 MCP Server 的 `/mcp`, `/sse` 端点
2. **认证检查** — 检查 MCP Server 是否配置认证
3. **绑定地址检查** — 检测 0.0.0.0 绑定暴露风险
4. **凭证泄漏检测** — 扫描 agent 配置文件中明文 API Keys
5. **已知漏洞检查** — 对照 CVE 数据库检查 MCP 版本
6. **加固建议** — 自动生成 MCP 配置加固方案

## 用法

```bash
# 扫描当前环境的 MCP 配置
openclaw run mcp-guardian scan

# 检查指定 MCP 端点
openclaw run mcp-guardian check-endpoint https://your-mcp-server.example.com

# 加固 MCP 配置（需确认）
openclaw run mcp-guardian harden

# 生成 MCP 安全报告
openclaw run mcp-guardian report

# 快速检查
openclaw run mcp-guardian quick
```

## 工作流程

### 阶段 1: 环境发现
- 扫描 `~/.openclaw/` 中所有 MCP 相关配置
- 检测 `~/.clawdbot/`, `~/.claude/` 等常用 agent 配置目录
- 列出所有 MCP Server 端点

### 阶段 2: 安全扫描
- 检查是否有绑定到 `0.0.0.0`
- 测试端点是否需要认证 (401/403 vs 200)
- 检查是否使用 HTTPS (vs 明文 HTTP)
- 扫描 credentials 文件中的 Key/Token

### 阶段 3: 漏洞匹配
- 对照已发布 CVE 匹配版本
- 检查已知的 MCP 漏洞模式
- 识别配置错误模式

### 阶段 4: 报告输出
- 风险评分 (0-100)
- 每个风险点的严重级别
- 针对性的修复建议
- 修复优先级排序

## 风险级别定义

| 级别 | 评分 | 说明 |
|------|------|------|
| 🔴 CRITICAL | 80-100 | 可直接利用的漏洞，立即修复 |
| 🟠 HIGH | 60-79 | 高风险配置错误，24小时内修复 |
| 🟡 MEDIUM | 30-59 | 需加固的配置，本周内修复 |
| 🟢 LOW | 0-29 | 建议改进，下个维护周期修复 |

## 集成

本 Skill 可集成到 Hermes 工作流中：

```python
from hermes_skills import skill_registry

# 注册为 Hermes Skill
skill_registry.skillify(
    "MCP安全巡检", "扫描并加固所有 MCP 配置",
    steps=["bittergourd", "pea"],  # 苦瓜风控 + 豌豆数据
    tags=["安全", "MCP", "巡检"],
)
```

也可通过 CRON 定时扫描：

```bash
openclaw cron add --name "mcp-guardian:daily-scan" \
  --schedule "0 6 * * *" \
  --command "openclaw run mcp-guardian quick"
```

## 参考

- [MCP Specification](https://modelcontextprotocol.io)
- [CVE-2026-32211: Azure DevOps MCP Auth Bypass](https://nvd.nist.gov/vuln/detail/CVE-2026-32211)
- [Trend Micro: 492 Exposed MCP Servers](https://blog.cyberdesserts.com/ai-agent-security-risks/)
- [OpenClaw Security Documentation](https://docs.openclaw.ai/gateway/security)
