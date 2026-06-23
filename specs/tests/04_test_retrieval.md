# 单元测试说明书：检索层 (retrieval)

## 对应模块
`04_retrieval.md`

## 目标测试文件
```
tests/
    test_retrieval/
        __init__.py
        conftest.py              # 测试用 chunk 数据集和 fixture
        test_embedding_store.py  # ChromaDB 向量存储
        test_bm25_store.py       # BM25 索引
        test_hybrid_retriever.py # 混合检索
        test_rank_fusion.py      # 分数融合 RRF
        test_reranker.py         # 二次排序（简化测试）
        test_evidence_builder.py # 证据构造
```

## 运行方式
```bash
pytest tests/test_retrieval/ -v
```

## 测试依赖
- 需要安装 `chromadb`、`sentence-transformers`、`rank_bm25`
- Embedding 模型可能在 CI 中不可用，使用 fixture 控制是否加载

## 测试数据生成

conftest.py 中构建内存测试数据，不读取外部文件：

```python
@pytest.fixture
def sample_chunks():
    """10 个 Chunk 对象，覆盖不同主题: AI, 数据分析, 编程"""
    return [
        Chunk(chunk_id="chunk_001", doc_id="doc_1", text="Transformer 使用自注意力机制...", page_num=1, ...),
        Chunk(chunk_id="chunk_002", doc_id="doc_1", text="多头注意力允许模型关注不同位置...", page_num=2, ...),
        # ... 共 10 条，包含不同关键词
    ]

@pytest.fixture
def temp_chroma_dir(tmp_path):
    """临时 ChromaDB 目录"""
    return str(tmp_path / "chroma")
```

## 测试用例清单

### test_embedding_store.py

```python
def test_embedding_store_init(temp_chroma_dir):
    """EmbeddingStore 能初始化并创建集合"""

def test_add_chunks_increases_count(embed_store, sample_chunks):
    """添加 10 个 chunk 后，集合中存在 10 条记录"""

def test_search_returns_results(embed_store, sample_chunks):
    """检索能返回 top_k 条结果"""

def test_search_relevant_query(embed_store, sample_chunks):
    """"注意力机制" 应召回 chunk_001 和 chunk_002"""

def test_search_empty_query(embed_store):
    """空 query 引发 ValueError"""

def test_search_no_match(embed_store, sample_chunks):
    """不相关 query 返回空列表"""

def test_double_add_does_not_duplicate(embed_store, sample_chunks):
    """重复添加相同 chunk 不产生重复记录"""

def test_delete_collection(embed_store, sample_chunks):
    """清空集合后检索返回空"""

def test_search_respects_top_k(embed_store, sample_chunks):
    """top_k=3 时最多返回 3 条"""
```

### test_bm25_store.py

```python
def test_bm25_init(bm25_store, sample_chunks):
    """BM25Store 添加 chunk 后索引不为空"""

def test_bm25_search_exact_match(bm25_store, sample_chunks):
    """搜索 "自注意力机制" 能召回包含该词的 chunk"""

def test_bm25_search_partial_match(bm25_store, sample_chunks):
    """搜索 "注意力" 能召回包含注意力的多个 chunk"""

def test_bm25_search_no_match(bm25_store, sample_chunks):
    """搜索不存在的关键词返回空列表"""

def test_bm25_search_empty_query(bm25_store):
    """空 query 返回空列表"""

def test_bm25_score_higher_for_exact(bm25_store, sample_chunks):
    """精确匹配的分数高于部分匹配"""

def test_bm25_store_empty_index():
    """未添加任何 chunk 时检索返回空列表，不崩溃"""
```

### test_rank_fusion.py

```python
def test_rrf_basic():
    """
    输入两组结果:
    vec: [A, B, C]
    bm25: [C, D, A]
    融合后 A 和 C 在顶部
    """

def test_rrf_weights():
    """不同 weight 影响排序结果"""

def test_rrf_empty_input():
    """两组都为空时返回空列表"""

def test_rrf_one_empty():
    """一组为空时返回另一组的排序"""

def test_rrf_no_duplicates_in_result():
    """融合结果中无重复 chunk_id"""

def test_rrf_k_parameter():
    """不同 k 值影响分数但排名不变（稳定）"""
```

### test_hybrid_retriever.py

```python
def test_hybrid_search_basic(hybrid_retriever, sample_chunks):
    """混合搜索返回非空结果"""

def test_hybrid_search_relevant(hybrid_retriever, sample_chunks):
    """相关 query 的 top-1 结果包含关键词匹配"""

def test_hybrid_search_not_match(hybrid_retriever, sample_chunks):
    """不相关 query 返回空列表"""

def test_hybrid_search_top_k(hybrid_retriever, sample_chunks):
    """top_k 参数有效"""

def test_hybrid_search_ranking(hybrid_retriever, sample_chunks):
    """向量 + BM25 融合后排序优于单一路径（向量高 + BM25 高）"""
```

### test_reranker.py

```python
def test_reranker_keep_top_k():
    """rerank 后只保留 top_k 条"""

def test_reranker_scores_added():
    """rerank 结果包含 rerank_score 字段"""

def test_reranker_order():
    """rerank 后排序与原始不同（如果模型能区分相关性）"""

def test_reranker_empty_input():
    """空输入返回空列表"""

@pytest.mark.skip(reason="需要下载 reranker 模型")
def test_reranker_model_loading():
    """reranker 模型能成功加载"""
```

### test_evidence_builder.py

```python
def test_evidence_builder_basic():
    """build_evidence 返回包含 results/total_found/source 的 dict"""

def test_evidence_builder_fields():
    """每条 result 包含 chunk_id/text/score/page_num/doc_id/filename/hit_reason"""

def test_evidence_builder_empty():
    """空输入返回 total_found=0"""

def test_evidence_builder_hit_reason(hybrid_retriever, sample_chunks):
    """hit_reason 不为空字符串"""
```