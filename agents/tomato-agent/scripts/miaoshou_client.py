#!/usr/bin/env python3
"""
妙手开放平台 API 客户端 v2 ✅ (路径已修正)
Base: https://openapi-erp.91miaoshou.com
签名: HmacSHA256(appSecret, appSecret + path + timestamp + appKey + bodyJson + appSecret)

⚠️ v1 bug: 所有API路径都是瞎编的，不是真实路径
   真实路径来自 apis.md 文档，带完整/collect_box/层级
"""
import hmac, hashlib, json, time
from typing import Optional, Dict, Any, List
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_URL = "https://openapi-erp.91miaoshou.com"

# ── 签名 ──
def generate_sign(app_secret: str, path: str, timestamp: int, app_key: str, body_json: str = "") -> str:
    content = app_secret + path + str(timestamp) + app_key + body_json + app_secret
    return hmac.new(
        app_secret.encode("utf-8"),
        content.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

class MiaoshouClient:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret

    def request(self, path: str, body: Optional[Dict] = None) -> Dict:
        timestamp = int(time.time())
        body_json = json.dumps(body, ensure_ascii=False, separators=(",", ":")) if body else ""
        sign = generate_sign(self.app_secret, path, timestamp, self.app_key, body_json)

        headers = {
            "x-app-key": self.app_key,
            "x-timestamp": str(timestamp),
            "x-sign": sign,
            "Content-Type": "application/json",
        }
        url = f"{BASE_URL}{path}"
        data = body_json.encode("utf-8") if body_json else b""

        req = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            return {"error": True, "http_code": e.code, "detail": err_body}

    # ═══════════════════════════════════════
    # 3. 店铺
    # ═══════════════════════════════════════
    def get_shop_list(self, platform: str = "tiktok", site: str = "TH",
                      page_no: int = 1, page_size: int = 20) -> Dict:
        """获取店铺列表"""
        return self.request("/open/v1/product/shop/shop/get_shop_list", {
            "platform": platform, "site": site,
            "pageNo": page_no, "pageSize": page_size
        })

    # ═══════════════════════════════════════
    # 1. 公共采集箱
    # ═══════════════════════════════════════
    _PUBLIC = "/open/v1/product/common_collect_box/common_collect_box"

    def fetch_item(self, collect_links: List[str]) -> Dict:
        """采集货源链接到公共采集箱（最多50条/次）"""
        return self.request(f"{self._PUBLIC}/fetch_item", {"collectLinks": collect_links})

    def get_collect_box_list(self, page_no: int = 1, page_size: int = 20,
                             tab_pane: str = "all", keyword: str = "") -> Dict:
        """公共采集箱列表"""
        return self.request(f"{self._PUBLIC}/get_common_collect_box_list", {
            "pageNo": page_no, "pageSize": page_size,
            "filter": {"tabPaneName": tab_pane, "sourceItemIdKeyword": keyword}
        })

    def get_collect_box_detail(self, detail_id: int) -> Dict:
        """公共采集箱详情（含所有SKU/图片/描述/认证）"""
        return self.request(f"{self._PUBLIC}/get_common_collect_box_detail",
                            {"commonCollectBoxDetailId": detail_id})

    def add_collect_box_detail(self, data: Dict) -> Dict:
        """手动创建采集箱商品"""
        return self.request(f"{self._PUBLIC}/add_common_collect_box_detail", data)

    def edit_collect_box_detail(self, detail_id: int, oss_md5: str, edit_data: Dict) -> Dict:
        """编辑采集箱商品（需要先get_detail拿到ossMd5）"""
        return self.request(f"{self._PUBLIC}/edit_common_collect_box_detail", {
            "commonCollectBoxDetailId": detail_id,
            "ossMd5": oss_md5,
            "editCommonCollectBoxDetail": edit_data
        })

    def batch_delete_collect_box_detail(self, detail_ids: List[int]) -> Dict:
        """批量删除采集箱商品"""
        return self.request(f"{self._PUBLIC}/batch_delete_common_collect_box_detail",
                            {"commonCollectBoxDetailIds": detail_ids})

    def claimed(self, items: List[Dict]) -> Dict:
        """
        认领到平台采集箱 → 后续上架
        items: [{"detailId": 12345, "platform": "tiktok", "serialNumber": 1}, ...]
        """
        return self.request(f"{self._PUBLIC}/claimed",
                            {"detailSerialNumberPlatformList": items})

    # ═══════════════════════════════════════
    # 2. TK采集箱
    # ═══════════════════════════════════════
    _TK = "/open/v1/product/collect_box/tiktok/collect_box"

    def get_category_tree(self, site: str) -> Dict:
        """获取TK站点类目树"""
        return self.request(f"{self._TK}/get_category_tree_by_site", {"site": site})

    def get_category_metadata(self, site: str, cid: int, shop_ids: List[int] = None) -> Dict:
        """获取类目属性信息（上架前必查）"""
        params = {"cid": cid}
        if shop_ids:
            params["shopIds"] = shop_ids
        else:
            params["site"] = site
        return self.request(f"{self._TK}/get_category_metadata", params)

    def get_warehouse_list(self, shop_ids: List[int]) -> Dict:
        """获取店铺仓库列表"""
        return self.request(f"{self._TK}/get_shop_warehouse_list", {"shopIds": shop_ids})

    def get_manufacturer_list(self, shop_id: int, refresh: int = 0) -> Dict:
        """获取制造商列表"""
        return self.request(f"{self._TK}/get_manufacturer_list",
                            {"shopId": shop_id, "refresh": refresh})

    def get_responsible_person_list(self, shop_id: int, refresh: int = 0) -> Dict:
        """获取欧盟责任人列表"""
        return self.request(f"{self._TK}/get_responsible_person_list",
                            {"shopId": shop_id, "refresh": refresh})

    def claim_to_shop(self, shop_ids: List[int], detail_ids: List[int]) -> Dict:
        """认领到店铺预发布"""
        return self.request(f"{self._TK}/claim_to_shop",
                            {"shopIds": shop_ids, "detailIds": detail_ids})

    def search_collect_box_list(self, page_no: int = 1, page_size: int = 20,
                                status: str = "notPublished", keyword: str = "") -> Dict:
        """TK采集箱列表"""
        return self.request(f"{self._TK}/search_collect_box_detail_list", {
            "pageNo": page_no, "pageSize": page_size,
            "filter": {"status": status, "sourceItemIdKeyword": keyword}
        })

    def get_shop_collect_item_info(self, detail_id: int, shop_id: int) -> Dict:
        """获取采集箱店铺模式详情（含ossMd5）"""
        return self.request(f"{self._TK}/get_shop_collect_item_info",
                            {"detailId": detail_id, "shopId": shop_id})

    def save_shop_collect_item_info(self, oss_md5: str, detail_id: int, shop_id: int,
                                    info: Dict) -> Dict:
        """保存采集箱店铺模式详情"""
        return self.request(f"{self._TK}/save_shop_collect_item_info", {
            "ossMd5": oss_md5, "detailId": detail_id, "shopId": shop_id,
            "shopCollectItemInfo": info
        })

    def get_site_collect_item_info(self, detail_id: int, site: str) -> Dict:
        """获取采集箱站点模式详情"""
        return self.request(f"{self._TK}/get_site_collect_item_info",
                            {"detailId": detail_id, "site": site})

    def save_site_collect_item_info(self, oss_md5: str, detail_id: int, site: str,
                                    info: Dict) -> Dict:
        """保存采集箱站点模式详情"""
        return self.request(f"{self._TK}/save_site_collect_item_info", {
            "ossMd5": oss_md5, "detailId": detail_id, "site": site,
            "siteCollectItemInfo": info
        })

    def publish(self, shop_ids: List[int], detail_ids: List[int]) -> Dict:
        """正式发布产品到TK店铺"""
        return self.request(f"{self._TK}/save_move_collect_task", {
            "shopIds": shop_ids, "detailIds": detail_ids
        })


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("usage: python3 miaoshou_client.py <app_key> <app_secret>")
        sys.exit(1)

    app_key = sys.argv[1]
    app_secret = sys.argv[2]
    client = MiaoshouClient(app_key, app_secret)

    print("=== 妙手API v2 连通测试 ===\n")

    # 测试1: 店铺列表
    r = client.get_shop_list("tiktok", "TH")
    code = r.get("code", r.get("error", "unknown"))
    if code == "success":
        shops = r.get("data", {}).get("shopList", [])
        print(f"✅ get_shop_list (TH): {len(shops)} shops")
        for s in shops:
            print(f"   Shop {s['shopId']} | {s['siteName']} | {s['status']}")
    else:
        print(f"❌ get_shop_list: {r}")

    # 测试2: 类目树
    r = client.get_category_tree("TH")
    if r.get("code") == "success":
        cats = r.get("data", {}).get("cateTree", {})
        print(f"✅ get_category_tree (TH): {len(cats)} categories")
    else:
        print(f"⚠️  get_category_tree: {r.get('code', r)}")

    # 测试3: 获取所有5国店铺
    for site in ["TH", "MY", "VN", "PH", "SG"]:
        r = client.get_shop_list("tiktok", site)
        if r.get("code") == "success":
            shops = r.get("data", {}).get("shopList", [])
            for s in shops:
                print(f"✅ {site}: Shop {s['shopId']} | auth_expire: {s['gmtExpire']}")
        else:
            print(f"❌ {site}: {r.get('code', r)}")