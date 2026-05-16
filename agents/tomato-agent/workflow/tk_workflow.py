"""
TK电商全链路 LangGraph 工作流

方案B: 1个 StateGraph + 7个顺序node，每个node调用对应Python脚本
版本: 1.0
创建: 2026-05-08
"""

import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, END

# ============================================================
# 配置
# ============================================================
SCRIPTS_DIR = "/Users/a1234/.openclaw/workspace/scripts"
SHOP_ID = "TH001"
COUNTRY = "TH"
CATEGORY = "美妆工具"
PRICE_MIN = 10
PRICE_MAX = 50

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tk-workflow")


# ============================================================
# State 定义
# ============================================================
class WorkflowState(TypedDict):
    """工作流状态 - 每一步的输入输出"""

    # 工作流控制
    step_index: int
    total_steps: int
    errors: List[Dict[str, Any]]
    status: str  # running | completed | failed

    # Step 1: 选品输出
    selected_products: Optional[List[Dict[str, Any]]]
    pricing_report: Optional[str]

    # Step 2: 视频输出
    video_id: Optional[str]
    video_path: Optional[str]
    video_url: Optional[str]

    # Step 3: 发布输出
    publish_result: Optional[Dict[str, Any]]
    copy_text: Optional[str]

    # Step 4: 客服输出
    csr_result: Optional[Dict[str, Any]]

    # Step 5: 风控输出
    risk_result: Optional[Dict[str, Any]]
    risk_alerts: Optional[List[str]]

    # Step 6: 数据输出
    data_report: Optional[Dict[str, Any]]

    # Step 7: 迭代输出
    evolution_result: Optional[Dict[str, Any]]

    # 参数
    shop_id: str
    category: str
    country: str
    price_min: float
    price_max: float


def create_initial_state() -> WorkflowState:
    """创建初始状态"""
    return WorkflowState(
        step_index=0,
        total_steps=7,
        errors=[],
        status="running",
        selected_products=None,
        pricing_report=None,
        video_id=None,
        video_path=None,
        video_url=None,
        publish_result=None,
        copy_text=None,
        csr_result=None,
        risk_result=None,
        risk_alerts=None,
        data_report=None,
        evolution_result=None,
        shop_id=SHOP_ID,
        category=CATEGORY,
        country=COUNTRY,
        price_min=PRICE_MIN,
        price_max=PRICE_MAX,
    )


# ============================================================
# 工具函数
# ============================================================
def _call_script(script_name: str, args: List[str] = None, input_data: str = None) -> Dict[str, Any]:
    """调用 Python 脚本并返回结果"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        return {"success": False, "error": f"脚本不存在: {script_path}"}

    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "PYTHONPATH": SCRIPTS_DIR},
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "脚本执行超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Node 函数
# ============================================================

def step_1_selection(state: WorkflowState) -> WorkflowState:
    """🍅 Step 1: 爆款选品 (booster_matrix.py)"""
    logger.info("=" * 40)
    logger.info("🍅 [Step 1/7] 爆款选品 开始...")

    result = _call_script("booster_matrix.py", [
        "--category", state["category"],
        "--country", state["country"],
        "--limit", "5",
    ])

    if result["success"]:
        logger.info("🍅 选品完成 ✅")
        state["status"] = "running"
    else:
        logger.error(f"🍅 选品失败: {result.get('error', '')}")
        state["errors"].append({
            "step": 1, "name": "爆款选品",
            "error": result.get("error", "unknown"),
            "stderr": result.get("stderr", ""),
        })

    state["step_index"] = 1
    state["pricing_report"] = result.get("stdout", "")
    return state


def step_2_video(state: WorkflowState) -> WorkflowState:
    """🌽 Step 2: 生成视频 (video_pipeline_v2.py)"""
    logger.info("=" * 40)
    logger.info("🌽 [Step 2/7] 生成视频 开始...")

    result = _call_script("video_pipeline_v2.py", [
        "--country", state["country"],
        "--product_ids", "auto",
    ])

    if result["success"]:
        logger.info("🌽 视频生成完成 ✅")
    else:
        logger.error(f"🌽 视频生成失败: {result.get('error', '')}")
        state["errors"].append({
            "step": 2, "name": "生成视频",
            "error": result.get("error", "unknown"),
            "stderr": result.get("stderr", ""),
        })

    state["step_index"] = 2
    return state


def step_3_publish(state: WorkflowState) -> WorkflowState:
    """🥬 Step 3: 文案生成+发布上架 (copy_engine.py)"""
    logger.info("=" * 40)
    logger.info("🥬 [Step 3/7] 文案发布 开始...")

    result = _call_script("copy_engine.py", [
        "--country", state["country"],
        "--shop_id", state["shop_id"],
    ])

    if result["success"]:
        logger.info("🥬 文案发布完成 ✅")
    else:
        logger.error(f"🥬 文案发布失败: {result.get('error', '')}")
        state["errors"].append({
            "step": 3, "name": "文案发布",
            "error": result.get("error", "unknown"),
            "stderr": result.get("stderr", ""),
        })

    state["step_index"] = 3
    return state


def step_4_csr(state: WorkflowState) -> WorkflowState:
    """🥬 Step 4: 自动回复客服 (hermes_engine.py)"""
    logger.info("=" * 40)
    logger.info("🥬 [Step 4/7] 客服回复 开始...")

    result = _call_script("hermes_engine.py", [
        "--shop_id", state["shop_id"],
        "--mode", "auto_reply",
    ])

    if result["success"]:
        logger.info("🥬 客服回复完成 ✅")
    else:
        logger.error(f"🥬 客服回复失败: {result.get('error', '')}")
        state["errors"].append({
            "step": 4, "name": "客服回复",
            "error": result.get("error", "unknown"),
            "stderr": result.get("stderr", ""),
        })

    state["step_index"] = 4
    return state


def step_5_risk(state: WorkflowState) -> WorkflowState:
    """🥒 Step 5: 风控巡检 (risk_controller.py)"""
    logger.info("=" * 40)
    logger.info("🥒 [Step 5/7] 风控巡检 开始...")

    result = _call_script("risk_controller.py", [
        "--shop_id", state["shop_id"],
        "--check_all",
    ])

    if result["success"]:
        logger.info("🥒 风控巡检完成 ✅")
    else:
        logger.error(f"🥒 风控巡检失败: {result.get('error', '')}")
        state["errors"].append({
            "step": 5, "name": "风控巡检",
            "error": result.get("error", "unknown"),
            "stderr": result.get("stderr", ""),
        })

    state["step_index"] = 5
    return state


def step_6_data(state: WorkflowState) -> WorkflowState:
    """🫘 Step 6: 数据分析 (data_monitor.py)"""
    logger.info("=" * 40)
    logger.info("🫘 [Step 6/7] 数据分析 开始...")

    result = _call_script("data_monitor.py", [
        "--shop_id", state["shop_id"],
        "--summary",
    ])

    if result["success"]:
        logger.info("🫘 数据分析完成 ✅")
    else:
        logger.error(f"🫘 数据分析失败: {result.get('error', '')}")
        state["errors"].append({
            "step": 6, "name": "数据分析",
            "error": result.get("error", "unknown"),
            "stderr": result.get("stderr", ""),
        })

    state["step_index"] = 6
    return state


def step_7_evolution(state: WorkflowState) -> WorkflowState:
    """🫘 Step 7: 技能迭代优化 (gep_engine.py)"""
    logger.info("=" * 40)
    logger.info("🫘 [Step 7/7] 技能迭代 开始...")

    result = _call_script("gep_engine.py", [
        "--iterate",
        "--all_skills",
    ])

    if result["success"]:
        logger.info("🫘 技能迭代完成 ✅")
        state["status"] = "completed"
    else:
        logger.error(f"🫘 技能迭代失败: {result.get('error', '')}")
        state["errors"].append({
            "step": 7, "name": "技能迭代",
            "error": result.get("error", "unknown"),
            "stderr": result.get("stderr", ""),
        })

    state["step_index"] = 7
    return state


def summarize_results(state: WorkflowState) -> WorkflowState:
    """总结工作流执行结果"""
    logger.info("=" * 40)
    total_errors = len(state["errors"])

    if total_errors == 0:
        logger.info("🎉 全链路执行完成! 7步全部通过")
        state["status"] = "completed"
    elif state["status"] == "failed":
        logger.error(f"❌ 全链路执行失败! {total_errors}个步骤出错")
    else:
        logger.warning(f"⚠️ 全链路执行完成但有 {total_errors} 个错误")
        state["status"] = "completed_with_errors"

    return state


def should_continue(state: WorkflowState) -> str:
    """检查是否继续执行"""
    if len(state["errors"]) > 3:
        state["status"] = "failed"
        return "end"
    return "continue"


# ============================================================
# 构建图
# ============================================================
def build_tk_workflow() -> StateGraph:
    """构建 TK 全链路工作流 StateGraph"""

    workflow = StateGraph(WorkflowState)

    # 注册所有节点
    workflow.add_node("step_1_selection", step_1_selection)
    workflow.add_node("step_2_video", step_2_video)
    workflow.add_node("step_3_publish", step_3_publish)
    workflow.add_node("step_4_csr", step_4_csr)
    workflow.add_node("step_5_risk", step_5_risk)
    workflow.add_node("step_6_data", step_6_data)
    workflow.add_node("step_7_evolution", step_7_evolution)
    workflow.add_node("summarize", summarize_results)

    # 设置入口
    workflow.set_entry_point("step_1_selection")

    # 顺序连接
    workflow.add_edge("step_1_selection", "step_2_video")
    workflow.add_edge("step_2_video", "step_3_publish")

    # step_4 (客服) 和 step_5 (风控) 依赖 step_3, 可以并行
    workflow.add_edge("step_3_publish", "step_4_csr")
    workflow.add_edge("step_3_publish", "step_5_risk")

    # step_6 等待 step_4 和 step_5 都完成
    workflow.add_edge("step_4_csr", "step_6_data")
    workflow.add_edge("step_5_risk", "step_6_data")

    # step_7 依赖 step_6
    workflow.add_edge("step_6_data", "step_7_evolution")
    workflow.add_edge("step_7_evolution", "summarize")

    # 结束
    workflow.add_edge("summarize", END)

    return workflow.compile()


# ============================================================
# 工厂函数 — 供 LangGraph / DeerFlow 调用
# ============================================================
def make_tk_workflow(config: dict = None):
    """创建可运行的 TK 工作流 (工厂函数)"""
    graph = build_tk_workflow()
    initial_state = create_initial_state()
    return graph, initial_state


def run_full_workflow() -> Dict[str, Any]:
    """直接运行全链路 (CLI入口)"""
    graph = build_tk_workflow()
    state = create_initial_state()
    result = graph.invoke(state)
    return result


# ============================================================
# CLI 入口
# ============================================================
if __name__ == "__main__":
    print("▶️ TK全链路工作流 启动")
    print(f"   国家: {COUNTRY}  品类: {CATEGORY}")
    print("=" * 55)

    result = run_full_workflow()

    status = result.get("status", "unknown")
    errors = result.get("errors", [])
    print("\n" + "=" * 55)
    if status == "completed":
        print("🎉 全链路执行成功! 所有7步通过")
    elif status == "completed_with_errors":
        print(f"⚠️ 执行完成, 但有 {len(errors)} 个错误:")
        for e in errors:
            print(f"   ❌ Step {e['step']} {e['name']}: {e['error']}")
    else:
        print(f"❌ 执行失败: {status}")
    print("=" * 55)
