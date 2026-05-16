#!/usr/bin/env python3
"""
调试：尝试用collectBoxDetailId代替commonCollectBoxDetailId
也检查claim_to_shop的detailIds到底用哪个字段
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 确认TK采集箱中的实际字段名和值
print("=== TK采集箱完整详情 ===")
r = client.search_collect_box_list(page_no=1, page_size=10, status="notPublished")
for item in r.get("data", {}).get("detailList", []):
    print(f"\ncollectBoxDetailId={item.get('collectBoxDetailId')}")
    print(f"commonCollectBoxDetailId={item.get('commonCollectBoxDetailId')}")
    print(f"title={item.get('title')}")
    print(f"collectBoxDetailShopList={item.get('collectBoxDetailShopList')}")
    print(f"editModel={item.get('editModel')}")
    print(f"所有字段: {json.dumps(item, ensure_ascii=False)[:500]}")
    print()

# 尝试用collectBoxDetailId（这个API文档显示的真实TK采集箱ID）
TK_COLLECT_BOX_DETAIL_IDS = [2962333377]  # 虽然是同一个ID...

print("=== 尝试 claim_to_shop with collectBoxDetailId ===")
r = client.claim_to_shop([14681455, 14772485, 14681328, 14772551, 14772775], [2962333377])
print(json.dumps(r, ensure_ascii=False)[:500])

# 再试试单个shop单个product
print("\n=== 试单个shop + 单个product (collectBoxDetailId) ===")
r = client.claim_to_shop([14681455], [2962333377])
print(json.dumps(r, ensure_ascii=False)[:500])
