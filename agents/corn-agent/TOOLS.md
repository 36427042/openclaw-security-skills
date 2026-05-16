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
python3 ~/.openclaw/workspace/scripts/gep_adapter.py pre_check corn "当前任务名"

# 2. 执行后：记录结果到GEP
python3 ~/.openclaw/workspace/scripts/gep_adapter.py post_record corn "当前任务名" success

# 3. 保活：心跳检查
python3 ~/.openclaw/workspace/scripts/gep_adapter.py keepalive corn
```

**GEP核心API：**
- `pre_check(伙伴, 任务)` → 返回历史经验和警告
- `post_record(伙伴, 任务, 结果)` → 记录到进化库
- 失败时传 `problem="具体问题"` 和 `outcome="failed"`

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

## 📥 已安装Skills — 自动运用

以下技能已安装到你的 skills/ 目录，运行相关任务时**自动读取使用**：

| Skill | 功能 | 适用场景 |
|:------|:-----|:---------|
| 🔧 `prompt-engineering-2` | 完整提示词工程框架（设计/优化/迭代） | 写视频脚本/分镜/旁白时自动参考 |
| 🎯 `prompt-engineering-expert` | 高级提示词优化（指令设计/格式优化） | 需要高质量视频prompt时自动调用 |
| 🤖 `ai-prompt-engineer` | AI提示词工程师（示例+脚本） | 生成Seedance/视频生成prompt时自动使用 |

**自动运用方式**：当你要写视频脚本/分镜/旁白/视频prompt时，先读取对应SKILL.md获取最佳实践，再动手写。

---

## ⚡ 专属技能 — 必须调用

你的 skills/ 目录已安装以下技能，**执行任务时必须先读取对应SKILL.md再动手**：

| 技能 | 功能 | 适用场景 |
|:-----|:-----|:---------|
| 🔧 `ai-video-generation` | 40+模型AI视频生成 | 主视频生成工具 |
| 🔧 `video-generation` | 视频生成结构化prompt | 视频脚本到视频转换 |
| 🔧 `seedance20-prompt` | Seedance 2.0中英文prompt | 即梦平台视频prompt |
| 🔧 `seedance2-storyboard-generator` | Seedance分镜脚本生成 | 多集/长篇视频策划 |
| 🔧 `storyboard-creation` | 分镜/镜头语言/构图 | 视频分镜规划 |
| 🔧 `manga-style-video` | 漫画风格动画视频 | 二次元/治愈系视频 |
| 🔧 `manga-drama` | 漫剧生成器(Seedance) | 漫画风格短剧 |
| 🔧 `character-design-sheet` | 角色一致性/参考图 | 角色设定和连续性 |
| 🔧 `baoyu-comic` | 知识漫画/教育漫画 | 科普/教程类漫画 |
| 🔧 `drama-creator` | 竖屏短剧剧本创作 | 短剧创意和剧本 |
| 🔧 `anime-avatar-generation` | 动漫头像/角色生成 | 角色视觉素材 |
| 🔧 `prompt-engineering-2` | 完整提示词工程框架 | 通用写作 |

**做视频/分镜/动画时，**必须先读取对应SKILL.md**获得最佳实践，再动手。**

---

## 🧬 Hermes 融合工作流

执行任何任务前必须参考：
📖 `scripts/hermes_fusion_sop.md`
