"""
基于 ChromaDB 的向量存储。
Embedding 模型使用 sentence-transformers。
"""

import os


class EmbeddingStore:
    """
    基于 ChromaDB 的向量存储。
    Embedding 模型使用 sentence-transformers。
    """

    def __init__(self, persist_dir: str, model_name: str = "BAAI/bge-small-zh-v1.5",
                 device: str = "cpu"):
        self.persist_dir = persist_dir
        self.model_name = model_name
        self.device = device
        self._model = None
        self._collection = None
        self._chroma_client = None

    def _get_model(self):
        """延迟加载 embedding 模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except ImportError:
                raise ImportError("需要安装 sentence-transformers: pip install sentence-transformers")
        return self._model

    def _get_collection(self):
        """获取或创建 ChromaDB 集合"""
        if self._collection is None:
            try:
                import chromadb
            except ImportError:
                raise ImportError("需要安装 chromadb: pip install chromadb")

            os.makedirs(self.persist_dir, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = self._chroma_client.get_or_create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_chunks(self, chunks: list) -> int:
        """
        将 Chunk 列表写入向量库。
        每条包含: chunk_id, text, metadata(doc_id, page_num, heading)
        返回写入条数。
        """
        if not chunks:
            return 0

        model = self._get_model()
        collection = self._get_collection()

        texts = [c.text for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "doc_id": c.doc_id,
                "page_num": str(c.page_num) if c.page_num is not None else "",
                "heading": c.heading or "",
                "filename": "",
            }
            for c in chunks
        ]

        # 批量写入，避免重复
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            collection.add(
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end],
                metadatas=metadatas[i:batch_end],
                documents=texts[i:batch_end],
            )

        return len(ids)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """
        向量检索。
        返回: [{"chunk_id", "text", "score", "metadata"}, ...]
        """
        model = self._get_model()
        collection = self._get_collection()

        query_embedding = model.encode([query], show_progress_bar=False).tolist()[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, 100),
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                output.append({
                    "chunk_id": chunk_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "score": float(results["distances"][0][i]) if results["distances"] else 0.0,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                })
        return output

    def delete_collection(self):
        """清空当前集合（重新索引时使用）"""
        try:
            import chromadb
        except ImportError:
            return
        client = chromadb.PersistentClient(path=self.persist_dir)
        try:
            client.delete_collection("documents")
        except Exception:
            pass
        self._collection = None

    def get_collection_stats(self) -> dict:
        """获取集合统计信息"""
        collection = self._get_collection()
        return {
            "count": collection.count(),
            "name": collection.name,
        }
