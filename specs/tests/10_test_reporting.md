# 单元测试说明书：报告与引用层 (reporting)

## 对应模块
`10_reporting.md`

## 目标测试文件
```
tests/
    test_reporting/
        __init__.py
        conftest.py              # 示例报告、引用、证据 fixture
        test_report_builder.py   # 报告构建
        test_citation_checker.py # 引用校验
        test_markdown_builder.py # Markdown 格式化
        test_pdf_exporter.py     # PDF 导出（可选，可跳过）
```

## 运行方式
```bash
pytest tests/test_reporting/ -v
```

## 测试策略
- 不依赖 LLM，纯字符串处理和数据结构操作
- 使用预定义的固定报告片段和引用列表
- PDF 导出测试可跳过

## 测试用例清单

### test_report_builder.py

```python
@pytest.fixture
def builder(temp_artifact_dir):
    return ReportBuilder(artifact_manager=MockArtifactManager(temp_artifact_dir))

@pytest.fixture
def sample_report_content():
    return """# 测试报告

## 核心结论
Transformer 使用自注意力机制[cite_001]。

## 数据分析
平均销售额为 100 万元。
"""

@pytest.fixture
def sample_citations():
    return [
        {
            "citation_id": "cite_001",
            "claim": "Transformer 使用自注意力机制",
            "source_file": "attention.pdf",
            "page_num": 3,
            "chunk_id": "chunk_001",
            "source_type": "local_literature",
            "confidence": 0.95
        }
    ]

def test_build_returns_report_bundle(builder, sample_report_content, sample_citations):
    """build 返回 dict 包含 report_markdown/citations/chart_paths/log_paths"""

def test_build_saves_report_file(builder, sample_report_content, sample_citations):
    """build 后 report.md 存在于产物目录"""

def test_build_saves_citations_json(builder, sample_report_content, sample_citations):
    """build 后 citations.json 存在于产物目录"""

def test_citation_footnote_replacement(builder, sample_report_content, sample_citations):
    """[cite_001] 被替换为 [1]"""

def test_footnote_list_at_end(builder, sample_report_content, sample_citations):
    """报告末尾有 [1] 来源的脚注列表"""

def test_build_without_charts(builder, sample_report_content, sample_citations):
    """无图表时 report 不含图片引用"""

def test_build_with_charts(builder, sample_report_content, sample_citations, sample_chart_paths):
    """有图表时 report 包含 ![](...) 格式的图片引用"""

def test_build_empty_report(builder):
    """空报告也能生成标准格式"""
```

### test_citation_checker.py

```python
@pytest.fixture
def valid_mappings():
    return {
        "chunk_001": {"doc_id": "doc_1", "page_num": 3, "filename": "attention.pdf", "text_snippet": "自注意力机制..."},
        "chunk_002": {"doc_id": "doc_1", "page_num": 5, "filename": "attention.pdf", "text_snippet": "多头注意力..."},
    }

@pytest.fixture
def checker(valid_mappings):
    return CitationChecker(citation_mappings=valid_mappings)

def test_check_valid_citation(checker):
    """存在的 chunk_id -> True"""

def test_check_invalid_chunk_id(checker):
    """不存在的 chunk_id -> False"""

def test_check_missing_page_num(checker):
    """page_num 为 None 时（非 PDF 来源）-> True（允许）"""

def test_check_report_all_valid(checker, sample_valid_citations):
    """所有引用有效 -> valid=True"""

def test_check_report_with_invalid(checker, sample_mixed_citations):
    """有无效引用 -> valid=False, invalid_citations 不为空"""

def test_check_report_empty(checker):
    """空引用列表 -> valid=True"""

def test_check_report_contains_claim(checker, sample_valid_citations):
    """每项 invalid_citations 包含 claim 和 reason"""
```

### test_markdown_builder.py

```python
def test_build_report_has_title():
    """build_report 以 # 标题开头"""

def test_build_report_sections_ordered():
    """sections 按传入顺序排列"""

def test_build_report_includes_charts():
    """图表列表中的路径被转为 Markdown 图片格式"""

def test_insert_footnotes():
    """[cite_001] 被替换为 [1]，文末添加脚注"""

def test_insert_footnotes_multiple():
    """多个 [cite_xxx] 编号递增"""

def test_sanitize_unmatched_bold():
    """修复 **text 为 **text**"""

def test_sanitize_broken_table():
    """修复表格缺少的分隔线"""

def test_sanitize_normal_markdown_unchanged():
    """正常 Markdown 不被修改"""
```

### test_pdf_exporter.py（可跳过）

```python
@pytest.mark.skip(reason="需要安装 pandoc 或 weasyprint")
def test_pdf_export_from_markdown():
    """Markdown 文件能被转换为 PDF"""

@pytest.mark.skip(reason="需要安装 pandoc 或 weasyprint")
def test_pdf_export_creates_file():
    """输出文件存在且为 .pdf 扩展名"""
```