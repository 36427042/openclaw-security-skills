#!/usr/bin/env python3
"""
🎬 玉米视频管线 · 本地化混剪引擎 (V5 Final) — 🚫铁律固化版
====================================================

⚠️ ⚠️ ⚠️ ⚠️ 铁律（2026-05-11 天赐确认，不可违背） ⚠️ ⚠️ ⚠️ ⚠️
#
#  源视频只需生成1个（中文版），其余5国视频全部走此本地混剪脚本
#  ❌ 禁止调用任何API（即梦/简创/火山/三方视频生成接口）
#  ❌ 禁止上传视频到任何云渲染/云处理平台
#  ✅ 唯一外部依赖：edge-tts（微软Azure语音合成，文件存本地）
#  ✅ 全链路：源视频.mp4 → ffmpeg本地混剪 → 5国.mp4 → ~/Desktop/已处理美妆视频/
#
#  违反此铁律的脚本已全部移入 scripts/archive/ 废弃区
#  如有新想法，先和天赐确认再动手。
#
⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️

"""

import json, os, sys, subprocess, random, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# ⚙️ 配置区（改这3个地方即可——换产品/文案/BGM）
# ============================================================

import json, os, sys, subprocess, random, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# ⚙️ 配置区（改这3个地方即可——换产品/文案/BGM）
# ============================================================

# === [行11] 源视频路径（换产品就改这个）===
VIDEO_SRC = os.path.expanduser("~/Desktop/已处理美妆视频/双头眉刷_CN.mp4")

# === [行40] BGM映射（各国用不同BGM，换BGM改这个字典）===
BGM_MAP = {
    "TH": "~/Desktop/网易云音乐/六少飞 - ให้เคอรี่มาส่งได้บ่(弹鼓版).mp3",
    "MY": "~/Desktop/网易云音乐/DJMuchY - Ke Cap Gap Ba Gia.mp3",
    "VN": "~/Desktop/网易云音乐/Hoàng Read - The Magic Bomb.mp3",
    "PH": "~/Desktop/网易云音乐/zero two - Izantachi.mp3",
    "SG": "~/Desktop/网易云音乐/DJ Desa - Ahh Mantap Tik Tok Tarik Sis De Yang Gatal Bukan Pho (Remix).mp3",
    "CN": "~/Desktop/网易云音乐/潮妹 - Cu Phe Thoi (越南鼓版).mp3",
}

# === [行55] 各国配音文案（换文案改这个字典）===
SCRIPTS = {
    "TH": "ดูสิ ใช้แล้วสวยขึ้นจริงๆ เลยค่ะ",
    "MY": "Nampak tak? Guna memang jadi cantik!",
    "VN": "Thấy không? Dùng xong đẹp thật đó!",
    "PH": "Kita mo? Ang ganda ng resulta!",
    "SG": "See? The results are really amazing!",
    "CN": "你看，效果真不错！",
}

# ============================================================
# 固定参数（一般不用改）
# ============================================================
# 5国配置（Edge-TTS语音，语速1.15x，音调+8Hz）
# 详见: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support
COUNTRIES = [
    {"cc": "TH", "name": "🇹🇭 泰国",  "voice": "th-TH-PremwadeeNeural", "speed": 1.15, "pitch": "+8Hz"},
    {"cc": "MY", "name": "🇲🇾 马来西亚", "voice": "ms-MY-YasminNeural",    "speed": 1.15, "pitch": "+8Hz"},
    {"cc": "VN", "name": "🇻🇳 越南",  "voice": "vi-VN-HoaiMyNeural",     "speed": 1.15, "pitch": "+8Hz"},
    {"cc": "PH", "name": "🇵🇭 菲律宾", "voice": "fil-PH-BlessicaNeural",  "speed": 1.15, "pitch": "+8Hz"},
    {"cc": "SG", "name": "🇸🇬 新加坡", "voice": "en-SG-LunaNeural",      "speed": 1.15, "pitch": "+8Hz"},
    {"cc": "CN", "name": "🇨🇳 中文",  "voice": "zh-CN-XiaoxiaoNeural",   "speed": 1.15, "pitch": "+8Hz"},
]

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
if not os.path.exists(FONT_PATH):
    # Fallback to any available font
    import glob
    fonts = glob.glob("/System/Library/Fonts/**/*.ttf", recursive=True)
    FONT_PATH = fonts[0] if fonts else FONT_PATH

OUTPUT_DIR = os.path.expanduser("~/Desktop/已处理美妆视频")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMP_DIR = tempfile.mkdtemp(prefix="composer_")

# 防重参数（每国不同，混淆平台指纹）
ANTI_DUP_CONFIG = {
    "TH": {"speed": 1.00, "brightness": 0.02, "contrast": 1.02, "saturation": 1.03, "noise": 0.001, "rgb_r": 1.00, "rgb_g": 0.98, "rgb_b": 1.01, "crf": 26},
    "MY": {"speed": 0.99, "brightness": 0.03, "contrast": 1.01, "saturation": 0.97, "noise": 0.002, "rgb_r": 1.01, "rgb_g": 1.00, "rgb_b": 0.99, "crf": 27},
    "VN": {"speed": 1.01, "brightness": 0.01, "contrast": 0.99, "saturation": 1.02, "noise": 0.001, "rgb_r": 0.99, "rgb_g": 1.01, "rgb_b": 1.00, "crf": 25},
    "PH": {"speed": 0.98, "brightness": 0.04, "contrast": 1.03, "saturation": 0.98, "noise": 0.003, "rgb_r": 1.02, "rgb_g": 0.99, "rgb_b": 0.98, "crf": 28},
    "SG": {"speed": 1.02, "brightness": 0.00, "contrast": 1.00, "saturation": 1.01, "noise": 0.002, "rgb_r": 0.98, "rgb_g": 1.02, "rgb_b": 1.01, "crf": 26},
    "CN": {"speed": 1.00, "brightness": 0.01, "contrast": 1.01, "saturation": 1.00, "noise": 0.001, "rgb_r": 1.00, "rgb_g": 1.00, "rgb_b": 1.00, "crf": 25},
}


# ============================================================
# 功能实现
# ============================================================

def get_video_duration(video_path):
    """获取视频时长（秒）"""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    return float(r.stdout.strip()) if r.stdout.strip() else 10.0


def generate_tts(text, country_cfg, out_path):
    """用 Edge-TTS 生成高质量音频（语速1.15x，音调+8Hz）"""
    import asyncio, edge_tts
    
    voice = country_cfg["voice"]
    speed = country_cfg["speed"]
    pitch = country_cfg["pitch"]
    
    async def _tts():
        tts = edge_tts.Communicate(
            text,
            voice=voice,
            rate=f"+{int((speed-1)*100)}%",  # +15%
            pitch=pitch  # +8Hz
        )
        await tts.save(out_path)
    
    try:
        asyncio.run(_tts())
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
    except Exception as e:
        print(f"❌ Edge-TTS失败: {e}")
    
    return None


def mix_audio(tts_path, bgm_path, out_path, bgm_volume_db=-14):
    """混合人声+BGM，人声突出"""
    cmd = [
        "ffmpeg", "-y",
        "-i", bgm_path,
        "-i", tts_path,
        "-filter_complex",
        f"[0:a]volume={bgm_volume_db}dB[bgm];"
        f"[1:a]volume=-3dB[voice];"
        f"[bgm][voice]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "[aout]",
        "-codec:a", "libmp3lame", "-b:a", "128k",
        out_path
    ]
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    if r.returncode != 0:
        print(f"    ⚠️ 混音失败")
        return tts_path  # fallback: 只用配音
    return out_path


def create_subtitle_image(text, font_size=42, img_width=1080, img_height=1920):
    """用PIL生成字幕PNG（放中部偏下，避开源视频底部字幕区）"""
    # 创建全透明画布
    img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 尽量用大字体
    font = None
    for size in [font_size, 40, 36, 30]:
        try:
            font = ImageFont.truetype(FONT_PATH, size)
            break
        except:
            continue
    
    if not font:
        font = ImageFont.load_default()
    
    # 自动换行
    max_width = img_width - 120
    lines = []
    line = ""
    for char in text:
        test_line = line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width and line:
            lines.append(line)
            line = char
        else:
            line = test_line
    if line:
        lines.append(line)
    
    # 计算总高度
    line_height = font_size + 12
    total_height = len(lines) * line_height + 30
    
    # 字幕放在中下部（y=1400~1650），不挡脸也不碰底部drawbox
    y_start = 1400
    
    # 背景半透明框
    if lines:
        max_line_w = max(draw.textbbox((0, 0), l, font=font)[2] - draw.textbbox((0, 0), l, font=font)[0] for l in lines)
        bg_x = (img_width - max_line_w - 40) // 2
        bg_y = y_start - 10
        bg_h = total_height + 20
        draw.rectangle(
            [bg_x, bg_y, bg_x + max_line_w + 40, bg_y + bg_h],
            fill=(0, 0, 0, 140)
        )
    
    # 白色文字 + 描边
    for j, line in enumerate(lines):
        y = y_start + j * line_height
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (img_width - (bbox[2] - bbox[0])) // 2
        
        # 描边
        for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1), (0,-1), (0,1), (-1,0), (1,0)]:
            draw.text((x+dx, y+dy), line, font=font, fill=(0, 0, 0, 200))
        # 主文字
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    
    out_path = os.path.join(TEMP_DIR, f"subtitle_{hash(text)}.png")
    img.save(out_path)
    return out_path


def apply_remix(src_video, tts_audio, subtitle_text, country_cfg, out_path):
    """
    核心混剪函数
    流程：视频防重 + 字幕叠加 + 音频混音
    """
    cc = country_cfg["cc"]
    ad = ANTI_DUP_CONFIG[cc]
    
    # 1. 预处理视频部分（速度/颜色/防重 + 覆盖源视频底部字幕）
    video_filter = (
        f"setpts={1/ad['speed']}*PTS,"  # 速度
        f"eq="
        f"brightness={ad['brightness']}:"
        f"contrast={ad['contrast']}:"
        f"saturation={ad['saturation']},"
        f"colorbalance="
        f"rs={ad['rgb_r']-1:.2f}:"
        f"gs={ad['rgb_g']-1:.2f}:"
        f"bs={ad['rgb_b']-1:.2f},"
        f"drawbox=x=0:y=1700:w=1080:h=220:color=black@1.0:t=fill"  # 覆盖源视频底部字幕（1700-1920区域）
    )
    
    # 2. 生成字幕
    sub_png = create_subtitle_image(subtitle_text)
    
    # 3. 混音
    mixed_audio = os.path.join(TEMP_DIR, f"mixed_audio_{cc}.mp3")
    bgm = os.path.expanduser(BGM_MAP.get(cc, ""))
    
    # BGM音量按国差异化（TikTok去重+听感差异）
    bgm_volumes = {"TH": -14, "MY": -16, "VN": -15, "PH": -18, "SG": -15, "CN": -12}
    bgm_vol = bgm_volumes.get(cc, -16)
    
    if os.path.exists(bgm):
        final_audio = mix_audio(tts_audio, bgm, mixed_audio, bgm_vol)
    else:
        print(f"    ⚠️ 未找到BGM: {bgm}")
        final_audio = tts_audio
    
    # 4. 最终合成
    cmd = [
        "ffmpeg", "-y",
        "-i", src_video,
        "-i", sub_png,
        "-i", final_audio,
        "-filter_complex",
        f"[0:v]{video_filter}[v1];"
        f"[v1][1:v]overlay=0:0[vout]",
        "-map", "[vout]",
        "-map", "2:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", str(ad["crf"]),
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out_path
    ]
    
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    
    if r.returncode != 0:
        err = r.stderr.decode()[-200:]
        print(f"    ❌ 输出失败: {err}")
        return False
    
    return os.path.exists(out_path) and os.path.getsize(out_path) > 100000


# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 55)
    print("🎬 玉米视频管线 · 本地化混剪引擎 (V5 Final)")
    print(f"   源视频: {os.path.basename(VIDEO_SRC)}")
    print(f"   输出目录: {OUTPUT_DIR}")
    print("=" * 55)
    
    # 检查源视频
    if not os.path.exists(VIDEO_SRC):
        print(f"\n❌ 源视频不存在: {VIDEO_SRC}")
        print("   请修改 VIDEO_SRC 路径（第11行）")
        return
    
    src_duration = get_video_duration(VIDEO_SRC)
    print(f"   源视频时长: {src_duration:.1f}s\n")
    
    # 逐国处理
    results = []
    for country in COUNTRIES:
        cc = country["cc"]
        print(f"\n{'='*45}")
        print(f"  🌍 {country['name']} ({cc})")
        print(f"{'='*45}")
        
        script = SCRIPTS.get(cc, "")
        if not script:
            print(f"  ⚠️ 无文案配置，跳过")
            continue
        
        print(f"  📝 文案: {script}")
        
        # Step 1: TTS
        tts_path = os.path.join(TEMP_DIR, f"tts_{cc}.mp3")
        print(f"  🎙️ TTS配音 (语速{country['speed']}x)...", end=" ", flush=True)
        tts_result = generate_tts(script, country, tts_path)
        if tts_result:
            print(f"✅ {os.path.getsize(tts_result)/1024:.0f}KB")
        else:
            print(f"❌ 失败")
            continue
        
        # Step 2: 混剪（输出到独立文件名）
        in_base = os.path.splitext(os.path.basename(VIDEO_SRC))[0]
        # 去掉源视频语言后缀换新
        clean_base = in_base
        for lang_suffix in ["_CN", "_TH", "_MY", "_VN", "_PH", "_SG"]:
            if clean_base.endswith(lang_suffix):
                clean_base = clean_base[:-len(lang_suffix)]
                break
        out_file = f"{clean_base}_{cc}.mp4"
        out_path_full = os.path.join(OUTPUT_DIR, out_file)
        # 跳过与源视频同名的国家（源视频已含该语言）
        if os.path.abspath(out_path_full) == os.path.abspath(VIDEO_SRC):
            print(f"    ℹ️ 跳过（源视频已是{cc}版）")
            continue
        out_path = os.path.join(OUTPUT_DIR, out_file)
        
        print(f"  🎬 混剪输出...", end=" ", flush=True)
        ok = apply_remix(VIDEO_SRC, tts_result, script, country, out_path)
        if ok:
            size_mb = os.path.getsize(out_path) / (1024*1024)
            print(f"✅ {size_mb:.1f}MB → {out_file}")
            results.append((cc, out_path, size_mb))
        else:
            print(f"❌ 失败")
    
    # 汇总
    print(f"\n{'='*55}")
    print(f"📊 汇总")
    print(f"{'='*55}")
    for cc, path, size in results:
        print(f"  ✅ {cc}: {os.path.basename(path)} ({size:.1f}MB)")
    print(f"\n🎉 完成! 成功: {len(results)}/{len(COUNTRIES)}")
    
    # 清理临时文件
    shutil.rmtree(TEMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
