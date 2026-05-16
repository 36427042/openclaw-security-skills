#!/usr/bin/env python3
"""
🎵 BGM下载引擎
从免版权/CC0音乐源下载50首TikTok风格BGM
来源：Pixabay Music (通过其公开API) / Freesound / Uppbeat
"""
import os, json, urllib.request, urllib.parse, time, random, subprocess, wave, struct, math

OUTPUT_DIR = os.path.expanduser("~/Desktop/BGM库")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_synth_bgm(count=50):
    """用Python生成简单lo-fi风格BGM（无版权问题 - 纯算法生成）"""
    sample_rate = 44100
    bpm_range = [(70, 90)]  # Chill lo-fi tempo
    
    for i in range(count):
        filename = os.path.join(OUTPUT_DIR, f"bgm_synth_{i+1:03d}.wav")
        duration = 30  # 30秒
        total_samples = sample_rate * duration
        
        bpm = random.randint(70, 90)
        beat_interval = 60.0 / bpm
        
        # Key and scale
        root = random.choice([261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88])  # C-B
        scale_type = random.choice(["major", "minor", "pentatonic"])
        
        if scale_type == "major":
            scale_intervals = [0, 2, 4, 5, 7, 9, 11]
        elif scale_type == "minor":
            scale_intervals = [0, 2, 3, 5, 7, 8, 10]
        else:  # pentatonic
            scale_intervals = [0, 2, 4, 7, 9]
        
        scale_notes = [root * (2 ** (i/12)) for i in scale_intervals]
        
        samples = []
        t = 0.0
        beat_counter = 0
        chord_notes = [random.choice(scale_notes) for _ in range(3)]
        melody_notes = [random.choice(scale_notes) * random.choice([1, 1.5, 2]) for _ in range(8)]
        
        melody_idx = 0
        chord_change_interval = beat_interval * 4  #每4拍换和弦
        
        while t < duration:
            # Chord (pad) - soft sine wave
            chord_sample = 0
            for freq in chord_notes:
                chord_sample += math.sin(2 * math.pi * freq * t) * 0.08
            
            # Melody - plucked-like sound on beats
            melody_sample = 0
            beat_phase = (t % beat_interval) / beat_interval
            
            if beat_phase < 0.1:  # Attack phase
                freq = melody_notes[melody_idx % len(melody_notes)]
                decay = 1.0 - (beat_phase / 0.1) * 0.95
                melody_sample = math.sin(2 * math.pi * freq * t) * decay * 0.15
            
            if int(t / beat_interval) != beat_counter:
                beat_counter = int(t / beat_interval)
                melody_idx += 1
                if int(t / chord_change_interval) > int((t - 0.1) / chord_change_interval):
                    chord_notes = [random.choice(scale_notes) for _ in range(3)]
            
            # Bass drum on downbeats
            kick_sample = 0
            downbeat = int(t / beat_interval) % 4 == 0
            kick_phase = (t % beat_interval) / beat_interval
            if downbeat and kick_phase < 0.08:
                kick_freq = 60 * (1 - kick_phase/0.08)
                kick_sample = math.sin(2 * math.pi * max(kick_freq, 30) * t) * 0.3 * (1 - kick_phase/0.08)
            
            # Hi-hat on off-beats
            hat_sample = 0
            if beat_phase > 0.45 and beat_phase < 0.55:
                hat_sample = random.random() * 0.1 * (1 - abs(beat_phase - 0.5) / 0.05)
            elif beat_phase > 0.95:
                hat_sample = random.random() * 0.08 * (1 - (beat_phase - 0.95) / 0.05)
            
            combined = chord_sample + melody_sample + kick_sample + hat_sample
            # Soft clip
            combined = max(-1.0, min(1.0, combined))
            samples.append(int(combined * 32767))
            
            t += 1.0 / sample_rate
        
        # Write WAV file
        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack(f'<{len(samples)}h', *samples))
        
        size_kb = os.path.getsize(filename) / 1024
        print(f"  ✅ bgm_synth_{i+1:03d}.wav (gen) ({size_kb:.0f}KB)")

def convert_wav_to_mp3():
    """用ffmpeg把wav转mp3"""
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith(".wav"):
            wav_path = os.path.join(OUTPUT_DIR, f)
            mp3_path = wav_path.replace(".wav", ".mp3")
            if not os.path.exists(mp3_path):
                subprocess.run([
                    "ffmpeg", "-y", "-i", wav_path,
                    "-codec:a", "libmp3lame", "-b:a", "128k",
                    mp3_path
                ], capture_output=True)
                size_kb = os.path.getsize(mp3_path) / 1024
                print(f"  🔄 {f} → {os.path.basename(mp3_path)} ({size_kb:.0f}KB)")
            else:
                pass  # Already converted

def main():
    print("=" * 50)
    print("🎵 BGM生成引擎启动")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print("=" * 50)
    
    print("\n🎹 合成50首lo-fi/chill BGM (纯算法生成，无版权问题)...")
    generate_synth_bgm(50)
    convert_wav_to_mp3()
    
    print(f"\n📊 最终统计:")
    mp3_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3") and os.path.getsize(os.path.join(OUTPUT_DIR, f)) > 10000])
    for f in mp3_files:
        size_kb = os.path.getsize(os.path.join(OUTPUT_DIR, f)) / 1024
        print(f"  ✅ {f}: {size_kb:.0f}KB")
    print(f"\n✅ 总计: {len(mp3_files)} 首BGM")
    return len(mp3_files)

if __name__ == "__main__":
    main()
