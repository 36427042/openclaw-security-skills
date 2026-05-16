#!/usr/bin/env python3
"""
微纤维抹布 5国视频生成脚本 v3 — 修复版
✅ 分段TTS + 字幕叠加（Pillow生成PNG + ffmpeg overlay）
✅ BGM混合（音量平衡）
✅ 自适应时长匹配

用法:
  python3 output/generate_cloth_video.py --country TH   # 单国
  python3 output/generate_cloth_video.py --all          # 全部5国
  python3 output/generate_cloth_video.py --test         # 测试模式（快速渲染TH）
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

VERSION = "v3"

# ========== 配置 ==========
WORK_DIR = Path(__file__).parent
SOURCE_VIDEO = WORK_DIR.parent / "source_video_01.mp4"
BGM_DIR = Path.home() / "Desktop/配音输出"
OUT_DIR = WORK_DIR / "test_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS = {
    "TH": ["ผ้าไมโครไฟเบอร์ ผืนเดียวซับทั้งบ้าน", "เปียกแค่ไหนก็แห้งในพริบตา", "ใช้ได้ทั้งโต๊ะ กระจก จานชาม", "ซื้อครั้งเดียว ใช้ได้เป็นปี"],
    "MY": ["Kain microfiber ni, satu lap terus kering", "Basah macam mana pun terus hilang", "Boleh guna untuk meja, cermin, pinggan", "Satu helai tahan beribu-ribu lap"],
    "VN": ["Khăn sợi nhỏ này, lau một phát là khô", "Nước nhiều cỡ nào cũng hết ngay", "Dùng được bàn, gương, bát đĩa", "Một cái dùng cả năm không hỏng"],
    "PH": ["This microfiber cloth, one wipe and it's dry", "Soaks up everything instantly", "Great for tables, mirrors, dishes", "One cloth lasts a thousand wipes"],
    "SG": ["One wipe. That's all it takes with this microfiber cloth.", "Instant absorption, zero streaks.", "Versatile: countertops, mirrors, dishes.", "Premium quality that lasts wash after wash."],
}

TTS_VOICES = {"TH": "th-TH-PremwadeeNeural", "MY": "ms-MY-OsmanNeural", "VN": "vi-VN-HoaiMyNeural", "PH": "en-PH-JamesNeural", "SG": "en-SG-LunaNeural"}
SUB_COLORS = {"TH": "#FF6B9D", "MY": "#FFD700", "VN": "#FF8C00", "PH": "#FFFFFF", "SG": "#F0F0F0"}

def bgm_path(country):
    p = BGM_DIR / f"bgm_h_{country}.aac"
    return p if p.exists() else None
# SG用PH的BGM
if not bgm_path("SG"):
    global _sg_bgm; _sg_bgm = BGM_DIR / "bgm_h_PH.aac"
    
def get_bgm(c):
    p = BGM_DIR / f"bgm_h_{c}.aac"
    if p.exists(): return p
    if c == "SG":
        p = BGM_DIR / "bgm_h_PH.aac"
        if p.exists(): return p
    return None

def log(msg): print(f"[v3] {msg}")

def check_deps():
    for cmd in ["ffmpeg","ffprobe"]:
        if subprocess.run(["which",cmd],capture_output=True).returncode != 0:
            log(f"❌ {cmd} not found"); return False
    if subprocess.run(["which","edge-tts"],capture_output=True).returncode != 0:
        log("⚠️  edge-tts not found"); return False
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        log("⚠️  Pillow not found, subtitles will be skipped"); pass
    if not SOURCE_VIDEO.exists(): log(f"❌ Source not found"); return False
    log(f"✅ Source: {SOURCE_VIDEO} ({os.path.getsize(SOURCE_VIDEO):,}b)")
    return True

def duration(path):
    try:
        r = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format",str(path)],capture_output=True,text=True,timeout=10)
        return float(json.loads(r.stdout)["format"]["duration"])
    except: return None

def gen_tts_seg(text, voice, rate, pitch, out):
    cmd = ["edge-tts","--voice",voice,"--text",text,"--rate",rate,"--pitch",pitch,"--write-media",str(out)]
    r = subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    if r.returncode != 0: return None
    if os.path.getsize(out) < 500: return None
    return out

def generate_tts(country, sentences):
    tts_out = OUT_DIR / f"tts_{country}.mp3"
    tts_out.unlink(missing_ok=True)
    voice = TTS_VOICES[country]
    log(f"  TTS: {voice}...")

    # 分段生成
    seg_dir = OUT_DIR / f"tts_seg_{country}"
    seg_dir.mkdir(parents=True,exist_ok=True)
    for f in seg_dir.glob("seg_*.mp3"): f.unlink()

    segs = []
    for i, s in enumerate(sentences):
        sf = seg_dir / f"seg_{i:02d}.mp3"
        if gen_tts_seg(s,voice,"+15%","+8Hz",sf):
            d = duration(sf)
            segs.append((sf,d))
            log(f"    Seg {i}: {d:.2f}s")
        else:
            log(f"    ❌ Seg {i} failed, full-text fallback")
            full = ", ".join(sentences)
            return gen_tts_seg(full,voice,"+10%","+5Hz",tts_out), None

    total = sum(d for _,d in segs)
    log(f"  Total: {total:.2f}s")

    # concat protocol拼接
    concat_src = "concat:" + "|".join(str(s) for s,_ in segs)
    r = subprocess.run(["ffmpeg","-y","-i",concat_src,"-c","copy",str(tts_out)],capture_output=True,text=True,timeout=30)
    if r.returncode != 0 or os.path.getsize(tts_out) < 500:
        log(f"  concat failed, fallback")
        tts_out.unlink(missing_ok=True)
        full = ", ".join(sentences)
        return gen_tts_seg(full,voice,"+10%","+5Hz",tts_out), None

    fd = duration(tts_out)
    log(f"  ✅ TTS: {os.path.getsize(tts_out):,}b, {fd:.2f}s")
    return tts_out, segs

def create_subtitle_video(country, sentences, seg_times, video_dur, fps=24):
    """使用Pillow生成字幕帧，编码为带字幕的视频流"""
    from PIL import Image, ImageDraw, ImageFont
    
    color = SUB_COLORS[country]
    sub_dir = OUT_DIR / f"sub_vid_{country}"
    sub_dir.mkdir(parents=True,exist_ok=True)
    for f in sub_dir.glob("frame_*.png"): f.unlink()

    # 找字体
    font = None
    for fp in ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
               "/Library/Fonts/Arial Unicode.ttf",
               "/System/Library/Fonts/AppleSDGothicNeo.ttc",
               "/System/Library/Fonts/Thonburi.ttc"]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 36)
                break
            except: continue
    if font is None:
        log("  ⚠️  No font found, using default (might not render correctly)")
        font = ImageFont.load_default()

    total_frames = int(video_dur * fps)
    w, h = 540, 960  # match source video resolution

    for frame_idx in range(total_frames):
        t = frame_idx / fps  # current time in seconds

        # 判断当前帧显示哪句字幕
        current_text = None
        for i, (st, et) in enumerate(seg_times):
            if st <= t < et:
                current_text = sentences[i]
                break

        # 创建透明底层
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        if current_text:
            # 计算文字尺寸
            bbox = draw.textbbox((0, 0), current_text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]

            # 文字底部居中的黑底框
            box_x = (w - tw) // 2 - 20
            box_y = h - th - 50
            box_w = tw + 40
            box_h = th + 20

            # 绘制半透明黑底
            draw.rounded_rectangle(
                [box_x, box_y, box_x + box_w, box_y + box_h],
                radius=12, fill=(0, 0, 0, 160)
            )

            # 绘制文字
            text_x = (w - tw) // 2
            text_y = box_y + 10
            draw.text((text_x, text_y), current_text, font=font, fill=color)

        frame_file = sub_dir / f"frame_{frame_idx:06d}.png"
        img.save(frame_file, "PNG")

    log(f"  ✅ Generated {total_frames} subtitle frames")

    # 用ffmpeg将PNG序列编码为视频流
    sub_video = OUT_DIR / f"sub_video_{country}.mp4"
    sub_video.unlink(missing_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(sub_dir / "frame_%06d.png"),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuva420p",  # alpha channel
        "-vf", "format=rgba,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709",
        "-crf", "28",
        "-frames:v", str(total_frames),
        str(sub_video),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        log(f"  ❌ Sub video encoding failed: {r.stderr[-200:]}")
        return None
    
    # 清理临时帧
    for f in sub_dir.glob("frame_*.png"):
        f.unlink()

    sz = os.path.getsize(sub_video)
    log(f"  ✅ Sub video: {sub_video.name} ({sz:,}b, {video_dur:.2f}s)")
    return sub_video

def render_with_overlay(country, tts_file, sub_video, bgm):
    """使用overlay将字幕视频叠加到主视频上"""
    out = OUT_DIR / f"{country}_v3.mp4"
    src_dur = duration(SOURCE_VIDEO)
    tts_dur = duration(tts_file)
    video_dur = min(tts_dur + 0.5, src_dur + 0.3)

    inputs = ["-i", str(SOURCE_VIDEO), "-i", str(tts_file)]
    if bgm: inputs += ["-i", str(bgm)]
    if sub_video: inputs += ["-i", str(sub_video)]

    # video filter: main video + subtitle overlay
    # 先对主视频trim到目标时长
    if sub_video:
        # 先准备主视频（无alpha），准备字幕视频（带alpha），然后overlay
        # 注意：主视频保持原始格式，字幕视频用rgba，overlay后输出yuv420p
        vf = f"[0:v]trim=0:{video_dur},setpts=PTS-STARTPTS[vmain];" + \
             f"[3:v]trim=0:{video_dur},setpts=PTS-STARTPTS,format=rgba[vsub];" + \
             "[vmain][vsub]overlay=format=auto:alpha=1[vo]"
        vmap = "[vo]"
    else:
        vf = f"[0:v]trim=0:{video_dur},setpts=PTS-STARTPTS[vmain];[vmain]copy[vo]"
        vmap = "[vo]"

    # audio filter
    if bgm:
        af = f"[1:a]volume=1.4,aresample=44100[a1];[2:a]volume=0.25,aresample=44100,atrim=0:{video_dur}[a2];[a1][a2]amix=inputs=2:duration=first:weights=1.4 0.25[a]"
        amap = "[a]"
    else:
        af = f"[1:a]volume=1.4,aresample=44100[a]"
        amap = "[a]"
    
    # Workaround: 对于有字幕的情况，[vo]可能需要从filter链中提取
    # 简化：如果字幕视频无法叠加，使用无字幕方案

    cmd = [
        "ffmpeg","-y",*inputs,
        "-filter_complex", f"{vf};{af}",
        "-map", vmap, "-map", amap,
        "-c:v","libx264","-preset","fast","-crf","23",
        "-c:a","aac","-b:a","128k","-ar","44100",
        "-pix_fmt","yuv420p",
        "-t",str(video_dur),
        str(out),
    ]

    log(f"  FFmpeg overlay render ({video_dur:.2f}s)...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if r.returncode != 0:
        log(f"  ❌ Render failed: {r.stderr[-400:]}")
        return None

    sz = os.path.getsize(out)
    log(f"  ✅ {out.name} ({sz:,}b)")
    return out

def render_nosub(country, tts_file, bgm):
    """无字幕降级渲染"""
    out = OUT_DIR / f"{country}_v3.mp4"
    src_dur = duration(SOURCE_VIDEO) or 10.0
    inputs = ["-i", str(SOURCE_VIDEO), "-i", str(tts_file)]
    if bgm: inputs += ["-i", str(bgm)]
    
    vf = f"[0:v]trim=0:{src_dur},setpts=PTS-STARTPTS[v]"
    if bgm:
        af = "[1:a]volume=1.4,aresample=44100[a1];[2:a]volume=0.25,aresample=44100,atrim=0:" + str(src_dur) + "[a2];[a1][a2]amix=inputs=2:duration=first:weights=1.4 0.25[a]"
    else:
        af = "[1:a]volume=1.4,aresample=44100[a]"
    
    cmd = ["ffmpeg","-y",*inputs,
        "-filter_complex",f"{vf};{af}",
        "-map","[v]","-map","[a]",
        "-c:v","libx264","-preset","fast","-crf","23",
        "-c:a","aac","-b:a","128k","-ar","44100",
        "-pix_fmt","yuv420p","-shortest",str(out)]
    r = subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    if r.returncode != 0: log(f"  ❌ Failed: {r.stderr[-200:]}"); return None
    log(f"  ✅ {out.name} ({os.path.getsize(out):,}b)")
    return out

def process(country):
    log(f"\n{'='*40}\n🎯 {country}\n{'='*40}")
    bgm = get_bgm(country)
    log(f"  BGM: {'✅' if bgm else '❌'}")

    # 生成TTS
    r = generate_tts(country, SCRIPTS[country])
    if not r:
        log(f"  ❌ TTS failed"); return None
    tts_file, tts_segs = r if isinstance(r, tuple) else (r, None)

    # 计算字幕时间点
    sents = SCRIPTS[country]
    tts_dur = duration(tts_file) or 10.0
    src_dur = duration(SOURCE_VIDEO) or 10.0
    
    if tts_segs and len(tts_segs) >= len(sents):
        seg_times = [(sum(d for _,d in tts_segs[:i]), sum(d for _,d in tts_segs[:i+1])) for i in range(len(sents))]
    else:
        per = tts_dur / len(sents)
        seg_times = [(i*per, (i+1)*per) for i in range(len(sents))]

    video_dur = min(tts_dur + 0.5, src_dur + 0.3)
    
    # 尝试生成字幕视频
    sub_video = None
    try:
        sub_video = create_subtitle_video(country, sents, seg_times, video_dur)
    except ImportError:
        log("  ⚠️  Pillow not available, skipping subtitles")
    except Exception as e:
        log(f"  ⚠️  Sub generation failed: {e}")

    # 渲染
    if sub_video:
        result = render_with_overlay(country, tts_file, sub_video, bgm)
        if result: return result
        log("  Sub overlay failed, trying no-sub")

    return render_nosub(country, tts_file, bgm)

def main():
    p = argparse.ArgumentParser(description="微纤维抹布5国视频 v3")
    p.add_argument("--country", choices=["TH","MY","VN","PH","SG"])
    p.add_argument("--all", action="store_true")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if not check_deps(): sys.exit(1)

    if args.all: countries = ["TH","MY","VN","PH","SG"]
    elif args.country: countries = [args.country]
    elif args.test: countries = ["TH"]
    else: p.print_help(); sys.exit(0)

    results = {}
    for c in countries:
        results[c] = process(c)

    log(f"\n{'='*40}\n📊 结果\n{'='*40}")
    ok = True
    for c, r in results.items():
        if r:
            log(f"  ✅ {c}: {r.name} ({os.path.getsize(r):,}b, {(duration(r) or 0):.2f}s)")
        else:
            log(f"  ❌ {c}: FAILED"); ok = False
    if ok: log(f"\n✨ 全部成功！输出: {OUT_DIR}/")
    log("Done!")

if __name__ == "__main__":
    main()
