#!/bin/bash
# ============================================================
# 双头眉刷 - 5国视频自动化合成测试脚本 v4
# 解决FFmpeg filter graph的冒号转义问题
# ============================================================
# 使用: bash test_5lang_video.sh [TH|VN|ID|MY|PH|ALL]
# ============================================================

LANG_CODE="${1:-TH}"
OUTPUT_DIR="$HOME/Desktop/5国视频测试"
mkdir -p "$OUTPUT_DIR"

echo ""
echo "==========================================="
echo "🌏 双头眉刷 ${LANG_CODE} 版本测试"
echo "==========================================="

# 转义函数: 将文本中的冒号转义为FFmpeg filter语法
escape_filter_text() {
  # 对drawtext来说需要用反斜杠转义冒号: 替换 : 为 \\:
  echo "$1" | sed 's/:/\\:/g'
}

SRC_VIDEO="$HOME/Desktop/简创5国视频/双头眉刷_${LANG_CODE}.mp4"
if [ ! -f "$SRC_VIDEO" ]; then
  SRC_VIDEO="$HOME/Desktop/双头眉刷.mp4"
fi
echo "  输入: $(basename "$SRC_VIDEO")"

# === 方法C: 使用printf构建filter string避免shell解析问题 ===
# FFmpeg的drawtext filter中, text内的冒号和引号需要转义
# 方案: 使用Python生成filter string并执行

echo ""
echo "[1/1] 用Python调用FFmpeg..."

OUTPUT_FILE="$OUTPUT_DIR/双头眉刷_${LANG_CODE}_final.mp4"
TMP_PY="/tmp/render_video_${LANG_CODE}.py"

python3 -c "
import subprocess, sys

lang = '$LANG_CODE'
src = '$SRC_VIDEO'
out = '$OUTPUT_FILE'

# 5语言的文本
texts = {
    'TH': ('Khw mai sa-mart? Long an nee si', 'Dual-head one side brush one side shape', '#beauty #eyebrow'),
    'VN': ('Long may khong deu? Thu cai nay xem', 'Dual-head mot dau chai mot dau tao dang', '#beauty #longmay'),
    'ID': ('Alis tidak simetris? Coba yang ini', 'Dual-head satu sisir satu bentuk', '#beauty #alis'),
    'MY': ('Kening tak simetri? Cuba yang ni', 'Dual-head satu hujung sikat satu bentuk', '#beauty #kening'),
    'PH': ('Hindi pantay ang kilay? Try this', 'Dual-head isang dulo suklay isang dulo form', '#beauty #kilay'),
}

t1, t2, t3 = texts.get(lang, ('Eyebrows uneven? Try this', 'Dual-head design', '#beauty'))

# 对drawtext来说, 文本中的冒号需要用反斜杠转义, 然后是引号
# 但安全的做法是: 使用textfile参数从文件读取文本
import tempfile, os

# 用textfile方式避免转义问题
t1_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='/tmp')
t1_file.write(t1)
t1_file.close()

t2_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='/tmp')
t2_file.write(t2)
t2_file.close()

t3_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, dir='/tmp')
t3_file.write(t3)
t3_file.close()

# 构建filter complex - 用textfile避免转义
filter_complex = (
    \"[0:v]\" +
    f\"drawtext=textfile='{t1_file.name}':fontsize=20:fontcolor=white:bordercolor=black:borderw=2:x=(w-text_w)/2:y=h-100:enable='between(t,0,2.5)',\" +
    f\"drawtext=textfile='{t2_file.name}':fontsize=18:fontcolor=white:bordercolor=black:borderw=2:x=(w-text_w)/2:y=h-70:enable='between(t,2.5,4.5)',\" +
    f\"drawtext=textfile='{t3_file.name}':fontsize=14:fontcolor=lightgray:borderw=1:x=(w-text_w)/2:y=h-40:enable='between(t,4.5,5.0)'\" +
    \"[v]\"
)

cmd = [
    'ffmpeg', '-i', src,
    '-filter_complex', filter_complex,
    '-map', '[v]', '-map', '0:a',
    '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
    '-c:a', 'copy',
    '-y', out
]

print(f'Running: {\" \".join(cmd[:3])} ...')
result = subprocess.run(cmd, capture_output=True, text=True)

if os.path.exists(out):
    size = os.path.getsize(out)
    print(f'✅ 成功! 输出: {size/1024/1024:.1f}MB')
else:
    print('❌ 失败')
    print('STDERR:', result.stderr[-500:])

# 清理
os.unlink(t1_file.name)
os.unlink(t2_file.name)
os.unlink(t3_file.name)
" 2>&1

echo ""
echo "==========================================="
if [ -f "$OUTPUT_FILE" ]; then
  echo "✅ ${LANG_CODE} 完成: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
else
  echo "❌ ${LANG_CODE} 失败"
fi  
echo "==========================================="

# ALL
if [ "$LANG_CODE" = "ALL" ]; then
  for code in TH VN ID MY PH; do
    bash "$0" "$code"
  done
fi
