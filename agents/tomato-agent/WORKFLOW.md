# WORKFLOW.md — 6伙伴状态速查（每次启动后必读）

> **目的**: 防止记忆丢失导致重复劳动。每个伙伴的最新状态一目了然。

## 🍅 番茄·选品
- **最新版脚本**: `scripts/booster_matrix.py` ✅ argparse+JSON+exit标准化
- **最新产出**: 爆单矩阵分析 + EchoTik 3品类×5国 TOP100
- **阻塞项**: EchoTik API 404（美妆类目持续无数据）
- **状态**: 🟢 待命中

## 🥬 生菜·文案
- **最新版脚本**: `scripts/copy_engine.py` ✅
- **核心功能**: `generate_seedance_prompt()` — Seedance 2.0 15秒提示词生成
- **提示词模板**: 3480字符（3品类：美妆/家居/厨房），含商品一致性强制规则
- **最新产出**: `~/Desktop/视屏生成prompt/top20_v4_prompts.md` — 多样性改造版（5种变体A/B/C/D/E）
- **进行中**: V4→V5优化（15秒+商品一致性），生菜子代理执行中
- **状态**: 🟡 V4→V5优化中

## 🌽 玉米·视频
- **最新版脚本**: `agents/corn-agent/scripts/pipeline_video.py` V8 ✅
- **核心功能**: 源视频→横竖自动转换→Edge TTS 6国→BGM库→PIL字幕→20维防重
- **输出格式**: 1080×1920竖屏，AAC 44100Hz
- **Seedance适配**: 720p→1080p Lanczos上采样，TTS 5行15秒
- **调用方式**: `hermes_engine.py run --subtasks '["video"]'`
- **已废除**: 简创AIGC（video_pipeline_v2.py归档）、CapCut桌面版（computer-use-capcut删除）
- **状态**: 🟢 就绪，等天赐放源视频

## 🥕 萝卜·配音
- **脚本**: `scripts/qwen_tts_engine.py` ✅
- **状态**: 🟢 待命中

## 🥒 苦瓜·风控
- **脚本**: `scripts/risk_controller.py` ✅
- **状态**: 🟢 待命中

## 🫘 豌豆·数据
- **脚本**: `scripts/data_monitor.py` ✅
- **状态**: 🟢 待命中

---

## 🚦 行动前强制检查（每次任务前必过）

```
□ 这是什么任务？（选品/文案/视频/配音/风控/数据）
□ 昨天是否已完成类似工作？→ memory_search 检索
□ 伙伴最新脚本/文档是什么版本？→ 看上面速查表
□ 是需要微调还是重做？→ 默认微调，除非天赐明确说重做
□ 是否应该派给伙伴而不是自己动手？→ hermes_engine / sessions_spawn
```
