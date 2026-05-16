#!/usr/bin/env python3
"""
hermes_perms.py — 权限分级系统
从 Claude Code Permission System + hermes_tools PermissionLevel 借鉴

规则:
  - 通配符: "partner_*" 匹配所有伙伴工具
  - 级别: auto / notify / confirm / escalate
  - 角色继承: 苦瓜(风控) > 普通伙伴 > 土豆(管理员)

用法:
    from hermes_perms import perms

    # 注册权限规则
    perms.rule("partner_booster", level="auto")
    perms.rule("partner_risk", level="notify")
    perms.rule("partner_video", level="confirm")

    # 检查权限
    result = perms.check("partner_video", user="lettuce")
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

logger = logging.getLogger("hermes_perms")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/permissions")
os.makedirs(DATA_DIR, exist_ok=True)


class Level(Enum):
    AUTO = "auto"         # 自动执行，不需审批
    NOTIFY = "notify"     # 执行后通知土豆
    CONFIRM = "confirm"   # 执行前需土豆确认
    ESCALATE = "escalate" # 需升级到天赐审批


# 角色等级（数值越大权限越高）
ROLE_HIERARCHY = {
    "土豆": 100,    # 管理员
    "苦瓜": 80,     # 风控官（可确认大部分操作）
    "番茄": 50,     # 选品专员
    "玉米": 50,     # 视频专员
    "生菜": 50,     # 文案专员
    "萝卜": 50,     # 配音专员
    "豌豆": 50,     # 数据专员
    "天赐": 999,    # 最高权限
}

# 伙伴 → key 映射
PARTNER_KEYS = {
    "booster": "番茄", "corn": "玉米", "lettuce": "生菜",
    "bittergourd": "苦瓜", "carrot": "萝卜", "pea": "豌豆",
}


@dataclass
class PermissionRule:
    """权限规则"""
    pattern: str          # 工具名/通配符, 如 "partner_*", "partner_booster"
    level: Level
    created_at: str = ""
    description: str = ""
    created_by: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def matches(self, tool_name: str) -> bool:
        """检查工具名是否匹配此规则"""
        if self.pattern == "*":
            return True
        if self.pattern == tool_name:
            return True
        # 通配符匹配: partner_* → 匹配 partner_booster, partner_corn 等
        if self.pattern.endswith("*"):
            prefix = self.pattern[:-1]
            return tool_name.startswith(prefix)
        return False

    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "level": self.level.value,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


@dataclass
class AuditLog:
    """审计日志"""
    tool: str
    user: str
    action: str       # "allowed", "denied", "confirmed", "escalated"
    level: str
    reason: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "tool": self.tool,
            "user": self.user,
            "action": self.action,
            "level": self.level,
            "reason": self.reason,
            "created_at": self.created_at,
        }


class PermissionManager:
    """权限管理"""

    def __init__(self):
        self._lock = threading.Lock()
        self._rules: List[PermissionRule] = []
        self._audit_log: List[AuditLog] = []
        self._load()

    # ── 规则管理 ──

    def rule(self, pattern: str, level: str = "auto",
             description: str = "", created_by: str = "系统") -> PermissionRule:
        """注册权限规则"""
        r = PermissionRule(
            pattern=pattern,
            level=Level(level),
            description=description,
            created_by=created_by,
        )
        with self._lock:
            # 替换同pattern的旧规则
            self._rules = [x for x in self._rules if x.pattern != pattern]
            self._rules.append(r)
        self._save()
        logger.info("📜 权限规则: %s → %s", pattern, level)
        return r

    def remove_rule(self, pattern: str) -> bool:
        """删除规则"""
        with self._lock:
            before = len(self._rules)
            self._rules = [x for x in self._rules if x.pattern != pattern]
            return len(self._rules) < before

    def list_rules(self) -> List[dict]:
        """列出所有规则"""
        with self._lock:
            return [r.to_dict() for r in self._rules]

    # ── 权限检查 ──

    def check(self, tool_name: str, user: str = "",
              params: dict = None) -> dict:
        """检查用户是否有权限执行工具
        返回: {"allowed": bool, "level": str, "reason": str}
        """
        params = params or {}
        level = self._resolve_level(tool_name)

        # 管理员/天赐直接放行
        role = self._resolve_role(user)
        if role in ("土豆", "天赐"):
            self._log(tool_name, user, "allowed", level.value,
                      f"管理员角色({role}), 自动放行")
            return {"allowed": True, "level": level.value, "reason": "管理员放行"}

        # 苦瓜（风控官）可以确认大部分操作
        if level == Level.CONFIRM and role == "苦瓜":
            self._log(tool_name, user, "confirmed", level.value,
                      f"风控官确认, 允许执行")
            return {"allowed": True, "level": level.value, "reason": "风控官确认"}

        # 根据级别判断
        if level == Level.AUTO:
            self._log(tool_name, user, "allowed", "auto", "自动放行")
            return {"allowed": True, "level": "auto", "reason": "自动放行"}

        if level == Level.NOTIFY:
            self._log(tool_name, user, "allowed", "notify", "执行后通知")
            return {"allowed": True, "level": "notify", "reason": "执行后通知土豆"}

        if level == Level.CONFIRM:
            self._log(tool_name, user, "denied", "confirm",
                      "需要土豆确认")
            return {"allowed": False, "level": "confirm",
                    "reason": f"工具 '{tool_name}' 需要土豆确认"}

        if level == Level.ESCALATE:
            self._log(tool_name, user, "escalated", "escalate",
                      "已升级到天赐")
            return {"allowed": False, "level": "escalate",
                    "reason": f"工具 '{tool_name}' 需要天赐审批, 已升级"}

        # 默认放行
        return {"allowed": True, "level": "auto", "reason": "无匹配规则, 默认放行"}

    def _resolve_level(self, tool_name: str) -> Level:
        """解析工具对应的权限级别（按规则优先级）"""
        with self._lock:
            # 最具体规则优先
            exact = [r for r in self._rules if r.pattern == tool_name]
            if exact:
                return exact[0].level
            # 通配符规则
            wild = [r for r in self._rules if r.pattern.endswith("*") and r.matches(tool_name)]
            if wild:
                return wild[0].level
        return Level.AUTO

    def _resolve_role(self, user: str) -> str:
        """解析用户角色"""
        if not user:
            return ""
        # 直接匹配角色名
        if user in ROLE_HIERARCHY:
            return user
        # 通过key映射
        if user in PARTNER_KEYS:
            return PARTNER_KEYS[user]
        return user

    # ── 审计日志 ──

    def _log(self, tool: str, user: str, action: str,
             level: str, reason: str = ""):
        """记录审计日志"""
        entry = AuditLog(tool=tool, user=user, action=action,
                         level=level, reason=reason)
        with self._lock:
            self._audit_log.append(entry)
            if len(self._audit_log) > 1000:
                self._audit_log = self._audit_log[-500:]
        self._save_audit(entry)

    def audit_log(self, limit: int = 50) -> List[dict]:
        """查看审计日志"""
        with self._lock:
            logs = [a.to_dict() for a in self._audit_log]
        return logs[-limit:]

    # ── 持久化 ──

    def _save(self):
        """保存规则"""
        try:
            path = os.path.join(DATA_DIR, "rules.json")
            with self._lock:
                data = [r.to_dict() for r in self._rules]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存权限规则失败: %s", e)

    def _save_audit(self, entry: AuditLog):
        """追加审计日志"""
        try:
            path = os.path.join(DATA_DIR, "audit.jsonl")
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("保存审计日志失败: %s", e)

    def _load(self):
        """加载规则"""
        try:
            path = os.path.join(DATA_DIR, "rules.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with self._lock:
                    self._rules = [
                        PermissionRule(
                            pattern=r["pattern"],
                            level=Level(r.get("level", "auto")),
                            description=r.get("description", ""),
                            created_by=r.get("created_by", ""),
                            created_at=r.get("created_at", ""),
                        )
                        for r in data
                    ]
            # 加载审计日志
            audit_path = os.path.join(DATA_DIR, "audit.jsonl")
            if os.path.exists(audit_path):
                with open(audit_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                entry = AuditLog(
                                    tool=data["tool"],
                                    user=data.get("user", ""),
                                    action=data.get("action", ""),
                                    level=data.get("level", ""),
                                    reason=data.get("reason", ""),
                                    created_at=data.get("created_at", ""),
                                )
                                with self._lock:
                                    self._audit_log.append(entry)
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            logger.warning("加载权限数据失败: %s", e)

    def stats(self) -> dict:
        with self._lock:
            return {
                "rules": len(self._rules),
                "audit_entries": len(self._audit_log),
            }


# ── 默认规则 ──
_DEFAULT_RULES = [
    ("partner_booster", "auto", "选品工具, 自动放行"),
    ("partner_corn", "auto", "视频工具, 自动放行"),
    ("partner_lettuce", "auto", "文案工具, 自动放行"),
    ("partner_carrot", "auto", "配音工具, 自动放行"),
    ("partner_pea", "auto", "数据工具, 自动放行"),
    ("partner_risk", "notify", "风控工具, 执行后通知土豆"),
    ("partner_video", "notify", "视频生成, 执行后通知土豆"),
    ("partner_*", "auto", "其他伙伴工具, 默认自动"),
    ("deerflow_run", "notify", "全链路工作流, 执行后通知"),
    ("deerflow_health", "auto", "健康检查, 自动放行"),
    ("土豆_调度", "auto", "土豆调度, 自动放行"),
]


# ── 全局实例 ──
perms = PermissionManager()

# 注册默认规则
for pattern, level, desc in _DEFAULT_RULES:
    if not any(r.pattern == pattern for r in perms._rules):
        perms.rule(pattern, level, desc, "系统初始化")


def _test():
    # 1. 查看规则
    rules = perms.list_rules()
    print(f"✅ 权限规则: {len(rules)}条")
    for r in rules[:5]:
        print(f"  {r['pattern']:25s} → {r['level']:10s} {r['description']}")

    # 2. 检查权限
    r1 = perms.check("partner_booster", user="booster")
    print(f"✅ booster使用booster: allowed={r1['allowed']} ({r1['level']})")

    r2 = perms.check("partner_risk", user="booster")
    print(f"✅ booster使用risk:   allowed={r2['allowed']} ({r2['level']})")

    r3 = perms.check("partner_risk", user="bittergourd")
    print(f"✅ 苦瓜使用risk:   allowed={r3['allowed']} ({r3['level']})")

    # 3. 审计日志
    logs = perms.audit_log(3)
    print(f"✅ 审计日志: {len(perms.audit_log(999))}条")
    for l in logs[-3:]:
        print(f"  [{l['action']:>8}] {l['user']}: {l['tool']} ({l['level']})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
