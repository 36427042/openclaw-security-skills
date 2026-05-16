#!/usr/bin/env python3
"""
publish成功一个了！现在：
1. 检查已publish假睫毛→TH的状态
2. 分析为什么其他shop的publish说"未选择类目"
3. 尝试设置shop模式和类目

关键发现：
- publish使用tid(collectBoxDetailId)作为detailIds
- 需要先设置类目/定价/其他信息再publish
- 一个site模式产品只能claim到一个shop
"""
import sys, json, time
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

SHOPS = {
    "TH": 14681455,
    "MY": 14772485,
    "VN": 14681328,
    "PH": 14772551,
    "SG": 14772775,
}

# 1. 检查publish成功后的状态
print("=== publish后的状态 ===")
for status in ["all", "notPublished", "published"]:
    r = client.search_collect_box_list(page_no=1, page_size=50, status=status)
    print(f"\nstatus={status}: {len(r.get('data',{}).get('detailList',[]))} items")
    for item in r.get("data", {}).get("detailList", []):
        cid = item.get("commonCollectBoxDetailId")
        if cid in ["3579185120", "3579185121", 3579185120, 3579185121]:
            print(f"  cid={cid} | tid={item.get('collectBoxDetailId')} | model={item.get('editModel')} | shops={[s.get('shopId') for s in item.get('collectBoxDetailShopList',[])]}")

# 2. 看看假睫毛→TH已publish的detail
print("\n=== 假睫毛→TH(已publish)的shop详情 ===")
r = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
print(f"code={r.get('code')} msg={r.get('message','')}")
if r.get("code") == "success":
    data = r.get("data", {})
    print(f"  ossMd5: {data.get('ossMd5','')[:20] if data.get('ossMd5') else '空'}")
    print(f"  editModel: {data.get('editModel')}")
    print(f"  shopCollectItemInfo: {json.dumps(data.get('shopCollectItemInfo',{}), ensure_ascii=False)[:500]}")

# 3. 设置美妆蛋→SG（已有shop模式）的类目和定价
print("\n=== 尝试设置美妆蛋→SG的shop详情 ===")
r = client.get_shop_collect_item_info(detail_id=2962333379, shop_id=14772775)
print(f"code={r.get('code')} msg={r.get('message','')}")
if r.get("code") == "success":
    data = r.get("data", {})
    oss_md5 = data.get("ossMd5", "")
    print(f"  ossMd5: {oss_md5[:20] if oss_md5 else '空'}")
    
    # 构建完整的shopCollectItemInfo
    info = {
        "price": "1.80",
        "productName": "美妆蛋粉扑4件套",
    }
    
    r_save = client.save_shop_collect_item_info(
        oss_md5=oss_md5,
        detail_id=2962333379,
        shop_id=14772775,
        info=info
    )
    print(f"  save: {json.dumps(r_save, ensure_ascii=False)[:300]}")

# 4. 检查publish后假睫毛→TH的状态
print("\n=== 假睫毛→TH publish后检查 ===")
r = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
print(f"code={r.get('code')} msg={r.get('message','')}")

# 看published状态
print("\n=== published状态 ===")
r = client.search_collect_box_list(page_no=1, page_size=50, status="published")
for item in r.get("data",{}).get("detailList",[]):
    print(f"  {json.dumps(item, ensure_ascii=False)[:200]}")

print("\n=== 所有采集箱产品 ===")
r = client.search_collect_box_list(page_no=1, page_size=50, status="all")
for item in r.get("data",{}).get("detailList",[]):
    print(f"  cid={item.get('commonCollectBoxDetailId')} | tid={item.get('collectBoxDetailId')} | {item.get('title','')[:20]}")
