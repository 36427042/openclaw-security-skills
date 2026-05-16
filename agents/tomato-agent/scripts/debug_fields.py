#!/usr/bin/env python3
"""
假睫毛→TH publish成功的shop info作为参考
补全美妆蛋→SG所有必填字段
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 参考假睫毛→TH
print("=== 假睫毛→TH(已publish) shop info参考 ===")
r = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
if r.get("code") == "success":
    info = r.get("data", {}).get("shopCollectItemInfo", {})
    for k, v in info.items():
        if k not in ["skuMap"]:
            val_str = json.dumps(v, ensure_ascii=False)
            print(f"  {k}: {val_str[:200]}")

# 美妆蛋→SG
print("\n=== 美妆蛋→SG shop info ===")
r = client.get_shop_collect_item_info(detail_id=2962333379, shop_id=14772775)
if r.get("code") == "success":
    info = r.get("data", {}).get("shopCollectItemInfo", {})
    missing = []
    ref_r = client.get_shop_collect_item_info(detail_id=2962333377, shop_id=14681455)
    ref_info = ref_r.get("data", {}).get("shopCollectItemInfo", {}) if ref_r.get("code") == "success" else {}
    
    for k, v in ref_info.items():
        if k not in info or not info.get(k):
            val_str = json.dumps(v, ensure_ascii=False)[:100]
            print(f"  缺失: {k} = {val_str}")
            missing.append(k)
    
    print(f"\n缺失字段: {missing}")
