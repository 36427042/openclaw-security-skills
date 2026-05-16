# ✅ 正确剪辑SOP v2 — 微纤维抹布产品视频

> **基于**: 天赐源视频 `source_video_01.mp4`（540×960, 10s, 微纤维抹布擦拭演示）
> **版本**: v2 — 彻底重写，抛弃旧方案
> **时间**: 2026-05-11 22:49 GMT+8
> **责任人**: 🌽玉米

---

## 一、📹 源视频分析

| 项目 | 值 |
|------|-----|
| 分辨率 | 540×960（非1080p，需考虑画质） |
| 时长 | 10.08s |
| 帧率 | 24fps（242帧） |
| 产品 | 灰色微纤维抹布（高吸水性清洁布） |
| 拍摄方式 | 手持POV，第一人称桌面擦拭 |
| 内容 | ① 擦拭湿桌面（瞬间吸干） → ② 擦拭镜子（玻璃无痕） |
| 已有文字 | "1 lap = kering"（印尼语：一次擦拭就干） |
| 画质 | 良好，自然光+厨房台面场景，现代简洁风格 |

### 核心优势（保留）
- ✅ 已经是**使用演示（usage demo）**而非静态展示
- ✅ "1擦即干"的痛点解决非常直观
- ✅ 白色厨房背景干净、有质感
- ✅ 手持POV风格符合TikTok/Shopee短视频审美

### 核心短板（需修复）
- ❌ 分辨率540p略低 → 需轻度AI升频或保持原分辨率避免缩小显糊
- ❌ 无配音/旁白 → 需加TTS讲解
- ❌ 无BGM → 需加背景音乐
- ❌ 无文字强调卖点 → 需加高亮文字
- ❌ 缺乏钩子开头的节奏变化 → 需速度变速+文字钩子

---

## 二、🎯 正确剪辑理念（vs 旧方案错误）

### ❌ 旧方案错误
| 错误 | 问题 |
|------|------|
| 20维防重参数矩阵 | 极度过度工程化，参数间互相冲突，实际不可用 |
| FFmpeg批量跑参数 | 色彩/伽马/噪点叠加后画质严重下降，破坏视频质量 |
| 一次性处理15产品×6国 | 不切实际的流水线思维，产品不同需不同处理 |
| 把所有剪辑交给自动化 | 视频质量无法保证，缺少人工判断 |
| 忽视源视频分辨率限制 | 540p不建议做缩放裁切，画质会进一步降低 |

### ✅ 正确方案
1. **每产品单独处理** — 质量优先，不搞流水线
2. **保留源视频画质** — 不裁切/不缩放，仅做微调
3. **强化内容而非参数** — 加点文字/配音/BGM/变速即可出效果
4. **5国版本差异化 = 文案+BGM替换** — 不要动视频底层参数
5. **先跑通1个版本，再批量** — 验证后再扩展

---

## 三、📋 正确剪辑流程（10步完成）

### Step 1: 提取源视频关键帧（已做）
```bash
ffmpeg -i source_video_01.mp4 -vf "fps=1/2" output/frames_tmp/frame_%d.jpg
```
→ 已验证 ✓ 第1帧桌面有水→第4帧干净→第5帧擦镜子

### Step 2: 分析节奏点（人工判断）
| 时间 | 内容 | 剪辑策略 |
|:----:|:-----|:---------|
| 0-1s | 手拿抹布准备擦 | 🎣 钩子：慢速开始+文字标题 |
| 1-4s | 擦拭桌面（吸水效果） | ⚡ 加速1.2x → 瞬间吸干效果 |
| 4-5s | 桌面已干（效果展示） | 🛑 稍慢0.9x → 强调干净 |
| 5-8s | 切换擦镜子 | 🎬 正常速度 |
| 8-10s | 镜子干净 / 收尾 | 📌 文字收尾+产品信息 |

### Step 3: 首帧/尾帧视觉强化（可选AI生成）
如使用Seedance/即梦AI生成增强效果：
- 首帧钩子：湿桌面特写 + 产品入画
- 末帧：干净镜面反射 + "1擦即干" 大字

详见下方的[AI增强方案](#六-ai-视频增强方案可选)。

### Step 4: 编写5国脚本

| 国家 | 语言 | 脚本 (每国4句) |
|:----:|:----:|:--------------|
| 🇹🇭 TH | ไทย | ① ผ้าไมโครไฟเบอร์ ผืนเดียวซับทั้งบ้าน<br>② เปียกแค่ไหนก็แห้งในพริบตา<br>③ ใช้ได้ทั้งโต๊ะ กระจก จานชาม<br>④ ซื้อครั้งเดียว ใช้ได้เป็นปี |
| 🇲🇾 MY | Melayu | ① Kain microfiber ni, satu lap terus kering<br>② Basah macam mana pun terus hilang<br>③ Boleh guna untuk meja, cermin, pinggan<br>④ Satu helai tahan beribu-ribu lap |
| 🇻🇳 VN | Tiếng Việt | ① Khăn sợi nhỏ này, lau một phát là khô<br>② Nước nhiều cỡ nào cũng hết ngay<br>③ Dùng được bàn, gương, bát đĩa<br>④ Một cái dùng cả năm không hỏng |
| 🇵🇭 PH | English/Filipino | ① This microfiber cloth, one wipe and it's dry<br>② Soaks up everything instantly<br>③ Great for tables, mirrors, dishes<br>④ One cloth lasts a thousand wipes |
| 🇸🇬 SG | English | ① One wipe. That's all it takes with this microfiber cloth<br>② Instant absorption, zero streaks<br>③ Versatile: countertops, mirrors, dishes<br>④ Premium quality that lasts wash after wash |

### Step 5: 生成TTS配音
```bash
# TH
edge-tts --voice th-TH-PremwadeeNeural --text "..." --rate +15% --pitch +8Hz -o ~/Desktop/配音输出/抹布_TH.mp3

# MY
edge-tts --voice ms-MY-OsmanNeural --text "..." --rate +15% --pitch +8Hz -o ~/Desktop/配音输出/抹布_MY.mp3

# VN
edge-tts --voice vi-VN-HoaiMyNeural --text "..." --rate +15% --pitch +8Hz -o ~/Desktop/配音输出/抹布_VN.mp3

# PH
edge-tts --voice en-PH-JamesNeural --text "..." --rate +10% --pitch +5Hz -o ~/Desktop/配音输出/抹布_PH.mp3

# SG
edge-tts --voice en-SG-LunaNeural --text "..." --rate +10% --pitch +5Hz -o ~/Desktop/配音输出/抹布_SG.mp3
```

### Step 6: 准备BGM（每国不同）
使用已下载好的BGM高潮段：
```
~/Desktop/配音输出/bgm_h_TH.aac  → TH版
~/Desktop/配音输出/bgm_h_MY.aac  → MY版
~/Desktop/配音输出/bgm_h_VN.aac  → VN版
~/Desktop/配音输出/bgm_h_PH.aac  → PH版
~/Desktop/配音输出/bgm_h_ID.aac  → ID版（可给SG备用）
~/Desktop/配音输出/bgm_h_CN.aac  → CN版（备用）
```

### Step 7: 合成最终视频（FFmpeg一次性管线）
```python
# 使用composer_final.py的输出管线思路，但简化配置
# 核心：源视频 + TTS + BGM + 速度变速 + 字幕 = 最终视频
```

### Step 8: 5国差异化 = 只换2样
| 版本 | 配音 | BGM | 文字语言 | 文字颜色 |
|:----:|:----:|:---:|:--------:|:--------:|
| TH | 🇹🇭泰语 | bgm_h_TH.aac | 泰文 | 粉红 #FF6B9D |
| MY | 🇲🇾马来语 | bgm_h_MY.aac | 马来文 | 金色 #FFD700 |
| VN | 🇻🇳越南语 | bgm_h_VN.aac | 越南文 | 亮橙 #FF8C00 |
| PH | 🇵🇭菲律英语 | bgm_h_PH.aac | 英文 | 白色 #FFFFFF |
| SG | 🇸🇬新加坡英语 | bgm_h_PH.aac | 英文 | 灰白 #F0F0F0 |

**不做参数差异化（❌ 旧方案错误）！**
- 不调色彩/伽马/噪点 → 保持原视频画质
- 不调速度/亮度 → 只做合理节奏变速
- 不调裁切 → 540p已低，裁切损害更大

### Step 9: 质量验收标准
| 检查项 | 标准 |
|--------|------|
| 画质 | 保持540p原始画质，无明显损失 |
| 配音 | 清晰可辨，语速自然（+15%不赶） |
| BGM | 背景不压人声（TTS×1.4 : BGM×0.25） |
| 字幕 | 逐句同步，无错字 |
| 整体 | "1擦即干"的核心卖点清晰传达 |

### Step 10: 命名规范
```
source_video_01_TH.mp4
source_video_01_MY.mp4
source_video_01_VN.mp4
source_video_01_PH.mp4
source_video_01_SG.mp4
```

---

## 四、🎬 实际生成脚本

见同目录下的 `generate_cloth_video.py`：
```
python3 output/generate_cloth_video.py --country TH
python3 output/generate_cloth_video.py --country MY
...

# 或生成全部5国
python3 output/generate_cloth_video.py --all
```

该脚本使用composer_final.py（已验证可用）的核心逻辑，简化后专为微纤维抹布视频服务。

---

## 五、🔧 备选方案：CapCut手动剪辑

如果自动化脚本遇到问题，采用CapCut手动流程：

1. 源视频拖入时间线
2. 0-1s加文字标题"1擦即干！"
3. 1-4s段加速1.2x（产生瞬间吸干的爽感）
4. 4-5s段减速0.9x（展示洁净效果）
5. 添加配音轨道 → 对齐文字
6. 添加BGM轨道 → 音量-24dB
7. 添加字幕 → 逐句同步
8. 导出1080p → 完成

**单条视频手工约3分钟，5国共需15分钟。**

---

## 六、🤖 AI视频增强方案（可选）

如使用AI生成替代或增强画面（seedance/ai-video-generation）：

### 方案A：首帧+末帧AI替换
生成两张参考图，作为视频首帧和尾帧：

**首帧Prompt（0-2秒钩子画面）：**
```
微距镜头，厨房台面上有大片水渍和水珠，一只手拿着灰色超细纤维抹布从画面右侧入镜，准备擦拭。暖色自然光，画面干净简约，白色瓷砖背景。电影质感，景深浅。
```

**末帧Prompt（最后2秒收尾画面）：**
```
擦干净的镜面反射出明亮的厨房空间，镜面中央弹出一行大字"1擦=即干"，金色粗体字，干净利落。暖色调，柔和光线，高级感。
```

### 方案B：全视频用Seedance重新生成
写完整的Seedance 2.0分镜prompt，用AI生成完整视频（作为备选）。

---

## 七、⚠️ 风险 & 应对

| 风险 | 概率 | 应对 |
|:----|:----:|:-----|
| 540p升频后画质差 | 中 | 保持540p输出，不放缩 |
| TTS配音口音不自然 | 低 | 检查发音，必要时人工重录 |
| BGM版权问题 | 中 | 使用已下载无版权或去水印素材 |
| 自动化脚本异常 | 中 | 回退手动CapCut流程 |
| 视频被TK判重 | 低 | 5国版本只有文案+BGM不同，视频内容相同是合理的（同一产品） |

---

## 八、📈 对比旧方案

| 维度 | ❌ 旧方案（废弃） | ✅ 新方案（v2） |
|:-----|:----------------:|:--------------:|
| 复杂度 | 20维参数矩阵，过度工程化 | 简单5国文案差异化 |
| 画质 | 参数叠加损画质 | 保持原始画质 |
| 可执行性 | 理论方案，实际跑不通 | 已验证的composer_final.py管线 |
| 灵活性 | 硬编码参数 | 按需每产品调整 |
| 批量能力 | 15产品×6国一次性 | 先跑通1个，再批量同类产品 |

---

> **总结**: 不做过度工程化。源视频已好 → 只需要配音+BGM+字幕+节奏微调。
> 5国差异 = 文案+配音+BGM不同，视频主体不动。
