#!/usr/bin/env python3
"""
搜索TK类目树找到粉扑/美妆蛋类目ID
同时修正美妆蛋title到25字符+
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

# 深度搜索TK类目树
def print_tree(tree, indent=0):
    for k, v in tree.items():
        if isinstance(v, dict):
            name = v.get("categoryName", v.get("name", k))
            cid = v.get("cid", v.get("categoryId", k))
            prefix = "  " * indent
            print(f"{prefix}{name} (cid={cid})")
            kids = v.get("children", v.get("subCateList", {}))
            if kids and isinstance(kids, dict):
                print_tree(kids, indent + 1)

# 先看根类目
print("=== TH类目树根节点 ===")
r = client.get_category_tree("TH")
tree = r.get("data", {}).get("cateTree", {})
for k, v in tree.items():
    if isinstance(v, dict):
        name = v.get("categoryName", v.get("name", k))
        cid = v.get("cid", v.get("categoryId", k))
        print(f"  {name} (cid={cid})")

# 找"美妆"类目
print("\n=== 搜索美妆/化妆工具类目 ===")
def search_cats(tree, target, path=""):
    results = []
    for k, v in tree.items():
        if isinstance(v, dict):
            name = v.get("categoryName", v.get("name", k))
            cid = v.get("cid", v.get("categoryId", k))
            curr = f"{path}/{name}" if path else name
            if target.lower() in name.lower() or target.lower() in k.lower():
                results.append({"path": curr, "cid": cid, "name": name})
            kids = v.get("children", v.get("subCateList", {}))
            if kids and isinstance(kids, dict):
                results.extend(search_cats(kids, target, curr))
    return results

for target in ["美妆", "美妆工具", "化妆工具", "美容", "彩妆", "粉扑", "海绵", "脸部"]:
    results = search_cats(tree, target)
    if results:
        print(f"\n'{target}':")
        for r in results[:10]:
            print(f"  {r['path']} → cid={r['cid']}")
