# 🎬 CAPCUT_SCRIPT_SOP.md — 玉米视频管线操作手册

## ⚠️ 铁律（2026-05-11 天赐确认，不可违背）

**源视频只需要生成1个（中文版），其余5国全部走本地混剪**
- ❌ 禁止调用任何API（即梦/简创/火山/三方视频生成）
- ❌ 禁止上传到云渲染/云处理平台
- ✅ 唯一外部依赖：edge-tts（语音合成，音频文件存本地）
- ✅ 全链路纯本地：ffmpeg + PIL + edge-tts

**违反铁律的脚本已全部移入 scripts/archive/ 废弃区**

---

## 一句话用法

只要改 `composer_final.py` **最上面3个变量**就能换产品/文案/BGM：

```python
VIDEO_SRC = "..."   # 行11 - 换产品视频
BGM_MAP = {...}     # 行40 - 换BGM（每国一首）
SCRIPTS = {...}     # 行55 - 换文案（每国一句）
```

## 执行

```bash
cd ~/.openclaw/workspace/agents/tomato-agent
python3 scripts/composer_final.py
```

## 详细说明

### 📹 换产品（VIDEO_SRC）
- 源视频放在: `~/Desktop/已处理美妆视频/`
- 文件名格式: `产品名_CN.mp4`
- 源视频必须是带画面的1080P mp4，音频可有可无（会被覆盖）

### 🎵 换BGM（BGM_MAP）
- BGM文件放在: `~/Desktop/网易云音乐/` 或 `~/Desktop/BGM库/`
- 支持 `.mp3` 格式
- NCM格式会自动解密（已有解密脚本）
- 每国可以配不同BGM（用于TikTok防重）

### 📝 换文案（SCRIPTS）
- 自然口语化，10秒左右
- 粘贴即可，注意引号
- TH=泰语, MY=马来语, VN=越南语, PH=菲律宾语, SG=英语, CN=中文

## 防重机制（内置，无需配置）
- 每国速度微调 (±2%)
- 每国颜色偏移 (RGB+亮度+对比度+饱和度)
- 每国BGM不同
- 每国CRF编码参数不同
- 人声音量 -3dB（突出人声）
- BGM音量 -12dB~-18dB（不盖人声）

## 字幕
- 42pt 大字（PIL生成PNG → ffmpeg overlay）
- 半透明黑底 + 白色描边文字
- 自动换行，在画面底部

## 常见问题

### 说"No module named PIL"
```bash
pip install Pillow
```

### 字幕显示乱码
字体文件问题，改 `FONT_PATH` 变量第44行，换成系统中文字体

### 输出只有几KB
TTL语音生成失败 → 检查macOS是否有对应语音（`say -v ?` 列出所有）

### 想只跑某个国家
修改 `COUNTRIES` 列表，删掉不想跑的国家

### BGM自动调音量
人声-3dB，BGM按国别-12~-18dB，用compand动态压缩防止人声被盖
