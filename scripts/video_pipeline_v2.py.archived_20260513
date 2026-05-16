#!/usr/bin/env python3
"""
简创AIGC 5国视频批量生成管线
双头眉刷10秒片段 → 5国语言版本 → 云渲染导出
"""
import json, os, sys, time, requests, tempfile
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading, subprocess, signal, atexit

# ========== GEP自进化引擎 ==========
try:
    from scripts.gep_engine import GEP
    gep = GEP("🌽玉米·视频")
    GEP_AVAILABLE = True
except Exception:
    # GEP不可用时静默降级
    class _GepDummy:
        def pre_check(self, *a, **kw): return None
        def post_record(self, *a, **kw): return None
    gep = _GepDummy()
    GEP_AVAILABLE = False

# ========== 配置 ==========
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
API_KEY = "0bd37772-f107-44dd-b0f4-4bf8c7b07ca2"
BASE_URL = "https://capcut-mate.jcaigc.cn"
TEMPLATE_ID = "7343088446683326729"  # 已验证的美妆模板
SOURCE_VIDEO = os.path.expanduser("~/Desktop/双头眉刷.mp4")
OUTPUT_DIR = os.path.expanduser("~/Desktop/简创5国视频")

# 5国配置
COUNTRIES = {
    "TH": {"lang": "th",   "voice": "Kanya",    "text": "เห็นไหม ใช้แล้วสวยจริง!",            "name": "🇹🇭 泰国"},
    "MY": {"lang": "ms",   "voice": "Zuzana",   "text": "Nampak tak? Hasilnya memang cantik!",  "name": "🇲🇾 马来西亚"},
    "VN": {"lang": "vi",   "voice": "Minh",     "text": "Thấy không? Dùng xong đẹp thật!",      "name": "🇻🇳 越南"},
    "ID": {"lang": "id",   "voice": "Damayanti","text": "Lihat? Hasilnya cantik banget!",        "name": "🇮🇩 印尼"},
    "PH": {"lang": "fil",  "voice": "Samantha", "text": "Kita mo? Ang ganda talaga ng resulta!", "name": "🇵🇭 菲律宾"},
}

http_server = None
tunnel_process = None
public_url = None


# ========== HTTP服务器 + 隧道 ==========

class SilentHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 静默日志

def start_http_server(port=8899):
    """启动本地HTTP文件服务器（Desktop目录）"""
    desktop = os.path.expanduser("~/Desktop")
    os.chdir(desktop)
    server = HTTPServer(("0.0.0.0", port), SilentHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"  ✅ HTTP服务器: http://localhost:{port} -> {desktop}")
    return server

def start_localtunnel(port=8899):
    """通过localtunnel暴露到公网（不固定subdomain，避免冲突）"""
    proc = subprocess.Popen(
        ["lt", "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True
    )
    time.sleep(5)
    # 尝试读取URL
    url = None
    import re
    for line in iter(proc.stdout.readline, ''):
        m = re.search(r'https?://[-a-zA-Z0-9.]+\.loca\.lt', line)
        if m:
            url = m.group(0)
            break
    return proc, url


# ========== 音频生成 ==========

def gen_audio(text: str, lang: str, voice: str, out_path: str) -> str:
    """用 macOS say 命令生成语音"""
    try:
        subprocess.run(
            ["say", "-v", voice, "-o", out_path, "--data-format=alac"],
            input=text, text=True, capture_output=True, timeout=15
        )
        # 转wav再转aac/mp3
        wav_path = out_path.replace(".aiff", ".wav")
        subprocess.run([
            "ffmpeg", "-y", "-i", out_path, "-acodec", "pcm_s16le",
            "-ar", "44100", "-ac", "1", wav_path
        ], capture_output=True, timeout=10)
        
        # 再转aac
        aac_path = out_path.replace(".aiff", ".aac")
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_path, "-acodec", "aac",
            "-b:a", "128k", "-ar", "44100", "-ac", "1", aac_path
        ], capture_output=True, timeout=10)
        return aac_path
    except Exception as e:
        print(f"  ⚠️ 音频生成失败: {e}")
        return None


# ========== 简创API ==========

# 重试支持（v3.1+）
_HAS_RETRY = False
try:
    from hermes_retry import retry_call, RetryConfig
    _HAS_RETRY = True
except ImportError:
    pass


def jc_api(method: str, endpoint: str, data: dict = None) -> dict:
    """调用简创AIGC API（v3.1+ 带指数退避重试）"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}

    def _do_request():
        r = requests.request(method, url, json=data, headers=headers, timeout=30)
        return r.json()

    if _HAS_RETRY:
        import asyncio
        try:
            return asyncio.run(retry_call(
                _do_request,
                max_attempts=3,
                base_delay=2.0,
                max_delay=15.0,
                retryable_exceptions=(ConnectionError, TimeoutError, OSError, requests.ConnectionError, requests.Timeout),
            ))
        except Exception as e:
            return {"code": -1, "message": f"重试3次后仍失败: {e}"}

    # 无重试模块时的原始逻辑
    try:
        return _do_request()
    except Exception as e:
        return {"code": -1, "message": str(e)}


def gen_country_video(country_code: str, config: dict, video_url: str, audio_url: str) -> dict:
    """为一个国家生成视频（GEP增强）"""
    ctx = {"country": country_code, "endpoint": "capcut-mate"}

    # GEP: 检查该国家API是否有历史问题
    advice = gep.pre_check("gen_video_api", ctx)
    if advice and advice.get("cautious"):
        print(f"  📖 GEP经验: {advice['advice'][:60]}")

    print(f"\n  ⏳ {config['name']} 开始...")

    try:
        # Step 1: create_draft
        r1 = jc_api("POST", "/openapi/capcut-mate/v1/create_draft", {
            "exportTemplateId": TEMPLATE_ID
        })
        if r1.get("code") != 0:
            gep.post_record("gen_video_api", ctx, "failed", f"create_draft失败: {r1}")
            return {"status": "error", "msg": f"create_draft失败: {r1}", "cc": country_code}

        draft_url = r1.get("draft_url", "")
        print(f"  📝 Draft URL: {draft_url}")

        # Step 2: easy_create_material
        r2 = jc_api("POST", "/openapi/capcut-mate/v1/easy_create_material", {
            "draft_url": draft_url,
            "video_url": video_url,
            "audio_url": audio_url
        })
        if r2.get("code") != 0 and r2.get("code") != 200:
            print(f"  ⚠️ 素材添加失败: {r2.get('message','')} | video:{video_url[:50]} | audio:{audio_url[:50]}")

        # Step 3: gen_video
        r3 = jc_api("POST", "/openapi/capcut-mate/v1/gen_video", {
            "draft_url": draft_url,
            "apiKey": API_KEY,
            "exportTemplateId": TEMPLATE_ID
        })
        if r3.get("code") != 0:
            gep.post_record("gen_video_api", ctx, "failed", f"gen_video提交失败: {r3}")
            return {"status": "error", "msg": f"gen_video提交失败: {r3}", "cc": country_code}
        print(f"  🎬 gen_video已提交")

        # Step 4: 轮询进度 (新版API: POST + draft_url body)
        max_polls = 60
        for i in range(max_polls):
            time.sleep(10)
            r4 = jc_api("POST", "/openapi/capcut-mate/v1/gen_video_status", {
                "draft_url": draft_url
            })
            progress = r4.get("progress", 0)
            status = r4.get("status", "")
            video_url_out = r4.get("video_url", "")
            error_msg = r4.get("error_message", "")

            print(f"     [{i+1}/60] 进度: {progress}% | 状态: {status} | {error_msg[:40] if error_msg else ''}", end="\r")

            if status == "completed" or progress == 100:
                print(f"\n  ✅ {config['name']} 完成!")
                gep.post_record("gen_video_api", ctx, "success", note=f"{config['name']} 渲染完成")
                return {
                    "status": "completed", "cc": country_code,
                    "video_url": video_url_out, "progress": progress
                }
            elif status in ("failed", "error"):
                print(f"\n  ❌ {config['name']} 失败: {error_msg or status}")
                gep.post_record("gen_video_api", ctx, "failed", f"渲染失败: {r4}")
                return {"status": "failed", "cc": country_code, "msg": error_msg or str(r4)}

        gep.post_record("gen_video_api", ctx, "timeout", f"{config['name']} 超过10分钟")
        return {"status": "timeout", "cc": country_code, "msg": "超过10分钟轮询上限"}

    except Exception as e:
        gep.post_record("gen_video_api", ctx, "error", f"{config['name']} 异常: {e}")
        return {"status": "error", "cc": country_code, "msg": str(e)}


# ========== 主线 ==========

def main():
    global http_server, tunnel_process, public_url
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    audio_dir = os.path.join(OUTPUT_DIR, "audio_tracks")
    os.makedirs(audio_dir, exist_ok=True)
    
    print("=" * 55)
    print("简创AIGC 5国视频批量管线")
    print(f"源视频: {SOURCE_VIDEO}")
    print(f"模板ID: {TEMPLATE_ID}")
    print(f"输出: {OUTPUT_DIR}")
    print("=" * 55)
    
    # 1. 启动HTTP服务（从Desktop目录提供文件）
    print("\n📡 启动本地文件服务器 (Desktop/)...")
    http_server = start_http_server()
    
    # 确保源视频存在
    if not os.path.exists(SOURCE_VIDEO):
        print(f"  ⚠️ 源视频不存在: {SOURCE_VIDEO}")
        return
    
    # 2. 启动localtunnel
    print("📡 启动公网隧道...")
    tunnel_process, public_url = start_localtunnel()
    if public_url:
        print(f"   ✅ 公网地址: {public_url}")
    else:
        print("   ⚠️ 无法获取隧道URL，用本地地址尝试")
        public_url = f"http://localhost:8899"
    
    # 3. 为每个国家处理
    results = []
    for cc, cfg in COUNTRIES.items():
        print(f"\n{'='*50}")
        print(f"  🌍 {cfg['name']}")
        print(f"{'='*50}")
        
        # 生成音频
        print(f"  🎙️ 生成语音...")
        audio_path = gen_audio(cfg["text"], cfg["lang"], cfg["voice"],
                                os.path.join(audio_dir, f"{cc}.aac"))
        
        audio_url = None
        if audio_path and os.path.exists(audio_path):
            # HTTP server 从 Desktop/ 目录提供文件
            audio_url = f"{public_url}/简创5国视频/audio_tracks/{cc}.aac"
        
        if not audio_url:
            print(f"  ⚠️ {cc} 音频未生成，跳过")
            continue
        
        # 视频URL（源视频，HTTP server从Desktop/提供）
        video_url = f"{public_url}/双头眉刷.mp4"
        
        # 调用简创云渲染
        result = gen_country_video(cc, cfg, video_url, audio_url)
        results.append(result)
        
        # 国与国之间间隔避免并发冲突
        time.sleep(3)
    
    # 5. 结果汇总
    print(f"\n\n{'='*55}")
    print("5国批量生成完成! 🎉")
    print("="*55)
    for r in results:
        status_icon = "✅" if r.get("status") == "completed" else "❌"
        print(f"  {status_icon} {COUNTRIES[r['cc']]['name']}: {r.get('status','?')} | {r.get('video_url','')[:60]}")
    
    # 尝试下载完成的视频
    print("\n⬇️ 下载成品视频...")
    for r in results:
        if r.get("status") == "completed" and r.get("video_url"):
            cc = r["cc"]
            out_path = os.path.join(OUTPUT_DIR, f"双头眉刷_{cc}.mp4")
            try:
                resp = requests.get(r["video_url"], timeout=30)
                if resp.status_code == 200:
                    with open(out_path, "wb") as f:
                        f.write(resp.content)
                    size = len(resp.content) / 1024 / 1024
                    print(f"  ✅ {COUNTRIES[cc]['name']} → {out_path} ({size:.1f}MB)")
                else:
                    print(f"  ⚠️ {COUNTRIES[cc]['name']} 下载失败: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  ⚠️ {COUNTRIES[cc]['name']} 下载异常: {e}")


def cleanup():
    """清理资源"""
    if tunnel_process:
        tunnel_process.terminate()
    print("\n🧹 清理完成")


if __name__ == "__main__":
    atexit.register(cleanup)
    main()
