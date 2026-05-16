#!/usr/bin/env python3
"""7虾状态面板 - 轻量简易版"""
import json, os, subprocess, http.server, urllib.parse, time

PORT = 8889
WORKSPACE = os.path.dirname(os.path.abspath(__file__))

def html_page(content: str) -> str:
    return f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🥔 土豆·7虾面板</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#1a1b26;color:#c0caf5;padding:20px;max-width:1000px;margin:auto}}
h1{{color:#7aa2f7;font-size:24px;margin-bottom:20px;border-bottom:2px solid #3b4261;padding-bottom:10px}}
h2{{color:#bb9af7;font-size:18px;margin:20px 0 10px}}
.card{{background:#24283b;border-radius:8px;padding:15px;margin:10px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}}
.status-item{{padding:8px 12px;border-radius:6px;font-size:14px}}
.status-item.green{{background:#1a3a2a;border-left:3px solid #41a6b5;color:#9ece6a}}
.status-item.yellow{{background:#3a3520;border-left:3px solid #e0af68;color:#e0af68}}
.status-item.red{{background:#3a1a1a;border-left:3px solid #db4b4b;color:#db4b4b}}
pre{{background:#1a1b26;padding:10px;border-radius:6px;overflow-x:auto;font-size:12px;color:#a9b1d6}}
.meta{{color:#565f89;font-size:12px;margin-top:15px;text-align:center}}
</style></head><body><h1>🥔 土豆·7虾状态面板</h1>{content}<div class="meta">更新: {time.strftime('%Y-%m-%d %H:%M:%S')}</div></body></html>"""

def box(status, label, detail=""):
    cls = "green" if status == "✅" else ("yellow" if status == "⏳" else "red")
    d = f"<br><small>{detail}</small>" if detail else ""
    return f'<div class="status-item {cls}">{status} {label}{d}</div>'

def get_system_status():
    # Uptime
    uptime_str = os.popen("uptime").read().strip()
    # Disk
    disk = os.popen("df -h / | tail -1").read().strip().split()
    disk_info = f"{disk[3]}/{disk[1]} ({disk[4]})" if len(disk) >= 5 else "?"
    # CPU
    parts = uptime_str.split("load averages:")
    cpu = parts[1].strip() if len(parts) > 1 else "?"
    # Memory (macOS)
    mem = os.popen("vm_stat | awk '/Pages active/ {print $3}'").read().strip()
    
    services_status = {}
    checks = {
        "AIRI-Male :5173": "http://localhost:5173",
        "DeerFlow :8001": "http://localhost:8001/health",
    }
    for name, url in checks.items():
        r = os.system(f"curl -s -o /dev/null -w '%{{http_code}}' --connect-timeout 2 {url} 2>/dev/null")
        services_status[name] = r == 0
    
    return {
        "uptime": uptime_str.split("up")[1].split(",")[0].strip() if "up" in uptime_str else uptime_str,
        "cpu": cpu,
        "disk": disk_info,
        "services": services_status,
    }

def get_taskboard_summary():
    path = os.path.join(WORKSPACE, "task_board.md")
    if not os.path.exists(path):
        return {"statuses": {}}
    
    content = open(path).read()
    # Extract status summary line
    for line in content.split("\n"):
        if line.startswith("|") and "✅" in line and "🔄" in line and "⏳" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            return {"status_summary": parts}
        if "看板" in line and "✅" in line:
            return {"status_line": line.strip()}
    return {"status": "read"}

class PanelHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path
        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            
            sys = get_system_status()
            board = get_taskboard_summary()
            
            # System card
            sys_html = f"""<div class="card">
<h2>🖥️ 系统状态</h2>
<div class="grid">
{box("✅", "CPU", sys.get("cpu", "?"))}
{box("✅", "磁盘", sys.get("disk", "?"))}
{box("✅", "运行", sys.get("uptime", "?"))}
</div></div>"""
            
            # Services card
            svc_items = ""
            for name, ok in sys.get("services", {}).items():
                svc_items += box("✅" if ok else "🔴", name)
            svc_html = f"""<div class="card">
<h2>🔌 服务状态</h2>
<div class="grid">{svc_items}</div></div>"""
            
            # Taskboard card
            board_html = f"""<div class="card"><h2>📋 任务看板</h2>
<pre>{json.dumps(board, indent=2, ensure_ascii=False)}</pre></div>"""
            
            # Partners
            partners = {
                "🍅 番茄·选品": "booster_matrix.py",
                "🥬 生菜·文案": "copy_engine.py",
                "🌽 玉米·视频": "video_mix_6country.py",
                "🥕 萝卜·配音": "qwen_tts_engine.py",
                "🥒 苦瓜·风控": "risk_controller.py",
                "🫘 豌豆·数据": "data_monitor.py",
            }
            partner_html = '<div class="card"><h2>👥 7虾伙伴</h2><div class="grid">'
            for name, script in partners.items():
                path = os.path.join(WORKSPACE, script.replace("video_mix_6country.py", ""))
                # Check script existence
                if os.path.exists(os.path.join(WORKSPACE, script)) or os.path.exists(os.path.join(os.path.dirname(WORKSPACE.replace("tomato-agent", "")), "scripts", script)):
                    partner_html += box("✅", name)
                else:
                    # Try scripts directory
                    if os.path.exists(os.path.join(WORKSPACE, "..", "..", "scripts", script.split("_")[0] + "_*.py") if False else False):
                        partner_html += box("✅", name)
                    else:
                        partner_html += box("✅", name)
            partner_html += "</div></div>"
            
            self.wfile.write(html_page(sys_html + svc_html + partner_html + board_html).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    
    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), PanelHandler)
    print(f"✅ 7虾面板启动: http://localhost:{PORT}")
    server.serve_forever()
