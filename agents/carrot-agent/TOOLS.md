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

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

## 🧬 GEP 接入 — 自进化引擎

**所有操作必须接入GEP（自进化引擎）：**

```bash
# 1. 执行前：检查历史经验
python3 ~/.openclaw/workspace/scripts/gep_adapter.py pre_check carrot "当前任务名"

# 2. 执行后：记录结果到GEP
python3 ~/.openclaw/workspace/scripts/gep_adapter.py post_record carrot "当前任务名" success

# 3. 保活：心跳检查
python3 ~/.openclaw/workspace/scripts/gep_adapter.py keepalive carrot
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
| 🔧 `faster-whisper` | 本地语音转写(large-v3) | 音频文字提取 |
| 🔧 `videoagent-audio-studio` | 音频工作室工具 | 配音处理/音效 |
| 🔧 `prompt-engineering-2` | 完整提示词工程框架 | 写配音脚本 |
| 🔧 `prompt-engineering-expert` | 高级提示词优化 | 高质量配音文案 |
| 🔧 `ai-prompt-engineer` | AI提示词工程师 | 结构化配音prompt |

**做配音/音频处理/直播脚本时，**必须先读取对应SKILL.md**获得最佳实践，再动手。**

---

## 🧬 Hermes 融合工作流

执行任何任务前必须参考：
📖 `scripts/hermes_fusion_sop.md`
