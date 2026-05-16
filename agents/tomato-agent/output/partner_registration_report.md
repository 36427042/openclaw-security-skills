# 📋 6伙伴节点注册报告
生成时间：2026-05-14 23:35:59

## 📊 注册概览
- **总节点数**：7
- **总注册次数**：7
- **总心跳次数**：28
- **健康状态**：7 活跃 | 0 脚本缺失 | 0 未注册

## 🧩 伙伴节点明细

| 伙伴 | 节点ID | 脚本 | 脚本存在 | 注册数 | 心跳数 | 最近心跳 | 能力 |
|------|--------|------|----------|--------|--------|----------|------|
| 🥔 土豆·调度 | `node_d355bf7768a9` | hermes_engine.py | ✅ | 1 | 4 | 22:13:50 | 任务分解, 伙伴调度… |
| 🍅 番茄·选品 | `node_9442cc76138a` | booster_matrix.py | ✅ | 1 | 4 | 22:13:50 | TikTok选品, 定价分析… |
| 🥬 生菜·文案 | `node_ab4bb102272e` | copy_engine.py | ✅ | 1 | 4 | 22:13:50 | 文案生成, 多语言翻译… |
| 🌽 玉米·视频 | `node_ab32d9089e9e` | video_mix_6country.py | ✅ | 1 | 4 | 22:13:50 | 视频混剪, 视频生成… |
| 🥕 萝卜·配音 | `node_8edf47611449` | qwen_tts_engine.py | ✅ | 1 | 4 | 22:13:50 | TTS配音, 多语言语音… |
| 🥒 苦瓜·风控 | `node_acc25c19500f` | risk_controller.py | ✅ | 1 | 4 | 22:13:50 | 内容审核, 合规检查… |
| 🫘 豌豆·数据 | `node_07c06aac619c` | data_monitor.py | ✅ | 1 | 4 | 22:13:50 | 数据监控, 报表生成… |

## 🔗 依赖关系

```mermaid
graph TD
    subgraph EvoMap节点注册
        土豆[🥔 土豆·调度] --- |node_id: node_d355bf7768a9|
        番茄[🍅 番茄·选品] --- |node_id: node_9442cc76138a|
        生菜[🥬 生菜·文案] --- |node_id: node_ab4bb102272e|
        玉米[🌽 玉米·视频] --- |node_id: node_ab32d9089e9e|
        萝卜[🥕 萝卜·配音] --- |node_id: node_8edf47611449|
        苦瓜[🥒 苦瓜·风控] --- |node_id: node_acc25c19500f|
        豌豆[🫘 豌豆·数据] --- |node_id: node_07c06aac619c|
    end

    subgraph 依赖关系
        番茄 --> 生菜
        生菜 --> 玉米
        番茄 --> 豌豆
        生菜 --> 豌豆
        玉米 --> 豌豆
        萝卜 --> 豌豆
        苦瓜 --> 豌豆
    end
```

## 📋 伙伴能力矩阵

| 伙伴 | 核心能力 | 依赖 | 下游依赖 |
|------|----------|------|----------|
| 🥔 土豆·调度 | 任务分解, 伙伴调度, 工作流编排, 系统监控 | — | 番茄, 生菜, 玉米, 萝卜, 苦瓜, 豌豆 |
| 🍅 番茄·选品 | TikTok选品, 定价分析, 爆单矩阵, 市场调研 | — | — |
| 🥬 生菜·文案 | 文案生成, 多语言翻译, 货品描述, 话术优化 | 番茄 | — |
| 🌽 玉米·视频 | 视频混剪, 视频生成, 素材处理 | 生菜 | 生菜 |
| 🥕 萝卜·配音 | TTS配音, 多语言语音, Edge-TTS | — | — |
| 🥒 苦瓜·风控 | 内容审核, 合规检查, 违禁词检测, 安全风控 | — | — |
| 🫘 豌豆·数据 | 数据监控, 报表生成, 异常检测, 预警通知 | 番茄, 生菜, 玉米, 萝卜, 苦瓜 | — |

## 🔄 注册流程

```
python3 partner_registration.py register   # 注册所有伙伴节点
python3 partner_registration.py status     # 查看当前状态
python3 partner_registration.py heartbeat  # 执行心跳检查
python3 partner_registration.py report     # 生成完整报告
```

### 与EvoMap集成

注册数据存储路径：`data/evolution/partner_registry.json`
GEP进化数据路径：`data/evolution/registry.jsonl`
EvoMap心跳保活：`scripts/evomap_heartbeat.py`（云端心跳，独立运行）

### 下一步

1. 确认EvoMap质押后就绪 → 将伙伴节点同步到云端
2. 将 `partner_registration.py heartbeat` 集成到保活cron
3. 建立伙伴健康告警：心跳丢失30分钟自动通知