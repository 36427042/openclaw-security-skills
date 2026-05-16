#!/usr/bin/env python3
"""
video_mix_6country.py — 源视频 → 6国防重混剪 (接入DeerFlow Step2)

功能:
  1. 横屏→竖屏 (9:16, 1080x1920) 转换
  2. 多国语言字幕烧录 (PIL生成字幕图片 + ffmpeg overlay)
  3. 6国独立防重指纹 (speed/bright/contrast/colorbalance/CRF)

用法:
  # 全流程：竖屏+字幕+防重混剪
  python3 video_mix_6country.py --source-dir ~/Desktop/源视屏 --output-dir ~/Desktop/输出视频 --preprocess --product "收纳篮"

  # 仅防重混剪（源视频已预处理OK）
  python3 video_mix_6country.py --source-dir ~/Desktop/已处理视频 --output-dir ~/Desktop/输出视频

GEP: 记录每次混剪参数，学习最优crf/码率组合
"""
import os, sys, json, subprocess, hashlib, textwrap
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── GEP集成 ──
try:
    from gep_engine import GEP
    gep = GEP("玉米")
except ImportError:
    gep = None

# ── 防重参数（6国不同指纹）──
ANTI_DUP = {
    "CN": {"speed": 0.998, "bright": 0.01, "contrast": 1.01, "rgb": (0, 0, 0),   "crf": 20},
    "TH": {"speed": 0.995, "bright": 0.02, "contrast": 1.02, "rgb": (0.008, 0, 0), "crf": 20},
    "MY": {"speed": 1.003, "bright": -0.01,"contrast": 0.99, "rgb": (0, 0.008, 0), "crf": 19},
    "VN": {"speed": 0.992, "bright": 0.03, "contrast": 1.03, "rgb": (0, 0, 0.004), "crf": 21},
    "PH": {"speed": 1.005, "bright": 0.0,  "contrast": 1.00, "rgb": (0.004, 0.004, 0), "crf": 20},
    "SG": {"speed": 1.000, "bright": -0.02,"contrast": 0.98, "rgb": (0, 0, 0.008), "crf": 18},
}

COUNTRIES = ["CN", "TH", "MY", "VN", "PH", "SG"]

# ── 目标竖屏尺寸 ──
TARGET_W, TARGET_H = 1080, 1920  # 9:16 TikTok竖屏
FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"  # 支持CJK+泰文+越南文

# ── 产品名 → 字幕文案映射 ──
#
# 字幕数据结构:
#   product: {
#     "CN": {"top": "顶部标语", "bottom": "底部产品名"},
#     "TH": {"top": "...", "bottom": "..."},
#     ...
#   }
#
SUBTITLE_DB = {
    "收纳篮": {
        "CN": {"top": "一键整洁，收纳无忧", "bottom": "高品质收纳篮"},
        "TH": {"top": "จัดระเบียบได้ง่ายในคลิกเดียว", "bottom": "ตะกร้าเก็บของคุณภาพสูง"},
        "MY": {"top": "Kemas satu klik, senang tak payah", "bottom": "Bakul simpanan berkualiti tinggi"},
        "VN": {"top": "Ngăn nắp chỉ một chạm", "bottom": "Giỏ đựng chất lượng cao"},
        "PH": {"top": "Ayusin sa isang pindot lang", "bottom": "Mataas na kalidad na basket"},
        "SG": {"top": "One-click tidy, hassle-free storage", "bottom": "Premium quality storage basket"},
    },
    "粉底刷": {
        "CN": {"top": "服帖底妆，一抹即匀", "bottom": "专业粉底刷"},
        "TH": {"top": "รองพื้นที่เนียนกริบ แปรงเดียวจบ", "bottom": "แปรงรองพื้นคุณภาพสูง"},
        "MY": {"top": "Foundation sekata sempurna", "bottom": "Berus foundation profesional"},
        "VN": {"top": "Nền mịn chỉ một lần quét", "bottom": "Cọ nền chuyên nghiệp"},
        "PH": {"top": "Perpektong foundation sa isang stroke", "bottom": "Propesyonal na foundation brush"},
        "SG": {"top": "Flawless base, one sweep", "bottom": "Professional foundation brush"},
    },
    "双头眉刷": {
        "CN": {"top": "精致眉形，轻松勾勒", "bottom": "双头精细眉刷"},
        "TH": {"top": "คิ้วเป๊ะทุกเส้น", "bottom": "แปรงเขียนคิ้วสองหัว"},
        "MY": {"top": "Kening cantik senang je", "bottom": "Berus kening dua hujung"},
        "VN": {"top": "Chân mày sắc nét dễ dàng", "bottom": "Cọ kẻ mày hai đầu"},
        "PH": {"top": "Perpektong kilay, madali lang", "bottom": "Brush ng kilay dalawang dulo"},
        "SG": {"top": "Perfect brows, effortless", "bottom": "Dual-end fine eyebrow brush"},
    },
}


def get_probe(src: str) -> dict:
    """获取视频元数据"""
    if isinstance(src, Path):
        src = str(src)
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", src],
        capture_output=True, text=True, timeout=15
    )
    return json.loads(r.stdout)


def has_audio(probe: dict) -> bool:
    """检查视频是否有音频流"""
    return any(s.get("codec_type") == "audio" for s in probe.get("streams", []))


def get_video_dims(src: str) -> tuple:
    """获取视频尺寸 (w, h)"""
    p = get_probe(src)
    for s in p.get("streams", []):
        if s.get("codec_type") == "video":
            return s.get("width", 0), s.get("height", 0)
    return (0, 0)


def get_fps(src: str) -> float:
    """获取视频fps"""
    p = get_probe(src)
    for s in p.get("streams", []):
        if s.get("codec_type") == "video":
            r = s.get("r_frame_rate", "24/1")
            num, den = r.split("/")
            return float(num) / float(den)
    return 24.0


def make_subtitle_png(text: str, width: int, height: int,
                      font_size: int = 42, is_top: bool = True) -> str:
    """
    用PIL生成字幕PNG图片（透明背景+白色文字+黑边阴影）
    overlay滤镜用它叠加到视频上
    """
    if not HAS_PIL:
        return None

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 加载字体
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()
        print(f"     ⚠️ 字体加载失败，使用默认字体: {FONT_PATH}")

    # 文字居中
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) // 2
    y = 40 if is_top else height - text_h - 80

    # 阴影（黑底）
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 180))
    # 白色文字
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    return img


def preprocess_video(src: str, tmp_dir: str, country: str, product: str) -> str:
    """
    单视频预处理：横屏→竖屏 + 字幕烧录
    返回预处理后的视频路径
    """
    name = Path(src).stem
    out_path = os.path.join(tmp_dir, f"{country}_pre.mp4")

    # 检查缓存
    if os.path.exists(out_path):
        return out_path

    os.makedirs(tmp_dir, exist_ok=True)
    w, h = get_video_dims(src)
    fps = get_fps(src)

    # Step 1: 横屏→竖屏转换（先用ffmpeg做scale+crop）
    temp_vert = os.path.join(tmp_dir, f"vert.mp4")
    vert_filters = []

    if w > h:
        # 横屏(1280x720) → 竖屏(1080x1920)
        # 方案：scale让宽达到1080（内容最大化），上下加黑边
        # 或：scale让高充满，裁剪宽到1080
        # 1280x720 → scale高度到1920: 1280*(1920/720)=3413x1920 → crop到1080x1920
        # 这样内容比例正确且有覆盖面
        vert_filters.append(
            f"scale=-2:{TARGET_H},crop={TARGET_W}:{TARGET_H}:(iw-{TARGET_W})/2:0"
        )
    elif h > w and h > TARGET_H:
        # 竖屏但分辨率更高，scale down
        vert_filters.append(f"scale={TARGET_W}:{TARGET_H}")
    else:
        # 已经是竖屏且尺寸匹配，直接copy
        pass

    if vert_filters:
        vf = ",".join(vert_filters)
        subprocess.run([
            "ffmpeg", "-y", "-i", src,
            "-vf", vf,
            "-c:v", "libx264", "-crf", "18",
            "-preset", "fast",
            "-an",  # 暂不处理音频，等字幕叠加完一并处理
            temp_vert
        ], capture_output=True, text=True, timeout=180)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-i", src,
            "-c:v", "libx264", "-crf", "18",
            "-preset", "fast",
            "-an",
            temp_vert
        ], capture_output=True, text=True, timeout=180)

    # Step 2: 生成字幕PNG
    subs = get_subtitle_text(country, product)
    overlay_inputs = [temp_vert]
    filter_complex_parts = ["[0:v]setpts=PTS[v0]"]
    overlay_idx = 1

    top_text = subs.get("top", "")
    bottom_text = subs.get("bottom", "")

    subtitle_labels = []
    sub_images = []

    if top_text:
        top_png = make_subtitle_png(top_text, TARGET_W, TARGET_H, font_size=42, is_top=True)
        if top_png:
            top_path = os.path.join(tmp_dir, "sub_top.png")
            top_png.save(top_path)
            sub_images.append(top_path)
            subtitle_labels.append(f"[{overlay_idx}:v]")

    if bottom_text:
        bottom_png = make_subtitle_png(bottom_text, TARGET_W, TARGET_H, font_size=40, is_top=False)
        if bottom_png:
            bottom_path = os.path.join(tmp_dir, "sub_bottom.png")
            bottom_png.save(bottom_path)
            sub_images.append(bottom_path)
            subtitle_labels.append(f"[{overlay_idx}:v]")

    # Step 3: 叠加字幕到视频
    if sub_images:
        # 建overlay命令
        cmd = ["ffmpeg", "-y", "-i", temp_vert]
        for sub_path in sub_images:
            cmd.extend(["-i", sub_path])

        # overlay滤镜：顶部字幕在y=0，底部字幕在底部
        # 字幕PNG已按正确尺寸生成，直接overlay
        overlay_filters = []
        current_label = "v0"

        for i, sub_path in enumerate(sub_images):
            label = f"overlay_{i}"
            if "top" in sub_path:
                overlay_filters.append(
                    f"[{current_label}][{i+1}:v]overlay=0:0[{label}]"
                )
            else:
                overlay_filters.append(
                    f"[{current_label}][{i+1}:v]overlay=0:0[{label}]"
                )
            current_label = label

        cmd.extend([
            "-filter_complex", ";".join(overlay_filters),
            "-map", f"[{current_label}]",
            "-c:v", "libx264", "-crf", "18",
            "-preset", "fast",
            out_path
        ])
    else:
        # 没有字幕，直接把临时文件当输出
        cmd = ["cp", temp_vert, out_path]
        subprocess.run(cmd)
        return out_path

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"      字幕叠加失败: {r.stderr[:300]}")
        # fallback: 直接返回竖屏版
        cmd2 = ["cp", temp_vert, out_path]
        subprocess.run(cmd2)
    else:
        # 清理临时文件
        try:
            os.remove(temp_vert)
            for p in sub_images:
                os.remove(p)
        except:
            pass

    return out_path


def get_subtitle_text(country: str, product: str) -> dict:
    """获取指定产品+国家的字幕文案"""
    if not product:
        return {"top": "", "bottom": ""}

    # 精确匹配
    if product in SUBTITLE_DB:
        db = SUBTITLE_DB[product]
        return db.get(country, db.get("CN", {"top": "", "bottom": ""}))

    product_lower = product.lower().strip()

    # 模糊匹配
    for key, val in SUBTITLE_DB.items():
        if key.lower() in product_lower or product_lower in key.lower():
            return val.get(country, val.get("CN", {"top": "", "bottom": ""}))

    return {"top": "", "bottom": ""}


def mix_video(src: str, out_dir: str, country: str, params: dict,
              preprocessed: bool = False, pre_dir: str = None,
              output_name: str = None) -> dict:
    """对单个视频做防重混剪"""
    name = output_name or Path(src).stem

    # 输出目录结构: out_dir/产品名/产品名_CN.mp4
    out_path = os.path.join(out_dir, name, f"{name}_{country}.mp4")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 如果有预处理输出，用预处理后的视频作为输入
    video_input = src
    if preprocessed and pre_dir:
        pre_path = os.path.join(pre_dir, f"{country}_pre.mp4")
        if os.path.exists(pre_path):
            video_input = pre_path

    speed, bright, contrast, rgb, crf = (
        params["speed"], params["bright"], params["contrast"],
        params["rgb"], params["crf"]
    )

    vf_parts = [f"setpts={speed}*PTS",
                f"eq=brightness={bright}:contrast={contrast}"]

    if any(rgb):
        r_val, g_val, b_val = rgb
        if r_val: vf_parts.append(f"colorbalance=rs={r_val}")
        if g_val: vf_parts.append(f"colorbalance=gs={g_val}")
        if b_val: vf_parts.append(f"colorbalance=bs={b_val}")

    vf = ",".join(vf_parts)

    cmd = [
        "ffmpeg", "-y", "-i", video_input,
        "-vf", vf,
        "-c:v", "libx264", "-crf", str(crf),
        "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",  # 保留并转码音频
        out_path
    ]

    start = datetime.now()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    elapsed = (datetime.now() - start).total_seconds()

    size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    md5 = hashlib.md5(open(out_path, "rb").read()).hexdigest() if size else "MISSING"

    probe_out = get_probe(out_path) if os.path.exists(out_path) else {}
    vid_out = next((s for s in probe_out.get("streams", []) if s["codec_type"] == "video"), {})
    has_audio_out = has_audio(probe_out)

    return {
        "video": name, "country": country,
        "file": out_path, "size_mb": round(size / 1024 / 1024, 2),
        "md5": md5[:8], "crf": crf,
        "duration_s": round(elapsed, 1),
        "resolution": f"{vid_out.get('width','?')}x{vid_out.get('height','?')}",
        "has_audio": has_audio_out,
        "success": result.returncode == 0,
    }


def main(source_dir: str, output_dir: str, preprocess: bool = False,
         product: str = None, temp_dir: str = None, output_name: str = None):
    """批量处理源视频 → 6国防重混剪"""
    # 收集视频文件
    videos = sorted(Path(source_dir).glob("*.mp4"))
    if not videos:
        videos = sorted(Path(source_dir).glob("*.mov"))
    if not videos:
        videos = sorted(Path(source_dir).glob("*.MOV"))
    if not videos:
        print(json.dumps({"status": "error", "error": f"无视频文件: {source_dir}"}))
        return 1

    if preprocess and not HAS_PIL:
        print(json.dumps({"status": "error", "error": "预处理模式需要PIL: pip3 install Pillow"}))
        return 1

    # 输出名称（默认用产品名或源文件名）
    product_name = output_name or product or Path(videos[0]).stem
    # 清理特殊字符做目录名
    safe_name = "".join(c for c in product_name if c.isalnum() or c in "_- " ).strip()
    if not safe_name:
        safe_name = "product"
    safe_name = safe_name[:60]  # 限制长度

    # 预处理目录（每个源视频独享一个子目录，避免缓存冲突）
    pre_dir = temp_dir or os.path.join(output_dir, ".preprocessed")
    if preprocess:
        os.makedirs(pre_dir, exist_ok=True)
        print(f"  📐 预处理模式: 竖屏转换+字幕烧录")
        print(f"  🏷️  产品: {product_name}")
        print(f"  📂 预处理目录: {pre_dir}")

        for vid in videos:
            # 每个源视频独立子目录，避免缓存冲突
            vid_hash = hashlib.md5(str(vid).encode()).hexdigest()[:8]
            vid_cache = os.path.join(pre_dir, f"{safe_name}_{vid_hash}")
            print(f"\n  🎬 预处理: {vid.name} (→ {TARGET_W}x{TARGET_H})")
            for c in COUNTRIES:
                start = datetime.now()
                pre_out = preprocess_video(str(vid), vid_cache, c, product_name)
                elapsed = (datetime.now() - start).total_seconds()
                size = os.path.getsize(pre_out) if os.path.exists(pre_out) else 0
                status = "✅" if os.path.exists(pre_out) else "❌"
                res = get_video_dims(pre_out) if os.path.exists(pre_out) else (0, 0)
                print(f"    {status} {c}: {res[0]}x{res[1]} | {size/1024/1024:.1f}MB ({elapsed:.0f}s)")
        print(f"  ✅ 预处理完成\n")

    # 防重混剪
    results = []
    errors = []
    total_start = datetime.now()

    print(f"  {'='*50}")
    print(f"  🎯 6国防重混剪")
    print(f"  {'='*50}")

    for vid in videos:
        print(f"\n  🌽 处理: {vid.name}")
        vid_hash = hashlib.md5(str(vid).encode()).hexdigest()[:8]
        vid_pre_dir = os.path.join(pre_dir, f"{safe_name}_{vid_hash}") if preprocess else None
        for c in COUNTRIES:
            r = mix_video(str(vid), output_dir, c, ANTI_DUP[c],
                          preprocessed=preprocess, pre_dir=vid_pre_dir,
                          output_name=safe_name)
            results.append(r)
            status = "✅" if r["success"] else "❌"
            details = f"{r['resolution']} | {r['size_mb']}MB | md5={r['md5']}"
            details += " 🔊" if r["has_audio"] else " ⚠️无音频"
            print(f"    {status} {r['country']}: {details} ({r['duration_s']}s)")
            if not r["success"]:
                errors.append(r)

    total_time = round((datetime.now() - total_start).total_seconds(), 1)

    # 防重验证
    md5s = [r["md5"] for r in results if r["success"]]
    unique = len(set(md5s))
    dup = (len(md5s) - unique) > 0

    summary = {
        "status": "completed" if not errors else "completed_with_errors",
        "mode": "preprocess_mix" if preprocess else "mix_only",
        "product": product or "auto",
        "source_videos": len(videos),
        "total_outputs": len(results),
        "success_count": len(md5s),
        "error_count": len(errors),
        "unique_md5": unique,
        "has_duplicate": dup,
        "total_size_mb": round(sum(r["size_mb"] for r in results), 1),
        "total_time_s": total_time,
        "output_dir": output_dir,
        "files": [{"name": r["video"], "country": r["country"],
                    "size_mb": r["size_mb"], "md5": r["md5"],
                    "resolution": r["resolution"], "has_audio": r["has_audio"]}
                  for r in results if r["success"]],
    }

    # GEP记录
    if gep:
        try:
            gep.post_record(
                task="6国防重混剪",
                context={
                    "videos": [v.name for v in videos],
                    "countries": COUNTRIES,
                    "mode": "preprocess_mix" if preprocess else "mix_only",
                    "product": product
                },
                outcome="success" if not errors else "partial",
                note=f"{len(videos)}视频→{len(md5s)}输出, {unique}唯一指纹, {total_time}s"
            )
        except:
            pass

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="6国防重混剪（竖屏+字幕+防重）")
    parser.add_argument("--source-dir", default=os.path.expanduser("~/Desktop/源视屏"),
                        help="源视频目录（默认: ~/Desktop/源视屏）")
    parser.add_argument("--output-dir", default=os.path.expanduser("~/Desktop/输出视频"),
                        help="输出目录（默认: ~/Desktop/输出视频）")
    parser.add_argument("--preprocess", action="store_true",
                        help="打开预处理模式：自动做竖屏转换+字幕烧录")
    parser.add_argument("--product", default=None,
                        help="产品名称，用于自动字幕文案匹配")
    parser.add_argument("--temp-dir", default=None,
                        help="预处理中间目录（默认: output/.preprocessed）")
    parser.add_argument("--output-name", default=None,
                        help="输出子目录名（默认: --product 值或源文件名）")
    args = parser.parse_args()
    sys.exit(main(args.source_dir, args.output_dir, args.preprocess,
                  args.product, args.temp_dir, args.output_name))
