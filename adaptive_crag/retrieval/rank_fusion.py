"""
分数融合：使用 Reciprocal Rank Fusion (RRF) 算法融合两个检索结果。
"""


def reciprocal_rank_fusion(
    vector_results: list[dict],
    bm25_results: list[dict],
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
    k: int = 60,
) -> list[dict]:
    """
    使用 Reciprocal Rank Fusion (RRF) 算法融合两个检索结果。

    score = weight * 1 / (k + rank)
    按融合分降序排列，合并相同的 chunk_id。

    Args:
        vector_results: 向量检索结果列表
        bm25_results: BM25 检索结果列表
        vector_weight: 向量检索权重
        bm25_weight: BM25 检索权重
        k: RRF 常数（防止除零）

    Returns:
        融合排序后的结果列表
    """
    score_map: dict[str, float] = {}
    result_map: dict[str, dict] = {}

    # 计算向量检索的 RRF 分数
    for rank, item in enumerate(vector_results):
        chunk_id = item.get("chunk_id", "")
        if not chunk_id:
            continue
        score = vector_weight * (1.0 / (k + rank + 1))
        score_map[chunk_id] = score_map.get(chunk_id, 0) + score
        result_map[chunk_id] = item

    # 计算 BM25 检索的 RRF 分数
    for rank, item in enumerate(bm25_results):
        chunk_id = item.get("chunk_id", "")
        if not chunk_id:
            continue
        score = bm25_weight * (1.0 / (k + rank + 1))
        score_map[chunk_id] = score_map.get(chunk_id, 0) + score
        if chunk_id not in result_map:
            result_map[chunk_id] = item

    # 按融合分降序排列
    sorted_items = sorted(score_map.items(), key=lambda x: x[1], reverse=True)

    fused_results = []
    for chunk_id, fused_score in sorted_items:
        item = dict(result_map[chunk_id])
        item["score"] = fused_score
        fused_results.append(item)

    return fused_results
