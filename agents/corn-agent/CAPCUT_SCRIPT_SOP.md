# 视频合成脚本 - composer_final.py（永久存档）

此脚本由土豆🥔开发并固化，玉米请永久保存，不可修改核心逻辑。

## 脚本位置
```
~/.openclaw/workspace/agents/corn-agent/composer_final.py
```

## 脚本用途
将基础产品视频（1080×1920，10秒）合成为6国语言版本：
- 🇨🇳 CN 中文
- 🇹🇭 TH 泰文
- 🇲🇾 MY 马来文
- 🇻🇳 VN 越南文
- 🇮🇩 ID 印尼文
- 🇵🇭 PH 菲律宾文

## 依赖
- Python 3.10+
- `pip install edge-tts Pillow`
- ffmpeg（已安装）
- 字体：/Library/Fonts/Arial Unicode.ttf（英文/中文/越南/印尼/马来/菲律宾）
- 字体：/System/Library/Fonts/Supplemental/Thonburi.ttc（泰文）

## 使用方法
```bash
python3 ~/.openclaw/workspace/agents/corn-agent/composer_final.py
```
输出在 `~/Desktop/已处理美妆视频/双头眉刷_{CC}.mp4`

## 核心配置（如需换产品，只改以下部分）
### 1. 视频源
脚本第11行：`VIDEO_SRC` → 替换为新产品视频路径（1080×1920，≤10秒）

### 2. 配音文案
脚本第55-62行：`SCRIPTS` 字典 → 每国4句文案
- [0] 产品第一印象/痛点引入
- [1] 功能描述1
- [2] 功能描述2
- [3] 自然夸赞收尾（禁用引导语：试试/买/下单/小黄车）

### 3. BGM
脚本第40-46行：`BGM_MAP` → 对应国家的BGM高潮文件
BGM文件放在 `~/Desktop/配音输出/bgm_h_{CC}.aac`

### 4. 输出目录
脚本第13行：`OUT_DIR` → 默认为 `~/Desktop/已处理美妆视频`

## 音频参数
- **配音**：Edge TTS neural voices，各国本地女声
- **语速**：`rate='+15%'`（快而不赶）
- **音调**：`pitch='+8Hz'`（温暖亲切）
- **BGM归一化**：自动检测原始响度，统一到-26dB LUFS
- **BGM音量**：TTS×1.4 + BGM×0.25（配音清晰为主，BGM背景不压人声）

## 字幕参数
- **字体大小**：64px
- **位置**：底部居中（Y=1820，即距底部100px）
- **样式**：纯白字，无背景框
- **自动换行**：每行最多22字，最多2行
- **时间同步**：逐句TTS时间驱动，无间隙连续

## BGM来源（天赐下载）
TH → 六少飞-ให้เคอรี่มาส่งได้บ่(弹鼓版)
ID → DJ Desa-Ahh Mantap Tik Tok Remix
VN → 潮妹-Cu Phe Thoi(越南鼓版)
CN → 古琴禅修-巫娜（网易云API）
MY → 千与千寻主题曲-何茂林（网易云API）
PH → 菲律宾没有雪(纯音乐)-战一柔（网易云API）

## NCM解密
天赐下载的网易云音乐.ncm文件放到 `~/Desktop/网易云音乐/` 后：
```bash
pip install ncmdump
cd ~/Desktop/网易云音乐 && ncmdump *.ncm
```
自动输出.mp3到当前目录，再提取高潮段：
```bash
ffmpeg -i input.mp3 -ss 5 -t 12 -c:a aac ~/Desktop/配音输出/bgm_h_CC.aac
```

## 视频源文件
当前：`~/Desktop/双头眉刷.mp4`（6.0MB，1080×1920，10秒）
产品：双头眉刷（美妆工具）
