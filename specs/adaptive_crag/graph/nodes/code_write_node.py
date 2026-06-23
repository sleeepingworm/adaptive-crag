"""
Code Write 节点：根据分析方案编写执行代码。
实际上此处由 LLM 生成代码，但考虑到分析阶段已有 code_plan，
这里可以调用 LLM 生成具体代码，或者使用模板。
"""

from datetime import datetime


def code_write_node(state: dict) -> dict:
    """根据分析方案生成代码"""
    _emit_event(state, "code_write", "running", "正在生成分析代码...")

    code_plan = state.get("code_plan", "")
    query = state.get("query", "")
    chunks = state.get("retrieved_chunks", [])

    # 简化实现：从 code_plan 或默认模板生成代码
    if code_plan:
        # 理想情况应调 LLM 生成，这里构建默认分析模板
        code = _build_analysis_code(code_plan, chunks)
    else:
        code = "# 无需数据分析\nprint('分析完成，无需额外代码执行')"

    return {
        "code": code,
        "current_step": "code_write",
    }


def _build_analysis_code(code_plan: str, chunks: list[dict]) -> str:
    """基于 code_plan 构建基础分析代码（模板）"""
    imports = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.environ.get('CRAG_OUTPUT_DIR', '.')
"""

    code = imports + "\n"
    code += f"# 分析任务: {code_plan[:200]}\n"
    code += """
# ========== 数据分析开始 ==========

# 检查是否有 CSV 数据文件
data_files = [f for f in os.listdir('.') if f.endswith('.csv')]
if data_files:
    df = pd.read_csv(data_files[0])
    print(f"数据文件: {data_files[0]}")
    print(f"数据形状: {df.shape}")
    print(f"列名: {list(df.columns)}")
    print(df.describe())
    
    # 保存数据摘要
    summary = df.describe(include='all').to_dict()
    with open(os.path.join(output_dir, 'data_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(str(summary), f, ensure_ascii=False, indent=2)
    
    # 生成基础图表
    numeric_cols = df.select_dtypes(include=[np.number]).columns[:4]
    if len(numeric_cols) > 0:
        fig, axes = plt.subplots(1, min(len(numeric_cols), 4), figsize=(15, 4))
        if len(numeric_cols) == 1:
            axes = [axes]
        for ax, col in zip(axes, numeric_cols):
            df[col].hist(ax=ax, bins=20)
            ax.set_title(col)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'histograms.png'), dpi=150)
        print(f"已生成直方图: histograms.png")
else:
    print("未找到 CSV 数据文件，跳过数据分析")

# ========== 数据分析结束 ==========
"""
    return code


def _emit_event(state: dict, step: str, status: str, message: str):
    callbacks = state.get("_callbacks", {})
    on_step = callbacks.get("on_step_change")
    if on_step:
        try:
            on_step(step, status, message, datetime.now().isoformat())
        except Exception:
            pass
