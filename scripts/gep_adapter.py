#!/usr/bin/env python3
"""
🧬 GEP Adapter — 6伙伴GEP接入适配器
每个伙伴通过此脚本接入GEP：
  1. pre_check: 执行前检查历史经验
  2. post_record: 执行后记录结果
  3. keepalive: 心跳保活检查
"""

import sys, os, json, subprocess, time
sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/scripts"))
from gep_engine import GEP

# ── 伙伴映射 ──
PARTNERS = {
    "booster": "番茄",
    "corn": "玉米",
    "lettuce": "生菜",
    "bittergourd": "苦瓜",
    "carrot": "萝卜",
    "pea": "豌豆",
}

def pre_check(name, task, context=None):
    """执行前检查：GEP历史经验"""
    partner = PARTNERS.get(name, name)
    gep = GEP(partner)
    advice = gep.pre_check(task, context or {})
    if advice:
        print(f"📖 [{partner}] 历史经验：{len(advice.get('warnings',[]))}条警告")
        for w in advice.get("warnings", [])[:3]:
            print(f"  ⚠️  {w}")
        if advice.get("solutions"):
            print(f"  💡 建议方案: {advice['solutions'][0][:100]}")
    else:
        print(f"🟢 [{partner}] 无相关历史经验，可正常执行")
    return advice

def post_record(name, task, outcome, context=None, problem="", note=""):
    """执行后记录：结果写入GEP"""
    partner = PARTNERS.get(name, name)
    gep = GEP(partner)
    context = context or {}
    node_id = gep.post_record(task, context, outcome, problem, note)
    print(f"📝 [{partner}] {task} → {outcome} (节点: {node_id})")
    return node_id

def keepalive(name):
    """保活心跳：伙伴健康检查 + GEP接入"""
    partner = PARTNERS.get(name, name)
    gep = GEP(partner)
    
    # 1. GEP检查
    advice = gep.pre_check("保活检查", {"action": "keepalive"})
    
    # 2. 状态检查
    check_items = {
        "memory": os.path.isdir(os.path.expanduser(f"~/.openclaw/workspace/agents/{name}-agent/memory")),
        "identity": os.path.isfile(os.path.expanduser(f"~/.openclaw/workspace/agents/{name}-agent/IDENTITY.md")),
        "soul": os.path.isfile(os.path.expanduser(f"~/.openclaw/workspace/agents/{name}-agent/SOUL.md")),
    }
    all_ok = all(check_items.values())
    
    # 3. GEP记录
    gep.post_record("保活检查", {"status": "ok" if all_ok else "warning"},
                    outcome="success" if all_ok else "warning",
                    note=f"保活检查: {check_items}")
    
    # 4. GEP统计
    stats = gep.get_stats()
    
    print(f"[{partner}] 保活检查结果:")
    print(f"  文件完整性: {'✅' if all_ok else '⚠️'}")
    for k, v in check_items.items():
        print(f"    {k}: {'✅' if v else '❌'}")
    print(f"  GEP统计: 总{stats['total']}节点, 成功{stats.get('by_outcome',{}).get('success',0)}")
    print(f"  GEP咨询: {'有历史经验' if advice else '无历史经验'}")
    
    return all_ok

def keepalive_all():
    """全部6伙伴保活"""
    results = {}
    for name in PARTNERS:
        print(f"\n{'='*40}")
        print(f"  {PARTNERS[name]} ({name})")
        print(f"{'='*40}")
        ok = keepalive(name)
        results[name] = ok
    
    print(f"\n{'='*40}")
    print(f"  保活汇总")
    print(f"{'='*40}")
    ok_count = sum(1 for v in results.values() if v)
    print(f"  ✅ {ok_count}/6 正常")
    for name, ok in results.items():
        print(f"  {'✅' if ok else '⚠️'} {PARTNERS[name]} ({name})")
    
    return results

def export_report():
    """导出GEP报告"""
    from gep_engine import export_report
    path = export_report()
    print(f"📋 GEP报告已导出: {path}")
    return path

def get_status():
    """全局状态"""
    from gep_engine import GEPRegistry
    registry = GEPRegistry()
    stats = registry.get_stats()
    print("📊 GEP全局状态:")
    print(f"  总节点: {stats['total']}")
    print(f"  伙伴分布:")
    for p, c in sorted(stats.get("by_partner", {}).items(), key=lambda x: -x[1]):
        print(f"    {p}: {c}")
    print(f"  结果分布:")
    for o, c in sorted(stats.get("by_outcome", {}).items()):
        print(f"    {o}: {c}")
    print(f"  最后更新: {stats.get('last_update','?')[:19]}")
    return stats

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  gep_adapter.py status          # GEP全局状态")
        print("  gep_adapter.py keepalive <伙伴>  # 单个伙伴保活")
        print("  gep_adapter.py keepalive_all    # 全部6伙伴保活")
        print("  gep_adapter.py pre_check <伙伴> <任务>  # 执行前检查")
        print("  gep_adapter.py post_record <伙伴> <任务> <结果>  # 执行后记录")
        print("  gep_adapter.py report           # 导出GEP报告")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        get_status()
    elif cmd == "keepalive":
        if len(sys.argv) < 3:
            print("需要指定伙伴名 (booster/corn/lettuce/bittergourd/carrot/pea)")
            sys.exit(1)
        keepalive(sys.argv[2])
    elif cmd == "keepalive_all":
        keepalive_all()
    elif cmd == "pre_check":
        if len(sys.argv) < 4:
            print("用法: gep_adapter.py pre_check <伙伴> <任务>")
            sys.exit(1)
        pre_check(sys.argv[2], sys.argv[3])
    elif cmd == "post_record":
        if len(sys.argv) < 5:
            print("用法: gep_adapter.py post_record <伙伴> <任务> <结果>")
            sys.exit(1)
        post_record(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "report":
        export_report()
    else:
        print(f"未知命令: {cmd}")
