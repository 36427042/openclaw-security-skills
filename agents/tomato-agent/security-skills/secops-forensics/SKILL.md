---
name: secops-forensics
description: "安全取证与事件分析工具 — 对已发生的安全事件进行取证分析。支持审计日志分析、入侵时间线重构、IOC 检测、攻击路径追溯。适用于事件响应和安全审计场景。"
---

# SecOps Forensics — 安全取证分析 🔍

当安全事件发生后，快速定位攻击入口、确定影响范围、重建入侵时间线是恢复和防御的关键。本 Skill 对 Agent 安全事件进行全链路取证分析。

## 数据源

| 数据源 | 说明 | 使用场景 |
|-------|------|---------|
| ~/.openclaw/ 审计日志 | Gateway 请求和响应日志 | 检测异常命令 |
| ~/.openclaw/cron/ 任务日志 | 定时任务执行记录 | 发现被篡改的定时任务 |
| Hermes watch 日志 | Hermes 运行时监控日志 | 追踪异常行为 |
| OpenClaw 会话记录 | Agent 对话历史 | 发现注入攻击 |
| 系统日志 (macOS unified log) | 系统级安全事件 | 发现提权/文件篡改 |

## 功能

1. **审计日志分析** — 解析 Gateway 请求日志，检测异常模式
2. **入侵时间线重构** — 按时间顺序构建攻击事件链
3. **IOC 检测** — 检测系统沦陷指标 (异常进程、未知端口、后门文件)
4. **攻击路径追溯** — 从入口点到影响面完整分析
5. **风险评分卡** — 客观量化受损程度

## 用法

```bash
# 进行完整安全取证分析
openclaw run secops-forensics analyze

# 侵入时间线重建
openclaw run secops-forensics timeline

# IOC 检测
openclaw run secops-forensics ioc-scan

# 检查特定日志文件
openclaw run secops-forensics check-log <文件路径>

# 生成取证报告
openclaw run secops-forensics report

# 快速健康检查
openclaw run secops-forensics health-check
```

## 取证分析流程

### 阶段 1: 数据采集
- 自动发现所有可用的安全日志源
- 读取 Gateway 审计日志
- 读取 Hermes 监控日志
- 读取系统安全日志

### 阶段 2: 异常检测
- 检测异常时间段的请求（无活动时间窗口外）
- 检测大量请求突增（Brute-force 扫描）
- 检测命令模式异常（非典型 Agent 操作）

### 阶段 3: IOC 扫描
- 异常进程检测（未知名称、高 CPU、无父进程）
- 后门文件检测（SUID 文件、新建的可执行文件）
- 网络后门检测（非常规监听端口、反向 shell 连接）
- 持久化检测（新增 cron/launchd/系统服务）

### 阶段 4: 时间线重构
- 按时间组织所有检测到的事件
- 标记已知的恶意活动时间窗
- 绘制攻击路径图

### 阶段 5: 风险评分
- 综合评估受损程度 (0-100)
- 分类输出: 已确认入侵 / 可疑活动 / 安全

## 集成 Hermes

```python
from hermes_skills import skill_registry

skill_registry.skillify(
    "安全取证分析", "对 Agent 安全事件进行全链路取证",
    steps=["pea", "bittergourd"],
    tags=["安全", "取证", "响应"],
)
```

## 参考

- [OpenClaw Security Incident Response](https://docs.openclaw.ai/gateway/security)
- [NIST SP 800-61: Computer Security Incident Handling Guide](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final)
- [MITRE ATT&CK Framework](https://attack.mitre.org)
