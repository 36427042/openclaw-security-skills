#!/usr/bin/env python3
"""
产品claim后消失了，查不同状态
还有search_collect_box_list的参数可能不同
"""
import sys, json, time
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 查所有状态
for status in ["all", "notPublished", "waitPublish", "published", "draft", "failed"]:
    print(f"\n=== status={status} ===")
    r = client.search_collect_box_list(page_no=1, page_size=50, status=status)
    code = r.get("code", "?")
    items = r.get("data", {}).get("detailList", [])
    print(f"  code={code}, count={len(items)}")
    for item in items:
        cid = item.get("commonCollectBoxDetailId")
        if cid in ["3579185120", "3579185121", 3579185120, 3579185121]:
            print(f"  ✅ FOUND: cid={cid} | tid={item.get('collectBoxDetailId')} | model={item.get('editModel')} | shops={[s.get('shopId') for s in item.get('collectBoxDetailShopList',[])]}")

# 再用关键字搜索
print("\n=== 关键字搜索假睫毛 ===")
r = client.search_collect_box_list(page_no=1, page_size=20, status="all", keyword="假睫毛")
print(f"code={r.get('code')}: {len(r.get('data',{}).get('detailList',[]))} items")
for item in r.get("data",{}).get("detailList",[])[:5]:
    print(f"  cid={item.get('commonCollectBoxDetailId')} | tid={item.get('collectBoxDetailId')} | model={item.get('editModel')} | shops={[s.get('shopId') for s in item.get('collectBoxDetailShopList',[])]}")

# 试试get_shop_collect_item_info用最新的tid
print("\n=== 用最新的collectBoxDetailId查 ===")
# 刚才claim到TH成功，试试不同的detail参数
r = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
print(f"get_shop_collect_item_info(tid=2962333377, TH): {json.dumps(r, ensure_ascii=False)[:300]}")

# 用公共采集箱id再试试
r = client.get_shop_collect_item_info(detail_id=3579185120, shop_id=14681455)
print(f"get_shop_collect_item_info(cid=3579185120, TH): {json.dumps(r, ensure_ascii=False)[:300]}")
