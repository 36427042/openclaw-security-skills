#!/usr/bin/env python3
"""
🔄 统一 API 客户端 — 所有外部API对接的核心层

功能：
- EchoTik API (Basic Auth + 指数退避)
- 飞书 Bot API (自动Token缓存刷新)
- 1688 搜索 (直接requests替代curl subprocess)
- 通用 REST API (GET/POST + retry + timeout)

用法：
    from api_client import EchoTikAPI, FeishuBot, search_1688
"""

import json, os, sys, time, base64, re
from datetime import datetime, timedelta
from typing import Optional, Any
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ──────────────────────────────────────────
# 🗂️ 路径配置
# ──────────────────────────────────────────
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(SCRIPTS_DIR)
CONFIG_DIR = os.path.join(WORKSPACE, "config")


# ──────────────────────────────────────────
# 🧰 统一Session工厂（连接池+自动重试）
# ──────────────────────────────────────────

def create_session(retries: int = 3, backoff: float = 1.0,
                   pool_connections: int = 10, pool_maxsize: int = 20,
                   timeout: int = 30) -> requests.Session:
    """创建带连接池和自动重试的 Session"""
    session = requests.Session()

    # 重试策略
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.timeout = timeout
    return session


# ──────────────────────────────────────────
# 📄 EchoTik API — 选品数据
# ──────────────────────────────────────────

class EchoTikAPI:
    """EchoTik Open API 客户端（带连接池）"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(CONFIG_DIR, "echotik.json")
        with open(config_path, "r", encoding="utf-8") as f:
            creds = json.load(f)

        self.base_url = creds["base_url"].rstrip("/")
        self.session = create_session(retries=3, backoff=1.0)
        self.session.headers.update(self._build_auth_header(creds))

        # 国家配置
        self.regions = {
            "TH": {"lang": "th-TH", "currency": "THB", "name": "泰国", "rate2usd": 0.028},
            "MY": {"lang": "ms-MY", "currency": "MYR", "name": "马来西亚", "rate2usd": 0.22},
            "VN": {"lang": "vi-VN", "currency": "VND", "name": "越南", "rate2usd": 0.000041},
            "PH": {"lang": "en-US", "currency": "PHP", "name": "菲律宾", "rate2usd": 0.018},
            "SG": {"lang": "en-US", "currency": "SGD", "name": "新加坡", "rate2usd": 0.74},
        }

    @staticmethod
    def _build_auth_header(creds: dict) -> dict:
        """构建 Basic Auth 请求头"""
        auth_str = f"{creds['username']}:{creds['password']}"
        encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}

    def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        """统一请求方法"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = self.session.request(method, url, timeout=30, **kwargs)
            resp.raise_for_status()
            data = resp.json()
            code = data.get("code")
            if code not in (None, 0, 200):
                print(f"  ⚠ API警告 [{path}]: code={code} msg={data.get('message','')}")
            return data
        except requests.exceptions.Timeout:
            print(f"  ⚠ 超时 [{path}]")
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ 请求失败 [{path}]: {e}")
        except json.JSONDecodeError as e:
            print(f"  ⚠ 解析失败 [{path}]: {e}")
        return None

    def get(self, path: str, params: dict = None) -> Optional[dict]:
        return self._request("GET", path, params=params)

    def post(self, path: str, json_data: dict = None) -> Optional[dict]:
        return self._request("POST", path, json=json_data)

    def search_products(self, region: str, category_l3_id: str = None,
                        page_num: int = 1, page_size: int = 10,
                        sort_field: int = 5, sort_type: int = 1,
                        min_price: float = None, max_price: float = None,
                        min_sale_30d: int = None, from_flag: int = None,
                        keyword: str = None) -> list:
        """
        搜索商品列表（正确端点 product/list）
        参数:
            region: TH/MY/VN/PH/SG
            sort_field: 1=总销量 2=总GMV 5=近30天销量 7=近30天GMV
            from_flag: 1=本土 2=跨境
        """
        params_list = [
            f"region={region}",
            f"page_num={page_num}",
            f"page_size={page_size}",
            f"product_sort_field={sort_field}",
            f"sort_type={sort_type}",
        ]
        if category_l3_id:
            params_list.append(f"category_l3_id={category_l3_id}")
        if min_price is not None:
            params_list.append(f"min_spu_avg_price={min_price}")
        if max_price is not None:
            params_list.append(f"max_spu_avg_price={max_price}")
        if min_sale_30d is not None:
            params_list.append(f"min_total_sale_30d_cnt={min_sale_30d}")
        if from_flag is not None:
            params_list.append(f"from_flag={from_flag}")
        if keyword:
            from urllib.parse import quote
            params_list.append(f"keyword={quote(keyword)}")

        path = f"product/list?{'&'.join(params_list)}"
        data = self.get(path)
        if data and isinstance(data, dict):
            return data.get("data", [])
        return []

    def search_by_keyword(self, region: str, keyword: str,
                          page_num: int = 1, page_size: int = 10) -> list:
        """按关键词搜索商品 (v2已移除search端点，用product/list +关键词代替)"""
        return self.search_products(region=region, keyword=keyword,
                                    page_num=page_num, page_size=page_size)

    def get_bgm_songs(self, region: str, page: int = 1,
                      page_size: int = 20, sort: str = "hot") -> list:
        """获取热门BGM (v2已移除bgm端点，返回空)"""
        print(f"  ⚠ bgm/songs端点已在EchoTik v2中移除")
        return []


# ──────────────────────────────────────────
# 📩 飞书 Bot API — 消息推送
# ──────────────────────────────────────────

class FeishuBot:
    """飞书Bot API客户端（带Token自动缓存刷新）"""

    _token_cache: dict = {}  # 类级缓存，全局共享

    def __init__(self, app_id: str = None, app_secret: str = None):
        if app_id and app_secret:
            self.app_id = app_id
            self.app_secret = app_secret
        else:
            # 从config读取（避免硬编码）
            config_path = os.path.join(CONFIG_DIR, "feishu.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.app_id = cfg.get("app_id", "")
                self.app_secret = cfg.get("app_secret", "")
            else:
                # 兜底用环境变量
                self.app_id = os.environ.get("FEISHU_APP_ID", "")
                self.app_secret = os.environ.get("FEISHU_APP_SECRET", "")

        self.session = create_session(retries=2, backoff=0.5)
        self.base = "https://open.feishu.cn/open-apis"
        self.user_open_id = os.environ.get("FEISHU_USER_OPEN_ID",
                                           "ou_71152d1258a3112babdbcd1e2523b785")

    def _get_token(self) -> str:
        """获取（或缓存）飞书 tenant_access_token"""
        # 检查缓存是否过期
        cached = self._token_cache.get(self.app_id)
        if cached and cached["expires_at"] > time.time():
            return cached["token"]

        # 刷新token
        resp = self.session.post(
            f"{self.base}/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取token失败: {data.get('msg')}")

        token = data["tenant_access_token"]
        expire = data.get("expire", 7200)
        # 提前5分钟过期
        self._token_cache[self.app_id] = {
            "token": token,
            "expires_at": time.time() + expire - 300,
        }
        return token

    def send_text(self, text: str, open_id: str = None) -> bool:
        """发送文本消息"""
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "receive_id": open_id or self.user_open_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}),
        }
        resp = self.session.post(
            f"{self.base}/im/v1/messages?receive_id_type=open_id",
            headers=headers, json=payload, timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            print(f"  ⚠ 飞书发送失败: {data.get('msg')}")
            return False
        return True

    def send_markdown(self, title: str, content: str,
                      open_id: str = None) -> bool:
        """发送富文本/消息卡片"""
        token = self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "receive_id": open_id or self.user_open_id,
            "msg_type": "post",
            "content": json.dumps({
                "zh_cn": {
                    "title": title,
                    "content": [[{"tag": "text", "text": content}]],
                }
            }),
        }
        resp = self.session.post(
            f"{self.base}/im/v1/messages?receive_id_type=open_id",
            headers=headers, json=payload, timeout=10,
        )
        data = resp.json()
        if data.get("code") != 0:
            print(f"  ⚠ 飞书富文本失败: {data.get('msg')}")
            return False
        return True


# ──────────────────────────────────────────
# 🏭 1688 搜索（改良版，不再用curl子进程）
# ──────────────────────────────────────────

def search_1688(keyword: str, max_pages: int = 1,
                page_size: int = 5) -> list:
    """
    搜索1688商品（用requests替代curl子进程）

    返回: [{"title": str, "price": str, "url": str, "shop": str, "score": str}]
    """
    from urllib.parse import urlencode

    results = []
    session = create_session(retries=2, backoff=0.5)
    headers = {
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    for page in range(1, max_pages + 1):
        params = {
            "keywords": keyword,
            "n": "y",
            "beginPage": page,
            "pageSize": page_size,
        }
        url = f"https://s.1688.com/selloffer/offer_search.htm?{urlencode(params)}"

        try:
            resp = session.get(url, headers=headers, timeout=15)
            html = resp.text
        except requests.RequestException as e:
            print(f"  ⚠ 1688搜索失败 [{keyword}]: {e}")
            break

        # 提取offer信息
        offer_ids = re.findall(r'//detail\.1688\.com/offer/(\d+)\.html', html)
        titles = re.findall(r'title="([^"]+)"', html)

        for i, oid in enumerate(offer_ids[:page_size]):
            title = titles[i] if i < len(titles) else keyword
            results.append({
                "title": title.strip(),
                "url": f"https://detail.1688.com/offer/{oid}.html",
                "offer_id": oid,
            })

        if len(offer_ids) < page_size:
            break  # 没有更多结果

    return results


# ──────────────────────────────────────────
# 🔌 通用 REST API 客户端
# ──────────────────────────────────────────

class RestAPI:
    """通用 REST API 客户端（带连接池、自动重试）"""

    def __init__(self, base_url: str, headers: dict = None,
                 auth: tuple = None, retries: int = 3):
        self.base_url = base_url.rstrip("/")
        self.session = create_session(retries=retries)
        if headers:
            self.session.headers.update(headers)
        if auth:
            self.session.auth = auth

    def get(self, path: str, **kwargs) -> Optional[dict]:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Optional[dict]:
        return self._request("POST", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = self.session.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"  ⚠ REST [{method} {path}]: {e}")
            return None


# ──────────────────────────────────────────
# 🧪 快速测试
# ──────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 api_client.py <test>")
        print("  test-1688 <关键词>     — 测试1688搜索")
        print("  test-echotik <region>  — 测试EchoTik连接")
        print("  test-feishu <消息>     — 测试飞书推送")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "test-1688":
        keyword = sys.argv[2] if len(sys.argv) > 2 else "切菜器"
        results = search_1688(keyword)
        print(f"🔍 1688搜索「{keyword}」: {len(results)}条结果")
        for r in results[:3]:
            print(f"  📦 {r['title'][:40]} → {r['url']}")
        print("✅ 1688 API 测试完成")

    elif cmd == "test-echotik":
        region = sys.argv[2] if len(sys.argv) > 2 else "TH"
        client = EchoTikAPI()
        products = client.search_products(region, page_size=3)
        print(f"🔍 EchoTik [{region}]: {len(products)}商品")
        if products:
            print(f"  首条: {json.dumps(products[0], ensure_ascii=False)[:200]}")
        print("✅ EchoTik API 测试完成")

    elif cmd == "test-feishu":
        msg = sys.argv[2] if len(sys.argv) > 2 else "🥔 API客户端测试消息"
        bot = FeishuBot()
        ok = bot.send_text(msg)
        print(f"{'✅' if ok else '❌'} 飞书推送: {msg}")
