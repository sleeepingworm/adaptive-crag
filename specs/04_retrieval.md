# 模块说明书：检索层 (retrieval)

## 所属层级
能力工具层

## 目标目录
`adaptive_crag/retrieval/`

生成文件：
```
adaptive_crag/retrieval/
    __init__.py             # 导出 HybridRetriever
    embedding_store.py      # ChromaDB 向量存储
    bm25_store.py           # BM25 索引
    hybrid_retriever.py     # 混合检索入口
    rank_fusion.py          # 分数融合
    reranker.py             # 二次排序
    evidence_builder.py     # 证据集合构造
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 Chunk, SearchResult, EvidenceSet）
- **必须先生成**：`02_config`（使用 RetrievalConfig）
- **必须先生成**：`03_ingestion`（消费 Chunk 数据建立索引）

## 职责边界

**做：**
- 接收 Chunk 列表，建立 ChromaDB 向量索引
- 接收 Chunk 列表，建立 BM25 关键词索引
- 对用户问题进行向量召回
- 对用户问题进行 BM25 关键词召回
- 对向量召回和 BM25 结果做融合排序
- 使用 Cross-Encoder 或轻量模型做 Rerank
- 构建带来源、页码、命中原因的证据集合

**不做：**
- 不做文件解析和切片
- 不做联网搜索
- 不调用 LLM
- 不决定证据是否足够（那是 Grader Agent 的事）

## 核心接口

### embedding_store.py

```python
class EmbeddingStore:
    """
    基于 ChromaDB 的向量存储。
    Embedding 模型使用 sentence-transformers。
    """

    def __init__(self, persist_dir: str, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cpu"):
        """
        初始化向量存储。
        - 加载 embedding 模型
        - 连接或创建 ChromaDB 集合
        """

    def add_chunks(self, chunks: list[Chunk]) -> int:
        """
        将 Chunk 列表写入向量库。
        每条包含: chunk_id, text, metadata(doc_id, page_num, heading)
        返回写入条数。
        """

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        向量检索。
        输入: 自然语言查询、返回条数
        输出: [{"chunk_id": str, "text": str, "score": float, "metadata": dict}, ...]
        """

    def delete_collection(self):
        """清空当前集合（重新索引时使用）"""
```

重要实现细节：
- embedding 模型用 `sentence-transformers` 加载，MVP 用 CPU
- 每次 `add_chunks` 前检查是否已有相同 doc_id 的索引，避免重复
- ChromaDB 使用持久化模式，数据存到 `persist_dir`

### bm25_store.py

```python
class BM25Store:
    """
    基于 rank_bm25 的关键词索引。
    适合函数名、公式、缩写等精确匹配。
    """

    def __init__(self):
        self.index: dict[str, list] = {}   # {"doc_id": {"corpus": [...], "bm25": BM25Okapi}}
        self.corpus_map: dict[int, Chunk] = {}  # idx -> Chunk

    def add_chunks(self, chunks: list[Chunk]):
        """
        将 Chunk 分词后建立 BM25 索引。
        分词规则：中文按字/词，英文按空格 + 小写。
        """

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        关键词检索。
        输出格式同 EmbeddingStore.search。
        """
```

### hybrid_retriever.py

```python
class HybridRetriever:
    """
    混合检索入口。同时执行向量检索和 BM25 检索，
    合并去重后返回。
    """

    def __init__(self, embed_store: EmbeddingStore, bm25_store: BM25Store, config: RetrievalConfig):
        ...

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        1. 向量检索 -> vec_results
        2. BM25 检索 -> bm25_results
        3. rank_fusion 融合排序
        4. reranker 重新排序
        5. evidence_builder 构建证据集合
        返回 list[dict]（由 evidence_builder 构造）
        """
```

### rank_fusion.py

```python
def reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    k: int = 60
) -> list[dict]:
    """
    使用 Reciprocal Rank Fusion (RRF) 算法融合两个检索结果。
    score = weight * 1/(k + rank)
    按融合分降序排列，合并相同的 chunk_id。
    """
```

### reranker.py

```python
class Reranker:
    """
    对候选结果做二次排序，过滤低相关片段。
    MVP 阶段可简化实现。
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str = "cpu"):
        """
        加载 Cross-Encoder reranker 模型。
        """

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """
        对 query 和每个 candidate.text 做相关度打分。
        重新排序后返回 top_k 条。
        每条增加 rerank_score 字段。
        """
```

### evidence_builder.py

```python
def build_evidence(
    query: str,
    ranked_chunks: list[dict],
    source: str = "hybrid"
) -> dict:
    """
    将排序后的搜索结果构造成 EvidenceSet 的 dict 形态。
    输出结构:
    {
        "results": [
            {
                "chunk_id": str,
                "text": str,
                "score": float,
                "rerank_score": float | None,
                "page_num": int | None,
                "doc_id": str,
                "filename": str,
                "hit_reason": str    # 简短说明为什么匹配
            }
        ],
        "total_found": int,
        "source": str                # "hybrid" | "vector" | "bm25"
    }
    """
```

## 实现约束

1. **Embedding 模型加载**：只在首次初始化时加载一次，避免重复加载
2. **BM25 分词**：简单中文分词可用 `jieba` 或直接按字切，MVP 不需要复杂 NLP
3. **Chunk 去重**：向量和 BM25 结果合并时，相同 chunk_id 只保留最高分
4. **空结果处理**：检索结果为空时返回空列表，不报错
5. **分数归一化**：向量分数和 BM25 分数在融合前应做 min-max 或 softmax 归一化
6. **Rerank 降级**：如果 reranker 模型加载失败，直接使用融合排序结果

## 与上下游模块的对接

- **上游**：ingestion 模块提供 Chunk 列表
- **上游调用方**：LangGraph 工作流的 Retriever Agent 节点
- **下游**：Document Grader 节点消费 EvidenceSet

## 测试要点

- 建立索引后能召回内容
- 相同 query 多次检索结果一致
- 向量检索和 BM25 对"函数名/公式"类 query 各有侧重
- 融合排序结果优于单路
- 空语料库检索不报错
- 增量添加 chunk 后索引正确更新