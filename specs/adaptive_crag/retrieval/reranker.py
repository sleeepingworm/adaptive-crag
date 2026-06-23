"""
对候选结果做二次排序，过滤低相关片段。
使用 Cross-Encoder 模型。
"""


class Reranker:
    """
    对候选结果做二次排序，过滤低相关片段。
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._model = None

    def _load_model(self):
        """延迟加载 reranker 模型"""
        if self._model is None:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                import torch

                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                )
                self._model.to(self.device)
                self._model.eval()
            except ImportError:
                # 降级：无法加载模型时不 rerank
                self._model = "unavailable"
            except Exception:
                self._model = "unavailable"
        return self._model

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        """
        对 query 和每个 candidate.text 做相关度打分。
        重新排序后返回 top_k 条。

        如果模型加载失败，直接按原分数排序返回。
        """
        if not candidates:
            return []

        model = self._load_model()
        if model == "unavailable":
            # 降级：按原分数排序
            sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
            return sorted_candidates[:top_k]

        try:
            import torch

            pairs = [(query, c.get("text", "")) for c in candidates]
            inputs = self._tokenizer(
                pairs, padding=True, truncation=True, return_tensors="pt", max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model(**inputs)
                scores = outputs.logits.squeeze(-1).tolist()

            if not isinstance(scores, list):
                scores = [scores]

            for i, candidate in enumerate(candidates):
                candidate["rerank_score"] = float(scores[i]) if i < len(scores) else 0.0

            # 按 rerank 分数重新排序
            reranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0), reverse=True)
            return reranked[:top_k]

        except Exception:
            # 降级
            sorted_candidates = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
            return sorted_candidates[:top_k]
