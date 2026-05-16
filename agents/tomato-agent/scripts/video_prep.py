#!/usr/bin/env python3
"""
🎬 视频预处理脚本
- 抽帧（准备给 image tool 分析）
- 提取音频（准备给 faster-whisper 转写）
- 输出帧列表和时间线
"""
import sys, os, json, tempfile, subprocess, argparse
from pathlib import Path

def process_video(video_path, frame_interval=3, output_dir=None):
    video_path = Path(video_path)
    if not video_path.exists():
        print(json.dumps({"error": f"File not found: {video_path}"}))
        sys.exit(1)

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
    else:
        out = Path(tempfile.mkdtemp(prefix="video_prep_"))

    # Get duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True, check=True
    )
    duration = float(probe.stdout.strip())

    # Check for audio
    audio_check = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
         str(video_path)], capture_output=True, text=True
    )
    has_audio = "audio" in audio_check.stdout

    # Extract frames
    fps = 1.0 / frame_interval
    frames_dir = out / "frames"
    frames_dir.mkdir(exist_ok=True)
    subprocess.run([
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps},scale=1024:-1",
        "-q:v", "5", "-y",
        str(frames_dir / "frame_%04d.jpg")
    ], capture_output=True, check=True)

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    frame_list = []
    for i, f in enumerate(frames):
        timestamp = i * frame_interval
        minutes, secs = divmod(timestamp, 60)
        frame_list.append({
            "index": i + 1,
            "path": str(f.resolve()),
            "timestamp": timestamp,
            "time_str": f"{int(minutes):02d}:{int(secs):02d}"
        })

    # Extract audio if present
    audio_info = {}
    if has_audio:
        audio_path = out / "audio.wav"
        subprocess.run([
            "ffmpeg", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            "-y", str(audio_path)
        ], capture_output=True, check=True)
        audio_info = {
            "path": str(audio_path.resolve()),
            "format": "wav",
            "sample_rate": 16000
        }

    result = {
        "video": str(video_path.resolve()),
        "video_name": video_path.name,
        "duration": duration,
        "has_audio": has_audio,
        "frame_interval": frame_interval,
        "total_frames": len(frames),
        "frames": frame_list,
        "audio": audio_info if has_audio else None,
        "output_dir": str(out.resolve())
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="视频预处理：抽帧+提音频")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("--interval", type=int, default=3, help="抽帧间隔（秒）")
    parser.add_argument("--output", "-o", help="输出目录（可选，默认临时目录）")
    args = parser.parse_args()
    process_video(args.video, args.interval, args.output)
