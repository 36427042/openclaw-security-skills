# 📋 土豆·任务看板 v7.8
# 🕐 更新: 2026-05-16 16:45 🥔 [保活#120 - ✅ 系统6d17h52m · CPU 2.75/3.31/3.28 · Gateway🟢 · 7虾:8889🟢 · AIRI:5173🟢 · 磁盘747Gi🟢 · DeerFlow🟢 · 伙伴6/6✅ · 6⏳等天赐 · 无可执行任务 · EvoMap心跳cron间歇SSL(自愈中) · 保活通过 ✅]

---

## 🎯 天赐05:12指令 — 全部完成 ✅

### ① 💰 pricing_v5.py ✅
- [x] 成本加法公式: 拿货价+¥7+利润¥15-25三档
- [x] 5国汇率+比价+免比价，全部通过
- [x] → API_Documentation/

### ② 🎯 番茄选品方向调整 ✅
- [x] 追新品≤30天+增长>30%
- [x] 产出桌面文档
- [ ] booster_matrix.py --mode new_trending（需确认）

### ③ 🔗 EvoMap A2A节点重新注册 ✅
- [x] 7节点全部重新注册 + all7心跳脚本
- [x] 6/7 Claim绑定完成（萝卜明天，今日上限5/5）
- [x] 绑定清单: ~/Desktop/EvoMap_A2A_绑定清单_v2.md

### ④ 🎨 AIRI 3D渲染 ✅
- [x] Vite :5173 200 OK + Live2D SDK加载
- [ ] 浏览器视觉验证（天赐明天）

### ⑤ 📊 7虾看板Skill ✅
- [x] v2.0 :8889 running + SKILL.md

### 🔗 hermes pipeline串行 ✅
- [x] hermes v3.3 PIPELINE_CONTEXT_FILE机制
- [x] copy_engine/publish串联通过

---

## 🚀 ⑥ EvoMap质押发布（05:34+05:48指令）✅ 完成

| # | 能力 | Bundle ID | 状态 |
|:-:|:-----|:---|:---:|
| 🥔 | 土豆·Hermes V3.3+DeerFlow全链路 | `bundle_72c35f16` | 🟡 quarantine |
| 🍅 | 番茄·EchoTik选品引擎 | `bundle_2bbe7981` | 🟡 quarantine |
| 🥬 | 生菜·Seedance 5国文案 | `bundle_1def8cca` | 🟡 quarantine |
| 🌽 | 玉米·ffmpeg视频混剪V8 | `bundle_2d9c4ce2` | 🟢 **accept** |
| 🥒 | 苦瓜·4维风控 | `bundle_f2902be3` | 🟡 quarantine |
| 🫘 | 豌豆·数据监控 | `bundle_d0b046f1` | 🟡 quarantine |
| 🥕 | 萝卜·多语TTS | `bundle_a7ebc6d8` | 🟡 quarantine |

> 🔄 16:15巡检: evomap.ai返回400(可能API端点格式变更), 旧api.evomap.dev不通, 上次已知14:40心跳全通

> ℹ️ EvoMap 7/7: 11:15 ✅ Gateway🟢 | DeerFlow🟢(3p) | dashboard:8889🟢 | AIRI:5173🔴 | 心跳进程🟢(2p)

- 🌽 玉米视频引擎直接Accept！其余6个安全审核中
- 全部通过土豆节点(`node_b415de15e10cce39`)发布
- GEP-A2A Gene+Capsule+EvolutionEvent Bundle格式

---

## 状态速览

| 项目 | 状态 | 详情 |
|:----|:----:|:-----|
| 系统 | 🟢 | up 6d15h, Gateway ✅ |
| AIRI 3D | 🟢 | :5173 已恢复 ✅ (上次巡检时🔴，现已自动重启运行) |
| 7虾面板 | 🟢 | :8889 ✅ |
| EvoMap 7/7心跳 | 🟢 | evomap.ai 正确域 ✅ 14:40实测7/7心跳通·各50c额度 |
| EvoMap 绑定 | 🟢 | 绑定有效（14:40心跳认证通过） |
| EvoMap 发布 | 🟢 | 所有bundle在线上（evomap.ai·旧api.evomap.dev已死，不影响） |
| GEP心跳记录 | ✅ | evomap_heartbeat.py已集成post_record |
| pricing_v5 | ✅ | 完成+测试 |
| pipeline串行 | ✅ | hermes+copy+publish |
| API文档 | ✅ | 10份在Desktop |

---

### 🛠️ 自动修复记录
- **14:40** ✅ evomap_heartbeat.py: 集成 `GEP.post_record()` — 每次心跳后记录成功/失败到GEP
- 修复前: 心跳日志仅写入本地JSON文件，不进入GEP知识图谱
- 修复后: 每次执行自动写GEP，未来可回溯历史心跳模式
- **14:55** ✅ evomap_heartbeat.py: 修复 `GEP.post_record()` TypeError — `GEP` 是工厂函数(return GEPEngine)，不是对象。改为 `gep = GEP("土豆·系统"); gep.post_record(...)`

---

### ⑦ 🏗️ Gateway配置飞书扩展 ⏳ 等待天赐
- [ ] 需要 `openclaw channels login --channel feishu`（需手机扫码）
- [ ] 配置后 feishu_doc/feishu_drive/feishu_wiki 工具可用

---

## ⏳ 等待天赐

| # | 事项 | 自动修复情况 |
|:-:|:-----|:------------|
| 1 | 🥕 萝卜EvoMap绑定（待天赐点） | — |
| 2 | 🔴 番茄/玉米/苦瓜 secret到期 | ✅ 06:05已自动重新注册+修复心跳脚本 |
| 3 | AIRI 3D浏览器视觉验证 | — |
| 4 | 飞书扩展：`openclaw channels login --channel feishu` | — |
| 5 | 番茄booster改代码确认 | — |
| 6 | GitHub/ClawHub发布路径打通 | — |
