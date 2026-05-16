#!/usr/bin/env python3
"""
🥬 生菜·TK Shop认领+发布全流程
流程: claimed → claim_to_shop → save_shop_collect_item_info(定价) → publish

天赐定价公式: (拿货价+3.5)/分母×汇率
假睫毛(¥1.5): TH฿63 MY-RM9 VN₫52K PH₱123 SG-S$2.3
美妆蛋(¥0.45): TH฿50 MY-RM7 VN₫41K PH₱97 SG-S$1.8
"""
import sys, json, time
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

# 5国店铺ID (confirmed from memory)
SHOPS = {
    "TH": 14681455,
    "MY": 14772485,
    "VN": 14681328,
    "PH": 14772551,
    "SG": 14772775,
}
ALL_SHOP_IDS = list(SHOPS.values())

# 产品定价（天赐公式计算值）
PRICES = {
    # product_id -> { site: price }
    3579185120: {"TH": 63, "MY": 9, "VN": 52000, "PH": 123, "SG": 2.3},  # 假睫毛
    3579185121: {"TH": 50, "MY": 7, "VN": 41000, "PH": 97, "SG": 1.8},   # 美妆蛋
}

PRODUCT_NAMES = {
    3579185120: "假睫毛 (Eyelashes)",
    3579185121: "美妆蛋 (Makeup Sponge)",
}

def log_step(step: str, result: dict):
    code = result.get("code", result.get("error", "?"))
    if code == "success":
        print(f"  ✅ {step}: 成功")
    else:
        print(f"  ❌ {step}: code={code} detail={json.dumps(result, ensure_ascii=False)[:300]}")

def main():
    client = MiaoshouClient(APP_KEY, APP_SECRET)
    print("="*60)
    print("🥬 TK Shop 认领+发布全流程")
    print("="*60)
    print(f"产品: {json.dumps(PRODUCT_NAMES, ensure_ascii=False)}")
    print(f"店铺: {json.dumps(SHOPS)}")
    print()

    # ═══════════════════════════════════════
    # STEP 1: claimed → TK采集箱
    # ═══════════════════════════════════════
    print("[Step 1] 🏁 claimed → TK采集箱")
    claimed_items = [
        {"detailId": 3579185120, "platform": "tiktok", "serialNumber": 1},
        {"detailId": 3579185121, "platform": "tiktok", "serialNumber": 1},
    ]
    r1 = client.claimed(claimed_items)
    log_step("claimed", r1)

    if r1.get("code") != "success":
        print("\n❌ claimed失败，退出。")
        sys.exit(1)

    # 等一会让系统处理
    time.sleep(2)

    # ═══════════════════════════════════════
    # STEP 2: 查TK采集箱确认产品已过来
    # ═══════════════════════════════════════
    print("\n[Step 2] 🔍 查TK采集箱确认产品")
    r2 = client.search_collect_box_list(page_no=1, page_size=20, status="notPublished")
    log_step("search_collect_box_list", r2)

    if r2.get("code") == "success":
        data = r2.get("data", {})
        items = data.get("list", data.get("records", []))
        print(f"   采集箱产品数: {len(items)}")
        for item in items:
            did = item.get("detailId", item.get("id", "?"))
            title = item.get("title", item.get("productName", "?"))[:30]
            print(f"   detailId={did} | {title}")
    else:
        print("   ⚠️  查询采集箱失败，继续尝试claim_to_shop")

    # ═══════════════════════════════════════
    # STEP 3: claim_to_shop → 全部5国
    # ═══════════════════════════════════════
    print("\n[Step 3] 📦 claim_to_shop → 全部5国")
    r3 = client.claim_to_shop(ALL_SHOP_IDS, [3579185120, 3579185121])
    log_step("claim_to_shop", r3)

    if r3.get("code") != "success":
        print("\n❌ claim_to_shop失败，尝试按国家逐个认领...")
        for shop_id in ALL_SHOP_IDS:
            r = client.claim_to_shop([shop_id], [3579185120, 3579185121])
            log_step(f"claim_to_shop(shop={shop_id})", r)

    time.sleep(2)

    # ═══════════════════════════════════════
    # STEP 4: save_shop_collect_item_info → 定价
    # ═══════════════════════════════════════
    print("\n[Step 4] 💰 设置定价 (save_shop_collect_item_info)")
    
    for did in [3579185120, 3579185121]:
        for site, shop_id in SHOPS.items():
            price = PRICES[did][site]
            print(f"\n   产品 #{did} ({PRODUCT_NAMES[did]}) → {site} (shop={shop_id}) 定价={price}")
            
            # 先获取当前详情（拿到ossMd5）
            r_info = client.get_shop_collect_item_info(detail_id=did, shop_id=shop_id)
            
            if r_info.get("code") == "success":
                data = r_info.get("data", {})
                oss_md5 = data.get("ossMd5", "")
                print(f"   ossMd5: {oss_md5[:20] if oss_md5 else '空'}...")
                
                # 构建定价信息
                price_info = {
                    "price": price,
                    "productName": PRODUCT_NAMES[did],
                }
                
                r_save = client.save_shop_collect_item_info(
                    oss_md5=oss_md5,
                    detail_id=did,
                    shop_id=shop_id,
                    info=price_info
                )
                log_step(f"save_shop_collect_item_info({site})", r_save)
            else:
                # 尝试站点模式
                print(f"   ⚠️  店铺模式失败，尝试站点模式...")
                r_site = client.get_site_collect_item_info(detail_id=did, site=site)
                if r_site.get("code") == "success":
                    data = r_site.get("data", {})
                    oss_md5 = data.get("ossMd5", "")
                    price_info = {
                        "price": price,
                        "productName": PRODUCT_NAMES[did],
                    }
                    r_save = client.save_site_collect_item_info(
                        oss_md5=oss_md5,
                        detail_id=did,
                        site=site,
                        info=price_info
                    )
                    log_step(f"save_site_collect_item_info({site})", r_save)
                else:
                    print(f"   ❌ {site} 两种模式都失败: {json.dumps(r_info, ensure_ascii=False)[:200]}")

    time.sleep(2)

    # ═══════════════════════════════════════
    # STEP 5: publish → 全部5国
    # ═══════════════════════════════════════
    print("\n[Step 5] 🚀 publish 到全部5国")
    r5 = client.publish(ALL_SHOP_IDS, [3579185120, 3579185121])
    log_step("publish", r5)

    # ═══════════════════════════════════════
    # 报告
    # ═══════════════════════════════════════
    print("\n" + "="*60)
    print("📋 最终报告")
    print("="*60)
    
    results = {
        "step1_claimed": r1.get("code") == "success",
        "step2_check_collect_box": r2.get("code") == "success",
        "step3_claim_to_shop": r3.get("code") == "success",
        "step5_publish": r5.get("code") == "success",
    }
    
    for k, v in results.items():
        print(f"  {'✅' if v else '❌'} {k}: {'成功' if v else '失败'}")
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\n  📊 总进度: {success_count}/{len(results)} 成功")
    
    if all(results.values()):
        print("\n  🎉 全链路完成！产品已发布到5国TK店铺！")
    else:
        print("\n  ⚠️  部分步骤失败，详见上方日志")

    print("="*60)

if __name__ == "__main__":
    main()
