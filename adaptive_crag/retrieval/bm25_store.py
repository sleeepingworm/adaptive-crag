"""
基于 rank_bm25 的关键词索引。
适合函数名、公式、缩写等精确匹配。
"""

import re


class BM25Store:
    """
    基于 rank_bm25 的关键词索引。
    """

    def __init__(self):
        self.index: dict[str, dict] = {}  # {"doc_id": {"corpus": [...], "bm25": BM25Okapi}}
        self.corpus_map: dict[int, dict] = {}  # idx -> chunk info

    def add_chunks(self, chunks: list) -> None:
        """
        将 Chunk 分词后建立 BM25 索引。
        分词规则：中文按字，英文按空格 + 小写。
        """
        if not chunks:
            return

        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            raise ImportError("需要安装 rank_bm25: pip install rank_bm25")

        new_corpus = []
        new_ids = []

        for chunk in chunks:
            tokens = self._tokenize(chunk.text)
            new_corpus.append(tokens)
            new_ids.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "text": chunk.text,
                "page_num": chunk.page_num,
                "filename": getattr(chunk, "filename", ""),
            })

        start_idx = len(self.corpus_map)
        for i, item in enumerate(new_ids):
            self.corpus_map[start_idx + i] = item

        bm25 = BM25Okapi(new_corpus)
        doc_id = chunks[0].doc_id
        self.index[doc_id] = {
            "corpus": new_corpus,
            "bm25": bm25,
            "start_idx": start_idx,
            "count": len(new_ids),
        }

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        关键词检索。
        输出: [{"chunk_id", "text", "score", "metadata"}, ...]
        """
        query_tokens = self._tokenize(query)
        all_scores = []

        for doc_id, entry in self.index.items():
            bm25 = entry["bm25"]
            scores = bm25.get_scores(query_tokens)
            for idx, score in enumerate(scores):
                if score > 0:
                    map_idx = self._find_map_idx(doc_id, idx)
                    if map_idx is not None:
                        info = self.corpus_map[map_idx]
                        all_scores.append({
                            "chunk_id": info["chunk_id"],
                            "text": info["text"],
                            "score": float(score),
                            "metadata": {
                                "doc_id": info["doc_id"],
                                "page_num": info["page_num"],
                                "filename": info["filename"],
                            },
                        })

        # 按分数降序排列
        all_scores.sort(key=lambda x: x["score"], reverse=True)
        return all_scores[:top_k]

    def _tokenize(self, text: str) -> list[str]:
        """分词：中文按字符、英文按单词"""
        # 英文单词
        words = re.findall(r"[a-zA-Z_]+", text)
        # 中文按字
        chars = re.findall(r"[\u4e00-\u9fff]", text)
        # 数字
        numbers = re.findall(r"\d+", text)
        return [w.lower() for w in words] + chars + numbers

    def _find_map_idx(self, doc_id: str, local_idx: int) -> int | None:
        """在全局 corpus_map 中查找对应的索引，基于存储的 start_idx 偏移"""
        entry = self.index.get(doc_id)
        if entry is None:
            return None
        start_idx = entry.get("start_idx")
        count = entry.get("count")
        if start_idx is None or count is None:
            return None
        if local_idx < 0 or local_idx >= count:
            return None
        return start_idx + local_idx

    def clear(self):
        """清空索引"""
        self.index.clear()
        self.corpus_map.clear()
