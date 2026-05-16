# 🔒 WORKFLOW_LOCK.md — 工作流契约锁

> ⚠️ 每次派遣伙伴前，必须读取本文件确认已锁定的版本和格式。
> ⛔ 伙伴不得自行修改已锁定的工作流。修改须经天赐+土豆双重确认。

---

## 锁定规则

| 状态 | 含义 |
|:----:|:-----|
| 🔒 LOCKED | 最终确认版，任何人不得修改，直接使用 |
| 🔄 ACTIVE | 进行中，可继续优化 |
| 📋 TEMPLATE | 模板格式锁定，内容按需填充 |

---

## 📋 已锁定工作流

### 1. 视频Prompt格式 🔒 LOCKED
| 项目 | 值 |
|:-----|:-----|
| **版本** | V5 |
| **模板文件** | `~/Desktop/视屏生成prompt/top20_v5_prompts.md` |
| **锁定日期** | 2026-05-13 |
| **目标平台** | Runway Gen-4 / Seedance 2.0 |
| **关键参数** | |

**强制8要素（不可删减）**:
1. Technical（技术描述）
2. Product（产品描述）
3. Character（人物/手部描述）
4. Scene（场景描述）
5. Timeline（时序分镜：0-3s/3-7s/7-10s/10-15s）
6. Camera+Lighting（镜头+灯光）
7. Negative（禁止项）
8. Color Palette（色彩方案hex色码）

**V5三大硬指标**:
- ⏱️ 15秒视频（非10秒）⚠️ Timeline分镜必须真正分布到15秒：0-3s/3-7s/7-10s/10-15s，不可只改声明不改内容
- 🔒 强制商品一致性：【PRODUCT CONSISTENCY RULE - CRITICAL】英文大写醒目
- 📏 字符数3400-3500区间，<3300为不合格

**品类区分**:
- 🪞 美妆工具 → 真人出镜（20岁当地女生）
- 🏠 家居日用品 → 无面部（只拍手+场景效果）
- 🍳 厨房用品 → 只拍手+食物（无面部）

**5种模板变体（交错使用，相邻产品不重复）**:
- A: 特写开场·结构型
- B: 场景引入·问题对比型
- C: 功能直打型
- D: 多角度环绕展示型
- E: 使用中截入型

---

### 2. 玉米视频剪辑管线 🔒 LOCKED
| 项目 | 值 |
|:-----|:-----|
| **版本** | V8 |
| **脚本** | `agents/corn-agent/scripts/pipeline_video.py` |
| **锁定日期** | 2026-05-13 |
| **管线** | 横→竖自动检测 → Edge TTS 6国配音 → BGM库匹配 → PIL字幕叠加(58pt) → 20维防重混剪 |

**禁止**:
- ❌ 调用外部视频API
- ❌ 使用CapCut桌面版
- ❌ 重写剪辑管线

---

### 3. 定价公式 🔒 LOCKED
| 项目 | 值 |
|:-----|:-----|
| **版本** | v3.0 |
| **公式** | `售价 = (1688拿货价 + 供应商实际运费) ÷ 国家分母` |
| **TK比价** | 公式售价 ≤ TK同类均价 × 0.92 → 通过 |
| **文件** | `~/Desktop/TK定价公式_5国_v3.0.md` |

---

### 4. 🫘→🥬→🥒→auto_publish 产研链路 🔒 LOCKED
| 项目 | 值 |
|:-----|:-----|
| **版本** | v2.0 |
| **锁定日期** | 2026-05-14(凌晨固化) |
| **文件** | `pea-agent/sop/selection_workflow_v1.md` |

**6步流程（不可打乱）**：
```
天赐/土豆 → 🫘豌豆(主控)
  ├─ 1. EchoTik扫品 → 提取TOP排行
  ├─ 2. 妙手查1688运费（实际运费非固定¥3.5）
  ├─ 3. 定价v3.0 + TK比价92%过滤
  ├─ 4. 调→ 🥬生菜(写各站标题/描述/卖点)
  ├─ 5. 调→ 🥒苦瓜(违禁词审核)
  └─ 6. 写入PRODUCTS → auto_publish.py上架验证
```

**禁止**：
- ❌ 玉米/其他伙伴做上架 → 上架专属auto_publish.py
- ❌ 跳过生菜直接上架 → 标题描述必须生菜写
- ❌ 跳过苦瓜审核 → 违禁词370词5国审核必做
- ❌ 土豆手动调妙手API → 统一走auto_publish.py

### 5. 妙手上架脚本 🔒 LOCKED
| 项目 | 值 |
|:-----|:-----|
| **脚本** | `scripts/auto_publish.py` (v2.3 FINAL) |
| **流程** | `add_common_collect_box_detail` → `claimed` → `claim_to_shop` → `save_move_collect_task` |

---

### 6. 禁止词审核 🔒 LOCKED
| 项目 | 值 |
|:-----|:-----|
| **词库** | `bittergourd-agent/sop/违禁词库_v2.0.md` (510词/5国) |
| **流程** | 生菜输出 → 苦瓜本地审核 → 妙手平台终审 |

---

### 7. 10店映射 🔒 LOCKED
| 品类 | 品牌 | 妙手ID | 站点 |
|:-----|:-----|:------|:-----|
| 🎨 美妆工具 | Bloom Lane | 14681328 | 🇻🇳 VN |
| 🎨 美妆工具 | Bloom Lane | 14772485 | 🇲🇾 MY |
| 🏠 家居用品 | Daily Home | 15471357 | 🇹🇭 TH |
| 🏠 家居用品 | Daily Home | 15471249 | 🇲🇾 MY |
| 🏠 家居用品 | Daily Home | 15471504 | 🇻🇳 VN |
| 🏠 家居用品 | Daily Home | 15471552 | 🇸🇬 SG |
| 🍳 厨房用品 | Smart Kitchen Life | 15470949 | 🇹🇭 TH |
| 🍳 厨房用品 | Smart Kitchen Life | 15471582 | 🇲🇾 MY |
| 🍳 厨房用品 | Smart Kitchen Life | 15470863 | 🇻🇳 VN |
| 🍳 厨房用品 | Smart Kitchen Life | 15470918 | 🇸🇬 SG |

---

### 8. 🔴 派遣铁律：唯一通道 Hermes 引擎 🔒 LOCKED v2.0
| 项目 | 值 |
|:-----|:-----|
| **版本** | v2.0 (sessions_spawn已废除) |
| **锁定日期** | 2026-05-15 03:43 |
| **引擎路径** | `~/workspace/scripts/hermes_engine.py` |

**唯一派遣方式（无例外）**：
```bash
# 单伙伴所有任务
python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --partner <key>

# 多伙伴并行
python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --subtasks '["booster","copy","video"]'

# 全链路
python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --workflow deerflow
```

**强制校验（每次派遣前）**：
```
□ 是否走hermes_engine？→ 否 → 停止，改用hermes_engine ❌
□ 伙伴SOUL.md是否有hermes_engine强制条款？→ 6/6全部有 ✅
□ 是否裸跑sessions_spawn？→ 死刑，绝不使用 🔴
□ 是否自己动手写脚本？→ 是 → 停止，让伙伴做 🔴
```

**禁止**：
- 🔴 sessions_spawn — 已废除，死刑，任何场景都不可用
- ❌ 建临时新子代理（没有工作流的空壳agent）
- ❌ 绕过hermes_engine直接调伙伴脚本
- ❌ 土豆自己执行伙伴任务（写脚本/生成文案/做Prompt）

**无例外。所有任务走hermes_engine。**

## ⚡ 派遣前检查清单

每次派遣伙伴前，土豆必须检查：
```
□ 该任务是否已有锁定工作流？→ 读 WORKFLOW_LOCK.md
□ 该任务是否已有缓存结果？→ memory_search 查询
□ 伙伴是否获得了正确的模板/格式？→ 附带锁定版本
□ 伙伴的 SOUL.md 是否要求先读 WORKFLOW_LOCK？
□ 🔴 是否走hermes_engine？→ 唯一通道，无例外
□ 🔴 是否建临时新子代理？→ 禁止，只用6伙伴agentId
□ 🔴 是否自己动手？→ 禁止，让伙伴做
```

---

## 📝 变更日志

| 日期 | 变更 | 锁定项 |
|:-----|:-----|:-----|
| 2026-05-15 03:43 | 🔴 派遣铁律v2.0 | sessions_spawn彻底废除，唯一通道hermes_engine |
| 2026-05-14 22:37 | 🔒 新增派遣铁律 | 必须通过hermes_engine，禁止sessions_spawn裸跑 |
| 2026-05-14 20:47 | 🔒 新增产研链路 | 🫘→🥬→🥒→auto_publish 6步工作流 |
| 2026-05-14 | 创建契约锁 | V5 Prompt格式/玉米V8管线/定价v3.0/妙手上架/违禁词/10店 |
| 2026-05-13 | V5 Prompt最终确认 | 15秒+商品一致性+3400-3500字符 |
| 2026-05-13 | 玉米V8固化 | 全本地ffmpeg管线 |
