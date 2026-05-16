# FRAMEWORK.md — Hermes V3.3 + DeerFlow + EvoMap 三位一体联邦宪法

> 最后修订：2026-05-13 01:38
> 宪法效力：此文件 > SOUL.md > AGENTS.md。任何与本文冲突的规则以本文为准。

## 一、核心原则

**所有工作必须走框架，禁止裸跑。**

| 禁止 | 必须 |
|:---|:---|
| ❌ 直接 `python3 脚本.py` | ✅ `hermes_engine.py run --subtasks '["partner"]'` |
| ❌ 直接 ffmpeg 命令 | ✅ DeerFlow Step2 → video_mix_6country.py |
| ❌ 手动调 API/写文件 | ✅ 通过注册脚本 + GEP记录 |
| ❌ 跳过 EvoMap 进化 | ✅ 每步产出 → gep_engine.post_record() |

## 二、三层架构

```
┌──────────────────────────────────────┐
│  🥔 土豆·统筹 (Commander)            │
│  唯一入口：hermes_engine.py           │
│  两种调度：                            │
│    • run --subtasks → 选伙伴执行       │
│    • run --workflow deerflow → 全链路   │
└──────────────┬───────────────────────┘
               │
    ┌──────────▼──────────┐
    │  Hermes Engine      │
    │  TaskDelegator      │
    │  • 拆解任务          │
    │  • 并行调度          │
    │  • 超时/重试         │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  DeerFlow (LangGraph)│
    │  7步全链路工作流      │
    │  Step1: 选品 🍅       │
    │  Step2: 视频 🌽       │
    │  Step3: 文案 🥬       │
    │  Step4: 客服 🥬       │
    │  Step5: 风控 🥒       │
    │  Step6: 数据 🫘       │
    │  Step7: 进化 🧬       │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  EvoMap (GEP)       │
    │  • 自动进化记录       │
    │  • 失败模式学习        │
    │  • 参数优化反馈        │
    └──────────────────────┘
```

## 三、伙伴脚本 → 框架映射

| 伙伴 | 脚本 | Hermes直调 | DeerFlow步骤 | GEP记录 |
|:---|:---|:---|:---|:---:|
| 🍅 番茄 | booster_matrix.py | `--subtasks '["booster"]'` | Step1 | ✅ |
| 🌽 玉米 | video_mix_6country.py | `--subtasks '["video"]'` | Step2 | ✅ |
| 🥬 生菜 | copy_engine.py | `--subtasks '["copy"]'` | Step3 | ✅ |
| 🥬 生菜 | hermes_engine.py | - | Step4 | ✅ |
| 🥒 苦瓜 | risk_controller.py | `--subtasks '["risk"]'` | Step5 | ✅ |
| 🫘 豌豆 | data_monitor.py | `--subtasks '["data"]'` | Step6 | ✅ |
| 🥕 萝卜 | qwen_tts_engine.py | `--subtasks '["tts"]'` | - | ✅ |

## 四、土豆强制调度规则

1. **收到天赐任务 → 判断类型**
   - 单伙伴任务(选品/风控/数据) → `hermes_engine run --subtasks '["partner"]'`
   - 多伙伴并行 → `hermes_engine run --subtasks '["a","b","c"]'`
   - 全链路工作流 → `hermes_engine run --workflow deerflow`
   - AI创意推理(写文案) → `sessions_spawn` (走子代理，不走直接API)

2. **禁止行为**
   - ❌ 直接 `python3 ~/workspace/scripts/xxx.py`
   - ❌ 直接 ffmpeg / API 调用
   - ❌ 跳过 hermes_engine 调任何脚本
   - ❌ 任务完成后不生成报告

3. **必须行为**
   - ✅ 每一步通过 hermes_engine/TaskDelegator 派遣
   - ✅ 每一步产出自动 push_to_feishu + run_evolution
   - ✅ 错误自动记录到 `data/evolution/failures.jsonl`
   - ✅ 所有脚本内置 gep_engine.post_record()

## 五、伙伴强制规则

每个伙伴的脚本必须：
1. 接收参数通过 argparse（框架传入）
2. 输出 JSON 到 stdout（框架捕获）
3. 调用 gep_engine.post_record() 记录进化
4. 正常完成返回退出码 0，失败返回 1

每个伙伴的 SOUL.md 必须包含：
```
## ⛓️ 框架绑定（强制）
- 我的脚本通过 hermes_engine 被调用，我不裸跑
- 我输出的 JSON 被 DeerFlow LangGraph 消费
- 我每步产出自动记录到 EvoMap GEP
- 如果框架出问题 → 报告土豆，不绕过框架
```

## 六、验证方式

```bash
# 验证链路完整性
python3 hermes_engine.py run --workflow deerflow
# 预期: status=completed, errors=0, steps=7
# 预期: 12个视频文件, 12个唯一MD5
# 预期: 飞书推送报告
# 预期: EvoMap GEP记录
```
