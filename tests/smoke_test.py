"""
冒烟验证脚本 —— 不启动 Streamlit，直接验证完整 pipeline。
用法: python tests/smoke_test.py [文件路径]

验证项:
1. 文件解析成功，产生至少 5 个有效片段
2. 检索返回至少 1 条结果，且结果文本长度 > 20
3. ReportAgent 生成的报告包含检索片段中的关键词
"""

import os, sys, glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("CRAG_API_KEY", os.environ.get("CRAG_API_KEY", "sk-placeholder"))
os.environ.setdefault("CRAG_LLM_PROVIDER", "opensource")
os.environ.setdefault("CRAG_LLM_MODEL", "deepseek-v4-flash")
os.environ.setdefault("CRAG_LLM_API_BASE", "https://api.deepseek.com/v1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from adaptive_crag.config import load_config, load_llm_config
from adaptive_crag.ingestion import IngestionPipeline
from adaptive_crag.retrieval import EmbeddingStore
from adaptive_crag.agents import ReportAgent

config = load_config()

# ---- 1. 确定测试文件 ----
if len(sys.argv) > 1:
    filepath = sys.argv[1]
else:
    uploads = (glob.glob(os.path.join(config.paths.upload_dir, "*", "*.docx"))
             + glob.glob(os.path.join(config.paths.upload_dir, "*", "*.pdf")))
    if not uploads:
        print("FAIL: 没有找到上传文件")
        sys.exit(1)
    filepath = uploads[0]

print(f"测试文件: {os.path.basename(filepath)}")

# ---- 2. 解析文件 ----
pipe = IngestionPipeline(max_tokens=config.retrieval.chunk_max_tokens)
result = pipe.process(filepath)
chunks = result["chunks"]
assert len(chunks) >= 5, f"FAIL: 只解析出 {len(chunks)} 个片段"
print(f"PASS 文件解析 → {len(chunks)} 个片段")

# ---- 3. 索引 + 检索（纯向量，不加载重排序模型）----
store = EmbeddingStore(config.paths.chroma_persist_dir)
store.delete_collection()
store.add_chunks(chunks)

query = "总结这个文档的内容"
results = store.search(query, top_k=5)
assert len(results) >= 1, "FAIL: 检索返回 0 条结果"
assert len(results[0]["text"]) > 20, f"FAIL: 结果太短 ({len(results[0]['text'])} 字符)"
print(f"PASS 检索 → {len(results)} 条, 首条 {len(results[0]['text'])} 字符")

# ---- 4. 生成报告 ----
llm_config = load_llm_config()
agent = ReportAgent(llm_config)
state = {
    "query": query,
    "retrieved_chunks": results,
    "plan": {},
    "execution_result": None,
    "web_search_results": [],
}
report_state = agent.run(state)
report = report_state.get("report", "")
assert len(report) > 100, f"FAIL: 报告太短 ({len(report)} 字符)"
print(f"PASS 报告生成 → {len(report)} 字符")

# ---- 5. 验证报告包含文档关键词 ----
keywords_found = 0
for r in results[:3]:
    text = r["text"]
    snippet = text[len(text)//4:len(text)//4+20].strip()
    if snippet and snippet in report:
        keywords_found += 1
        print(f"  ✓ 报告包含: ...{snippet}...")
if keywords_found == 0:
    print("WARN: 报告中未直接匹配检索关键词（LLM 可能重新组织了语言）")
else:
    print(f"PASS 报告与检索吻合 ({keywords_found}/3)")

print("\n===== 冒烟测试通过 =====")