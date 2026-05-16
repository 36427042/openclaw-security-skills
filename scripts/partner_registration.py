#!/usr/bin/env python3
"""
📋 Partner Registration — 6伙伴节点注册到EvoMap/DeerFlow

核心功能：
1. 节点注册：6伙伴的名称、脚本路径、能力描述、注册时间戳
2. 心跳检查：每个伙伴的健康状态监控
3. 状态报告：生成节点注册状态报告

依赖：
- gep_engine.py（GEPNode、GEPEngine用于记录注册和心跳）
- hermes_engine.py（PARTNER_CONFIGS伙伴配置）

用法：
  python3 partner_registration.py register    # 注册所有伙伴节点
  python3 partner_registration.py status      # 查看节点状态
  python3 partner_registration.py heartbeat   # 检查所有伙伴心跳
  python3 partner_registration.py report      # 生成完整注册报告
"""

import json, os, sys, time, subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ========== 路径 ==========
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
SCRIPTS_DIR = os.path.join(WORKSPACE, "scripts")
DATA_DIR = os.path.join(WORKSPACE, "data", "evolution")
PARTNER_REG_FILE = os.path.join(DATA_DIR, "partner_registry.json")
OUTPUT_DIR = os.path.join(WORKSPACE, "agents", "tomato-agent", "output")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== 导入GEP引擎 ==========
sys.path.insert(0, SCRIPTS_DIR)
try:
    from gep_engine import GEP, GEPEngine, GEPNode, GEPRegistry, ALL_PARTNERS
    GEP_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ GEP导入失败: {e}")
    GEP_AVAILABLE = False
    ALL_PARTNERS = ["土豆", "番茄", "生菜", "玉米", "萝卜", "苦瓜", "豌豆"]

# ========== 伙伴配置（来自Hermes） ==========
# 与 hermes_engine.py 的 PARTNER_CONFIGS 保持一致
PARTNER_CONFIGS = {
    "土豆": {
        "key": "hermes",
        "name_cn": "🥔 土豆·调度",
        "script": "hermes_engine.py",
        "timeout": 600,
        "capabilities": ["任务分解", "伙伴调度", "工作流编排", "系统监控"],
        "description": "EvoMap/DeerFlow调度中枢，负责任务分解和6伙伴的协调调度",
        "dependents": ["番茄", "生菜", "玉米", "萝卜", "苦瓜", "豌豆"],
    },
    "番茄": {
        "key": "booster",
        "name_cn": "🍅 番茄·选品",
        "script": "booster_matrix.py",
        "timeout": 600,
        "capabilities": ["TikTok选品", "定价分析", "爆单矩阵", "市场调研"],
        "description": "TikTok东南亚美妆工具选品，生成定价报告和市场分析",
        "dependents": [],
    },
    "生菜": {
        "key": "copy",
        "name_cn": "🥬 生菜·文案",
        "script": "copy_engine.py",
        "timeout": 120,
        "capabilities": ["文案生成", "多语言翻译", "货品描述", "话术优化"],
        "description": "生成多语言商品文案和营销话术，支持东南亚多语种",
        "dependents": [],
    },
    "玉米": {
        "key": "video",
        "name_cn": "🌽 玉米·视频",
        "script": "video_mix_6country.py",
        "timeout": 600,
        "capabilities": ["视频混剪", "视频生成", "素材处理"],
        "description": "视频素材混剪与生成，支持6国家版本的批量制作",
        "dependents": ["生菜"],
    },
    "萝卜": {
        "key": "tts",
        "name_cn": "🥕 萝卜·配音",
        "script": "qwen_tts_engine.py",
        "timeout": 120,
        "capabilities": ["TTS配音", "多语言语音", "Edge-TTS"],
        "description": "多语言TTS配音，支持东南亚各国语言语音合成",
        "dependents": [],
    },
    "苦瓜": {
        "key": "risk",
        "name_cn": "🥒 苦瓜·风控",
        "script": "risk_controller.py",
        "timeout": 120,
        "capabilities": ["内容审核", "合规检查", "违禁词检测", "安全风控"],
        "description": "内容风控和安全审核，检测违禁词和不合规内容",
        "dependents": [],
    },
    "豌豆": {
        "key": "data",
        "name_cn": "🫘 豌豆·数据",
        "script": "data_monitor.py",
        "timeout": 120,
        "capabilities": ["数据监控", "报表生成", "异常检测", "预警通知"],
        "description": "数据监控和报表生成，跟踪各伙伴的产出和异常情况",
        "dependents": [],
    },
}

# 伙伴间依赖关系（用于DAG执行顺序）
DEPENDENCY_GRAPH = {
    "土豆": [],         # 调度中枢，无依赖
    "番茄": [],         # 选品独立
    "生菜": ["番茄"],   # 文案依赖选品结果
    "玉米": ["生菜"],   # 视频依赖文案
    "萝卜": [],         # 配音独立
    "苦瓜": [],         # 风控独立
    "豌豆": ["番茄", "生菜", "玉米", "萝卜", "苦瓜"],  # 数据监控依赖所有产出
}


# ====================================================================
# PartnerNode — 伙伴节点注册信息
# ====================================================================

class PartnerNode:
    """一个伙伴节点的完整注册信息"""

    def __init__(self, partner_name: str, config: dict):
        self.name = partner_name
        self.config = config
        self.node_id = self._gen_node_id()
        self.registrations = []     # 注册历史 [(timestamp, status)]
        self.heartbeats = []        # 心跳历史 [(timestamp, status, detail)]
        self.last_health = None     # 最近健康状态

    def _gen_node_id(self) -> str:
        import hashlib
        raw = f"partner:{self.name}:{self.config['script']}"
        return f"node_{hashlib.md5(raw.encode()).hexdigest()[:12]}"

    def register(self) -> dict:
        """注册一个伙伴节点"""
        reg = {
            "timestamp": datetime.now().isoformat(),
            "status": "registered",
            "script_path": os.path.join(SCRIPTS_DIR, self.config["script"]),
            "script_exists": os.path.exists(os.path.join(SCRIPTS_DIR, self.config["script"])),
        }
        self.registrations.append(reg)

        # 用GEP记录注册事件
        if GEP_AVAILABLE:
            try:
                gep = GEP(self.name)
                gep.post_record(
                    task="节点注册",
                    context={
                        "node_id": self.node_id,
                        "script": self.config["script"],
                        "capabilities": self.config["capabilities"],
                    },
                    outcome="success" if reg["script_exists"] else "warning",
                    problem="脚本文件不存在" if not reg["script_exists"] else "",
                    note=f"伙伴节点注册: {self.config['name_cn']}",
                )
            except Exception as e:
                reg["gep_error"] = str(e)

        return reg

    def do_heartbeat(self) -> dict:
        """执行一次心跳检查"""
        script_path = os.path.join(SCRIPTS_DIR, self.config["script"])
        detail = {
            "script_exists": os.path.exists(script_path),
            "script_mtime": None,
        }

        if detail["script_exists"]:
            mtime = os.path.getmtime(script_path)
            detail["script_mtime"] = datetime.fromtimestamp(mtime).isoformat()

        hb = {
            "timestamp": datetime.now().isoformat(),
            "status": "alive",
            "detail": detail,
        }

        self.heartbeats.append(hb)
        self.last_health = hb

        # 用GEP记录心跳
        if GEP_AVAILABLE:
            try:
                gep = GEP(self.name)
                gep.post_record(
                    task="保活检查",
                    context={"status": "ok" if detail["script_exists"] else "missing"},
                    outcome="success" if detail["script_exists"] else "warning",
                    note=f"心跳检查: {detail}",
                )
            except Exception:
                pass

        return hb

    def get_status(self) -> dict:
        """获取节点当前状态摘要"""
        script_path = os.path.join(SCRIPTS_DIR, self.config["script"])
        return {
            "node_id": self.node_id,
            "name": self.name,
            "name_cn": self.config["name_cn"],
            "script": self.config["script"],
            "script_exists": os.path.exists(script_path),
            "registered": len(self.registrations) > 0,
            "registration_count": len(self.registrations),
            "heartbeat_count": len(self.heartbeats),
            "last_heartbeat": self.heartbeats[-1]["timestamp"] if self.heartbeats else None,
            "last_heartbeat_status": self.heartbeats[-1]["status"] if self.heartbeats else "unknown",
            "capabilities": self.config["capabilities"],
            "dependents": self.config["dependents"],
        }

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "config": self.config,
            "registrations": self.registrations,
            "heartbeats": self.heartbeats,
            "last_health": self.last_health,
        }


# ====================================================================
# PartnerRegistry — 伙伴注册中心
# ====================================================================

class PartnerRegistry:
    """管理所有伙伴节点的注册、心跳、状态"""

    def __init__(self):
        self.nodes: Dict[str, PartnerNode] = {}
        self._load()
        self._init_all_nodes()

    def _init_all_nodes(self):
        """确保所有伙伴都有节点对象"""
        for name, config in PARTNER_CONFIGS.items():
            if name not in self.nodes:
                self.nodes[name] = PartnerNode(name, config)

    def _load(self):
        """从持久化文件加载"""
        if os.path.exists(PARTNER_REG_FILE):
            try:
                with open(PARTNER_REG_FILE) as f:
                    data = json.load(f)
                    for name, node_data in data.items():
                        node = PartnerNode(name, PARTNER_CONFIGS.get(name, {}))
                        node.node_id = node_data.get("node_id", node.node_id)
                        node.registrations = node_data.get("registrations", [])
                        node.heartbeats = node_data.get("heartbeats", [])
                        node.last_health = node_data.get("last_health")
                        self.nodes[name] = node
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ 加载持久化数据失败: {e}")

    def _save(self):
        """持久化到文件"""
        data = {name: node.to_dict() for name, node in self.nodes.items()}
        with open(PARTNER_REG_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_all(self) -> List[dict]:
        """注册所有伙伴节点"""
        results = []
        for name in PARTNER_CONFIGS:
            if name not in self.nodes:
                self.nodes[name] = PartnerNode(name, PARTNER_CONFIGS[name])
            result = self.nodes[name].register()
            results.append({"name": name, "name_cn": self.nodes[name].config["name_cn"], **result})
            print(f"  ✅ {self.nodes[name].config['name_cn']} 注册成功 (node_id={self.nodes[name].node_id})")
        self._save()
        return results

    def register_partner(self, name: str) -> Optional[dict]:
        """注册单个伙伴"""
        if name not in PARTNER_CONFIGS:
            print(f"❌ 未知伙伴: {name}")
            return None
        if name not in self.nodes:
            self.nodes[name] = PartnerNode(name, PARTNER_CONFIGS[name])
        result = self.nodes[name].register()
        self._save()
        return result

    def heartbeat_all(self) -> List[dict]:
        """对所有伙伴执行一次心跳检查"""
        results = []
        for name in PARTNER_CONFIGS:
            if name not in self.nodes:
                self.nodes[name] = PartnerNode(name, PARTNER_CONFIGS[name])
            hb = self.nodes[name].do_heartbeat()
            results.append({"name": name, "name_cn": self.nodes[name].config["name_cn"], **hb})
        self._save()
        return results

    def heartbeat_partner(self, name: str) -> Optional[dict]:
        """对单个伙伴执行心跳"""
        if name not in PARTNER_CONFIGS:
            print(f"❌ 未知伙伴: {name}")
            return None
        if name not in self.nodes:
            self.nodes[name] = PartnerNode(name, PARTNER_CONFIGS[name])
        hb = self.nodes[name].do_heartbeat()
        self._save()
        return hb

    def get_status_all(self) -> dict:
        """获取所有伙伴的状态"""
        statuses = {}
        health_summary = {"alive": 0, "missing_script": 0, "unregistered": 0}

        for name in PARTNER_CONFIGS:
            node = self.nodes.get(name)
            if node:
                s = node.get_status()
                if not s["script_exists"]:
                    health_summary["missing_script"] += 1
                elif s["last_heartbeat_status"] == "alive":
                    health_summary["alive"] += 1
                else:
                    health_summary["unregistered"] += 1
                statuses[name] = s
            else:
                health_summary["unregistered"] += 1
                statuses[name] = {
                    "name": name,
                    "name_cn": PARTNER_CONFIGS[name]["name_cn"],
                    "status": "unregistered"
                }

        return {
            "timestamp": datetime.now().isoformat(),
            "health_summary": health_summary,
            "partners": statuses,
        }

    def get_stats(self) -> dict:
        """获取注册统计"""
        total_nodes = len(self.nodes)
        total_hbs = sum(len(n.heartbeats) for n in self.nodes.values())
        total_regs = sum(len(n.registrations) for n in self.nodes.values())
        return {
            "total_nodes": total_nodes,
            "total_registrations": total_regs,
            "total_heartbeats": total_hbs,
            "last_updated": datetime.now().isoformat(),
        }


# ====================================================================
# Report Generation
# ====================================================================

def generate_registration_report(registry: PartnerRegistry) -> str:
    """生成节点注册报告（Markdown）"""
    status_data = registry.get_status_all()
    stats = registry.get_stats()

    lines = [
        "# 📋 6伙伴节点注册报告",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 📊 注册概览",
        f"- **总节点数**：{stats['total_nodes']}",
        f"- **总注册次数**：{stats['total_registrations']}",
        f"- **总心跳次数**：{stats['total_heartbeats']}",
        f"- **健康状态**：{status_data['health_summary']['alive']} 活跃 | {status_data['health_summary']['missing_script']} 脚本缺失 | {status_data['health_summary']['unregistered']} 未注册",
        "",
        "## 🧩 伙伴节点明细",
        "",
        "| 伙伴 | 节点ID | 脚本 | 脚本存在 | 注册数 | 心跳数 | 最近心跳 | 能力 |",
        "|------|--------|------|----------|--------|--------|----------|------|",
    ]

    for name, status in status_data["partners"].items():
        if "node_id" not in status:
            lines.append(f"| {status['name_cn']} | — | — | — | 0 | 0 | — | — |")
            continue

        caps_short = ", ".join(status["capabilities"][:2])
        if len(status["capabilities"]) > 2:
            caps_short += "…"
        last_hb = status.get("last_heartbeat", "—")
        if last_hb and last_hb != "—":
            last_hb = last_hb[11:19]  # 只保留时间部分

        lines.append(
            f"| {status['name_cn']} "
            f"| `{status['node_id']}` "
            f"| {status['script']} "
            f"| {'✅' if status['script_exists'] else '❌'} "
            f"| {status['registration_count']} "
            f"| {status['heartbeat_count']} "
            f"| {last_hb} "
            f"| {caps_short} |"
        )

    lines.extend([
        "",
        "## 🔗 依赖关系",
        "",
        "```mermaid",
        "graph TD",
        "    subgraph EvoMap节点注册",
    ])

    for name in PARTNER_CONFIGS:
        status = status_data["partners"].get(name, {})
        node_id = status.get("node_id", "unregistered")
        lines.append(f"        {name}[{PARTNER_CONFIGS[name]['name_cn']}] --- |node_id: {node_id}|")

    lines.extend([
        "    end",
        "",
        "    subgraph 依赖关系",
    ])

    for parent, deps in DEPENDENCY_GRAPH.items():
        for dep in deps:
            lines.append(f"        {dep} --> {parent}")

    lines.extend([
        "    end",
        "```",
        "",
        "## 📋 伙伴能力矩阵",
        "",
        "| 伙伴 | 核心能力 | 依赖 | 下游依赖 |",
        "|------|----------|------|----------|",
    ])

    for name, config in PARTNER_CONFIGS.items():
        status = status_data["partners"].get(name, {})
        caps = ", ".join(config["capabilities"])
        deps = ", ".join(DEPENDENCY_GRAPH.get(name, [])) or "—"
        dep_of = ", ".join(config.get("dependents", [])) or "—"
        lines.append(f"| {config['name_cn']} | {caps} | {deps} | {dep_of} |")

    lines.extend([
        "",
        "## 🔄 注册流程",
        "",
        "```",
        "python3 partner_registration.py register   # 注册所有伙伴节点",
        "python3 partner_registration.py status     # 查看当前状态",
        "python3 partner_registration.py heartbeat  # 执行心跳检查",
        "python3 partner_registration.py report     # 生成完整报告",
        "```",
        "",
        "### 与EvoMap集成",
        "",
        "注册数据存储路径：`data/evolution/partner_registry.json`",
        "GEP进化数据路径：`data/evolution/registry.jsonl`",
        "EvoMap心跳保活：`scripts/evomap_heartbeat.py`（云端心跳，独立运行）",
        "",
        "### 下一步",
        "",
        "1. 确认EvoMap质押后就绪 → 将伙伴节点同步到云端",
        "2. 将 `partner_registration.py heartbeat` 集成到保活cron",
        "3. 建立伙伴健康告警：心跳丢失30分钟自动通知",
    ])

    return "\n".join(lines)


# ====================================================================
# CLI 入口
# ====================================================================

def main():
    if len(sys.argv) < 2:
        print("📋 Partner Registration — 6伙伴节点注册系统")
        print("")
        print("用法：")
        print("  python3 partner_registration.py register    # 注册所有伙伴节点")
        print("  python3 partner_registration.py status      # 查看节点状态")
        print("  python3 partner_registration.py heartbeat   # 检查所有伙伴心跳")
        print("  python3 partner_registration.py report      # 生成完整注册报告")
        print("")
        print("单伙伴操作：")
        print("  python3 partner_registration.py register <名字>")
        print("  python3 partner_registration.py heartbeat <名字>")
        return

    cmd = sys.argv[1]
    registry = PartnerRegistry()

    if cmd == "register":
        if len(sys.argv) > 2:
            name = sys.argv[2]
            result = registry.register_partner(name)
            if result:
                print(f"✅ {PARTNER_CONFIGS[name]['name_cn']} 注册成功")
        else:
            print(f"📋 注册 {len(PARTNER_CONFIGS)} 个伙伴节点...")
            results = registry.register_all()
            print(f"✅ 全部注册完成")

    elif cmd == "status":
        status_data = registry.get_status_all()
        print(f"📊 伙伴节点状态 ({status_data['timestamp'][:19]})")
        print(f"  健康概览：{status_data['health_summary']}")
        print()
        for name, status in status_data["partners"].items():
            if "node_id" not in status:
                print(f"  {'—':>6} {PARTNER_CONFIGS[name]['name_cn']} → ❌ 未注册")
                continue
            icon = "✅" if status.get("last_heartbeat_status") == "alive" else "⚠️"
            missing = " ❌脚本缺失" if not status.get("script_exists") else ""
            last_hb = status.get("last_heartbeat", "—")[:19] if status.get("last_heartbeat") else "—"
            print(f"  {icon} {status['name_cn']} → {status['node_id']}{missing}")
            print(f"      脚本: {status['script']} | 心跳: {last_hb} | 心跳数: {status['heartbeat_count']}")

    elif cmd == "heartbeat":
        if len(sys.argv) > 2:
            name = sys.argv[2]
            hb = registry.heartbeat_partner(name)
            if hb:
                print(f"❤️ {PARTNER_CONFIGS[name]['name_cn']} 心跳正常: {hb['status']}")
        else:
            print(f"❤️ 执行 {len(PARTNER_CONFIGS)} 个伙伴的心跳检查...")
            results = registry.heartbeat_all()
            alive = sum(1 for r in results if r["status"] == "alive")
            print(f"✅ {alive}/{len(results)} 伙伴存活")

    elif cmd == "report":
        report = generate_registration_report(registry)
        report_path = os.path.join(OUTPUT_DIR, "partner_registration_report.md")
        with open(report_path, "w") as f:
            f.write(report)
        print(f"📋 报告已生成: {report_path}")

        # 同时用GEP记录报告生成
        if GEP_AVAILABLE:
            try:
                gep = GEP("土豆")
                gep.post_record(
                    task="生成注册报告",
                    context={"partners": list(PARTNER_CONFIGS.keys())},
                    outcome="success",
                    note=f"注册报告已生成: partner_registration_report.md",
                )
            except Exception:
                pass

    else:
        print(f"❌ 未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
