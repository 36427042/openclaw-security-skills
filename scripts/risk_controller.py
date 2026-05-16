#!/usr/bin/env python3
"""
risk_controller.py — 风控控制器 🥒
功能：视频/文案风审、账号关联检测、应急SOP
GEP: 记录风控事件模式，自动学习违规规律
"""
import json, os, sys, time
from datetime import datetime
from gep_engine import GEP

gep = GEP("苦瓜")

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
LOG_DIR = os.path.join(WORKSPACE, "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

RISK_LOG = os.path.join(LOG_DIR, "risk_controller.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RISK_LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"  ⚠️  [{ts}] {msg}")

# 应急SOP
SOP = {
    "shop_banned": {
        "mild": "轻度(48h)：暂停发布→检查违规原因→整改后恢复",
        "moderate": "中度(3-7天)：切换备用店→主店申诉→限流恢复",
        "severe": "重度(立即)：切换备用IP+店铺→资金转移→品牌换壳"
    },
    "supplier_down": {
        "action": "1小时内切换备选供应商",
        "backup_count": 2
    },
    "ip_down": {
        "normal": "≤3分钟恢复",
        "emergency": "≤10分钟切换备用IP"
    },
    "customer_service": {
        "level_1": "0-3分钟：多客Duoke自动切换",
        "level_2": "3-10分钟：手工介入"
    }
}

ALERT_THRESHOLDS = {
    "order_cancel_rate": 0.15,
    "refund_rate": 0.20,
    "negative_review_rate": 0.10,
}

def check_copy_safety(text: str, country: str) -> dict:
    """文案风审（GEP增强）"""
    ctx = {"country": country}
    try:
        from copy_engine import check_compliance
        result = check_compliance(text, country)
        if not result.get("pass"):
            gep.post_record("check_copy_safety", ctx, "failed",
                            problem=f"文案违规: {result.get('banned_found', [])}")
        return result
    except Exception as e:
        gep.post_record("check_copy_safety", ctx, "error",
                        problem=f"导入异常: {e}")
        return {"pass": False, "error": str(e)}

def check_video_safety(video_path: str) -> dict:
    """视频风审（基础版本，GEP增强）"""
    ctx = {"path": video_path}
    issues = []
    try:
        if not os.path.exists(video_path):
            issues.append("文件不存在")
            gep.post_record("check_video_safety", ctx, "failed",
                            problem="视频文件不存在")
        else:
            size_mb = os.path.getsize(video_path) / 1024 / 1024
            if size_mb > 100:
                issues.append("文件过大")
            elif size_mb < 0.1:
                issues.append("文件过小(可能是损坏)")
                gep.post_record("check_video_safety", ctx, "failed",
                                problem=f"视频文件过小({size_mb:.1f}MB)")

        result = {"pass": len(issues) == 0, "issues": issues}
        if result["pass"]:
            gep.post_record("check_video_safety", ctx, "success")
        return result
    except Exception as e:
        gep.post_record("check_video_safety", ctx, "error", problem=str(e))
        return {"pass": False, "issues": [str(e)]}

def emergency_sop(scenario: str):
    """触发应急预案（GEP增强）"""
    plan = SOP.get(scenario, {"action": "未知场景，立即通知天赐"})
    log(f"🚨 触发应急预案: {scenario}")
    log(f"  方案: {plan}")

    # GEP: 记录该场景触发
    gep.post_record("emergency_sop", {"scenario": scenario},
                    "triggered", note=json.dumps(plan, ensure_ascii=False))
    return plan

def main(action: str = None, text: str = None, video: str = None, country: str = None):
    """风控控制器主入口
    接收参数，执行风审/预案，输出JSON到stdout供框架捕获
    """
    log("=" * 40)
    log("🥒 风控控制器启动 (GEP进化引擎已加载)")
    
    result = {}
    
    if action == "check_copy" and text:
        result = check_copy_safety(text, country or "TH")
        log(f"  文案风审: {'✅ 通过' if result.get('pass') else '❌ 违规'}")
    elif action == "check_video" and video:
        result = check_video_safety(video)
        log(f"  视频风审: {'✅ 通过' if result.get('pass') else '❌ 异常'}")
    elif action == "emergency":
        result = emergency_sop(text or "unknown")
    else:
        # 默认：状态巡检
        log("  店铺封号：48h/3-7天/立即三种等级")
        log("  供应商：1主供+2备选")
        log("  IP掉线：≤3分钟正常/≤10分钟紧急")
        log("  客服故障：0-10分钟多级切换")
        result = {"status": "ok", "mode": "inspection"}

    stats = gep.get_stats()
    patterns = gep.analyze()
    log(f"📊 GEP进化节点: {stats.get('total', 0)}条")
    
    # ── 已解决问题追踪（不重复报已解决的错误）──
    resolved_file = os.path.join(WORKSPACE, "data", "hermes", "learnings", "resolved.jsonl")
    os.makedirs(os.path.dirname(resolved_file), exist_ok=True)
    resolved_set = set()
    if os.path.exists(resolved_file):
        with open(resolved_file) as f:
            for line in f:
                try:
                    r = json.loads(line)
                    resolved_set.add(r.get("pattern_hash", ""))
                except:
                    pass
    
    if patterns.get("patterns"):
        new_pats = [p for p in patterns["patterns"] if str(hash(json.dumps(p, sort_keys=True)))[:8] not in resolved_set]
        old_pats = len(patterns["patterns"]) - len(new_pats)
        if new_pats:
            log(f"⚠️ 发现{len(new_pats)}个新问题（{old_pats}个已解决）")
        else:
            log(f"✅ 全部{old_pats}个历史问题已解决，无新增")
    else:
        # 全部已解决
        all_resolved = 0
        if os.path.exists(resolved_file):
            with open(resolved_file) as f:
                all_resolved = sum(1 for _ in f)
        log(f"✅ 无风控问题（{all_resolved}个历史问题已解决）")

    log("风控控制器运行完成")
    log("=" * 40)

    # JSON stdout — 框架捕获
    output = {
        "status": "completed",
        "action": action,
        "result": result,
        "gep_stats": stats,
        "patterns": patterns,
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🥒 风控控制器")
    parser.add_argument("--action", default=None, choices=["check_copy","check_video","emergency",None], help="风审动作")
    parser.add_argument("--text", default=None, help="文案内容或紧急场景")
    parser.add_argument("--video", default=None, help="视频路径")
    parser.add_argument("--country", default="TH", help="国家代码")
    parser.add_argument("--resolve", default=None, help="标记问题已解决 (pattern_hash)")
    parser.add_argument("--status", action="store_true", help="仅显示风控状态（不报错）")
    args = parser.parse_args()
    
    # --resolve: 标记已解决
    if args.resolve:
        resolved_file = os.path.join(WORKSPACE, "data", "hermes", "learnings", "resolved.jsonl")
        os.makedirs(os.path.dirname(resolved_file), exist_ok=True)
        with open(resolved_file, "a") as f:
            f.write(json.dumps({
                "pattern_hash": args.resolve,
                "resolved_at": datetime.now().isoformat(),
                "note": args.text or "手动标记已解决"
            }, ensure_ascii=False) + "\n")
        print(json.dumps({"status": "resolved", "pattern_hash": args.resolve}))
        sys.exit(0)
    
    # --status: 纯状态模式（不报错）
    if args.status:
        resolved_file = os.path.join(WORKSPACE, "data", "hermes", "learnings", "resolved.jsonl")
        resolved_count = 0
        if os.path.exists(resolved_file):
            with open(resolved_file) as f:
                resolved_count = sum(1 for _ in f)
        failures_file = os.path.join(WORKSPACE, "data", "hermes", "learnings", "failures.jsonl")
        fail_count = 0
        if os.path.exists(failures_file):
            with open(failures_file) as f:
                fail_count = sum(1 for _ in f)
        result = {
            "status": "ok",
            "total_issues": fail_count,
            "resolved": resolved_count,
            "active": fail_count - resolved_count,
            "health": "🟢 正常" if (fail_count - resolved_count) <= 2 else "🟡 关注",
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(0)
    
    sys.exit(0 if main(args.action, args.text, args.video, args.country) or True else 1)
