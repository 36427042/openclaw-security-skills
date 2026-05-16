#!/usr/bin/env python3
"""
hermes_messages.py — 伙伴间通信系统
从 Claude Code SendMessageTool / TaskCreateTool 借鉴

每个伙伴有自己的收件箱，可互相发送消息、广播、组队协作

用法:
    from hermes_messages import messenger

    # 发送消息
    messenger.send(from_partner="booster", to_partner="corn",
                   subject="爆款发现", body="美白仪在泰国火了，准备视频素材")

    # 读收件箱
    messages = messenger.read("corn")

    # 标记已读
    messenger.mark_read("corn", msg_id)

    # 广播全员
    messenger.broadcast(from_partner="土豆", subject="紧急通知", body="停了停了")

    # 组队
    team = messenger.create_team("泰国专场", members=["booster", "corn", "lettuce"])
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hermes_messages")

DATA_DIR = os.path.expanduser("~/.openclaw/workspace/data/messages")
os.makedirs(DATA_DIR, exist_ok=True)

# 已知伙伴列表
PARTNER_ALIASES = {
    "booster": "🍅番茄", "corn": "🌽玉米", "lettuce": "🥬生菜",
    "bittergourd": "🥒苦瓜", "carrot": "🥕萝卜", "pea": "🫘豌豆",
    "tomato": "🥔土豆", "all": "全员",
}

# ---------------------------------------------------------------------------
#  Message
# ---------------------------------------------------------------------------

@dataclass
class Message:
    id: str
    from_partner: str
    to_partner: str
    subject: str
    body: str
    urgent: bool = False
    created_at: str = ""
    read: bool = False
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from": self.from_partner,
            "to": self.to_partner,
            "subject": self.subject,
            "body": self.body,
            "urgent": self.urgent,
            "created_at": self.created_at,
            "read": self.read,
            "metadata": self.metadata,
        }

    @property
    def summary(self) -> str:
        who = PARTNER_ALIASES.get(self.from_partner, self.from_partner)
        return f"[{'‼️' if self.urgent else '💬'}] {who}: {self.subject}"
# ---------------------------------------------------------------------------
#  Messenger
# ---------------------------------------------------------------------------

class Messenger:
    """伙伴间通信中心"""

    def __init__(self):
        self._lock = threading.Lock()
        self._teams: Dict[str, dict] = {}  # team_name -> {members, created_at}
        self._messages: Dict[str, List[Message]] = {}  # inbox -> [Message]
        self._load()

    # ── 发送消息 ──

    def send(self, from_partner: str, to_partner: str, subject: str,
             body: str = "", urgent: bool = False, metadata: dict = None) -> dict:
        """发送消息给指定伙伴"""
        msg = Message(
            id=_new_id(),
            from_partner=from_partner,
            to_partner=to_partner,
            subject=subject,
            body=body,
            urgent=urgent,
            metadata=metadata or {},
        )
        with self._lock:
            self._messages.setdefault(to_partner, []).append(msg)
        self._save(msg, to_partner)
        logger.info("💬 %s → %s: %s", from_partner, to_partner, subject)
        return msg.to_dict()

    def broadcast(self, from_partner: str, subject: str, body: str = "",
                  targets: List[str] = None, urgent: bool = False) -> List[dict]:
        """广播消息给多个伙伴或全部"""
        if targets is None:
            # 默认发给所有6伙伴
            targets = ["booster", "corn", "lettuce", "bittergourd", "carrot", "pea"]
        results = []
        for target in targets:
            results.append(self.send(from_partner, target, subject, body, urgent))
        return results

    # ── 读取收件箱 ──

    def read(self, partner: str, unread_only: bool = True,
             limit: int = 20) -> List[dict]:
        """读取指定伙伴的收件箱"""
        with self._lock:
            msgs = self._messages.get(partner, [])
            if unread_only:
                msgs = [m for m in msgs if not m.read]
            msgs = [m.to_dict() for m in msgs]
            # 按时间倒序
            msgs.sort(key=lambda m: m["created_at"], reverse=True)
        return msgs[:limit]

    def mark_read(self, partner: str, msg_id: str) -> bool:
        """标记消息为已读"""
        with self._lock:
            for m in self._messages.get(partner, []):
                if m.id == msg_id:
                    m.read = True
                    self._save(m, partner)
                    return True
        return False

    def mark_all_read(self, partner: str) -> int:
        """标记所有消息为已读"""
        count = 0
        with self._lock:
            for m in self._messages.get(partner, []):
                if not m.read:
                    m.read = True
                    self._save(m, partner)
                    count += 1
        return count

    def delete(self, partner: str, msg_id: str) -> bool:
        """删除消息"""
        with self._lock:
            msgs = self._messages.get(partner, [])
            for i, m in enumerate(msgs):
                if m.id == msg_id:
                    msgs.pop(i)
                    self._delete_file(partner, msg_id)
                    return True
        return False

    # ── 团队协作 ──

    def create_team(self, name: str, members: List[str],
                    purpose: str = "") -> dict:
        """创建协作团队"""
        team = {
            "name": name,
            "members": members,
            "purpose": purpose,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._teams[name] = team
        # 通知所有成员
        self.broadcast("土豆", f"组队邀请: {name}", f"成员: {', '.join(members)}", targets=members)
        logger.info("🤝 创建团队: %s (%s)", name, ", ".join(members))
        return team

    def team_send(self, team_name: str, from_partner: str,
                  subject: str, body: str = "") -> List[dict]:
        """向团队所有成员发消息"""
        with self._lock:
            team = self._teams.get(team_name)
        if not team:
            logger.warning("团队不存在: %s", team_name)
            return []
        targets = [m for m in team["members"] if m != from_partner]
        return self.broadcast(from_partner, subject, body, targets=targets)

    def team_list(self) -> List[dict]:
        """列出所有团队"""
        with self._lock:
            return list(self._teams.values())

    # ── 统计 ──

    def stats(self) -> dict:
        """消息统计"""
        with self._lock:
            total = sum(len(msgs) for msgs in self._messages.values())
            unread = sum(
                1 for msgs in self._messages.values()
                for m in msgs if not m.read
            )
            inbox_counts = {
                k: {"total": len(v), "unread": sum(1 for m in v if not m.read)}
                for k, v in self._messages.items()
            }
        return {
            "total_messages": total,
            "unread": unread,
            "teams": len(self._teams),
            "inboxes": inbox_counts,
        }

    # ── 持久化 ──

    def _save(self, msg: Message, inbox: str):
        """保存消息到文件"""
        try:
            dir_path = os.path.join(DATA_DIR, inbox)
            os.makedirs(dir_path, exist_ok=True)
            path = os.path.join(dir_path, f"{msg.id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(msg.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("保存消息失败: %s", e)

    def _load(self):
        """从文件加载消息"""
        if not os.path.isdir(DATA_DIR):
            return
        for inbox in os.listdir(DATA_DIR):
            inbox_path = os.path.join(DATA_DIR, inbox)
            if not os.path.isdir(inbox_path):
                continue
            for fn in os.listdir(inbox_path):
                if not fn.endswith(".json"):
                    continue
                try:
                    path = os.path.join(inbox_path, fn)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    msg = Message(
                        id=data["id"],
                        from_partner=data.get("from", ""),
                        to_partner=data.get("to", inbox),
                        subject=data.get("subject", ""),
                        body=data.get("body", ""),
                        urgent=data.get("urgent", False),
                        created_at=data.get("created_at", ""),
                        read=data.get("read", False),
                        metadata=data.get("metadata", {}),
                    )
                    with self._lock:
                        self._messages.setdefault(inbox, []).append(msg)
                except Exception as e:
                    logger.warning("加载消息失败 %s/%s: %s", inbox, fn, e)

    def _delete_file(self, inbox: str, msg_id: str):
        """删除消息文件"""
        path = os.path.join(DATA_DIR, inbox, f"{msg_id}.json")
        if os.path.exists(path):
            os.remove(path)

    def clear(self, partner: str, older_than_days: int = 7):
        """清理旧消息"""
        import time
        cutoff = time.time() - older_than_days * 86400
        count = 0
        with self._lock:
            msgs = self._messages.get(partner, [])
            remaining = []
            for m in msgs:
                if m.created_at:
                    try:
                        ts = datetime.fromisoformat(m.created_at).timestamp()
                        if ts < cutoff:
                            self._delete_file(partner, m.id)
                            count += 1
                            continue
                    except ValueError:
                        pass
                remaining.append(m)
            self._messages[partner] = remaining
        return count


# ── 工具函数 ──

import time as _time
_COUNTER = [0]

def _new_id() -> str:
    _COUNTER[0] += 1
    return f"msg_{int(_time.time()*1000)}_{_COUNTER[0]:04d}"


# ── 全局实例 ──
messenger = Messenger()


# ── 测试 ──
def _test():
    # 1. 发送消息
    m = messenger.send("booster", "corn", "泰国爆款: 美白仪",
                       "猫超同款, 客单价$12, 准备2个视频角度")
    print(f"✅ 消息已发送: {messenger.stats()['total_messages']}条")

    # 2. 收件箱
    inbox = messenger.read("corn")
    print(f"✅ 玉米收件箱: {len(inbox)}条未读")

    # 3. 标记已读
    messenger.mark_read("corn", m["id"])
    remaining = messenger.read("corn")
    print(f"✅ 标记已读后: {len(remaining)}条未读")

    # 4. 广播
    messenger.broadcast("土豆", "系统维护通知", "今晚2点上架, 1小时后开始", urgent=True)
    print(f"✅ 全员广播: 总{len(messenger.read('booster'))}条+")

    # 5. 创建团队
    messenger.create_team("泰国专场", ["booster", "corn", "lettuce"])
    print(f"✅ 团队: {messenger.team_list()}")

    print(f"\n📊 统计: {json.dumps(messenger.stats(), indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _test()
