# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 🧬 GEP 接入 — 自进化引擎

**所有操作必须接入GEP（自进化引擎）：**

```bash
# 1. 执行前：检查历史经验
python3 ~/.openclaw/workspace/scripts/gep_adapter.py pre_check booster "当前任务名"

# 2. 执行后：记录结果到GEP
python3 ~/.openclaw/workspace/scripts/gep_adapter.py post_record booster "当前任务名" success

# 3. 保活：心跳检查
python3 ~/.openclaw/workspace/scripts/gep_adapter.py keepalive booster
```

**GEP核心API：**
- `pre_check(伙伴, 任务)` → 返回历史经验和警告
- `post_record(伙伴, 任务, 结果)` → 记录到进化库
- 失败时传 `problem="具体问题"` 和 `outcome="failed"`

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

## ⚡ 专属技能 — 必须调用

你的 skills/ 目录已安装以下技能，**执行任务时必须先读取对应SKILL.md再动手**：

| 技能 | 功能 | 适用场景 |
|:-----|:-----|:---------|
| 🔧 `consulting-analysis` | 市场/品牌/竞品深度分析 | 选品调研、市场分析报告 |
| 🔧 `data-analysis` | Excel/CSV数据分析、统计汇总 | 销量数据、趋势分析 |
| 🔧 `prompt-engineering-2` | 完整提示词工程框架 | 写选品prompt、分析指令 |
| 🔧 `prompt-engineering-expert` | 高级提示词优化 | 高质量分析输出 |
| 🔧 `ai-prompt-engineer` | AI提示词工程师 | 结构化选品prompt |

**做选品分析/市场调研时，**必须先读取对应SKILL.md**获得最佳实践，再动手。**

---

## 🧬 Hermes 融合工作流

执行任何任务前必须参考：
📖 `scripts/hermes_fusion_sop.md`
