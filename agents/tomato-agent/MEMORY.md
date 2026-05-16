# MEMORY.md - 长期记忆

**最后整理**：2026-05-11 03:43
**整理人**：土豆 🥔
**策略**：只保留核心配置+原则，历史归档到 daily memory 文件

---

## 核心原则（8条铁律）

> **能用AI的绝不雇人** | **能自动化的绝不手动** | **能复用的绝不重做**
> **先跑通0→1，再放大** | **数据驱动，快速迭代**
> **任务完成必须清理环境**
> **绝对服从命令：100%按指令执行，不擅自做超出范围的操作**
> **天赐要的是正确的结果，不是快速但错误的结果。宁可多花时间查文档/确认，也不凭感觉编**
> **先审查（审查文档/逻辑/安全），再优化（优化代码/流程/质量），最后上线（安装/部署/交付）**
> **MEMORY.md永不清空/永不截断/永不删除内容（死规则）**
> **框架铁律：每次派遣必须走 hermes_engine，禁止裸跑脚本**

**商业模式**：不碰货·不压货·不建仓·全面轻资产·只做渠道曝光+销售+一键代发

---

## 🔑 API配置速查

### 通义千问 Coding Plan（主用）
- Base URL: `https://coding.dashscope.aliyuncs.com/v1`
- API Key: `sk-sp-905c3260217342fb85c23b99cc756a63`
- 支持多模态(图像): qwen3.5-plus, kimi-k2.5
- 额度: 6K次/5h, 45K/周, 90K/月
- ⚠️ 仅交互式场景，禁止API批量调用

### 火山方舟 Coding Plan（备用）
- 走 `/api/coding/v3` 路径抵扣套餐，禁止用 `/api/v3`
- 模型: doubao-seed-2.0-code/pro/lite, kimi-k2.5, deepseek-v3.2

### EchoTik API
- Base URL: `https://open.echotik.live/api/v3`，Basic Auth

### 图像识别
- imageModel: `qwen/qwen3.5-plus`（通千 Coding Plan 免费额度内）
- 主聊天模型: `deepseek-v4-flash`（纯文本，不切换）

---

## 🏗️ EvoMap 7节点（2026-05-11 全新注册）

| 节点 | Node ID | Claim |
|------|---------|-------|
| 🥔 土豆·统筹 | `tudou-commander-001` | YXVG-HTJZ |
| 🍅 番茄·选品 | `tomato-selection-001` | EEPZ-LRPK |
| 🥬 生菜·文案 | `lettuce-copy-001` | ZQUD-GDQJ |
| 🌽 玉米·视频 | `corn-video-001` | 8FBW-EWW4 |
| 🥕 萝卜·直播 | `carrot-livestream-001` | HX6Q-ZPWT |
| 🥒 苦瓜·风控 | `bittergourd-risk-001` | JHWD-5VT8 |
| 🫘 豌豆·数据 | `pea-data-001` | DWQM-V5E6 |

- 心跳: 5min (`POST /a2a/heartbeat`)
- Node Secret 已存本地

---

## 🛠️ 核心脚本速查

| 脚本 | 功能 |
|------|------|
| `scripts/video_prep.py` | ffmpeg抽帧+提音频（纯本地） |
| `scripts/pipeline_multi_agent.py` | 多Agent管线编排 |
| `agents/corn-agent/scripts/pipeline_video.py` | 5国视频剪辑管线 V8（全本地ffmpeg） |
| `scripts/video_anti_duplication_sop.md` | 12维防重参数 |
| `scripts/bgm_downloader.py` | EchoTik API BGM下载 |
| `scripts/hermes_memory_extract.py` | 记忆提取引擎 |
| `scripts/run_selection_with_suppliers.py` | 选品+1688供应商 |
| `skills/faster-whisper/` | 本地语音转写(large-v3) |

---

## 🎬 视频管线铁律（V8固化版 2026-05-13）

- **脚本**: `agents/corn-agent/scripts/pipeline_video.py`（symlink: `scripts/pipeline_video.py`）
- **调用**: `hermes_engine.py run --subtasks '["video"]'` → 自动扫描 ~/Desktop/源视频/ 全部处理
- **手动**: `python3 pipeline_video.py --input xxx.mp4 --product 产品名`
- **管线**: 横→竖自动检测（横屏自动scale+crop转1080×1920）→ Edge TTS 6国配音 → BGM库匹配 → PIL字幕叠加(58pt) → 20维防重混剪
- **源视频 → 6国本地ffmpeg混剪**，禁止调用任何外部视频API
- **已废除**: video_pipeline_v2.py（简创AIGC）、computer-use-capcut（CapCut桌面）
- 配音话术: 口语化·自然·无营销引导词·每产品不重复
- 10秒结构: [0-3s]痛点 → [3-7s]功能 → [7-10s]自然夸赞
- 输出: ~/Desktop/已处理TK视频_v8/
- **Seedance 2.0 15秒适配**（2026-05-13 16:45固）: 上采样720p→1080p(lanczos)，TTS 5行文案适配15s，自动音效+背景音
- **生菜Seedance提示词生成**：`copy_engine.py --product X --seedance 品类` → 商品统一性强制+15秒分镜+≤3500字符

---

## 💰 定价公式 v1.0（2026-05-13 天赐口述固化）

**售价 = (1688拿货价P + 3.5元国内运费) ÷ 国家分母 → 保证35%纯利**

| 国家 | 综合扣点 | 分母 |
|:---|:---:|:---:|
| 🇹🇭 泰 | 20% | 0.40 |
| 🇲🇾 马 | 23% | 0.37 |
| 🇵🇭 菲 | 27% | 0.33 |
| 🇸🇬 新 | 17% | 0.43 |
| 🇻🇳 越 | 26% | 0.34 |

- 国际运费买家全出，不摊成本
- 综合扣点=类目佣金+支付手续费+VAT
- 5%隐性损耗(汇率/丢件/售后)已内嵌分母
- 国内运费500g内固定¥3.5（供应商已确认, 2026-05-13更新）
- ⚠️ **定价规则 v2.0**：售价=比TK同商品实际售价低8% → 必须在±10%区间内（低于10%=恶意竞争下架）
- 约束：公式价(35%纯利) ≤ 目标售价(TK×0.92) → 产品才可做
- 参考: `~/Desktop/TK定价公式_5国.md` `~/Desktop/TOP20_五国精确定价_公式版.md`

## 🏪 10店映射（2026-05-14 天赐绑定）

| 品类 | 品牌 | 妙手ID | 站点 | TK原生ID |
|:---|:---|:---|:---|:---|
| 🎨 美妆工具 | Bloom Lane | 14681328 | 🇻🇳 VN | 8666980588878595560 |
| 🎨 美妆工具 | Bloom Lane | 14772485 | 🇲🇾 MY | 8666979854416381416 |
| 🏠 家居用品 | Daily Home | 15471357 | 🇹🇭 TH | - |
| 🏠 家居用品 | Daily Home | 15471249 | 🇲🇾 MY | 8670392346011469622 |
| 🏠 家居用品 | Daily Home | 15471504 | 🇻🇳 VN | 8670392651823744822 |
| 🏠 家居用品 | Daily Home | 15471552 | 🇸🇬 SG | 8670392651823810358 |
| 🍳 厨房用品 | Smart Kitchen Life | 15470949 | 🇹🇭 TH | 8670695568808772971 |
| 🍳 厨房用品 | Smart Kitchen Life | 15471582 | 🇲🇾 MY | 8670696990902551915 |
| 🍳 厨房用品 | Smart Kitchen Life | 15470863 | 🇻🇳 VN | 8670695568808707435 |
| 🍳 厨房用品 | Smart Kitchen Life | 15470918 | 🇸🇬 SG | 7494637719983064427 |

### 发布规则
- 商品品类 → 匹配对应品牌店铺 → 只发该品类店铺
- 美妆工具 → Bloom Lane (VN+MY)
- 家居用品 → Daily Home (TH+MY+VN+SG)
- 厨房用品 → Smart Kitchen Life (TH+MY+VN+SG)
- ⚠️ PH站暂无对应店铺

## 📋 业务现状

- TK东南亚美妆/家居/厨房 3品类10店
- 一店一IP + 指纹浏览器
- 15天0→1出单计划
- 客服: 多客Duoke AI全自动
- 风控: 苦瓜24h巡检，无阈值
- 天赐电话: 1399955506667

---

## 🏭 核心工作流（2026-05-13 框架固化版）

### 框架调用方式（强制）
```
hermes_engine.py 路径: ~/.openclaw/workspace/scripts/hermes_engine.py
FRAMEWORK.md 路径:   ~/.openclaw/workspace/FRAMEWORK.md

单伙伴任务:  python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --subtasks '["booster"]'
多伙伴并行:  python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --subtasks '["booster","copy","video"]'
全链路:      python3 ~/.openclaw/workspace/scripts/hermes_engine.py run --workflow deerflow
```

### 伙伴脚本映射
| 伙伴 | 子任务名 | 脚本 | 行数 |
|:---|:---|:---|:---:|
| 🍅 番茄·选品 | `booster` | booster_matrix.py | 111 |
| 🥬 生菜·文案 | `copy` | copy_engine.py | 133 |
| 🌽 玉米·视频 | `video` | pipeline_video.py (V8全本地) | ~540 |
| 🥕 萝卜·配音 | `tts` | qwen_tts_engine.py | - |
| 🥒 苦瓜·风控 | `risk` | risk_controller.py | 124 |
| 🫘 豌豆·数据 | `data` | data_monitor.py | 130 |

### 端到端测试结果（2026-05-13 09:11）
- ✅ `hermes_engine.py run --workflow deerflow` → 7步完成，0错误
- ✅ Hermes→DeerFlow subprocess 调用成功
- ✅ langgraph 已装到 DeerFlow venv
- ✅ 6伙伴 SOUL.md 框架绑定已固化

## 🛠️ 6伙伴技能部署（2026-05-11晚完成）

每个伙伴有自己的skills目录+TOOLS.md清单+SOUL.md强制指令：
"每次执行任务前，必须先读取对应SKILL.md获取最佳实践，再用自己的技能开展工作。严禁跳过技能直接输出。"

| 伙伴 | 技能数量 | 核心技能 |
|------|---------|---------|
| 🍅 番茄·选品 | 6 | consulting-analysis, data-analysis, 3×prompt, self-improving |
| 🥬 生菜·文案 | 4 | 3×prompt工程, self-improving |
| 🌽 玉米·视频 | 16 | ai-video-generation, seedance20-prompt, storyboard-creation, manga-style-video等 (V8全本地管线) |
| 🥒 苦瓜·风控 | 5 | skill-vetter, 3×prompt, self-improving |
| 🥕 萝卜·配音 | 6 | faster-whisper, audio-studio, 3×prompt, self-improving |
| 🫘 豌豆·数据 | 6 | data-analysis, github-deep-research, 3×prompt, self-improving |

### 指挥官原则
- **土豆不帮伙伴调用skill** — 让他们各自装好并自动运用
- 伙伴接到任务 → 自主读SKILL.md → 用自己技能干活
- skills文件、TOOLS.md、SOUL.md都已配好

---

## 🎯 桌面产出速查

| 文件 | 说明 |
|------|------|
| `番茄选品报告_含供应商_v2.md` | 30件精选+1688供应商 |
| `升级项_01_图像感知打通.md` | imageModel配置+sharp修复 |
| `升级项_02_video_prep.md` | ffmpeg预处理脚本 |
| `升级项_03_faster_whisper.md` | 语音转写skill |
| `升级项_04_视频感知方案_Agent编排.md` | Agent编排架构 |
| `BGM库/echotik_songs.json` | 50首东南亚热门BGM |

---

## ⚡ 记忆策略（2026-05-12更新）

- **MEMORY.md**：核心配置+原则+长期记忆，自然增长，**永不清空/永不截断/永不删除内容**（死规则）
- **memory/YYYY-MM-DD.md**：每日日志，保留近5天
- **自动存档**：`cron-memory-archive-30min` 每30分钟自动存档
- 天赐提过的每个话题 → `memory_search` 自动调取
- ⚠️ 之前<12K限制是记忆融合引擎的 `memory_hot_index.md`（24K热索引）造成的，引擎已卸载，限制已解除

## 🔴 派遣铁律 v2.0（2026-05-15 03:43 天赐亲令）
- **唯一通道**: hermes_engine，无例外
- **sessions_spawn**: 已废除死刑，任何场景不可用
- **土豆禁止**: 自己写脚本/生成prompt/做图片处理/执行伙伴任务
- **更新文件**: HEARTBEAT.md v5.2 / WORKFLOW_LOCK.md #8 v2.0 / SOUL.md
