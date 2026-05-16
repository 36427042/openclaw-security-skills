#!/usr/bin/env python3
"""
hermes_watch.py — Hermes 实时监控系统
监控系统事件：cron执行、伙伴状态、系统健康、异常告警

用法:
    from hermes_watch import watcher

    # 记录事件
    watcher.log("cron", "cron-morning-plan", "completed", "正常完成")

    # 查看事件
    events = watcher.events(limit=20)

    # 系统概览
    summary = watcher.summary()
"""

import json
import logging
import os
import threading
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Dict, List, Optional

logger = logging.getLogger("hermes_watch")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/events")
os.makedirs(DATA_DIR, exist_ok=True)
EVENTS_PATH = os.path.join(DATA_DIR, "events.jsonl")

# 事件严重级别
SEVERITY_EMOJI = {
    "info": "ℹ️",
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "critical": "🔥",
}


class Watcher:
    """实时监控"""

    def __init__(self, max_events: int = 2000):
        self._lock = threading.Lock()
        self._events: List[dict] = []
        self._max_events = max_events
        self._load()

    # ── 记录事件 ──

    def log(self, category: str, name: str, severity: str = "info",
            message: str = "", metadata: dict = None) -> dict:
        """记录一个系统事件"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "name": name,
            "severity": severity,
            "message": message,
            "metadata": metadata or {},
        }
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events // 2:]
        self._save(event)

        if severity in ("error", "critical"):
            logger.warning("🔥 [%s] %s: %s", severity.upper(), name, message)
        return event

    # ── 便捷记录 ──

    def info(self, category: str, name: str, message: str, **kw):
        return self.log(category, name, "info", message, kw or None)

    def ok(self, category: str, name: str, message: str, **kw):
        return self.log(category, name, "success", message, kw or None)

    def warn(self, category: str, name: str, message: str, **kw):
        return self.log(category, name, "warning", message, kw or None)

    def err(self, category: str, name: str, message: str, **kw):
        return self.log(category, name, "error", message, kw or None)

    def critical(self, category: str, name: str, message: str, **kw):
        return self.log(category, name, "critical", message, kw or None)

    # ── 查询 ──

    def events(self, limit: int = 50, category: str = "",
               severity: str = "", since_minutes: int = 0) -> List[dict]:
        """获取事件列表"""
        with self._lock:
            events = list(self._events)

        # 过滤
        if category:
            events = [e for e in events if e["category"] == category]
        if severity:
            events = [e for e in events if e["severity"] == severity]
        if since_minutes > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
            events = [e for e in events if self._parse_ts(e["timestamp"]) >= cutoff]

        events.reverse()
        return events[:limit]

    def last_hour(self) -> List[dict]:
        """最近1小时事件"""
        return self.events(limit=100, since_minutes=60)

    def last_error(self) -> Optional[dict]:
        """最近一次错误"""
        errors = self.events(limit=1, severity="error")
        return errors[0] if errors else None

    def last_critical(self) -> Optional[dict]:
        """最近一次严重错误"""
        crits = self.events(limit=1, severity="critical")
        return crits[0] if crits else None

    def summary(self, since_minutes: int = 60) -> dict:
        """系统概览摘要"""
        recent = self.events(limit=1000, since_minutes=since_minutes)

        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        by_hour = defaultdict(int)

        for e in recent:
            by_category[e["category"]] += 1
            by_severity[e["severity"]] += 1
            ts = e["timestamp"][:13] if len(e["timestamp"]) > 13 else "?"
            by_hour[ts] += 1

        return {
            "period_minutes": since_minutes,
            "total_events": len(recent),
            "by_severity": dict(by_severity),
            "by_category": dict(by_category),
            "errors": [e for e in recent[-20:] if e["severity"] in ("error", "critical")],
            "last_event": recent[-1] if recent else None,
        }

    # ── 持续监控检查 ──

    def check_system(self, cpu: float = None, memory_pct: float = None,
                     disk_pct: float = None, deerflow_ok: bool = None) -> List[dict]:
        """系统健康检查（生成事件）"""
        alerts = []

        if cpu is not None and cpu > 80:
            a = self.warn("system", "cpu_high", f"CPU负载过高: {cpu}%",
                          cpu=cpu, threshold=80)
            alerts.append(a)

        if memory_pct is not None and memory_pct > 85:
            a = self.warn("system", "memory_high", f"内存使用过高: {memory_pct}%",
                          memory_pct=memory_pct, threshold=85)
            alerts.append(a)

        if disk_pct is not None and disk_pct > 90:
            a = self.critical("system", "disk_full", f"磁盘将满: {disk_pct}%",
                              disk_pct=disk_pct, threshold=90)
            alerts.append(a)

        if deerflow_ok is not None and not deerflow_ok:
            a = self.err("deerflow", "deerflow_down", "DeerFlow服务不可用")
            alerts.append(a)

        return alerts

    def check_cron(self, cron_statuses: Dict[str, str]) -> List[dict]:
        """检查cron任务状态"""
        alerts = []
        for name, status in cron_statuses.items():
            if status in ("error", "skipped"):
                a = self.warn("cron", name, f"Cron任务状态: {status}")
                alerts.append(a)
        return alerts

    # ── 持久化 ──

    def _save(self, event: dict):
        try:
            with open(EVENTS_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("保存事件失败: %s", e)

    def _load(self):
        """加载历史事件（仅最近12h）"""
        if not os.path.exists(EVENTS_PATH):
            return
        cutoff = datetime.now(timezone.utc) - timedelta(hours=12)
        try:
            with open(EVENTS_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            ts = self._parse_ts(event.get("timestamp", ""))
                            if ts >= cutoff:
                                with self._lock:
                                    self._events.append(event)
                        except (json.JSONDecodeError, KeyError):
                            pass
            with self._lock:
                if len(self._events) > self._max_events:
                    self._events = self._events[-self._max_events:]
            logger.info("👁️ 已加载 %d 条事件", len(self._events))
        except Exception as e:
            logger.warning("加载事件失败: %s", e)

    @staticmethod
    def _parse_ts(ts: str) -> datetime:
        try:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)

    def stats(self) -> dict:
        with self._lock:
            return {
                "total_events": len(self._events),
                "categories": list(set(e["category"] for e in self._events)),
                "severities": list(set(e["severity"] for e in self._events)),
            }


watcher = Watcher()


def _test():
    print("=== 监控系统测试 ===")
    
    watcher.info("system", "startup", "系统启动")
    watcher.ok("cron", "cron-morning-plan", "执行成功", duration_s=23)
    watcher.warn("cron", "cron-booster-matrix", "执行超时", duration_s=120, timeout=60)
    watcher.err("video", "video_pipeline", "简创API超时", timeout=5)
    watcher.ok("partner", "booster-keepalive", "保活成功")
    watcher.info("system", "check", "CPU 2.11, 内存正常, 磁盘2%")

    print(f"✅ 已记录6条事件")

    summary = watcher.summary(since_minutes=1440)
    print(f"\n📊 摘要 (24h):")
    print(f"  总事件: {summary['total_events']}")
    print(f"  按级别: {dict(summary['by_severity'])}")
    for cat, cnt in summary.get("by_category", {}).items():
        print(f"  {cat}: {cnt}")

    events = watcher.events(limit=5)
    print(f"\n📋 最近5条:")
    for e in events:
        emoji = SEVERITY_EMOJI.get(e["severity"], "❓")
        print(f"  {emoji} [{e['timestamp'][:19]}] {e['name']:30s} {e['message'][:30]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
