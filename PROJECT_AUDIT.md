# Adaptive CRAG — 项目审查报告

**审查日期**: 2026-06-19  
**审查范围**: 全项目 `adaptive_crag/`、`app/`、`tests/`、`specs/`、`main.py`、`pyproject.toml`  
**审查维度**: 安全与配置、核心逻辑与数据流、UI 与应用层、代码质量与架构

---

## 总览

| 严重性 | 数量 | 主要类别 |
|--------|------|----------|
| CRITICAL | 8 | 安全漏洞、逻辑断路、数据污染、UI 失效 |
| HIGH | 12 | 安全加固、分支逻辑、异常降级、UI 体验 |
| MEDIUM | 14 | 数据一致性、状态管理、脆性耦合 |
| LOW | 27 | 代码重复、测试缺口、性能、规范偏差 |

**测试覆盖**: 仅 1 个 `tests/test_all.py`，摄入/检索/Agents/图节点/编排层均无测试，无集成测试。
**Spec 差异**: 17 处 spec 与实现不一致。

---

## CRITICAL — 8 项（需立即修复）

### C1. main.py 硬编码 DeepSeek API Key

- **文件**: `main.py:14`
- **描述**: `os.environ.setdefault("CRAG_API_KEY", "sk-88a5914664c0473c8ddbc2bd0e04eaa5")` — 真实可用的 API Key 嵌入源码，已提交到 git。
- **影响**: 任何人克隆仓库即可使用这笔 API 额度，存在账单滥用和 Key 吊销风险。
- **修复**: 删除硬编码 Key，改用 `.env` + `python-dotenv` 加载，添加 `.env.example` 模板。

### C2. 文件上传路径穿越

- **文件**: `app/pages/upload_page.py:73`, `app/views/upload_page.py:73`
- **描述**: `save_path = os.path.join(save_dir, f.name)` — 用户上传的文件名未经过滤。文件名 `../../etc/malicious` 可穿越出上传目录。
- **影响**: 攻击者可向进程有写权限的任意路径写文件，可能覆盖配置、索引或应用数据。
- **修复**: 用 `os.path.basename(f.name)` 提取纯文件名，拒绝包含路径分隔符的文件名。

### C3. Web 搜索结果未喂入证据评估器 —— 联网搜索形同虚设

- **文件**: `adaptive_crag/graph/nodes/web_search_node.py:29-36`, `adaptive_crag/agents/grader_agent.py:16-31`
- **描述**: `web_search_node` 将结果存入 `state["web_search_results"]`，但 `GraderAgent.build_user_prompt` 只读取 `retrieved_chunks` 和 `evidence_gap`，完全忽略 `web_search_results`。第二次 `grade` 调用评估的仍是原始检索块。
- **影响**: 证据不足 → 联网搜索 → 再评估的闭环完全失效。循环仅靠 `_grade_loop_count >= 2` 硬跳出，而非靠证据充分。浪费 API 调用和延迟。
- **修复**: 在 `GraderAgent.build_user_prompt` 中将 `web_search_results` 合并到评估上下文中。

### C4. 跨任务索引污染（数据泄漏 + 内存泄漏）

- **文件**: `adaptive_crag/application/task_orchestrator.py:88-103`
- **描述**: `TaskOrchestrator._init_retriever()` 懒加载一次后复用同一个 `BM25Store` 和 `EmbeddingStore`。每次 `start_task` 直接 `add_chunks()` 追加，从不清理旧索引。`clear()` 和 `delete_collection()` 方法存在但从未被调用。
- **影响**: 任务 B 的检索结果可能混入任务 A 的文档块（跨任务数据污染）；索引无限增长导致内存泄漏。
- **修复**: 每次任务启动时调用 `clear()` 清理索引，或在每个任务中使用独立的索引实例。

### C5. 向量检索得分语义反转

- **文件**: `adaptive_crag/retrieval/embedding_store.py:130`
- **描述**: ChromaDB 配置了 `hnsw:space: cosine`，`query()` 返回的是 `distances`（即 1 - cosine_similarity，值越小越相似）。但第 130 行将 `distances` 直接赋给 `score` 字段。后续 `evidence_builder.py:38` 保留此值，`reranker.py:59` 在退化模式下按 `score` 降序排序。
- **影响**: Reranker 不可用时，向量搜索结果按距离排序——最不相似的文档排在前面。
- **修复**: 统一 score 语义，或在 `embedding_store.py` 中将 distance 转换为 `1 - distance`。

### C6. 全局可变状态竞态条件

- **文件**: `adaptive_crag/tools/hybrid_search.py:8` (`_hybrid_retriever`), `adaptive_crag/tools/citation_lookup.py:7` (`_citation_mappings`)
- **描述**: 两个模块级全局变量通过 `set_hybrid_retriever()` / `set_citation_mappings()` 设置，无锁保护。多任务并发时后一个任务会覆盖前一个的检索器和引用映射。
- **影响**: 并发场景下检索结果和引用反查混乱，一个任务可能拿到另一个任务的检索器。
- **修复**: 将检索器和引用映射作为参数传入工具函数，而非通过模块级全局变量。或用 `threading.local()` 做线程隔离。

### C7. Tab 切换功能完全失效

- **文件**: `app/pages/task_page.py:158,163`, `app/views/task_page.py:158,163`, `app/main.py:40`
- **描述**: "查看报告" 按钮设置 `st.session_state["active_tab"] = 2`，"返回上传页" 设置为 0，但 `app/main.py` 无条件渲染全部 4 个 `st.tabs()`，从不读取 `active_tab`。Streamlit 的 `st.tabs()` 不支持通过 session_state 编程式切换。
- **影响**: 点击这些按钮无任何视觉效果，用户困惑。
- **修复**: 使用 URL query params（`st.query_params`）或 `st.navigation` 实现页面路由。

### C8. app/pages 与 app/views 完全重复的 4 个文件

- **文件**: `app/pages/upload_page.py`, `task_page.py`, `report_page.py`, `benchmark_page.py` 与 `app/views/` 下同名文件内容完全一致。
- **描述**: `app/main.py:14-17` 只从 `app.views.*` 导入，`app/pages/` 是无用死代码。
- **影响**: 维护陷阱——编辑 `pages/` 下的文件不会有任何效果，开发者困惑。
- **修复**: 删除 `app/pages/` 目录，保留 `app/views/`。

---

## HIGH — 12 项（应优先修复）

### H1. `sanitize_imports()` 是空桩

- **文件**: `adaptive_crag/sandbox/security.py:66-71`
- **描述**: `def sanitize_imports(code, allowed): return code` — 函数体为空，不执行任何过滤。文档注释说"MVP 阶段可直接拒绝"，但实际直接放行。
- **影响**: 任何调用 `sanitize_imports()` 的代码路径会获得未经审查的代码。
- **修复**: 实现实际的包名过滤逻辑，或抛出 NotImplementedError。

### H2. 仅客户端文件类型校验

- **文件**: `app/pages/upload_page.py:27`
- **描述**: `st.file_uploader(type=["pdf", "txt", ...])` — Streamlit 的 `type` 参数仅设置 HTML `accept` 属性，是客户端限制。后端 `_detect_type()` 在 `ingestion/__init__.py:82` 仅检查文件扩展名，不检查 magic bytes。
- **影响**: 恶意客户端可上传任意文件类型，可能触发 PyMuPDF / python-docx / pandas 的解析器 bug。
- **修复**: 服务端检查文件 magic bytes (如 `python-magic`)，拒绝不匹配的 MIME 类型。

### H3. 沙箱子进程继承父进程全部环境变量

- **文件**: `adaptive_crag/sandbox/runner.py:83`
- **描述**: `env = os.environ.copy()` 把包括 `CRAG_API_KEY`、`OPENAI_API_KEY` 在内的所有环境变量传给沙箱子进程。
- **影响**: 若沙箱代码通过某种方式读取 `os.environ`，API Key 等敏感凭据会泄漏。
- **修复**: 白名单式传递环境变量，或在 `check_code_safety` 中拦截 `os.environ` 访问。

### H4. `after_analyze` 条件分支无视 AnalyzerAgent 输出

- **文件**: `adaptive_crag/graph/conditions.py:32-42`, `adaptive_crag/agents/analyzer_agent.py:55-58`
- **描述**: `after_analyze` 读取的是 `state["plan"]["requires_code"]`（由 RouterAgent 在流程开始设置），而非 AnalyzerAgent 的分析结果。AnalyzerAgent 的 `update_state` 仅返回 `code_plan` 和 `current_step`，不更新 `plan.requires_code`。
- **影响**: Router 判 `requires_code=False` 时，AnalyzerAgent 即使分析出确实需要代码也无法修正。
- **修复**: 让 `after_analyze` 检查 `state["code_plan"]` 是否有内容，或让 AnalyzerAgent 更新 `plan.requires_code`。

### H5. validate_node 异常时降级通过

- **文件**: `adaptive_crag/graph/nodes/validate_node.py:33-41`
- **描述**: `ValidatorAgent` 抛出任何异常时返回 `"citations_valid": True`。
- **影响**: LLM 崩溃、网络错误、引用校验逻辑错误都会标记为"校验通过"，伪造或缺失引用完全无法检测。
- **修复**: 异常时设置 `citations_valid: False` 并记录错误原因；只有校验逻辑明确返回 True 时才通过。

### H6. report_node 异常时生成错误消息充报告

- **文件**: `adaptive_crag/graph/nodes/report_node.py:33-41`
- **描述**: ReportAgent 异常时返回 `report_ready: True`，报告内容就是错误字符串。
- **影响**: 下游 validate_node 将其当作正常报告处理，用户看到的"报告"是一行错误信息。
- **修复**: 异常时设置 `report_ready: False`，在 `final_state` 中区分成功和失败。

### H7. st.rerun() 在 st.spinner 上下文内调用

- **文件**: `app/pages/upload_page.py:60-89`, `app/views/upload_page.py:60-89`
- **描述**: `st.rerun()` 在第 89 行调用，而 `with st.spinner(...):` 在第 60 行进入。spinner 的 `__exit__` 未执行。
- **影响**: Spinner 可能残留，UI 状态不一致。
- **修复**: 将 `st.rerun()` 移到 spinner 块之外，或使用 `st.status` 替代。

### H8. 无服务端文件大小限制

- **文件**: `app/pages/upload_page.py:29`
- **描述**: Help text 说"单文件上限 50MB"，但代码中既无 `st.file_uploader` 的 `max_size` 参数，也无后端校验。
- **影响**: 超大文件上传导致磁盘/内存耗尽 (DoS)。
- **修复**: 添加 `st.set_option('server.maxUploadSize', 200)` 和上传后 `len(bytes_data)` 校验。

### H9. 无限自动刷新循环（无上限/无退避）

- **文件**: `app/pages/task_page.py:142-151`, `app/views/task_page.py:142-151`
- **描述**: 任务运行时每 2 秒 `st.rerun()`，无最大次数、无退避策略。且 `st.tabs()` 下所有 4 个页面每次都要重新渲染。
- **影响**: 后台线程挂起时 CPU 空转；服务器压力大。
- **修复**: 添加最大 rerun 次数（如 300 次 = 10 分钟），或使用 WebSocket 回调替代轮询。

### H10. Benchmark 页面装饰性控件（无功能）

- **文件**: `app/pages/benchmark_page.py:21,25,29`, `app/views/benchmark_page.py:21,25,29`
- **描述**: 三个 `st.selectbox()` 返回值被丢弃，无 `key` 参数。"开始跑分"按钮 `disabled=True` 写死。
- **影响**: 页面完全无交互功能，用户困惑。且缺少 key 可能在重复渲染时报 `DuplicateWidgetID`。
- **修复**: 实现选择逻辑并启用按钮，或将页面标记为"开发中"并隐藏无效控件。

### H11. 报告渲染无 HTML 过滤

- **文件**: `app/pages/report_page.py:41,48`, `app/views/report_page.py:41,48`
- **描述**: `st.markdown(task.report)` 直接渲染 LLM 生成的 Markdown。若报告包含恶意 HTML 或格式错误的 Markdown，可能注入内容或崩溃。
- **影响**: XSS 风险、渲染异常导致页面崩溃。
- **修复**: 关闭 `unsafe_allow_html` 或对输入做 HTML 实体转义后再渲染。

### H12. 重复文件名静默覆盖

- **文件**: `app/pages/upload_page.py:70-72`, `app/views/upload_page.py:70-72`
- **描述**: `save_path = os.path.join(save_dir, f.name)` — 两个同名文件上传时，后者静默覆盖前者。
- **影响**: 用户丢失数据且无提示。
- **修复**: 上传前检查文件是否已存在，重名时追加序号或 UUID。

---

## MEDIUM — 14 项（建议修复）

### M1. citation_mapper 可能找到错误的文本位置

- **文件**: `adaptive_crag/ingestion/citation_mapper.py:24-32`
- **描述**: `raw_text.find(chunk.text[:100])` — 如果相同的前 100 字符在原文中出现多次，`find()` 返回第一个匹配位置。

### M2. `on_step_change` 闭包捕获过期的 `task.status`

- **文件**: `adaptive_crag/application/task_orchestrator.py:153-158`
- **描述**: 闭包中 `task` 是第 52 行 `SessionManager.get_task()` 的快照，`task.status` 是早期状态。当步骤状态非 `running` 时用此过期值，可能覆盖其他线程的更新。

### M3. 沙箱 data_files 复制无边界校验

- **文件**: `adaptive_crag/sandbox/runner.py:67-69`
- **描述**: `shutil.copy2(f, work_dir)` 复制任意路径的 `data_files` 到沙箱目录，未验证路径是否在允许的上传目录内。

### M4. 两个 UI 层的 progress 计算不一致

- **文件**: `app/pages/task_page.py:25-38` vs `adaptive_crag/application/task_orchestrator.py:263-280`
- **描述**: UI 用 `(idx+1)/len(STEP_KEYS)` 线性计算，编排层用硬编码百分比。init 步骤 UI 显示 9% 而后端报告 0%。

### M5. execute_node 用硬编码字符串判断"无需代码"

- **文件**: `adaptive_crag/graph/nodes/execute_node.py:24`, `graph/nodes/code_write_node.py:31`
- **描述**: 精确字符串匹配 `"# 无需数据分析\nprint('分析完成，无需额外代码执行')"` 来判断跳过执行。字符串变更会导致判断失效。

### M6. Streamlit session_state 竞态

- **文件**: `adaptive_crag/application/session_manager.py:89-99`
- **描述**: `get_session()` 在第 86-91 行检查 `st.session_state` 与第 92 行获取锁之间存在窗口，后台线程可能在此期间修改数据。

### M7. task_orchestrator 用中文错误文本判断 abort

- **文件**: `adaptive_crag/application/task_orchestrator.py:182-187`
- **描述**: `if errors and any("自动终止" in str(e) for e in errors)` — 依赖中文错误消息文本。应检查 `final_state.get("current_step") == "aborted"`。

### M8. 无任务取消 UI

- **文件**: `adaptive_crag/application/task_orchestrator.py:244` 有 `cancel_task()`
- **描述**: 编排层已经实现了取消逻辑，但 UI 没有任何按钮暴露给用户。

### M9. `_emit_event` 回调异常静默吞掉

- **文件**: 所有 `graph/nodes/*.py` 中的 `_emit_event` 函数
- **描述**: `except Exception: pass` — 回调中的 bug 无法被发现。

### M10. `_grade_loop_count` 未在 grade_node 异常处理中设置

- **文件**: `adaptive_crag/graph/nodes/grade_node.py:47-54`
- **描述**: GraderAgent 异常时返回的 dict 不含 `_grade_loop_count`，循环计数器不递增。目前因 `web_search_node` 也会递增而不构成死循环，但脆弱。

### M11. 执行后图表收集生命周期不确定

- **文件**: `adaptive_crag/graph/nodes/execute_node.py:42`
- **描述**: `execute_node` 返回的 `generated_files` 指向 `output_dir`，该目录在 workflow 执行完毕时仍存在，但无明确生命周期保证。

### M12. API Key 在 fallback 链中的歧义

- **文件**: `adaptive_crag/config/llm_config.py:41`
- **描述**: `os.environ.get("CRAG_API_KEY") or os.environ.get("OPENAI_API_KEY")` — `main.py` 的 `setdefault` 让 `CRAG_API_KEY` 有默认值，导致 `OPENAI_API_KEY` 永远不被使用。

### M13. 环境变量无效值静默忽略

- **文件**: `adaptive_crag/config/settings.py:112-113`
- **描述**: `except (ValueError, TypeError): pass` — `CRAG_TOP_K=abc` 时静默使用默认值，用户无任何反馈。

### M14. 部分配置字段无环境变量覆盖

- **文件**: `adaptive_crag/config/settings.py:89-112`
- **描述**: `chunk_overlap_tokens`、`max_output_chars`、`min_score_threshold` 等没有对应的 `CRAG_*` 环境变量，运行时不可配置。

---

## LOW — 27 项（代码质量 / 优化方向）

### 代码重复

| # | 问题 | 文件 |
|---|------|------|
| L1 | `_emit_event` 函数在 10 个节点文件中完全重复 | `graph/nodes/*.py` |
| L2 | `profile_csv` 和 `profile_excel` 90% 相同 | `ingestion/dataset_profiler.py:10-98` |
| L3 | `_estimate_tokens` 在 `chunker.py` 和 `documents.py` 各实现一份 | `ingestion/chunker.py:184`, `schema/documents.py:84` |
| L4 | 10 个节点的 try/except/return error 模式完全一致 | `graph/nodes/*.py` |
| L5 | 所有节点输出必须手动传递 `query` / `uploaded_files` / `_workflow_step_count` | `graph/nodes/*.py` |
| L6 | `_collect_data_files` 和 `_collect_generated_files` 实现相同 | `sandbox/runner.py:151-168` |

### 性能

| # | 问题 | 文件 |
|---|------|------|
| L7 | `build_page_mapping` 每个 chunk 做 `raw_text.find()` 全文扫描 | `ingestion/citation_mapper.py:23-32` |
| L8 | `_generate_hit_reason` 每个 chunk 做关键词 × 文本扫描 | `retrieval/evidence_builder.py:64-69` |
| L9 | `EmbeddingStore._get_model` 非线程安全（无锁的 lazy init） | `retrieval/embedding_store.py:28-40` |
| L10 | BAAI reranker 模型 (~2-4GB) 首次使用时 eager 全量加载 | `retrieval/reranker.py:19-36` |
| L11 | 沙箱用 `shutil.copy2` 复制数据文件而非 symlink | `sandbox/runner.py:70-73` |
| L12 | 文件摄入串行 for 循环 | `application/task_orchestrator.py:76-114` |
| L13 | `run_workflow` 每次调用重建编译图 | `graph/workflow.py:83` |
| L14 | SessionManager 的 tasks 字典只增不删 | `application/session_manager.py:69` |

### 死代码 / 无用导入

| # | 问题 | 文件 |
|---|------|------|
| L15 | `import sys` 未使用 | `sandbox/security.py:5` |
| L16 | `import traceback as tb_module` 未使用 | `sandbox/error_parser.py:5` |
| L17 | `uploaded_files_cache` 设置但从未读取 | `app/pages/upload_page.py:20-21` |
| L18 | `web_search_trigger_accuracy` 返回常量 0.8 | `evaluation/scorers.py:55` |

### 脆性耦合

| # | 问题 | 文件 |
|---|------|------|
| L19 | BM25Store 的多文档 chunks 全归入第一个 doc_id | `retrieval/bm25_store.py:52-53` |
| L20 | `code_write_node` 的 `_build_analysis_code` 忽略 `chunks` 参数，生成固定模板 | `graph/nodes/code_write_node.py:42-80` |
| L21 | `bm25_search` / `vector_search` 从 `hybrid_search` 导入私有模块级变量 | `tools/bm25_search.py:5`, `tools/vector_search.py:5` |
| L22 | 所有节点文件函数体内的 `from . import check_abort` 懒加载避免循环导入 | `graph/nodes/*.py` |

### 规范偏差

| # | 问题 | 文件 |
|---|------|------|
| L23 | `python-docx>=1.0.0` 版本不存在（PyPI 最高 ~0.8.11） | `pyproject.toml:22` |
| L24 | 所有 dataclass 无运行时校验（无 Pydantic） | `schema/` |
| L25 | 无 `python-dotenv` 依赖 | `pyproject.toml` |
| L26 | `langgraph>=0.0.30` 早期预发布版本 | `pyproject.toml:14` |
| L27 | 无依赖锁定文件（poetry.lock / requirements.lock） | 项目根目录 |

---

## 测试缺口

| 模块 | 状态 | 说明 |
|------|------|------|
| `schema/` | 部分覆盖 | `test_all.py` 有 ~20 个测试，spec 预期 38+ |
| `config/` | 部分覆盖 | 仅基本加载测试 |
| `ingestion/` | 几乎无 | `document_loader`、`chunker`、`citation_mapper`、`dataset_profiler`、`IngestionPipeline.process()` 均无测试 |
| `retrieval/` | 几乎无 | 仅 `BM25Store._tokenize` 和空 `rank_fusion`；`EmbeddingStore`、`HybridRetriever`、`Reranker`、`evidence_builder` 均无 |
| `agents/` | 几乎无 | 仅 `_extract_json`；RouterAgent、GraderAgent、AnalyzerAgent 等全部无 |
| `graph/` | 无 | `build_workflow()`、所有节点函数、`conditions.py` 均无 |
| `application/` | 无 | `TaskOrchestrator`、`SessionManager`、`ArtifactManager` 均无 |
| `reporting/` | 无 | 无测试 |
| `evaluation/` | 无 | 无测试 |
| 集成测试 | 无 | 无端到端 file→index→query→report 测试 |

---

## Spec vs Implementation 差异

| # | 差异项 | Spec | Implementation |
|---|--------|------|----------------|
| 1 | Python 版本 | `>=3.10` | `>=3.11` |
| 2 | 项目名 | `adaptive-crag` (hyphen) | `adaptive_crag` (underscore) |
| 3 | build-backend | `setuptools.backends._legacy:_Backend` | `setuptools.build_meta` |
| 4 | MIT license | 已声明 | 未声明 |
| 5 | `scikit-learn` | main deps | dev deps |
| 6 | `scipy` | main deps | dev deps |
| 7 | `pytest-cov` | dev deps | 未包含 |
| 8 | `black` | dev deps | 未包含 |
| 9 | `flake8` | dev deps | 未包含 |
| 10 | `mypy` | dev deps | 未包含 |
| 11 | streamlit 版本 | `>=1.28.0` | `>=1.38,<1.40` |
| 12 | PDF 依赖 | `weasyprint>=60.0` | `fpdf2>=2.7.0` |
| 13 | `GraphState.plan` 类型 | `TaskPlan \| None` | `dict \| None` |
| 14 | `DocumentType` 枚举 | 6 个值（无 DOCX） | 7 个值（含 DOCX） |
| 15 | 测试文件结构 | 10 个模块化测试文件 | 1 个 `test_all.py` |
| 16 | `main.py` | 无硬编码 key | 硬编码 API key |
| 17 | `Citation.source_type` | 无默认值 | 默认 `"local_literature"` |

---

## 架构优化建议

1. **节点包装器装饰器**: 将 `check_abort()`、`try/except`、`_emit_event`、`query/uploaded_files` 透传等重复模式抽取为 `@node_handler` 装饰器，减少每个节点约 15 行样板代码。

2. **提取共享工具模块**: `_emit_event`、`_estimate_tokens`、错误返回构建器统一到 `graph/nodes/common.py` 或类似模块。

3. **结构化日志**: 将所有 `print("[LOG] ...")` 替换为 `logging` 模块，按级别控制输出，生产环境可关闭调试日志。

4. **会话级索引隔离**: 将全局 `_hybrid_retriever` / `_citation_mappings` 重构为 TaskOrchestrator 实例属性或请求级上下文，消除竞态条件。

5. **LLM 动态代码生成**: `code_write_node._build_analysis_code` 目前生成固定 CSV 模板，应改为调用 CodeWriterAgent 根据 `code_plan` 和 `chunks` 动态生成分析代码。

6. **引入 Pydantic 或运行时校验**: 所有 dataclass 目前接受任意 dict，无字段类型校验。Pydantic 或 `dataclasses.field(metadata=...)` + 手动校验可防止数据格式漂移。

7. **添加依赖锁定**: 用 `pip freeze > requirements.lock` 或切换到 Poetry/Pipenv 管理确定性依赖。

8. **WebSocket 替代轮询**: Streamlit 原生不支持，但可通过 `st.experimental_fragment` 配合服务端回调减少 `st.rerun()` 频率。长远考虑迁移到响应式框架。