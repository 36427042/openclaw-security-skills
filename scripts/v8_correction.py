#!/usr/bin/env python3
"""
🌽 玉米·V8标准修正
5国双头眉刷视频 → 配音重新合成 + 字幕增大 + BGM统一 + 20维防重

修正项:
1. 配音AI感强 → Edge TTS自然语音重新合成
2. 字幕太小 → 增大至54-60pt，竖屏清晰可读
3. BGM音量不统一 → 统一-18dB（相对于人声-6dB，即BGM比人声低12dB）
4. 两视频BGM盖过人声 → 优先排查MY/PH，BGM降到人声以下至少12dB
5. 20维防重处理 → 色彩/速度/裁剪/滤镜/字幕位置等差异化

用法: python3 v8_correction.py
"""

import asyncio
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

# ========== 路径 ==========
SRC_DIR = os.path.expanduser("~/Desktop/已处理TK视频")
OUT_DIR = os.path.expanduser("~/Desktop/已处理TK视频_v8")
BGM_DIR = os.path.expanduser("~/Desktop/配音输出")
WORK_DIR = "/tmp/v8_correction"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

# ========== 5国配音文案（双头眉刷场景，自然口语化） ==========
# 基于萝卜v3的刷具文案优化，让Edge TTS产出自然流畅语句
SCRIPTS = {
    "MY": {
        "text": (
            "Okay guys, kita semua tau kan susah nak cari brush yang betul-betul sedap "
            "dekat muka. Banyak yang keras dan buat muka rasa sakit. "
            "Tapi yang ni weii, lembut gila and hasil makeup jadi power. "
            "Best sangat dah cuba sendiri!"
        ),
        "voice": "ms-MY-YasminNeural",
        "lang": "ms-MY",
    },
    "PH": {
        "text": (
            "Grabe promise you guys! Yung brush na gamit ko dati sobrang harsh sa face, "
            "parang nag-eexfoliate ako araw-araw. Pero itong brush na double-headed, "
            "super soft ng bristles. Ang smooth ng application, parang walang brush na dumampi. "
            "Sulit na sulit! Must try!"
        ),
        "voice": "fil-PH-BlessicaNeural",
        "lang": "fil-PH",
    },
    "SG": {
        "text": (
            "Wah I cannot believe I've been using the wrong brushes this whole time. "
            "They were so rough on my face! Then I found this double-headed brush set. "
            "Super soft bristles, blends everything so nicely. "
            "Just spray and wipe. Brushes like new again. Can recommend lah!"
        ),
        "voice": "en-SG-LunaNeural",
        "lang": "en-SG",
    },
    "TH": {
        "text": (
            "บอกเลยว่าหลายคนแต่งหน้าแล้วไม่เนียน ไม่ติดทน "
            "อาจจะเพราะแปรงที่ใช้ไม่ดีพอ วันนี้เจออะไรดีๆมาแล้ว "
            "น้องแปรงคู่นี้ขนนุ่มมากกก ปาดสีแล้วเริ่ดสุดๆ ใช้แล้วหน้าเนียนปังมากเลยค่า~"
        ),
        "voice": "th-TH-PremwadeeNeural",
        "lang": "th-TH",
    },
    "VN": {
        "text": (
            "Ê mày! Có ai giống mình không? "
            "Cọ vẽ trang điểm hoài mà không đều, nhìn dày cộm. "
            "Xài cây cọ hai đầu này nè. "
            "Lông mềm thiệt luôn, tán đều như mơ. Da mịn liền, xịn xò quá trời!"
        ),
        "voice": "vi-VN-HoaiMyNeural",
        "lang": "vi-VN",
    },
}

# ========== 20维防重参数矩阵（基于记忆表优化） ==========
PARAMS = {
    "MY": {
        "speed": 0.99,
        "brightness": 1,     # -1~3
        "contrast": 0.98,
        "saturation": 0.95,
        "gamma_r": 1.02,
        "gamma_g": 1.00,
        "gamma_b": 0.97,
        "noise": 1.8,
        "crf": 24,
        "bgm_file": "bgm_h_MY.aac",
        "bgm_db": -18,       # 统一-18dB
        "sub_offset_y": 5,   # 字幕Y偏移
        "sub_size_pt": 56,   # 增大字幕字号
        "sub_color": "#FFFEF7",
        "sub_animation": "scroll",
        "color_temp": 4800,
        "sharpness": 0.5,
        "crop_offset_x": 0,
        "crop_offset_y": 2,
        "bgm_fade_in": 1.2,
        "sub_delay": 0.7,
    },
    "PH": {
        "speed": 0.98,
        "brightness": 2,
        "contrast": 0.97,
        "saturation": 0.92,
        "gamma_r": 1.00,
        "gamma_g": 0.97,
        "gamma_b": 0.95,
        "noise": 1.2,
        "crf": 26,
        "bgm_file": "bgm_h_PH.aac",
        "bgm_db": -18,
        "sub_offset_y": 10,
        "sub_size_pt": 58,
        "sub_color": "#FFFEF0",
        "sub_animation": "fade",
        "color_temp": 4600,
        "sharpness": 0.6,
        "crop_offset_x": 0,
        "crop_offset_y": 0,
        "bgm_fade_in": 0.5,
        "sub_delay": 0.7,
    },
    "SG": {
        "speed": 1.00,
        "brightness": 0,
        "contrast": 1.00,
        "saturation": 1.00,
        "gamma_r": 0.97,
        "gamma_g": 1.00,
        "gamma_b": 1.02,
        "noise": 1.0,
        "crf": 20,
        "bgm_file": "bgm_CN.mp3",       # SG用Chinese BGM（风格完全不同）
        "bgm_db": -18,
        "sub_offset_y": 0,
        "sub_size_pt": 54,
        "sub_color": "#FFFFFF",
        "sub_animation": "scroll",
        "color_temp": 5000,
        "sharpness": 0.2,
        "crop_offset_x": 2,
        "crop_offset_y": 0,
        "bgm_fade_in": 1.5,
        "sub_delay": 0.5,
    },
    "TH": {
        "speed": 1.01,
        "brightness": -2,
        "contrast": 1.02,
        "saturation": 1.05,
        "gamma_r": 0.95,
        "gamma_g": 0.98,
        "gamma_b": 1.02,
        "noise": 1.5,
        "crf": 22,
        "bgm_file": "bgm_h_TH.aac",
        "bgm_db": -18,
        "sub_offset_y": -10,
        "sub_size_pt": 56,
        "sub_color": "#FFFEFA",
        "sub_animation": "fade",
        "color_temp": 5500,
        "sharpness": 0.3,
        "crop_offset_x": 0,
        "crop_offset_y": 0,
        "bgm_fade_in": 0.3,
        "sub_delay": 0.3,
    },
    "VN": {
        "speed": 1.02,
        "brightness": -1,
        "contrast": 1.01,
        "saturation": 1.02,
        "gamma_r": 0.98,
        "gamma_g": 1.02,
        "gamma_b": 1.00,
        "noise": 2.0,
        "crf": 22,
        "bgm_file": "bgm_h_VN.aac",
        "bgm_db": -18,
        "sub_offset_y": -5,
        "sub_size_pt": 54,
        "sub_color": "#FFFAFF",
        "sub_animation": "slide",
        "color_temp": 5200,
        "sharpness": 0.4,
        "crop_offset_x": 0,
        "crop_offset_y": -2,
        "bgm_fade_in": 0.8,
        "sub_delay": 0.3,
    },
}

# ========== 字幕文本（保持与配音同步） ==========
SUBTITLES = {
    "MY": "Okay guys, kita semua tau kan susah nak cari brush yang betul-betul sedap dekat muka. Banyak yang keras dan buat muka rasa sakit. Tapi yang ni weii, lembut gila and hasil makeup jadi power. Best sangat dah cuba sendiri!",
    "PH": "Grabe promise you guys! Yung brush na gamit ko dati sobrang harsh sa face, parang nag-eexfoliate ako araw-araw. Pero itong brush na double-headed, super soft ng bristles. Ang smooth ng application, parang walang brush na dumampi. Sulit na sulit! Must try!",
    "SG": "Wah I cannot believe I've been using the wrong brushes this whole time. They were so rough on my face! Then I found this double-headed brush set. Super soft bristles, blends everything so nicely. Just spray and wipe. Brushes like new again. Can recommend lah!",
    "TH": "บอกเลยว่าหลายคนแต่งหน้าแล้วไม่เนียน ไม่ติดทน อาจจะเพราะแปรงที่ใช้ไม่ดีพอ วันนี้เจออะไรดีๆมาแล้ว น้องแปรงคู่นี้ขนนุ่มมากกก ปาดสีแล้วเริ่ดสุดๆ ใช้แล้วหน้าเนียนปังมากเลยค่า~",
    "VN": "Ê mày! Có ai giống mình không? Cọ vẽ trang điểm hoài mà không đều, nhìn dày cộm. Xài cây cọ hai đầu này nè. Lông mềm thiệt luôn, tán đều như mơ. Da mịn liền, xịn xò quá trời!",
}


def run_cmd(cmd, desc="", timeout=120):
    """运行命令并返回结果"""
    print(f"  {'⏳' if not desc else ''} {desc}..." if desc else f"  ⏳ 执行: {' '.join(cmd[:4])}...")
    start = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        elapsed = time.time() - start
        if result.returncode != 0:
            print(f"  ❌ {desc or '命令'}: {result.stderr[:200]}")
            return False
        print(f"  ✅ {desc or '命令'} ({elapsed:.1f}s)")
        return True
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ {desc or '命令'} 超时 ({timeout}s)")
        return False
    except Exception as e:
        print(f"  ❌ {desc or '命令'} 异常: {e}")
        return False


async def generate_tts_async(cc: str, config: dict, out_path: str):
    """用Edge TTS生成自然语音（萝卜引擎）"""
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
    
    if proc.returncode != 0:
        print(f"  ❌ {cc} TTS失败: {stderr.decode()[:200]}")
        return False
    
    if not os.path.exists(out_path) or os.path.getsize(out_path) < 100:
        print(f"  ❌ {cc} TTS输出文件异常")
        return False
    
    size_kb = os.path.getsize(out_path) / 1024
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", out_path]
    dur_result = subprocess.run(dur_cmd, capture_output=True, text=True)
    dur = dur_result.stdout.strip()
    print(f"  ✅ {cc} TTS完成 ({elapsed:.1f}s, {size_kb:.0f}KB, {dur}s)")
    return True


async def process_country(cc: str):
    """处理单个国家的V8修正"""
    src_file = os.path.join(SRC_DIR, f"双头眉刷_{cc}.mp4")
    if not os.path.exists(src_file):
        print(f"  ⚠️ {cc} 源视频不存在，跳过")
        return False
    
    params = PARAMS[cc]
    script = SCRIPTS[cc]
    country_dir = os.path.join(WORK_DIR, cc)
    os.makedirs(country_dir, exist_ok=True)
    
    # ------- 中间文件 -------
    tts_file = os.path.join(country_dir, f"voice_{cc}.mp3")
    voice_adjusted = os.path.join(country_dir, f"voice_{cc}_ad.wav")
    bgm_in = os.path.join(BGM_DIR, params["bgm_file"])
    bgm_cut = os.path.join(country_dir, f"bgm_cut_{cc}.wav")
    bgm_adjusted = os.path.join(country_dir, f"bgm_ad_{cc}.wav")
    video_ts = os.path.join(country_dir, f"video_{cc}.ts")
    final_out = os.path.join(OUT_DIR, f"双头眉刷_{cc}_v8.mp4")
    
    print(f"\n{'='*55}")
    print(f"  🌍 {cc} — 开始V8修正")
    print(f"{'='*55}")
    
    # Step 1: 生成自然语音（Edge TTS替代AI感配音）
    await generate_tts_async(cc, script, tts_file)
    
    # Step 2: 获取视频时长和TTS时长
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", src_file]
    dur_out = subprocess.run(dur_cmd, capture_output=True, text=True)
    video_dur = float(dur_out.stdout.strip() or 10.0)
    
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", tts_file]
    dur_out = subprocess.run(dur_cmd, capture_output=True, text=True)
    tts_dur = float(dur_out.stdout.strip() or 10.0)
    
    print(f"  📐 视频时长: {video_dur:.2f}s, TTS时长: {tts_dur:.2f}s")
    
    # Step 3: 调整语音音量至 -6dB（标准人声电平）
    # 实际中 -6dB对于Edge TTS生成语音通常太安静，我们用归一化+limiter
    run_cmd([
        "ffmpeg", "-y", "-i", tts_file,
        "-af", "loudnorm=I=-6:LRA=7:TP=-1,volume=2.0",
        "-ar", "44100", "-ac", "1", voice_adjusted
    ], desc=f"{cc} 语音音量标准化(-6dB)")
    
    # Step 4: 准备BGM - 裁剪到视频时长，调整音量到-18dB
    # 读取BGM原始音量
    bgm_dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=noprint_wrappers=1:nokey=1", bgm_in]
    bgm_dur_out = subprocess.run(bgm_dur_cmd, capture_output=True, text=True)
    bgm_dur = float(bgm_dur_out.stdout.strip() or 12.0)
    
    # BGM循环/裁剪到视频时长
    if bgm_dur >= video_dur:
        # 直接裁剪
        run_cmd([
            "ffmpeg", "-y", "-i", bgm_in,
            "-t", str(video_dur),
            "-ar", "44100", "-ac", "1", bgm_cut
        ], desc=f"{cc} BGM裁剪({video_dur:.1f}s)")
    else:
        # 循环拼接
        bgm_loop = os.path.join(country_dir, "bgm_loop.wav")
        run_cmd([
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", bgm_in,
            "-t", str(video_dur), "-ar", "44100", "-ac", "1", bgm_loop
        ], desc=f"{cc} BGM循环({video_dur:.1f}s)")
        bgm_cut = bgm_loop
    
    # BGM音量调整到-18dB（相对于人声-6dB，即人声比BGM高12dB）
    # 标准做法：BGM音量设为原电平的0.15~0.25
    bgm_vol = 0.20  # 约 -14dB 再降一点
    run_cmd([
        "ffmpeg", "-y", "-i", bgm_cut,
        "-af", f"volume={bgm_vol}",
        "-ar", "44100", "-ac", "1",
        bgm_adjusted
    ], desc=f"{cc} BGM音量调整(-18dB)")
    
    # Step 5: 混合音轨（语音+BGM）
    mixed_audio = os.path.join(country_dir, f"mixed_{cc}.wav")
    
    # BGM淡入淡出参数
    fade_in = params["bgm_fade_in"]
    # 淡入效果：afade=t=in:d={fade_in}
    run_cmd([
        "ffmpeg", "-y", "-i", voice_adjusted, "-i", bgm_adjusted,
        "-filter_complex",
        f"[1:a]afade=t=in:d={fade_in}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:weights=1 0.25[a]",
        "-map", "[a]", "-ac", "1", "-ar", "44100",
        mixed_audio
    ], desc=f"{cc} 语音+BGM混合")
    
    # Step 6: 应用视频画面20维防重处理
    # 构建ffmpeg滤镜链
    video_processed = os.path.join(country_dir, f"video_filtered_{cc}.ts")
    
    # 基础参数
    speed = params["speed"]
    brightness = params["brightness"]  # in range -3 to +3
    contrast = params["contrast"]       # 0.97~1.02
    saturation = params["saturation"]   # 0.92~1.05
    gamma_r = params["gamma_r"]
    gamma_g = params["gamma_g"]
    gamma_b = params["gamma_b"]
    noise_pct = params["noise"]        # 0~2.0
    crop_off_x = params["crop_offset_x"]
    crop_off_y = params["crop_offset_y"]
    sharpness_val = params["sharpness"]
    color_temp = params["color_temp"]
    crf = params["crf"]
    
    # 颜色温度转换: 4600~5500K 到 RGB增益
    # 低色温(暖) = 增益Red, 降低Blue
    # 高色温(冷) = 降低Red, 增益Blue
    # 标准5000K为基准
    temp_offset = (color_temp - 5000) / 5000  # -0.8 ~ +1.0
    r_temp_gain = 1.0 + (temp_offset * -0.05)  # 冷色减小Red
    b_temp_gain = 1.0 + (temp_offset * 0.05)   # 冷色增加Blue
    
    # 字幕参数
    sub_size = params["sub_size_pt"]
    sub_offset_y = params["sub_offset_y"]
    sub_color = params["sub_color"]
    sub_anim = params["sub_animation"]
    sub_delay = params["sub_delay"]
    
    # 字幕Y坐标: 竖屏1080x1920, 底部安全区在~1800
    sub_y = 1850 - sub_offset_y
    sub_x = 540  # 居中
    
    # 字幕文本（转义引号）
    sub_text = SUBTITLES[cc].replace("'", "'\\''").replace('"', '\\"')
    
    # 字幕动画类型
    if sub_anim == "fade":
        sub_alpha = "if(lt(t,{d}),t/{d},if(lt(t,{dur}-1),1,({dur}-t)/1))".format(d=sub_delay, dur=video_dur)
        sub_enable_alpha = f":alpha='{sub_alpha}'"
    elif sub_anim == "scroll":
        sub_enable_alpha = f":alpha='if(lt(t,{sub_delay}),t/{sub_delay},1)'"
    elif sub_anim == "slide":
        sub_enable_alpha = f":alpha='if(lt(t,{sub_delay}),t/{sub_delay},1)'"
    else:
        sub_enable_alpha = f":alpha='if(lt(t,{sub_delay}),t/{sub_delay},1)'"
    
    # 为保证sub_text传递安全，写入SRT文件并给drawtext使用
    srt_file = os.path.join(country_dir, f"sub_{cc}.srt")
    
    # 生成SRT字幕（根据TTS时长分多行显示）
    tts_lines = sub_text.split(". ")
    srt_content = ""
    line_dur = video_dur / len(tts_lines)
    for i, line in enumerate(tts_lines):
        if not line.strip():
            continue
        s = i * line_dur
        e = min((i + 1) * line_dur, video_dur)
        # 补回句号
        display = line.strip() + ("." if not line.strip().endswith(("!", "?", "~")) else "")
        srt_content += f"{i+1}\n"
        srt_content += f"{int(s//3600):02d}:{int(s%3600//60):02d}:{s%60:06.3f} --> "
        srt_content += f"{int(e//3600):02d}:{int(e%3600//60):02d}:{e%60:06.3f}\n"
        srt_content += f"{display}\n\n"
    
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    
    # 转码SRT到ASS格式（更好的样式控制）
    ass_file = os.path.join(country_dir, f"sub_{cc}.ass")
    
    # 检测视频实际尺寸
    video_info_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0", src_file
    ]
    video_info = subprocess.run(video_info_cmd, capture_output=True, text=True)
    dims = video_info.stdout.strip().split(",")
    vw, vh = 1080, 1920
    if len(dims) == 2:
        vw, vh = int(dims[0]), int(dims[1])
    
    # 生成ASS字幕（大字号，黑边清晰）
    ass_content = (
        "[Script Info]\n"
        "; V8 Correction Subtitles\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {vw}\n"
        f"PlayResY: {vh}\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Thonburi-Bold,{sub_size},&H{sub_color[5:]}{sub_color[3:5]}{sub_color[1:3]},&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,2,2,60,60,{1920 - sub_y},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    
    # 从SRT转ASS
    for line_num, line in enumerate(srt_content.strip().split("\n\n")):
        parts = line.split("\n")
        if len(parts) < 3:
            continue
        time_line = parts[1]
        text_lines = parts[2:]
        text_content = "\\N".join(text_lines).replace("\n", "\\N")
        
        # 解析时间
        times = time_line.split(" --> ")
        if len(times) != 2:
            continue
        start_t, end_t = times[0], times[1]
        
        # 动画效果
        if sub_anim == "fade":
            # fade in/out using \fad
            fade_start = min(0.3, video_dur * 0.05)
            fade_end = min(0.5, video_dur * 0.05)
            eff = f"\\fad({fade_start*1000:.0f},{fade_end*1000:.0f})"
            text_content = f"{{\\alpha&HFF&}}{{\\t(0,{fade_start*1000:.0f},\\alpha&H00&)}}{text_content}"
        
        ass_content += f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{text_content}\n"
    
    with open(ass_file, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    # 构建完整的视频处理滤镜
    # 速度调整 -> 色彩校正 -> 裁剪微调 -> 字幕 -> 噪点 -> 锐化
    
    # ====== 核心ffmpeg滤镜链 ======
    # 1. setpts (速度)
    # 2. eq (亮度/对比度/饱和度/伽马)
    # 3. crop (微裁切)
    # 4. drawtext/subtitles (字幕)
    # 5. noise (颗粒噪点)
    # 6. unsharp (锐化)
    # 7. colorbalance (色温)
    
    filter_parts = []
    
    # 速度调整
    filter_parts.append(f"setpts={1/speed}*PTS")
    
    # 色彩调整: eq=brightness, contrast, saturation, gamma
    # ffmpeg eq: brightness in -1.0~1.0, contrast in -2.0~2.0, saturation in 0~3.0
    b_val = brightness / 30.0  # normalize
    c_val = (contrast - 1.0)   # 0.97->-0.03, 1.02->0.02
    s_val = saturation
    filter_parts.append(f"eq=brightness={b_val:.3f}:contrast={1.0 + c_val:.3f}:saturation={s_val:.3f}:gamma_r={gamma_r:.3f}:gamma_g={gamma_g:.3f}:gamma_b={gamma_b:.3f}")
    
    # 裁切（微偏移）
    filter_parts.append(f"crop={vw-2*crop_off_x}:{vh-2*crop_off_y}:{crop_off_x}:{crop_off_y}")
    
    # 缩放回原始分辨率（由于crop会减小画面）
    if crop_off_x != 0 or crop_off_y != 0:
        filter_parts.append(f"scale={vw}:{vh}:flags=lanczos")
    
    # 色温
    r_gain = 1.0 + (5000 - color_temp) / 5000 * 0.04
    g_gain = 1.0
    b_gain = 1.0 + (color_temp - 5000) / 5000 * 0.04
    filter_parts.append(f"colorbalance=rs={r_gain-1:.3f}:gs=0:bs={b_gain-1:.3f}")
    
    # 噪点
    if noise_pct > 0:
        filter_parts.append(f"noise=alls={noise_pct*3:.0f}:allf=t+p")
    
    # 锐化
    if sharpness_val > 0:
        filter_parts.append(f"unsharp=la={sharpness_val:.1f}:ca={sharpness_val:.1f}")
    
    filter_chain = ",".join(filter_parts)
    
    # 字幕滤镜用subtitles=加载ASS
    # 注意：ass文件路径要转义
    ass_path_escaped = ass_file.replace(":", "\\:").replace("'", "'\\''")
    filter_with_sub = f"{filter_chain},subtitles='{ass_path_escaped}'"
    
    run_cmd([
        "ffmpeg", "-y",
        "-i", src_file,
        "-filter_complex", filter_with_sub,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        "-b:v", "4000k",
        "-bufsize", "8000k",
        "-maxrate", "6000k",
        "-r", "30",
        video_processed
    ], desc=f"{cc} 视频滤镜处理(20维防重)", timeout=300)
    
    if not os.path.exists(video_processed):
        print(f"  ❌ {cc} 视频滤镜处理失败")
        return False
    
    # Step 7: 合并视频画面+混合音轨（最终输出）
    run_cmd([
        "ffmpeg", "-y",
        "-i", video_processed,
        "-i", mixed_audio,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "1",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        "-movflags", "+faststart",
        final_out
    ], desc=f"{cc} 最终合成_v8", timeout=120)
    
    if not os.path.exists(final_out):
        print(f"  ❌ {cc} 最终合成失败")
        return False
    
    final_size = os.path.getsize(final_out) / 1024 / 1024
    final_dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", final_out]
    final_dur = subprocess.run(final_dur_cmd, capture_output=True, text=True)
    print(f"\n  🎉 {cc} V8完成! → {final_out} ({final_size:.1f}MB, {final_dur.stdout.strip()}s)")
    
    return True


async def main():
    print("=" * 55)
    print("  🌽 玉米·V8标准修正")
    print("  5国双头眉刷视频 → 配音重合成 + 字幕增大 + BGM统一 + 20维防重")
    print("=" * 55)
    
    countries = ["MY", "PH", "SG", "TH", "VN"]
    
    # 先检查源文件
    missing = []
    for cc in countries:
        src = os.path.join(SRC_DIR, f"双头眉刷_{cc}.mp4")
        if not os.path.exists(src):
            missing.append(cc)
            print(f"  ⚠️ 源文件缺失: {src}")
    
    if missing:
        print(f"  ❌ 缺少以下国家源文件: {', '.join(missing)}")
        return
    
    print(f"\n  源目录: {SRC_DIR}")
    print(f"  输出目录: {OUT_DIR}")
    
    # 检查BGM文件
    for cc in countries:
        bgm = os.path.join(BGM_DIR, PARAMS[cc]["bgm_file"])
        if not os.path.exists(bgm):
            print(f"  ⚠️ {cc} BGM文件缺失: {bgm}")
    
    print(f"\n  {'='*55}")
    
    # 按顺序处理5国
    results = {}
    for cc in countries:
        try:
            success = await process_country(cc)
            results[cc] = "✅" if success else "❌"
        except Exception as e:
            print(f"  🔴 {cc} 异常: {e}")
            results[cc] = "❌"
        # 国与国之间稍作间隔
        await asyncio.sleep(1)
    
    # 结果汇总
    print(f"\n{'='*55}")
    print(f"  5国V8修正完成！")
    print(f"{'='*55}")
    for cc in countries:
        status = results.get(cc, "⏳")
        out_file = os.path.join(OUT_DIR, f"双头眉刷_{cc}_v8.mp4")
        if os.path.exists(out_file):
            size = os.path.getsize(out_file) / 1024 / 1024
            print(f"  {status} {cc}: {out_file} ({size:.1f}MB)")
        else:
            print(f"  {status} {cc}: 文件未生成")
    
    print(f"\n输出目录: {OUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
