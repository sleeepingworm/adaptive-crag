"""Code Write 节点：根据分析方案编写执行代码。"""

from .common import node_handler


@node_handler("code_write", "正在生成分析代码...")
def code_write_node(state: dict) -> dict:
    """根据分析方案生成代码"""
    code_plan = state.get("code_plan", "")
    chunks = state.get("retrieved_chunks", [])

    if code_plan:
        code = _build_analysis_code(code_plan, chunks)
    else:
        code = "# 无需数据分析\nprint('分析完成，无需额外代码执行')"

    return {"code": code}


def _build_analysis_code(code_plan: str, chunks: list[dict]) -> str:
    """基于 code_plan 和检索到的证据构建分析代码。

    两步走：
    1. 如果 chunks 有文档证据 → 嵌入文本内容 → 生成文本分析代码
    2. 同时检查工作目录下的 CSV/XLSX 数据文件 → 生成数据分析代码
    """
    # ---- 提取 chunks 文本 ----
    import json as _json_mod
    chunk_texts = []
    for c in (chunks or [])[:30]:
        if hasattr(c, 'text'):
            text = c.text
            source = getattr(c, 'doc_id', getattr(c, 'source', 'unknown'))
        elif isinstance(c, dict):
            text = c.get('text', '')
            source = c.get('source', c.get('file', c.get('doc_id', 'unknown')))
        else:
            text = str(c)
            source = 'unknown'
        if text and text.strip():
            chunk_texts.append({
                'text': text[:500],
                'source': str(source),
            })

    imports = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import json
from collections import Counter, defaultdict

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

output_dir = os.environ.get('CRAG_OUTPUT_DIR', '.')
"""

    code = imports + "\n"
    code += f"# 分析任务: {code_plan[:200] if code_plan else '基于检索证据开展分析'}\n"

    # ---- 步骤 1：文本证据分析 ----
    if chunk_texts:
        chunks_json = _json_mod.dumps(chunk_texts, ensure_ascii=False)
        code += f"""
# ========== 文本证据分析 ==========
evidence_chunks = json.loads({chunks_json!r})

print(f"已加载 {{len(evidence_chunks)}} 条文献证据")
for i, chunk in enumerate(evidence_chunks, 1):
    source_label = chunk['source'][:40]
    print(f"[证据 {{i}}] 来源: {{source_label}} | 长度: {{len(chunk['text'])}} 字符")

# 合并全部文本做关键词分析
all_text = '\\n'.join(c['text'] for c in evidence_chunks)

# 基本统计
total_chars = len(all_text)
total_words = len(re.findall(r'[\\u4e00-\\u9fff]|[a-zA-Z]+', all_text))

print(f"\\n--- 文本统计 ---")
print(f"证据条数: {{len(evidence_chunks)}}")
print(f"总字符数: {{total_chars}}")
print(f"有效词数: {{total_words}}")

# 高频关键词（中英文分别处理）
chinese_chars = re.findall(r'[\\u4e00-\\u9fff]{{2,}}', all_text)
english_words = re.findall(r'[a-zA-Z]{{3,}}', all_text.lower())
all_tokens = chinese_chars + english_words

token_freq = Counter(all_tokens)
stopwords = {{'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was',
             'were', 'have', 'has', 'had', 'not', 'but', 'all', 'can', 'which',
             '进行', '一个', '可以', '我们', '他们', '这个', '那个', '没有', '不会'}}
filtered = [(t, c) for t, c in token_freq.most_common(50) if t.lower() not in stopwords][:20]

print(f"\\n--- 高频词汇 (Top 20) ---")
for word, count in filtered:
    print(f"  {{word}}: {{count}}")

# 按来源统计
source_stats = defaultdict(int)
for c in evidence_chunks:
    source_stats[c['source']] += 1
print(f"\\n--- 来源分布 ---")
for src, cnt in source_stats.items():
    print(f"  {{src[:50]}}: {{cnt}} 条证据")

# 保存文本分析结果
text_analysis = {{
    'total_chunks': len(evidence_chunks),
    'total_chars': total_chars,
    'total_words': total_words,
    'top_keywords': [{{'word': w, 'count': c}} for w, c in filtered],
    'source_distribution': dict(source_stats),
}}
with open(os.path.join(output_dir, 'text_analysis.json'), 'w', encoding='utf-8') as f:
    json.dump(text_analysis, f, ensure_ascii=False, indent=2)
print("\\n文本分析结果 → text_analysis.json")
"""
    else:
        code += """
print("未加载到文本证据，跳过文本分析")
"""

    # ---- 步骤 2：数据文件分析 ----
    code += """
# ========== 数据文件分析 ==========
data_files = [f for f in os.listdir('.') if f.endswith(('.csv', '.xlsx', '.xls'))]
if data_files:
    print(f"\\n找到 {{len(data_files)}} 个数据文件")
    for fname in data_files:
        try:
            if fname.endswith('.csv'):
                df = pd.read_csv(fname)
            else:
                df = pd.read_excel(fname)
            print(f"\\n文件: {{fname}} | 形状: {{df.shape}}")
            print(f"列名: {{list(df.columns)}}")
            print(df.describe())

            # 保存数据摘要
            summary = df.describe(include='all').to_json(force_ascii=False)
            base = os.path.splitext(fname)[0]
            with open(os.path.join(output_dir, f'{{base}}_summary.json'), 'w', encoding='utf-8') as f:
                f.write(summary)

            # 生成图表
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:4]
            if len(numeric_cols) > 0:
                fig, axes = plt.subplots(1, min(len(numeric_cols), 4), figsize=(15, 4))
                if len(numeric_cols) == 1:
                    axes = [axes]
                for ax, col in zip(axes, numeric_cols):
                    df[col].dropna().hist(ax=ax, bins=20)
                    ax.set_title(col)
                plt.tight_layout()
                chart_path = os.path.join(output_dir, f'{{base}}_histograms.png')
                plt.savefig(chart_path, dpi=150)
                print(f"  图表 → {{os.path.basename(chart_path)}}")
                plt.close()
        except Exception as e:
            print(f"处理 {{fname}} 失败: {{e}}")
else:
    print("未找到数据文件，跳过数据分析")

print("\\n===== 分析代码执行完毕 =====")
"""
    return code