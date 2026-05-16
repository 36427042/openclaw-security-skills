#!/usr/bin/env python3
"""
深度搜索TH类目树
"ความงามและของใช้ส่วนตัว" = Beauty & Personal Care (cid=601450)
需要找到粉扑/美妆蛋的TK类目ID
"""
import sys, json
sys.path.insert(0, "/Users/a1234/.openclaw/workspace/agents/tomato-agent/scripts")
from miaoshou_client import MiaoshouClient

APP_KEY = "ak_680398a828ce43de832d342c8dcc89ef"
APP_SECRET = "325da4319dc8431faca7fb13c8938cd436eb17a51b5947d794125fd3b8acc493"

client = MiaoshouClient(APP_KEY, APP_SECRET)

r = client.get_category_tree("TH")
tree = r.get("data", {}).get("cateTree", {})

# 往下钻取美妆类目
def find_kids(tree, target_cid, max_depth=5):
    """找特定cid的子类目"""
    def _recurse(node, target, depth):
        if depth > max_depth:
            return None
        if isinstance(node, dict):
            cid = str(node.get("cid", node.get("categoryId", "")))
            if cid == str(target):
                return node
            for k, v in node.items():
                if k == "children" or k == "subCateList":
                    result = _recurse(v, target, depth)
                    if result:
                        return result
                elif isinstance(v, dict):
                    result = _recurse(v, target, depth)
                    if result:
                        return result
        elif isinstance(node, (list, tuple)):
            for item in node:
                if isinstance(item, dict):
                    result = _recurse(item, target, depth)
                    if result:
                        return result
        return None
    
    return _recurse(tree, target_cid, 0)

def print_all_tree(node, indent=0, max_items=300):
    """打印完整的类目树"""
    count = [0]
    def _print(node, indent):
        if count[0] >= max_items:
            return
        if isinstance(node, dict):
            # Check if it's a leaf node or structure node
            name = node.get("categoryName", node.get("name", ""))
            cid = node.get("cid", node.get("categoryId", ""))
            if name and cid:
                prefix = "  " * indent
                print(f"{prefix}{name} (cid={cid})")
                count[0] += 1
            # Check children
            for k in ["children", "subCateList"]:
                if k in node and node[k] and isinstance(node[k], dict):
                    _print(node[k], indent + 1)
                elif k in node and node[k] and isinstance(node[k], list):
                    for item in node[k][:10]:
                        _print(item, indent + 1)
            # Check other keys for nested dicts
            for k, v in node.items():
                if k not in ["children", "subCateList", "categoryName", "name", "cid", "categoryId"]:
                    if isinstance(v, dict) and v:
                        _print(v, indent)
        elif isinstance(node, list):
            for item in node[:10]:
                _print(item, indent)
    
    _print(node, indent)

# 找Beauty类目
print("=== 搜索Beauty类目(601450)的子类目 ===")
beauty_node = find_kids(tree, 601450, max_depth=1)
if beauty_node:
    kids = beauty_node.get("children", beauty_node.get("subCateList", {}))
    if isinstance(kids, dict):
        print(f"子类目数量: {len(kids)}")
        print_all_tree(kids, indent=2, max_items=50)
    else:
        print(f"子类目类型: {type(kids)}, {json.dumps(kids, ensure_ascii=False)[:500]}")
else:
    print("没找到Beauty类目")

# 直接打印前几层
print("\n=== 完整树===")
def dump_structured_tree(node, depth=0, max_depth=3):
    if depth > max_depth:
        return ""
    result = ""
    if isinstance(node, dict):
        name = node.get("categoryName", node.get("name", ""))
        cid = node.get("cid", node.get("categoryId", ""))
        if name:
            result += "  " * depth + f"{name} (cid={cid})\n"
        for k in ["children", "subCateList"]:
            if k in node and node[k]:
                if isinstance(node[k], dict):
                    # Check if it's a dict of subcategories
                    for sub_k, sub_v in node[k].items():
                        if isinstance(sub_v, dict):
                            sub_name = sub_v.get("categoryName", sub_v.get("name", ""))
                            sub_cid = sub_v.get("cid", sub_v.get("categoryId", ""))
                            if sub_name:
                                result += "  " * (depth+1) + f"{sub_name} (cid={sub_cid})\n"
                                # Try to go deeper
                                for sub_k2 in ["children", "subCateList"]:
                                    if sub_k2 in sub_v and sub_v[sub_k2]:
                                        for ssk, ssv in sub_v[sub_k2].items():
                                            if isinstance(ssv, dict):
                                                ssn = ssv.get("categoryName", ssv.get("name", ""))
                                                ssc = ssv.get("cid", ssv.get("categoryId", ""))
                                                if ssn:
                                                    result += "  " * (depth+2) + f"{ssn} (cid={ssc})\n"
                elif isinstance(node[k], list):
                    for item in node[k][:5]:
                        if isinstance(item, dict):
                            iname = item.get("categoryName", item.get("name", ""))
                            icid = item.get("cid", item.get("categoryId", ""))
                            if iname:
                                result += "  " * (depth+1) + f"{iname} (cid={icid})\n"
    return result

print(dump_structured_tree(tree, max_depth=2))
