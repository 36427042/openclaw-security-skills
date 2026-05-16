---
name: skill-defender
description: "Skill 运行时安全防御者 — 扫描已安装 OpenClaw Skills 的恶意模式、供应链攻击检测、权限越界检查、代码注入检测。集成 Hermes 权限系统和 skill-vetter 审核框架，提供自动化 Skill 安全审计。"
---

# Skill Defender — Skill 运行时安全防御者 🛡️

2026年2月 Antiy CERT 确认 ClawHub 上 1,184 个恶意 Skills。Koi Security 发现 341/2,857 个审核过的 Skills 存在恶意行为。VirusTotal 将 Skill 生态系统描述为恶意软件分发渠道。本 Skill 负责检测和防御 Skill 层面的供应链攻击。

## 威胁背景

| 攻击类型 | 发现数量 | 影响 |
|---------|---------|------|
| 恶意 Skills | 1,184 (ClawHub, Feb 2026) | 凭证窃取、远程控制、数据泄露 |
| stealers/droppers | 大规模分布 (VirusTotal) | 嵌入式恶意负载 |
| 权限越界 | OpenClaw RFC 确认 | Skill "无权限模型、无代码签名、无沙箱" |
| 代码注入 | 各类 Skill 中 | eval/exec 带外部输入 |

## 功能

1. **全量扫描** — 扫描 `~/.openclaw/skills/` 中所有已安装 Skills
2. **红牌检测** — 22 种红牌模式（eval/exec/shell/curl/wget/base64/credential access 等）
3. **权限评估** — 自动化权限范围分析
4. **供应链攻击检测** — 网络外连、数据外泄、域名/IP 可疑模式
5. **集成 skill-vetter** — 基于 skill-vetter 框架增强检测
6. **运行时监控** — 积分 Hermes watch 系统监控 Skill 执行行为

## 用法

```bash
# 全量扫描所有已安装 Skills
openclaw run skill-defender scan

# 扫描指定 Skill
openclaw run skill-defender check <skill-name>

# 自动修复高危问题（需确认）
openclaw run skill-defender fix

# 持续监控 Skill 执行（后台运行）
openclaw run skill-defender watch

# 生成安全报告
openclaw run skill-defender report
```

## 22 种红牌检测模式

| # | 模式 | 严重度 | 说明 |
|:-:|:----|:------|:----|
| 1 | `eval()` / `exec()` | 🔴 CRITICAL | 任意代码执行风险 |
| 2 | `os.system()` | 🔴 CRITICAL | 系统命令注入 |
| 3 | `subprocess(shell=True)` | 🔴 CRITICAL | Shell 命令注入 |
| 4 | `curl`/`wget` to IP | 🔴 HIGH | 可疑网络连接 |
| 5 | `base64 decode` on input | 🔴 HIGH | 代码混淆/隐藏 |
| 6 | `~/.ssh` read | 🔴 CRITICAL | SSH 凭证窃取 |
| 7 | `~/.aws` read | 🔴 CRITICAL | AWS 凭证窃取 |
| 8 | `~/.config` read | 🟠 HIGH | 配置泄漏 |
| 9 | `__import__()` | 🟠 HIGH | 动态导入风险 |
| 10 | `compile()` on string | 🟠 HIGH | 动态代码编译 |
| 11 | `request.post` to unknown | 🟡 MEDIUM | 数据外泄 |
| 12 | `socket.connect` | 🟡 MEDIUM | 自定义网络连接 |
| 13 | `rm -rf /*` | 🔴 CRITICAL | 破坏性操作 |
| 14 | `sudo`/`su` | 🔴 HIGH | 提权操作 |
| 15 | `chmod 777` | 🟡 MEDIUM | 权限宽松 |
| 16 | `/etc/passwd` read | 🟠 HIGH | 系统信息窃取 |
| 17 | `crontab` modify | 🟠 HIGH | 持久化机制 |
| 18 | `open("/dev/"...)` | 🟡 MEDIUM | 设备文件访问 |
| 19 | `pty.spawn` | 🟠 HIGH | PTY 提权 |
| 20 | `os.environ` full dump | 🟡 MEDIUM | 环境变量泄露 |
| 21 | `tempfile.mkstemp` without cleanup | 🟢 LOW | 临时文件残留 |
| 22 | `shutil.rmtree` with user input | 🟠 HIGH | 路径遍历删除 |

## 工作流程

### 阶段 1: 环境收集
- 扫描 `~/.openclaw/skills/` 目录
- 读取每个 Skill 的 SKILL.md + 所有脚本文件
- 统计文件数量、代码行数、外部引用

### 阶段 2: 红牌检测
- 逐文件扫描 22 种红牌模式
- 记录模式出现位置（文件名:行号）
- 按严重级别分类

### 阶段 3: 权限分析
- 评估 Skill 需要的文件读写权限
- 评估网络访问范围
- 评估命令执行权限
- 与 Hermes 权限系统对比

### 阶段 4: 供应链分析
- 检查作者声誉（本地缓存）
- 检查最后更新日期
- 检查文件签名（如有）
- 评估整体风险

### 阶段 5: 报告输出
- 每个 Skill 的风险评分
- 整体安全评分
- 优先级排序的修复建议

## 集成 Hermes

```python
from hermes_skills import skill_registry

skill_registry.skillify(
    "Skill安全检查", "扫描所有已安装 Skill 的安全风险",
    steps=["bittergourd", "pea"],
    tags=["安全", "Skill", "供应链"],
)
```

结合 Hermes watch 系统实现运行时监控：

```bash
# 注册定时扫描
openclaw cron add --name "skill-defender:daily-audit" \
  --schedule "0 7 * * *" \
  --command "openclaw run skill-defender quick"
```

## 参考

- [ClawHavoc: 1,184 Malicious Skills](https://blog.cyberdesserts.com/ai-agent-security-risks/)
- [Koi Security: 341/2,857 Skills Malicious](https://www.netizen.net/news/post/7681/)
- [OpenClaw Skill Security RFC](https://github.com/openclaw/openclaw)
- [OpenClaw + VirusTotal Partnership](https://www.penligent.ai/hackinglabs/)
