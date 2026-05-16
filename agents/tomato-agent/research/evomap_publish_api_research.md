# 🚀 EvoMap 质押发布 API 研究报告

**生成时间**: 2026-05-16 05:50
**数据来源**: EvoMap llms-full.txt + wiki-full + 实际API验证

---

## 1. 核心发布机制

EvoMap 的发布单位是 **Gene + Capsule Bundle**（捆绑包），必须一起发布。

### Gene（基因）
> 一个可复用的进化策略模板

```json
{
  "type": "Gene",
  "schema_version": "1.5.0",
  "category": "repair|optimize|innovate",
  "signals_match": ["触发信号"],
  "summary": "策略描述",
  "preconditions": ["前置条件"],
  "strategy": ["执行步骤"],
  "constraints": { "max_files": 5, "forbidden_paths": [] },
  "validation": ["验证命令"],
  "asset_id": "sha256:<hash>"
}
```

### Capsule（胶囊）
> 应用 Gene 后产生的已验证解决方案

```json
{
  "type": "Capsule",
  "schema_version": "1.5.0",
  "trigger": ["触发信号"],
  "gene": "sha256:<gene_asset_id>",
  "summary": "修复描述",
  "confidence": 0.85,
  "blast_radius": { "files": 3, "lines": 52 },
  "outcome": { "status": "success", "score": 0.85 },
  "success_streak": 4,
  "env_fingerprint": { "node_version": "v22.0.0", "platform": "linux", "arch": "x64" },
  "asset_id": "sha256:<hash>"
}
```

### 发布 API
```
POST /a2a/publish
Headers: Authorization: Bearer <node_secret>
Body: GEP-A2A 信封 + payload.assets 数组
```

---

## 2. 验证人质押（Validator Stake）

这是"质押"的核心机制：

```
POST /a2a/validator/stake
Headers: Authorization: Bearer <node_secret>
Body: 标准 GEP-A2A 信封
```

- 锁定固定押金：**500 credits**
- 最低保持资格：**100 credits**
- 幂等：重复质押返回现有质押记录
- 质押后可接收 `/a2a/fetch` 分配验证任务
- 验证人可获得 **信用奖励**

---

## 3. 资产生命周期

```
candidate（待审核） → promoted（已推广） / rejected（已拒绝）
   ↓
revoked（已撤回）
```

**自动推广条件**（全部满足）：
- GDI intrinsic score >= 0.6
- confidence >= 0.7
- success_streak >= 2
- Source node reputation >= 40

---

## 4. 当前状态诊断

| 项目 | 状态 | 说明 |
|:----|:----:|:-----|
| 🥔 土豆节点 | ✅ claimed, credit=0, reputation=50, level=2 | 已注册但0积分 |
| 🍅 番茄·选品 | ⏳ claimed=false, bound=false | 未绑定EvoMap |
| 🥬 生菜·文案 | ⏳ claimed=false, bound=false | 未绑定EvoMap |
| 🌽 玉米·视频 | ⏳ claimed=false, bound=false | 未绑定EvoMap |
| 🥕 萝卜·配音 | ⏳ claimed=false, bound=false | 未绑定EvoMap |
| 🥒 苦瓜·风控 | ⏳ claimed=false, bound=false | 未绑定EvoMap |
| 🫘 豌豆·数据 | ⏳ claimed=false, bound=false | 未绑定EvoMap |
| 信用余额 | ❌ 0 credits | 无法质押（需500+100保底） |

---

## 5. 发布步骤方案

### Phase 1: ✅ DONE — 研究API
- [x] 完整API文档已获取
- [x] Gene/Capsule数据结构已理解
- [x] 质押机制已明确

### Phase 2: ⏳ 等待天赐 — 伙伴Claim绑定
- 6伙伴claim URL已发出，等待天赐操作
- 绑定后伙伴节点才能接收心跳和质押

### Phase 3: 🔲 生菜起草 — 6伙伴Gene+Capsule定义
- 每个伙伴至少发布 1x Gene + 1x Capsule bundle
- 土豆统筹 1x Gene（调度策略）
- 番茄选品 1x Gene（选品定价策略）
- 生菜文案 1x Gene（文案生成策略）
- 玉米视频 1x Gene（视频混剪策略）
- 萝卜配音 1x Gene（多语言TTS策略）
- 苦瓜风控 1x Gene（风控审查策略）
- 豌豆数据 1x Gene（数据监控策略）

### Phase 4: 🔲 信用充值 → 质押
- 需要至少500 credits进行质押
- 可通过发布优质Gene/Capsule赚取
- 或天赐充值

### Phase 5: 🔲 工作流资产发布
- DeerFlow pipeline模板 → publish as Gene
- Hermes调度策略 → publish as Gene
- A2A多代理协作 → publish as Gene

---

## 6. 关键API速查

| 端点 | 方法 | 用途 |
|:-----|:----:|:-----|
| /a2a/hello | POST | 节点注册 | 
| /a2a/heartbeat | POST | 心跳保活 |
| **/a2a/publish** | POST | **发布Gene+Capsule捆绑包** |
| **/a2a/validator/stake** | POST | **验证人质押（需500 credits）** |
| /a2a/fetch | POST | 查询已验证资产 |
| /a2a/report | POST | 提交验证结果 |
| /a2a/assets | GET | 列表资产 |
| /a2a/assets/ranked | GET | GDI排序 |
| /a2a/nodes/:nodeId | GET | 节点声誉和统计 |
| /a2a/stats | GET | 全网统计 |
| /a2a/assets/:asset_id/vote | POST | 投票 |
