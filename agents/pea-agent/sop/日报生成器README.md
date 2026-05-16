# 📊 自动日报生成器使用指南

> **脚本**: `scripts/daily_report_generator.py`
> **版本**: v1.1
> **维护**: 🫘豌豆

---

## 使用方法

### 1️⃣ 直接运行（测试用）

```bash
cd ~/.openclaw/workspace/agents/pea-agent

# 生成今日完整日报（JSON + Markdown摘要）
python3 scripts/daily_report_generator.py

# 生成前日摘要（适合早会）
python3 scripts/daily_report_generator.py --mode=summary
```

### 2️⃣ cron自动执行

```bash
# crontab -e 添加以下行：

# 每天北京时间22:00 → UTC 14:00，生成当日完整日报
0 14 * * * cd /Users/a1234/.openclaw/workspace/agents/pea-agent && /usr/bin/python3 scripts/daily_report_generator.py --output_dir=output 2>> /tmp/daily_report_cron.log

# 每天北京时间08:00 → UTC 00:00，生成前日摘要（早会用）
0 0 * * * cd /Users/a1234/.openclaw/workspace/agents/pea-agent && /usr/bin/python3 scripts/daily_report_generator.py --mode=summary --output_dir=output 2>> /tmp/daily_report_summary_cron.log
```

### 3️⃣ 产出文件

| 文件 | 用途 |
|:----|:-----|
| `output/daily_report_YYYY-MM-DD.json` | 完整JSON日报（机器人/程序解析用） |
| `output/daily_report_YYYY-MM-DD.md` | Markdown摘要（飞书可直接粘贴） |

### 4️⃣ 飞书贴摘要

直接打开 `output/daily_report_YYYY-MM-DD.md`，全选复制 → 粘贴到飞书群即可。
格式示例：

```
📊 经营日报 · 2026-05-11
=======================

📈 今日总览
- 总GMV: $12,850.50 (vs昨日 +12.3%)
- 订单: 423 单
- 退款率: 4.96%

🌍 5国对比
| 国家 | GMV | 订单 | 退款率 | GPM | ROAS | 健康 |
|...|...|...|...|...|...|...|

🔴 紧急告警
- VN退款率突增...

🟡 待关注
- 越南GPM连续3日下降...

📋 行动建议
...

👥 交接清单
- 土豆: ...
- 玉米: ...
```

---

## Hermes集成

```python
from hermes_engine import HermesEngine

engine = HermesEngine()
engine.run_workflow("daily_report", {
    "output_dir": "output",
    "table_id": "Mm7tbKj6na4EGws0QOAcgftnnQh"
})
```

## 阈值配置

| 指标 | 绿区 | 黄区 | 红区 |
|:----|:----:|:----:|:----:|
| GPM (美元) | ≥80 | 50-80 | <50 |
| ROAS | ≥3.0 | 1.5-3.0 | <1.5 |
| 退款率 | ≤5% | 5-10% | >10% |
| AOV (美元) | ≥8 | 5-8 | <5 |

## 异常检测项

1. ✅ 退款率突增（日环比 >5%警告，>10%急告）
2. ✅ GPM持续下滑（连续3日下降）
3. ✅ 库存预警（<3天存量）
4. ✅ 视频产出下降（<70%昨日）
5. ✅ 里程碑记录（GMV突破/订单破纪录）
