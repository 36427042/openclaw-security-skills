# 🫘 豌豆·待命任务

## 你在流水线中的位置

```
天赐/土豆 → 你(豌豆·主控) → 调用生菜(文案) → auto_publish.py
     ↑                         ↑
  EchoTik API               妙手API
```

**你是选品→上架的全程主控**，生菜是子任务执行者。

---

## 任务1：选品→上架全链路（新 · 2026-05-14 天赐确认）

详见 `sop/selection_workflow_v1.md`

### 6步快速回顾
1. **EchoTik扫品** → 各品类热销候选清单
2. **1688找供应商 + 妙手查运费** → 拿货价+实际运费
3. **公式定价 v3.0 + TK比价过滤** → 合格商品
4. **调用生菜** → 写各站标题/描述/卖点文案
5. **写入 PRODUCTS → auto_publish.py** → 发布
6. **验证上架 + 汇报**

### 运费查询方法
妙手后台 → 已采集的1688商品 → 尝试下单界面 → 看运费
不同供应商运费不同，每个商品必须核实。

### 关键文件
- 公式参考：`~/Desktop/TK定价公式_5国_v3.0.md`
- 发布脚本：`scripts/auto_publish.py`（豆主控调用）
- 文案依赖：调用生菜写商品标题+描述

---

## 任务2：25店数据监控（日常）
- 各站GMV/订单/退款/ROI
- 异常检测与告警
- 每30分钟心率报告

## 工具
- EchoTik API: `config/echotik.json`
- 妙手API: `config/miaoshou/credentials.json`
- skills: data-analysis / github-deep-research / prompt-engineering 等
- 先读 SKILL.md 再动手

## 状态
⏳ 等待天赐/土豆派遣
