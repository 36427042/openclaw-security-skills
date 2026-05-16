#!/usr/bin/env python3
"""
调试脚本：检查claimed后的TK采集箱状态
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 1. 查公共采集箱，看detailIds是否正确
print("=== 1. 公共采集箱列表 ===")
r = client.get_collect_box_list(page_no=1, page_size=20)
print(json.dumps(r, ensure_ascii=False, indent=2)[:2000])

print("\n=== 2. 查公共采集箱详情 detailId=3579185120 ===")
r = client.get_collect_box_detail(3579185120)
print(json.dumps(r, ensure_ascii=False, indent=2)[:2000])

print("\n=== 3. 查公共采集箱详情 detailId=3579185121 ===")
r = client.get_collect_box_detail(3579185121)
print(json.dumps(r, ensure_ascii=False, indent=2)[:2000])

# 4. TK采集箱 - 用不同状态查
for status in ["all", "notPublished", "published"]:
    print(f"\n=== 4. TK采集箱 (status={status}) ===")
    r = client.search_collect_box_list(page_no=1, page_size=50, status=status)
    print(f"code={r.get('code')}, data={json.dumps(r.get('data', {}), ensure_ascii=False)[:1000]}")
