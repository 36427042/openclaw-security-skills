# 🥔 土豆·主动心跳巡检 v5.2
# 🕐 更新: 2026-05-15 03:43
# ⚡ 收到心跳 → 读task_board → hermes_engine分派 → push飞书
# 🔴 V5.2: 唯一派遣通道=hermes_engine，sessions_spawn已废除

## 🚀 自动推进（每次心跳必做）
- [ ] 读 task_board.md → 找到所有 ⏳待执行 任务
- [ ] 按优先级排序：🥇生产 > 🥈基础设施 > 🥉优化
- [ ] 每个领域至少派1个任务（不要全堆一条线）
- [ ] 🔴 所有派遣走 hermes_engine（唯一通道，无例外）
- [ ] 派完后更新task_board状态
- [ ] push飞书汇报整体进度（不报单项，报汇总）

## 🔴 Hermes 派遣映射（v5.2唯一通道，无例外）

```bash
# 单伙伴任务
python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --partner <key>

# 多伙伴并行
python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --subtasks '["booster","copy"]'

# 全链路（产研从头到尾）
python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --workflow deerflow

# 带任务描述
python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --partner copy --task "具体任务描述"
```

| 派遣方式 | 适用场景 | 示例 |
|:---|:---|:---|
| `--partner` | 单伙伴所有任务 | 生菜写文案、豌豆扫数据、生菜写Prompt |
| `--subtasks` | 多伙伴并行所有任务 | 豌豆+生菜+苦瓜一条龙 |
| `--workflow deerflow` | 全链路自动化 | 从扫品到上架全自动 |

🔴 sessions_spawn 已彻底废除。任何直接调 sessions_spawn 均违反铁律。

## 📋 任务看板自动分派规则
```
收到心跳 → 读task_board.md
  ├─ 🥇 生产管线（豌豆/生菜/苦瓜/auto_publish）→ 链路完整就自动跑
  ├─ 🥈 基础设施（EvoMap心跳/7虾面板/Cron）→ 发现挂了就修
  ├─ 🥉 优化提升（AIRI/视频Prompt/技能发布）→ 有空就推
  └─ ⚡ 新增TASK → 扫描桌面/伙伴产出/天赐指令 → 自动加到看板
```

## 🔄 当前自动管线状态
| 管线 | 步骤 | 自动？ |
|:---|:-----|:---:|
| EchoTik→上架 | 豌豆扫品→定价→生菜文案→苦瓜审核→auto_publish | ✅ 已固化 |
| 视频生产 | 生菜Prompt→即梦生成→玉米剪辑 | ⏳ Prompt待产出 |
| GitHub发布 | SSH→推送→ClawHub | 🟡 天赐说靠边 |
| EvoMap | 心跳→悬赏→派活 | 🔄 待完善 |
| 7虾面板 | 扫描→API→展示 | 🔄 待优化 |

## 🧠 自主权内化规则
- ❌ 不问"要不要X"、"需要我X吗"——直接做
- ❌ 不等天赐说"下一步"——自己跑完整链路
- ❌ 不一条线管到底不管其他线——心跳扫描全部领域
- ✅ 只汇报结果，不汇报"进行中"
- ✅ 涉及资金/公开展示→需确认
- ✅ 遇到真阻塞→说清楚阻塞点+等什么

## 禁止
- ❌ 不动网关配置
- ❌ 不推送到公众面（视频发布/外部平台）
- ❌ 不动资金相关操作
- ❌ 心跳时不读task_board
- ❌ 等天赐指令才动
- 🔴 不调sessions_spawn（已废除，死刑）
- 🔴 不建临时新子代理
- 🔴 不绕过hermes_engine直接调伙伴脚本
- 🔴 土豆不自己执行伙伴任务（不写脚本、不生成文案、不做Prompt）