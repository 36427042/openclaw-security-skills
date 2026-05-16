#!/usr/bin/env python3
"""
🌽 玉米·V8标准修正 v2 — 无drawtext兼容版
5国双头眉刷视频 → 配音重合成 + 字幕增大 + BGM统一 + 20维防重

修正项:
1. 配音AI感强 → Edge TTS自然语音重新合成
2. 字幕太小 → 用Pillow生成高清字幕PNG后overlay，确保竖屏清晰可读
3. BGM音量不统一 → 统一-18dB（相对人声-6dB，差12dB）
4. 两视频BGM盖过人声 → 优先排查MY/PH，BGM降到人声以下至少12dB
5. 20维防重处理 → 色彩/速度/裁剪/滤镜/字幕位置等差异化

用法: python3 v8_correction_v2.py
"""

import asyncio
import json
import math
import os
import random
import subprocess
import sys
import time
import tempfile
from pathlib import Path

# Pillow
from PIL import Image, ImageDraw, ImageFont

# ========== 路径 ==========
SRC_DIR = os.path.expanduser("~/Desktop/已处理TK视频")
OUT_DIR = os.path.expanduser("~/Desktop/已处理TK视频_v8")
BGM_DIR = os.path.expanduser("~/Desktop/配音输出")
WORK_DIR = "/tmp/v8_correction"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

# ========== 5国配音文案（双头眉刷，自然口语化） ==========
SCRIPTS = {
    "MY": {
        "text": (
            "Okay guys, kita semua tau kan susah nak cari brush yang betul-betul sedap "
            "dekat muka. Banyak yang keras dan buat muka rasa sakit. "
            "Tapi yang ni weii, lembut gila and hasil makeup jadi power. "
            "Best sangat dah cuba sendiri!"
        ),
        "voice": "ms-MY-YasminNeural",
    },
    "PH": {
        "text": (
            "Grabe promise you guys! Yung brush na gamit ko dati sobrang harsh sa face, "
            "parang nag-eexfoliate ako araw-araw. Pero itong brush na double-headed, "
            "super soft ng bristles. Ang smooth ng application, parang walang brush na dumampi. "
            "Sulit na sulit! Must try!"
        ),
        "voice": "fil-PH-BlessicaNeural",
    },
    "SG": {
        "text": (
            "Wah I cannot believe I've been using the wrong brushes this whole time. "
            "They were so rough on my face! Then I found this double-headed brush set. "
            "Super soft bristles, blends everything so nicely. "
            "Just spray and wipe. Brushes like new again. Can recommend lah!"
        ),
        "voice": "en-SG-LunaNeural",
    },
    "TH": {
        "text": (
            "บอกเลยว่าหลายคนแต่งหน้าแล้วไม่เนียน ไม่ติดทน "
            "อาจจะเพราะแปรงที่ใช้ไม่ดีพอ วันนี้เจออะไรดีๆมาแล้ว "
            "น้องแปรงคู่นี้ขนนุ่มมากกก ปาดสีแล้วเริ่ดสุดๆ ใช้แล้วหน้าเนียนปังมากเลยค่า~"
        ),
        "voice": "th-TH-PremwadeeNeural",
    },
    "VN": {
        "text": (
            "Ê mày! Có ai giống mình không? "
            "Cọ vẽ trang điểm hoài mà không đều, nhìn dày cộm. "
            "Xài cây cọ hai đầu này nè. "
            "Lông mềm thiệt luôn, tán đều như mơ. Da mịn liền, xịn xò quá trời!"
        ),
        "voice": "vi-VN-HoaiMyNeural",
    },
}

# ========== 20维防重参数矩阵 ==========
PARAMS = {
    "MY": {
        "speed": 0.99,
        "brightness": 0.03,    # eq brightness (-1~1)
        "contrast": 0.98,      # eq contrast (0~2, 1=normal)
        "saturation": 0.95,
        "gamma_r": 1.02,
        "gamma_g": 1.00,
        "gamma_b": 0.97,
        "noise": 1.8,
        "crf": 24,
        "bgm_file": "bgm_h_MY.aac",
        "bgm_vol": 0.18,       # ~ -15dB
        "sub_offset_y": 5,
        "sub_size_pt": 56,
        "sub_color_r": 255, "sub_color_g": 254, "sub_color_b": 247,
        "color_temp_r": 0.02,
        "color_temp_b": -0.02,
        "sharpness": 0.5,
        "crop_off_x": 0, "crop_off_y": 2,
        "bgm_fade_in": 1.2,
    },
    "PH": {
        "speed": 0.98,
        "brightness": 0.07,
        "contrast": 0.97,
        "saturation": 0.92,
        "gamma_r": 1.00,
        "gamma_g": 0.97,
        "gamma_b": 0.95,
        "noise": 1.2,
        "crf": 26,
        "bgm_file": "bgm_h_PH.aac",
        "bgm_vol": 0.18,
        "sub_offset_y": 10,
        "sub_size_pt": 58,
        "sub_color_r": 255, "sub_color_g": 254, "sub_color_b": 240,
        "color_temp_r": 0.03,
        "color_temp_b": -0.03,
        "sharpness": 0.6,
        "crop_off_x": 0, "crop_off_y": 0,
        "bgm_fade_in": 0.5,
    },
    "SG": {
        "speed": 1.00,
        "brightness": 0.00,
        "contrast": 1.00,
        "saturation": 1.00,
        "gamma_r": 0.97,
        "gamma_g": 1.00,
        "gamma_b": 1.02,
        "noise": 1.0,
        "crf": 20,
        "bgm_file": "bgm_CN.mp3",
        "bgm_vol": 0.18,
        "sub_offset_y": 0,
        "sub_size_pt": 56,
        "sub_color_r": 255, "sub_color_g": 255, "sub_color_b": 255,
        "color_temp_r": 0.00,
        "color_temp_b": 0.01,
        "sharpness": 0.2,
        "crop_off_x": 2, "crop_off_y": 0,
        "bgm_fade_in": 1.5,
    },
    "TH": {
        "speed": 1.01,
        "brightness": -0.07,
        "contrast": 1.02,
        "saturation": 1.05,
        "gamma_r": 0.95,
        "gamma_g": 0.98,
        "gamma_b": 1.02,
        "noise": 1.5,
        "crf": 22,
        "bgm_file": "bgm_h_TH.aac",
        "bgm_vol": 0.18,
        "sub_offset_y": -10,
        "sub_size_pt": 56,
        "sub_color_r": 255, "sub_color_g": 254, "sub_color_b": 250,
        "color_temp_r": -0.02,
        "color_temp_b": 0.02,
        "sharpness": 0.3,
        "crop_off_x": 0, "crop_off_y": 0,
        "bgm_fade_in": 0.3,
    },
    "VN": {
        "speed": 1.02,
        "brightness": -0.03,
        "contrast": 1.01,
        "saturation": 1.02,
        "gamma_r": 0.98,
        "gamma_g": 1.02,
        "gamma_b": 1.00,
        "noise": 2.0,
        "crf": 22,
        "bgm_file": "bgm_h_VN.aac",
        "bgm_vol": 0.18,
        "sub_offset_y": -5,
        "sub_size_pt": 54,
        "sub_color_r": 255, "sub_color_g": 250, "sub_color_b": 255,
        "color_temp_r": -0.01,
        "color_temp_b": 0.01,
        "sharpness": 0.4,
        "crop_off_x": 0, "crop_off_y": 0,
        "bgm_fade_in": 0.8,
    },
}


def run_cmd(cmd, desc="", timeout=120, capture=True):
    """运行命令并返回(bool, output)"""
    if desc:
        print(f"  ⏳ {desc}...")
    else:
        print(f"  ⏳ {' '.join(str(c) for c in cmd[:5])}...")
    start = time.time()
    try:
        kw = {"capture_output": capture, "text": True, "timeout": timeout}
        result = subprocess.run(cmd, **kw)
        elapsed = time.time() - start
        if result.returncode != 0:
            err = result.stderr[:300] if capture else ""
            print(f"  ❌ {desc}: {err}")
            return False, (result.stdout if capture else "", result.stderr if capture else "")
        if desc:
            print(f"  ✅ {desc} ({elapsed:.1f}s)")
        return True, result.stdout if capture else ""
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ {desc} 超时 ({timeout}s)")
        return False, ""
    except Exception as e:
        print(f"  ❌ {desc} 异常: {e}")
        return False, ""


async def generate_tts(cc, config, out_path):
    """Edge TTS生成自然语音"""
    cmd = [
        "edge-tts",
        "--voice", config["voice"],
        "--text", config["text"],
        "--write-media", out_path,
    ]
    print(f"  🎙️ 生成{cc}配音 ({config['voice']})...")
    start = time.time()
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    elapsed = time.time() - start
    if proc.returncode != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) < 100:
        print(f"  ❌ {cc} TTS失败")
        return False
    size = os.path.getsize(out_path) / 1024
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", out_path],
        capture_output=True, text=True
    ).stdout.strip()
    print(f"  ✅ {cc} TTS ({elapsed:.1f}s, {size:.0f}KB, {dur}s)")
    return True


def split_text_for_subtitle(text, max_chars_per_line=35):
    """智能分行为适合竖屏的字幕"""
    sentences = text.replace("! ", "!\n").replace("? ", "?\n").replace(". ", ".\n").split("\n")
    lines = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= max_chars_per_line:
            lines.append(sentence)
        else:
            # 按空格分
            words = sentence.split()
            current = ""
            for w in words:
                if len(current) + len(w) + 1 <= max_chars_per_line:
                    current = (current + " " + w).strip()
                else:
                    if current:
                        lines.append(current)
                    current = w
            if current:
                lines.append(current)
    return lines


def generate_subtitle_png(text, font_size, font_color, out_path, bg_color=(0,0,0,100), vw=1080, vh=1920):
    """用Pillow生成高清字幕PNG，居中叠加到底部"""
    # 尝试加载字体
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except:
                continue
    if font is None:
        font = ImageFont.load_default()
    
    # 分行
    lines = split_text_for_subtitle(text)
    if not lines:
        lines = [text]
    
    # 计算尺寸（最多显示2行）
    display_lines = lines[:3]
    
    # 计算行高和宽度
    line_height = 0
    line_widths = []
    spacing = font_size * 0.3
    
    for line in display_lines:
        bbox = font.getbbox(line)
        lh = bbox[3] - bbox[1]
        lw = bbox[2] - bbox[0]
        line_height = max(line_height, lh)
        line_widths.append(lw)
    
    total_text_height = len(display_lines) * line_height + (len(display_lines) - 1) * spacing
    
    # 创建字幕PNG
    margin = int(font_size * 0.6)
    img_w = int(vw) - 40  # 左右各留20px边距
    img_h = int(total_text_height + margin * 2)
    canvas = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # 背景：半透明黑色圆角矩形
    pad = 10
    draw.rounded_rectangle(
        [pad, pad, img_w - pad, img_h - pad],
        radius=12,
        fill=bg_color
    )
    
    # 逐行绘制文字
    y_pos = margin
    for i, line in enumerate(display_lines):
        bbox = font.getbbox(line)
        lw = bbox[2] - bbox[0]
        x_pos = (img_w - lw) // 2
        
        # 白色文字 + 黑色描边（外发光效果）
        stroke_color = (0, 0, 0, 220)
        stroke_width = max(2, font_size // 12)
        draw.text((x_pos, y_pos), line, fill=font_color, font=font,
                  stroke_width=stroke_width, stroke_fill=stroke_color)
        y_pos += line_height + spacing
    
    canvas.save(out_path, "PNG")
    return out_path


def generate_subtitle_pngs(cc, text, params, vw=1080, vh=1920):
    """生成一个字幕PNG，显示所有文本（对于10秒短剧用一个字幕图就够了）"""
    font_size = params["sub_size_pt"]
    color = (params["sub_color_r"], params["sub_color_g"], params["sub_color_b"], 255)
    sub_dir = os.path.join(WORK_DIR, cc)
    os.makedirs(sub_dir, exist_ok=True)
    out = os.path.join(sub_dir, f"sub_{cc}.png")
    generate_subtitle_png(text, font_size, color, out, vw=vw, vh=vh)
    return out


async def process_country(cc):
    """处理单个国家V8修正"""
    src_file = os.path.join(SRC_DIR, f"双头眉刷_{cc}.mp4")
    if not os.path.exists(src_file):
        print(f"  ⚠️ {cc} 源视频不存在")
        return False
    
    params = PARAMS[cc]
    config = SCRIPTS[cc]
    country_dir = os.path.join(WORK_DIR, cc)
    os.makedirs(country_dir, exist_ok=True)
    
    # ------- 中间文件 -------
    tts_file = os.path.join(country_dir, f"voice_{cc}.mp3")
    voice_ad = os.path.join(country_dir, f"voice_ad_{cc}.wav")
    bgm_in = os.path.join(BGM_DIR, params["bgm_file"])
    bgm_cut = os.path.join(country_dir, f"bgm_cut_{cc}.wav")
    bgm_ad = os.path.join(country_dir, f"bgm_ad_{cc}.wav")
    mixed_audio = os.path.join(country_dir, f"mixed_{cc}.wav")
    video_vf = os.path.join(country_dir, f"video_vf_{cc}.ts")
    video_sub = os.path.join(country_dir, f"video_sub_{cc}.ts")
    final_out = os.path.join(OUT_DIR, f"双头眉刷_{cc}_v8.mp4")
    subtitle_png = os.path.join(country_dir, f"sub_{cc}.png")
    
    print(f"\n{'='*55}")
    print(f"  🌍 {cc} — V8修正")
    print(f"{'='*55}")
    
    if not os.path.exists(bgm_in):
        print(f"  ⚠️ BGM缺失: {bgm_in}，将仅用语音")
    
    # Step 1: 生成自然语音
    ok = await generate_tts(cc, config, tts_file)
    if not ok or not os.path.exists(tts_file):
        print(f"  ❌ {cc} TTS失败，跳过")
        return False
    
    # 获取时长
    def get_dur(f):
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", f],
            capture_output=True, text=True
        )
        return float(r.stdout.strip() or 10.0)
    
    video_dur = get_dur(src_file)
    tts_dur = get_dur(tts_file)
    print(f"  📐 视频: {video_dur:.2f}s, TTS: {tts_dur:.2f}s")
    
    # Step 2: 语音音量标准化（目标-6dB LUFS）
    ok, _ = run_cmd([
        "ffmpeg", "-y", "-i", tts_file,
        "-af", "loudnorm=I=-6:LRA=7:TP=-1,volume=1.5",
        "-ar", "44100", "-ac", "1", voice_ad
    ], f"{cc} 语音标准化-6dB", timeout=30)
    if not ok:
        # fallback: copy as-is
        run_cmd(["cp", tts_file, voice_ad], f"{cc} 语音回退", timeout=5)
    
    # Step 3: BGM准备（如果BGM文件存在）
    if os.path.exists(bgm_in):
        bgm_dur = get_dur(bgm_in)
        if bgm_dur >= video_dur:
            run_cmd([
                "ffmpeg", "-y", "-i", bgm_in,
                "-t", str(video_dur),
                "-ar", "44100", "-ac", "1", bgm_cut
            ], f"{cc} BGM裁剪", timeout=15)
        else:
            run_cmd([
                "ffmpeg", "-y", "-stream_loop", "-1", "-i", bgm_in,
                "-t", str(video_dur), "-ar", "44100", "-ac", "1", bgm_cut
            ], f"{cc} BGM循环", timeout=15)
        
        # BGM音量: 人声-6dB, BGM-18dB, 差12dB
        # bgm_vol=0.18 约-15dB, 加-6dB处理后语音约比BGM高9-12dB
        run_cmd([
            "ffmpeg", "-y", "-i", bgm_cut,
            "-af", f"volume={params['bgm_vol']}",
            bgm_ad
        ], f"{cc} BGM音量调低", timeout=15)
    else:
        # 无BGM时创建静音
        run_cmd([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"anullsrc=r=44100:cl=mono",
            "-t", str(video_dur), bgm_ad
        ], f"{cc} 静音BGM", timeout=5)
    
    # Step 4: 混合音轨（语音+BGM，BGM淡入）
    fade_in = params["bgm_fade_in"]
    run_cmd([
        "ffmpeg", "-y", "-i", voice_ad, "-i", bgm_ad,
        "-filter_complex",
        f"[1:a]afade=t=in:d={fade_in}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:weights=1 0.2[a]",
        "-map", "[a]", "-ac", "1", "-ar", "44100",
        mixed_audio
    ], f"{cc} 音频混合", timeout=30)
    
    # Step 5: 视频画面20维防重滤镜
    p = params
    b = p["brightness"]
    c = p["contrast"]
    s = p["saturation"]
    gr, gg, gb = p["gamma_r"], p["gamma_g"], p["gamma_b"]
    sp = 1 / p["speed"]
    cx, cy = p["crop_off_x"], p["crop_off_y"]
    n = p["noise"]
    sh = p["sharpness"]
    cr = p["color_temp_r"]
    cb = p["color_temp_b"]
    
    # 构建滤镜（无drawtext/subtitles）
    filters = []
    filters.append(f"setpts={sp}*PTS")
    filters.append(f"eq=brightness={b:.3f}:contrast={c:.3f}:saturation={s:.3f}:gamma_r={gr:.3f}:gamma_g={gg:.3f}:gamma_b={gb:.3f}")
    
    if cx != 0 or cy != 0:
        crop_h = max(480, 1920 - 2 * abs(cy))
        crop_x = max(0, min(cx, 20))
        crop_y = max(0, min(abs(cy), 20))
        filters.append(f"crop=1080:{crop_h}:{crop_x}:{crop_y}")
        filters.append("scale=1080:1920:flags=lanczos")
    
    if cr != 0 or cb != 0:
        filters.append(f"colorbalance=rs={cr:.3f}:gs=0:bs={cb:.3f}")
    
    if n > 0:
        filters.append(f"noise=alls={int(n*3)}:allf=t+p")
    
    if sh > 0:
        filters.append(f"unsharp=la={sh:.1f}:ca={sh:.1f}")
    
    filter_str = ",".join(filters)
    
    ok, _ = run_cmd([
        "ffmpeg", "-y", "-i", src_file,
        "-filter_complex", filter_str,
        "-c:v", "libx264", "-preset", "slow",
        "-crf", str(p["crf"]),
        "-pix_fmt", "yuv420p",
        "-b:v", "4000k", "-maxrate", "6000k", "-bufsize", "8000k",
        "-r", "30",
        "-an",
        video_vf
    ], f"{cc} 视频20维防重滤镜", timeout=300)
    
    if not ok:
        return False
    
    # Step 6: 生成字幕PNG并叠加
    sub_png = generate_subtitle_pngs(cc, config["text"], params)
    
    # 字幕位置（底部居中）
    sub_y = 1920 - params["sub_offset_y"] - 120  # 距底部边距
    
    # 字幕动画：从第delay秒开始显示直到结束
    delay = 0.5
    sub_dur = video_dur - delay - 0.3
    if sub_dur < 1:
        sub_dur = video_dur
    
    # overlay字幕PNG到视频
    ok, _ = run_cmd([
        "ffmpeg", "-y", "-i", video_vf, "-i", sub_png,
        "-filter_complex",
        f"[0:v][1:v]overlay=(W-w)/2:{sub_y}:enable='between(t,{delay},{delay+sub_dur})'[out]",
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", str(p["crf"]),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-an",
        video_sub
    ], f"{cc} 叠加字幕", timeout=300)
    
    if not ok:
        print(f"  ⚠️ 字幕叠加失败，使用无字幕版本")
        video_sub = video_vf
    
    # Step 7: 视频+音频最终合成
    ok, _ = run_cmd([
        "ffmpeg", "-y",
        "-i", video_sub,
        "-i", mixed_audio,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "1",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-movflags", "+faststart",
        final_out
    ], f"{cc} 最终合成_v8", timeout=120)
    
    if not ok or not os.path.exists(final_out):
        return False
    
    final_size = os.path.getsize(final_out) / 1024 / 1024
    print(f"\n  🎉 {cc} V8完成! ({final_size:.1f}MB)")
    return True


async def main():
    print("=" * 55)
    print("  🌽 玉米·V8标准修正 v2")
    print("  5国双头眉刷 → 配音重合成 + 字幕增大 + BGM统一 + 20维防重")
    print("=" * 55)
    
    countries = ["MY", "PH", "SG", "TH", "VN"]
    
    # 检查源文件
    for cc in countries:
        src = os.path.join(SRC_DIR, f"双头眉刷_{cc}.mp4")
        if not os.path.exists(src):
            print(f"  ❌ 缺失: {src}")
            return
    
    print(f"  源目录: {SRC_DIR}")
    print(f"  输出: {OUT_DIR}")
    
    # 顺序处理
    results = {}
    for cc in countries:
        try:
            results[cc] = await process_country(cc)
        except Exception as e:
            print(f"  🔴 {cc} 异常: {e}")
            import traceback
            traceback.print_exc()
            results[cc] = False
        await asyncio.sleep(0.5)
    
    # 汇总
    print(f"\n{'='*55}")
    print(f"  5国V8修正完成！")
    print(f"{'='*55}")
    all_ok = True
    for cc in countries:
        out = os.path.join(OUT_DIR, f"双头眉刷_{cc}_v8.mp4")
        if os.path.exists(out):
            size = os.path.getsize(out) / 1024 / 1024
            icon = "✅" if results.get(cc) else "⚠️"
            print(f"  {icon} {cc}: {out} ({size:.1f}MB)")
        else:
            print(f"  ❌ {cc}: 文件未生成")
            all_ok = False
    
    print(f"\n  📁 输出目录: {OUT_DIR}")
    
    # GEP记录
    if all_ok:
        print(f"\n  📝 记录到GEP...")
        os.system("python3 ~/.openclaw/workspace/scripts/gep_adapter.py post_record corn \"5国双头眉刷V8修正\" success")
    else:
        print(f"\n  ⚠️ 部分失败，GEP记录中...")
        os.system("python3 ~/.openclaw/workspace/scripts/gep_adapter.py post_record corn \"5国双头眉刷V8修正\" partial")


if __name__ == "__main__":
    asyncio.run(main())
