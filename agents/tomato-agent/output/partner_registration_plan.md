# 🧩 6伙伴节点注册到EvoMap — 注册计划

## 当前状态：✅ 已完成

## 一、架构总览

### 核心组件

```
partner_registration.py          ← 🆕 伙伴注册脚本（本计划产物）
├── PartnerNode                  ← 单个伙伴节点：节点ID、注册历史、心跳历史
├── PartnerRegistry              ← 注册中心：所有伙伴的管理器
└── CLI: register / status / heartbeat / report

gep_engine.py                    ← 已有，GEP自进化引擎
├── GEPNode                      ← 进化节点（问题→尝试→结果）
├── GEPRegistry                  ← 进化节点存储
└── GEP(pre_check / post_record) ← 执行前检查/执行后记录

evomap_heartbeat.py              ← 已有，EvoMap云端心跳保活
└── POST heartbeat → evomap.ai   ← ⏳ 需要天赐质押后才生效

hermes_engine.py                 ← 已有，伙伴调度引擎
└── PARTNER_CONFIGS              ← 6伙伴的配置映射
```

### 数据流

```
register() → PartnerNode → partner_registry.json (持久化)
          → GEP.post_record() → registry.jsonl (进化记录)

heartbeat() → PartnerNode → partner_registry.json (持久化)
           → GEP.post_record() → registry.jsonl (进化记录)

report() → PartnerRegistry → partner_registration_report.md (输出)
```

## 二、7伙伴节点注册表

| 伙伴 | 子任务Key | 节点ID | 脚本 | 能力 |
|------|-----------|--------|------|------|
| 🥔 土豆·调度 | hermes | `node_d355bf7768a9` | hermes_engine.py | 任务分解/伙伴调度/工作流编排 |
| 🍅 番茄·选品 | booster | `node_9442cc76138a` | booster_matrix.py | TikTok选品/定价分析/爆单矩阵 |
| 🥬 生菜·文案 | copy | `node_ab4bb102272e` | copy_engine.py | 文案生成/多语言翻译 |
| 🌽 玉米·视频 | video | `node_ab32d9089e9e` | video_mix_6country.py | 视频混剪/素材处理 |
| 🥕 萝卜·配音 | tts | `node_8edf47611449` | qwen_tts_engine.py | TTS配音/多语言语音 |
| 🥒 苦瓜·风控 | risk | `node_acc25c19500f` | risk_controller.py | 内容审核/合规检查 |
| 🫘 豌豆·数据 | data | `node_07c06aac619c` | data_monitor.py | 数据监控/报表生成 |

## 三、依赖关系（DAG）

```
番茄 (选品) ──→ 生菜 (文案) ──→ 玉米 (视频)
    │                              │
    └──────────┬───────────────────┘
               │
               ↓
            豌豆 (数据监控)
               ↑
    ┌──────────┴──────────┐
    │                     │
  萝卜 (配音)         苦瓜 (风控)
```

- **独立运行**：番茄、萝卜、苦瓜（无上游依赖）
- **串行依赖**：番茄→生菜→玉米（必须按序执行）
- **聚合依赖**：豌豆依赖所有其他伙伴的产出
- **调度中枢**：土豆依赖所有伙伴（负责调度和协调）

## 四、心跳检查机制

### 检查内容
每轮心跳检查每个伙伴：
- 脚本文件是否存在（物理存活）
- 脚本修改时间（版本检测）
- 注册记录是否健全

### 与GEP集成
- 每次心跳自动调用 `GEP(partner).post_record()` 记录到进化数据库
- 心跳异常自动写入失败记录，GEP的模式分析会检测到重复失败

### 与EvoMap集成的断点
- `evomap_heartbeat.py` 已配置单节点心跳（需天赐质押后生效）
- 后续可将伙伴节点注册到EvoMap云端，实现远程监控

## 五、执行记录

**注册执行（2026-05-14 21:53）:**
- 7伙伴全部成功注册
- 每伙伴生成唯一 `node_xxx` 节点ID
- 注册信息持久化到 `data/evolution/partner_registry.json`
- 7条GEP进化节点写入 `data/evolution/registry.jsonl`（任务: 节点注册）

**第一次心跳（2026-05-14 21:53）:**
- 7伙伴全部存活 ✅
- 脚本文件全部存在 ✅
- 14条GEP心跳记录写入 registry.jsonl

## 六、后续行动

| # | 行动 | 前置条件 | 优先级 |
|---|------|----------|--------|
| 1 | EvoMap质押完成 → 同步伙伴节点到云端 | 天赐确认质押 | 🔴 高 |
| 2 | 将 `partner_registration.py heartbeat` 集成到保活cron | 无 | 🟡 中 |
| 3 | 建立伙伴健康告警（心跳丢失30min） | EvoMap质押后 | 🟡 中 |
| 4 | 在Feishu Dashboard中添加节点状态面板 | EvoMap质押后 | 🟢 低 |

## 七、文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| 🆕 `partner_registration.py` | `scripts/partner_registration.py` | 注册脚本（核心产出） |
| 🆕 `partner_registration_report.md` | `agents/tomato-agent/output/partner_registration_report.md` | 详细注册报告 |
| 🆕 `partner_registration_plan.md` | `agents/tomato-agent/output/partner_registration_plan.md` | 本文件 |
| 🆕 `partner_registry.json` | `data/evolution/partner_registry.json` | 注册持久化数据 |
| ✅ `gep_engine.py` | `scripts/gep_engine.py` | GEP引擎（已有） |
| ✅ `evomap_heartbeat.py` | `scripts/evomap_heartbeat.py` | 心跳保活（已有） |
| ✅ `hermes_engine.py` | `scripts/hermes_engine.py` | 调度引擎（已有） |
