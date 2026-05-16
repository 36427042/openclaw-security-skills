#!/usr/bin/env python3
"""
🎬 视频全感知脚本
- 抽帧分析画面（通过 qwen3.5-plus 多模态 API）
- 提取音频转文字（通过 faster-whisper）
- 综合输出视频描述（画面+对话+时间线）
"""

import sys, os, json, time, tempfile, subprocess, argparse
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
SKILL_DIR = WORKSPACE / "skills" / "faster-whisper"

# ─── 配置 ───
OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"

def load_api_config():
    """从 OpenClaw 配置中获取 Qwen 多模态 API 信息"""
    with open(OPENCLAW_CONFIG) as f:
        cfg = json.load(f)
    providers = cfg.get("models", {}).get("providers", {})
    qwen = providers.get("qwen", {})
    api_key = qwen.get("apiKey", "")
    base_url = qwen.get("baseUrl", "https://coding.dashscope.aliyuncs.com/v1")
    # Find the image-capable model
    model_id = "qwen3.5-plus"
    return api_key, base_url, model_id


def extract_audio(video_path, audio_path, sample_rate=16000):
    """用 ffmpeg 提取音频"""
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le",
        "-ar", str(sample_rate), "-ac", "1",
        "-y", str(audio_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  ✅ 音频提取完成: {audio_path}")


def extract_frames(video_path, output_dir, interval=3):
    """每 N 秒抽一帧"""
    # 先获取视频时长
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True, check=True
    )
    duration = float(probe.stdout.strip())
    
    fps = 1.0 / interval
    output_pattern = str(output_dir / "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps},scale=1024:-1",
        "-q:v", "5", "-y", str(output_pattern)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    
    # 列出提取的帧文件
    frames = sorted(output_dir.glob("frame_*.jpg"))
    print(f"  ✅ 提取了 {len(frames)} 帧（每 {interval}秒/帧，视频总长 {duration:.1f}秒）")
    return frames, duration


def analyze_frame_via_api(frame_path, api_key, base_url, model_id):
    """通过 Qwen 多模态 API 分析单帧画面"""
    import requests
    
    # Read image as base64
    import base64
    with open(frame_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    
    # Detect format
    ext = frame_path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", 
                ".png": "image/png", ".webp": "image/webp"}
    mime = mime_map.get(ext, "image/jpeg")
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请用中文详细描述这张图片中的所有内容：人物、物体、场景、文字、颜色、动作等。"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}}
                ]
            }
        ],
        "max_tokens": 500
    }
    
    # Retry up to 3 times with longer timeout
    for attempt in range(3):
        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=120
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                return f"[分析失败: HTTP {resp.status_code}]"
        except Exception as e:
            if attempt < 2:
                print(f"⏳ 重试 {attempt+1}/3...", end=" ", flush=True)
                time.sleep(5)
            else:
                return f"[分析失败: {e}]"


def transcribe_audio(audio_path):
    """用 faster-whisper 转写音频"""
    script = SKILL_DIR / "scripts" / "transcribe.py"
    if not script.exists():
        return "[错误: faster-whisper 未安装]"
    
    # Use the skill's venv python
    venv_python = SKILL_DIR / ".venv" / "bin" / "python3"
    if venv_python.exists():
        python_exe = str(venv_python)
    else:
        python_exe = "python3"
    result = subprocess.run(
        [python_exe, str(script), str(audio_path), "--format", "text"],
        capture_output=True, text=True, timeout=600,
        env={**os.environ, "HF_ENDPOINT": "https://hf-mirror.com"}
    )
    
    if result.returncode == 0:
        # Try common output paths
        for suffix in [".txt", ".text", "_output.txt"]:
            out_txt = audio_path.with_suffix(suffix)
            if out_txt.exists():
                with open(out_txt) as f:
                    return f.read().strip()
        # Fallback to stdout
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        return stdout if stdout else (stderr if stderr else "[空输出]")
    else:
        return f"[转写失败: {result.stderr[:300]}]\n---stdout---\n{result.stdout[:300]}"


def analyze_video(video_path, frame_interval=3):
    """完整视频分析管线"""
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"❌ 文件不存在: {video_path}")
        return None
    
    print(f"\n🎬 分析视频: {video_path.name}")
    
    # 准备临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        # 1. 提取帧
        print("📸 步骤1: 抽帧分析画面...")
        frames, duration = extract_frames(video_path, tmp, interval=frame_interval)
        
        # 2. 分析每帧
        api_key, base_url, model_id = load_api_config()
        if not api_key:
            print("  ❌ 未找到 API Key（openclaw.json 中 qwen provider）")
            return None
        
        print(f"🧠 步骤2: 分析 {len(frames)} 帧画面...")
        frame_descriptions = []
        for i, f in enumerate(frames):
            timestamp = i * frame_interval
            print(f"  帧 {i+1}/{len(frames)} (⏱ {timestamp}s)...", end=" ", flush=True)
            desc = analyze_frame_via_api(f, api_key, base_url, model_id)
            frame_descriptions.append({"time": timestamp, "desc": desc})
            print("✅")
        
        # 3. 提取并转写音频
        print("🎤 步骤3: 提取音频 + 转写对话...")
        audio_path = tmp / "audio.wav"
        try:
            extract_audio(video_path, audio_path)
            transcript = transcribe_audio(audio_path)
            print(f"  📝 转写结果 ({len(transcript)}字)")
        except Exception as e:
            transcript = f"[音频处理失败: {e}]"
            print(f"  ⚠️ {e}")
        
        # 4. 综合分析
        print("📋 步骤4: 综合生成报告...")
        
        # 生成时间线描述
        timeline = []
        for fd in frame_descriptions:
            minutes = int(fd["time"] // 60)
            seconds = int(fd["time"] % 60)
            timeline.append(f"⏱ {minutes:02d}:{seconds:02d}\n{fd['desc']}")
        
        report = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 视频感知报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 文件: {video_path.name}
⏱ 时长: {duration:.1f}秒
📸 抽帧: {len(frames)}帧 (每{frame_interval}秒)

📖 画面时间线
{chr(10)+chr(10).join(timeline)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🗣️ 对话/音频内容:

{transcript}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return report


def main():
    parser = argparse.ArgumentParser(description="视频全感知分析（画面+声音）")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--interval", type=int, default=3, help="抽帧间隔（秒），默认3秒")
    parser.add_argument("--output", "-o", help="输出文件路径（可选）")
    args = parser.parse_args()
    
    report = analyze_video(args.video, args.interval)
    
    if report:
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"\n✅ 报告已保存: {args.output}")
        else:
            print(report)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
