"""
Adaptive CRAG 测试
"""

import unittest
from adaptive_crag.schema import (
    Document, Chunk, DatasetProfile, GraphState, TaskPlan,
    ExecutionArtifact, Citation, ReportBundle,
    DocumentType, ChunkStrategy, TaskType,
)


class TestSchema(unittest.TestCase):
    """测试所有数据类"""

    def test_document_create(self):
        doc = Document.create(
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            doc_type=DocumentType.PDF,
            file_size_bytes=1024,
            file_hash="abc123",
            page_count=10,
        )
        self.assertTrue(doc.doc_id.startswith("doc_"))
        self.assertEqual(doc.filename, "test.pdf")
        self.assertEqual(doc.doc_type, DocumentType.PDF)

    def test_chunk_create(self):
        chunk = Chunk.create(
            doc_id="doc_001",
            text="这是一段测试文本",
            strategy=ChunkStrategy.PARAGRAPH,
            page_num=1,
            paragraph_idx=0,
        )
        self.assertTrue(chunk.chunk_id.startswith("chunk_"))
        self.assertEqual(chunk.page_num, 1)
        self.assertEqual(chunk.strategy, ChunkStrategy.PARAGRAPH)

    def test_dataclass_asdict(self):
        from dataclasses import asdict
        doc = Document.create(
            filename="test.md",
            file_path="/path/to/test.md",
            doc_type=DocumentType.MARKDOWN,
        )
        d = asdict(doc)
        self.assertEqual(d["filename"], "test.md")
        self.assertEqual(d["doc_type"], "markdown")

    def test_enum_serialization(self):
        import json
        dt = DocumentType.PDF
        self.assertEqual(dt.value, "pdf")
        self.assertEqual(json.dumps(dt.value), '"pdf"')

    def test_graph_state_defaults(self):
        state = GraphState()
        self.assertEqual(state.current_step, "init")
        self.assertFalse(state.completed)
        self.assertEqual(state.retry_count, 0)
        self.assertEqual(state.max_retries, 3)
        self.assertEqual(state.errors, [])

    def test_graph_state_with_values(self):
        state = GraphState(query="测试问题", uploaded_files=["file1.pdf"])
        self.assertEqual(state.query, "测试问题")
        self.assertEqual(len(state.uploaded_files), 1)

    def test_execution_artifact(self):
        artifact = ExecutionArtifact(
            success=True,
            stdout="Hello World",
            exit_code=0,
            execution_time_ms=100,
        )
        d = artifact.to_dict()
        self.assertTrue(d["success"])
        self.assertEqual(d["stdout"], "Hello World")

    def test_execution_artifact_from_dict(self):
        d = {"success": True, "stdout": "test", "exit_code": 0}
        artifact = ExecutionArtifact.from_dict(d)
        self.assertTrue(artifact.success)
        self.assertEqual(artifact.stdout, "test")

    def test_nested_dataclass(self):
        cit = Citation(
            citation_id="cite_001",
            claim="这是一个结论",
            source_filename="paper.pdf",
            page_num=5,
            confidence=0.95,
        )
        bundle = ReportBundle(
            task_id="task_001",
            query="测试问题",
            report_markdown="# 报告",
            citations=[cit.to_dict()],
            generated_at="2025-01-01T00:00:00",
        )
        self.assertEqual(len(bundle.citations), 1)
        self.assertEqual(bundle.citations[0]["citation_id"], "cite_001")

    def test_nullable_fields(self):
        chunk = Chunk(
            chunk_id="chunk_001",
            doc_id="doc_001",
            text="text",
            page_num=None,
            heading=None,
            embedding=None,
        )
        self.assertIsNone(chunk.page_num)
        self.assertIsNone(chunk.heading)
        self.assertIsNone(chunk.embedding)


class TestConfig(unittest.TestCase):
    """测试配置模块"""

    def test_default_config(self):
        from adaptive_crag.config import load_config
        config = load_config()
        self.assertEqual(config.retrieval.top_k, 10)
        self.assertEqual(config.sandbox.timeout_seconds, 60)
        self.assertFalse(config.web_search.enabled)

    def test_llm_config_defaults(self):
        from adaptive_crag.config.llm_config import LLMConfig
        config = LLMConfig()
        self.assertEqual(config.model_name, "gpt-4o")
        self.assertEqual(config.temperature, 0.1)

    def test_sandbox_allowed_packages(self):
        from adaptive_crag.config.settings import SandboxConfig
        config = SandboxConfig()
        self.assertIn("pandas", config.allowed_packages)
        self.assertIn("os", config.restricted_modules)


class TestSecurity(unittest.TestCase):
    """测试沙箱安全"""

    def test_check_safe_code(self):
        from adaptive_crag.sandbox import check_code_safety
        code = "import pandas as pd\nprint('hello')"
        is_safe, reason = check_code_safety(code)
        self.assertTrue(is_safe)
        self.assertEqual(reason, "")

    def test_check_unsafe_code_os(self):
        from adaptive_crag.sandbox import check_code_safety
        code = "import os\nos.system('ls')"
        is_safe, reason = check_code_safety(code)
        self.assertFalse(is_safe)
        self.assertIn("os", reason)

    def test_check_unsafe_code_eval(self):
        from adaptive_crag.sandbox import check_code_safety
        code = "eval('print(1)')"
        is_safe, reason = check_code_safety(code)
        self.assertFalse(is_safe)

    def test_check_unsafe_code_subprocess(self):
        from adaptive_crag.sandbox import check_code_safety
        code = "from subprocess import run"
        is_safe, reason = check_code_safety(code)
        self.assertFalse(is_safe)


class TestErrorParser(unittest.TestCase):
    """测试错误解析"""

    def test_parse_name_error(self):
        from adaptive_crag.sandbox.error_parser import parse_traceback
        tb = 'Traceback (most recent call last):\n  File "script.py", line 5, in <module>\n    print(x)\nNameError: name \'x\' is not defined'
        parsed = parse_traceback(tb, "a=1\nb=2\nc=3\nd=4\nprint(x)")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.error_type, "NameError")
        self.assertEqual(parsed.line_number, 5)

    def test_parse_key_error(self):
        from adaptive_crag.sandbox.error_parser import parse_traceback
        tb = "KeyError: 'column_name'"
        parsed = parse_traceback(tb)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.error_type, "KeyError")

    def test_summarize_error(self):
        from adaptive_crag.sandbox.error_parser import summarize_error
        from adaptive_crag.schema import ExecutionArtifact

        artifact = ExecutionArtifact(
            success=False,
            stderr="NameError: name 'x' is not defined",
            exit_code=1,
        )
        summary = summarize_error(artifact)
        self.assertIn("NameError", summary)


class TestIngestion(unittest.TestCase):
    """测试文件解析"""

    def test_estimate_tokens(self):
        from adaptive_crag.schema.documents import estimate_tokens
        self.assertEqual(estimate_tokens("hello"), 3)
        self.assertGreater(estimate_tokens("这是一段中文"), 0)

    def test_text_cleaner(self):
        from adaptive_crag.ingestion.text_cleaner import clean_text
        text = "Hello\x00World\n\n\n\nTest"
        cleaned = clean_text(text)
        self.assertNotIn("\x00", cleaned)
        self.assertNotIn("\n\n\n", cleaned)

    def test_detect_type(self):
        pipeline = __import__("adaptive_crag.ingestion", fromlist=["IngestionPipeline"])
        # 测试类型检测逻辑
        from adaptive_crag.schema import DocumentType
        self.assertEqual(DocumentType.PDF.value, "pdf")


class TestRetrieval(unittest.TestCase):
    """测试检索模块"""

    def test_rank_fusion_empty(self):
        from adaptive_crag.retrieval.rank_fusion import reciprocal_rank_fusion
        result = reciprocal_rank_fusion([], [])
        self.assertEqual(result, [])

    def test_build_evidence_empty(self):
        from adaptive_crag.retrieval.evidence_builder import build_evidence
        result = build_evidence("query", [])
        self.assertEqual(result["total_found"], 0)

    def test_bm25_tokenize(self):
        from adaptive_crag.retrieval.bm25_store import BM25Store
        store = BM25Store()
        tokens = store._tokenize("Hello World 测试 123")
        self.assertIn("hello", tokens)
        self.assertIn("world", tokens)


class TestReporting(unittest.TestCase):
    """测试报告模块"""

    def test_markdown_builder(self):
        from adaptive_crag.reporting import MarkdownBuilder
        report = MarkdownBuilder.build_report(
            title="测试报告",
            sections=[{"heading": "摘要", "content": "这是一个测试"}],
        )
        self.assertIn("# 测试报告", report)
        self.assertIn("## 摘要", report)

    def test_citation_checker_empty(self):
        from adaptive_crag.reporting import CitationChecker
        checker = CitationChecker({})
        result = checker.check_report("", [])
        self.assertTrue(result["valid"])

    def test_report_builder(self):
        from adaptive_crag.reporting import ReportBuilder
        builder = ReportBuilder()
        bundle = builder.build(
            query="测试",
            report_markdown="# Test",
            task_id="task_001",
        )
        self.assertEqual(bundle.task_id, "task_001")
        self.assertIn("# Test", bundle.report_markdown)


class TestAgents(unittest.TestCase):
    """测试 Agent 模块"""

    def test_extract_json(self):
        from adaptive_crag.agents.base_agent import BaseAgent
        from adaptive_crag.config.llm_config import LLMConfig

        agent = type("TestAgent", (BaseAgent,), {
            "build_system_prompt": lambda self: "",
            "build_user_prompt": lambda self, s: "",
            "parse_response": lambda self, r: {},
            "update_state": lambda self, r, s: {},
        })(LLMConfig())

        json_text = '{"key": "value"}'
        result = agent._extract_json(json_text)
        self.assertEqual(result, {"key": "value"})

        # 测试 markdown 包裹
        md_text = '```json\n{"key": "value"}\n```'
        result = agent._extract_json(md_text)
        self.assertEqual(result, {"key": "value"})


if __name__ == "__main__":
    unittest.main()
