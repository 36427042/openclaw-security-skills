# OpenClaw Cybersecurity Skills Suite 🛡️

**5 个面向 AI Agent 安全的 OpenClaw 安全加固 Skills**

基于 2026 年 AI 网络安全态势研究开发，覆盖 MCP 安全、Skill 供应链攻击、实例加固、提示注入防御、安全取证五大关键领域。可发布到 GitHub 和 EvoMap 开放订阅。

## 安全威胁现状

| 威胁 | 数据 | 来源 |
|:----|:-----|:-----|
| 恶意 Skills | 1,184+ (ClawHub, Feb 2026) | Antiy CERT |
| 暴露 MCP 服务器 | 492 (无认证暴露) | Trend Micro |
| 暴露 Agent 实例 | 40,000+ (12,000 无认证) | Wiz Research |
| 恶意 Skills 审核 | 341/2,857 (12%) | Koi Security |
| MCP Auth Bypass | CVE-2026-32211 (CVSS 9.1) | NVD |
| Token 泄露 | CVE-2026-25253 (CVSS 8.5) | Penligent |

## Skills 概览

| Skill | 领域 | 核心功能 | 风险覆盖 |
|:----|:-----|:---------|:---------|
| 🛡️ **mcp-guardian** | MCP 安全 | 端点扫描、认证检查、0.0.0.0 暴露检测、凭证扫描、CVE 匹配 | 492 暴露 MCP + CVE-2026-32211 |
| 🔒 **skill-defender** | 供应链安全 | 22 种红牌检测、权限分析、供应链攻击检测、集成 Hermes watch | 1,184 恶意 Skills + 341/2,857 |
| 🔐 **instance-lockdown** | 实例加固 | Gateway 配置审计、网络暴露检测、Token 安全、防火墙检查 | 40,000+ 暴露实例 |
| 🤖 **prompt-guard** | 提示注入防御 | 12 种注入模式检测、对话监控、事件日志、自动防御 | OWASP LLM #1 |
| 🔍 **secops-forensics** | 安全取证 | 审计日志分析、IOC 检测、入侵时间线、健康检查 | 事件响应与取证 |

## 架构设计

```
security-skills/
├── README.md                    # 项目总览
├── EVOMAP.md                    # EvoMap 订阅清单
├── requirements.txt             # Python 依赖
├── LICENSE                      # MIT License
├── mcp-guardian/
│   ├── SKILL.md                 # MCP 安全守护者
│   └── mcp_guardian.py          # 端点扫描 + CVE 匹配
├── skill-defender/
│   ├── SKILL.md                 # Skill 运行时防御者
│   └── skill_defender.py        # 22 种红牌检测
├── instance-lockdown/
│   ├── SKILL.md                 # 实例安全加固器
│   └── instance_lockdown.py     # Gateway 审计 + 加固脚本
├── prompt-guard/
│   ├── SKILL.md                 # 提示注入防御系统
│   └── prompt_guard.py          # 12 种注入模式检测
└── secops-forensics/
    ├── SKILL.md                 # 安全取证分析
    └── secops_forensics.py      # IOC 检测 + 时间线
```

## 快速开始

### 直接使用 Python 脚本

```bash
# MCP 安全扫描
python3 security-skills/mcp-guardian/mcp_guardian.py scan
python3 security-skills/mcp-guardian/mcp_guardian.py check https://your-mcp-server.com

# Skill 安全审计
python3 security-skills/skill-defender/skill_defender.py scan
python3 security-skills/skill-defender/skill_defender.py check mcp-guardian

# 实例安全审计
python3 security-skills/instance-lockdown/instance_lockdown.py audit
python3 security-skills/instance-lockdown/instance_lockdown.py harden

# 提示注入检测
python3 security-skills/prompt-guard/prompt_guard.py check "你的输入内容"
python3 security-skills/prompt-guard/prompt_guard.py monitor

# 安全取证
python3 security-skills/secops-forensics/secops_forensics.py health-check
python3 security-skills/secops-forensics/secops_forensics.py ioc-scan
```

### 安装为 OpenClaw Skills

```bash
# 复制到 OpenClaw Skills 目录
cp -r security-skills/* ~/.openclaw/skills/

# 注册到 EvoMap
# 参考 EVOMAP.md 中的节点注册信息
```

### 集成 Hermes

每个 Skill 都设计为可集成到 Hermes 流程中：

```python
from hermes_skills import skill_registry

skill_registry.skillify(
    "MCP安全巡检", "扫描并加固所有MCP配置",
    steps=["bittergourd", "pea"],
    tags=["安全", "MCP", "巡检"],
)
```

## 威胁模型 (Threat Model)

| 攻击者 | 攻击向量 | 防护 Skill |
|:------|:---------|:----------|
| 远程攻击者 | MCP 端点暴露 → 凭证窃取 | mcp-guardian |
| 供应链攻击者 | 恶意 Skill 下载 → 代码执行 | skill-defender |
| 网络攻击者 | Gateway 暴露 → Agent 控制 | instance-lockdown |
| 用户交互攻击者 | 提示注入 → 指令提取 | prompt-guard |
| 入侵后攻击者 | 凭证窃取 → 横向移动 | secops-forensics |

## 参考

- [OpenClaw Security Documentation](https://docs.openclaw.ai/gateway/security)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-llm-applications/)
- [MITRE ATLAS](https://atlas.mitre.org)
- [MCP Specification](https://modelcontextprotocol.io)
- [NIST AI 600-1](https://www.nist.gov)

## License

MIT License
