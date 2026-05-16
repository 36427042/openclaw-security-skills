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

## 📥 Skill 下载部署流程（VETTER审核 → TRAE优化 → 测试部署）

**流程**：每次下载新skill必须按以下四个步骤执行：

### 1️⃣ VETTER 安全审核
```
① 确定Source（ClawdHub / GitHub / 其他）
② 读取所有文件：SKILL.md + 所有脚本
③ 逐项检查RED FLAGS：
   - curl/wget到未知URL？
   - 发送数据到外部服务器？
   - 索取credential/token/API key？
   - 读取~/.ssh, ~/.aws, ~/.config？
   - base64 decode/obfuscated code？
   - eval/exec带外部输入？
   - sudo/elevated权限请求？
   - 修改系统文件/浏览器cookie？
④ 评估权限范围：读哪些文件/写哪些文件/网络去哪/跑什么命令
⑤ 判定风险等级：🟢 LOW / 🟡 MEDIUM / 🔴 HIGH / ⛔ EXTREME
⑥ 输出VETTER报告 → 判定SAFE才进下一步
```

### 2️⃣ TRAE CN 代码优化
```
① 在脚本上运行TRAE优化命令
② 优化方向：性能/安全性/兼容性
③ 修复发现的问题
```

### 3️⃣ OpenClaw 安装测试
```
① 复制到 ~/.openclaw/skills/<skill-name>/
② 检查SKILL.md frontmatter格式
   - 必须有 name 和 description 字段
   - description在启动时会被扫描建立索引
③ 新会话中测试skill是否可调用
```

### 4️⃣ 部署后更新
```
① 记入本文件（TOOLS.md）的安装清单
② 写入 memory/YYYY-MM-DD.md 的记录
```

---

## 📋 安装的Skill清单

| Skill | 来源 | 状态 | 安装日期 |
|-------|------|------|----------|
| skill-vetter-1-0-0 | ~/.openclaw/skills/ | ✅ 已安装 | 清理前 |
| trae-cn | urwlee/skill-trae-cn | ✅ VETTER通过+已安装 | 2026-05-07 |
| self-improving | sundial-org/awesome-openclaw-skills | ✅ VETTER通过+已安装 | 2026-05-07 |
| find-skills | openclaw/skills (lq-productor) | ⏳ 网络问题待下载 | - |

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)
