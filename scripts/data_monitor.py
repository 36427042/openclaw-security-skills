#!/usr/bin/env python3
"""
data_monitor.py — 数据监控+飞书推送 🫘
功能：异常检测、经营数据汇总、飞书卡片推送
GEP: 记录检测模式，学习阈值调整
"""
import json, os, sys, time, requests
from datetime import datetime
from gep_engine import GEP

gep = GEP("豌豆")

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
DATA_DIR = os.path.join(WORKSPACE, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

FEISHU_WEBHOOK = ""  # 需要配置

# 飞书多维表格信息
BITABLE_APP_TOKEN = "Mm7tbK…nnQh"
FEISHU_TENANT_TOKEN = ""

# 异常阈值
THRESHOLDS = {
    "gmv_drop_pct": -30,
    "refund_rate_pct": 20,
    "negative_rate_pct": 10,
    "order_drop_pct": -40,
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(LOG_DIR, "data_monitor.log"), "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(f"  📊 [{ts}] {msg}")

def push_to_feishu(message: str):
    """推送消息到飞书（webhook方式）"""
    if not FEISHU_WEBHOOK:
        log("⚠️ 飞书webhook未配置")
        gep.post_record("push_to_feishu", {}, "skipped", problem="webhook未配置")
        return False
    try:
        resp = requests.post(FEISHU_WEBHOOK, json={
            "msg_type": "text", "content": {"text": message}
        }, timeout=10)
        success = resp.status_code == 200
        gep.post_record("push_to_feishu", {}, "success" if success else "failed")
        return success
    except Exception as e:
        gep.post_record("push_to_feishu", {}, "failed", problem=str(e),
                        solution="检查网络或webhook地址")
        log(f"❌ 飞书推送失败: {e}")
        return False

def push_card_to_feishu(title: str, content: str):
    """推送飞书卡片"""
    card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": title}, "template": "blue"},
        "elements": [{"tag": "markdown", "content": content}]
    }
    payload = {"msg_type": "interactive", "card": card}
    try:
        if FEISHU_WEBHOOK:
            resp = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
            gep.post_record("push_card_to_feishu", {}, "success" if resp.status_code == 200 else "failed")
        log(f"📋 飞书卡片: {title}")
    except Exception as e:
        gep.post_record("push_card_to_feishu", {}, "failed", problem=str(e))
        log(f"❌ 卡片推送失败: {e}")

def check_anomalies(stats: dict) -> list:
    """检测异常指标（GEP增强）"""
    alerts = []
    for metric, threshold in THRESHOLDS.items():
        value = stats.get(metric, 0)
        if isinstance(value, (int, float)):
            is_triggered = False
            if threshold < 0 and value <= threshold:
                is_triggered = True
            elif threshold > 0 and value >= threshold:
                is_triggered = True

            if is_triggered:
                alerts.append(f"⚠️ {metric}: {value}% (阈值: {threshold}%)")
                # GEP: 记录异常模式
                gep.post_record("check_anomalies", {"metric": metric, "value": value},
                                "alert", problem=f"{metric}={value}%超阈值{threshold}%")
    return alerts

def generate_daily_summary() -> dict:
    """生成每日经营摘要"""
    summary = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "countries": ["TH", "MY", "VN", "ID", "PH"],
        "total_orders": 0,
        "total_gmv": 0,
        "total_refunds": 0,
        "status": "模拟数据（待对接真实数据源）"
    }
    # GEP: 如果之前告警过数据缺失，记录提示
    gep.post_record("generate_daily_summary", {}, "info",
                    note="使用模拟数据，尚未对接真实API")
    return summary

def main(action: str = None, push: bool = False):
    """数据监控主入口
    接收参数，执行数据检测，输出JSON到stdout供框架捕获
    """
    log("=" * 40)
    log("🫘 数据监控启动 (GEP进化引擎已加载)")

    summary = generate_daily_summary()
    alerts = check_anomalies(summary)

    if action == "push" or push:
        if alerts:
            alert_text = f"【数据告警】{summary['date']}:\n" + "\n".join(alerts)
            log(f"🚨 发现 {len(alerts)} 个异常")
            for a in alerts:
                log(f"  {a}")
            push_to_feishu(alert_text)
            push_card_to_feishu(summary['date'] + "经营数据", "\n".join(alerts))
        else:
            log("✅ 无异常，跳过推送")
    else:
        if alerts:
            log(f"🚨 发现 {len(alerts)} 个异常")
            for a in alerts:
                log(f"  {a}")
        else:
            log("✅ 无异常")

    stats = gep.get_stats()
    log(f"📊 GEP进化节点: {stats.get('total', 0)}条")
    log("数据监控运行完成")
    log("=" * 40)

    # JSON stdout — 框架捕获
    output = {
        "status": "completed",
        "summary": summary,
        "alerts": alerts,
        "alert_count": len(alerts),
        "gep_stats": stats,
    }
    print(json.dumps(output, ensure_ascii=False))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🫘 豌豆·数据监控")
    parser.add_argument("--action", default=None, choices=["check","push",None], help="动作")
    parser.add_argument("--push", action="store_true", help="推送飞书")
    args = parser.parse_args()
    sys.exit(0 if main(args.action, args.push) or True else 1)
