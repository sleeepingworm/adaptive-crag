# 模块说明书：报告与引用层 (reporting)

## 所属层级
能力工具层

## 目标目录
`adaptive_crag/reporting/`

生成文件：
```
adaptive_crag/reporting/
    __init__.py             # 导出 ReportBuilder, CitationChecker
    report_builder.py       # 报告构建器
    citation_checker.py     # 引用校验器
    markdown_builder.py     # Markdown 格式化工具
    pdf_exporter.py         # PDF 导出（可选，MVP 可不做）
```

## 依赖模块

- **必须先生成**：`01_schema`（使用 Citation, ReportBundle）
- **必须先生成**：`09_agents`（report_agent 生成报告内容）
- **可选**：`06_sandbox`（读取执行日志和图表）

## 职责边界

**做：**
- 将 report_agent 生成的 Markdown 报告内容整合为标准格式
- 构建 Citation 索引（来源文件、页码、chunk 的映射关系）
- 校验每个引用是否能反查
- 支持导出 Markdown 文件
- 支持导出 PDF（可选）

**不做：**
- 不做 LLM 调用
- 不做图表生成
- 不做文件解析

## 核心接口

### report_builder.py

```python
class ReportBuilder:
    """
    报告构建器。完整的报告由两部分组成：
    1. 报告正文（report_agent 生成的 Markdown）
    2. 引用映射、图表索引、证据包等元信息

    最终产出 ReportBundle。
    """

    def __init__(self, artifact_manager: "ArtifactManager"):
        self.artifact_manager = artifact_manager

    def build(
        self,
        query: str,
        report_markdown: str,
        evidence_set: dict | None,
        execution_artifact: dict | None,
        citations: list[dict],
        chart_paths: list[str],
        log_paths: list[str],
        task_id: str
    ) -> ReportBundle:
        """
        构造完整的 ReportBundle。

        流程:
        1. 将 citations 按文件分组，生成引用索引
        2. 将 report_markdown 中的 [^cite_id] 替换为带页码的脚注
        3. 将图表路径插入报告中（如 ![](charts/xxx.png)）
        4. 保存报告文件到产物目录
        5. 保存 citations.json
        6. 返回 ReportBundle
        """

    def _format_citations(self, citations: list[dict]) -> str:
        """
        将引用列表格式化为可读的引用脚注。
        格式: [1] 文件名, 第 X 页
        """

    def _embed_charts(self, report: str, chart_paths: list[str], artifact_dir: str) -> str:
        """
        将图表路径嵌入 Markdown。
        chart_paths 是绝对路径，需转为相对产物目录的路径。
        插入位置：找到"## 数据分析"或"## 数据图表"标题，在其后插入。
        """
```

### citation_checker.py

```python
class CitationChecker:
    """
    引用校验器。检查报告中的关键结论：
    1. 是否能反查到具体的 Chunk
    2. 引用是否来自已上传的文档
    3. 页码信息是否完整
    """

    def __init__(self, citation_mappings: dict[str, dict]):
        """
        citation_mappings: {chunk_id: {doc_id, page_num, filename, text_snippet}}
        由 ingestion 模块提供。
        """

    def check_report(self, report: str, citations: list[dict]) -> dict:
        """
        检查报告中的所有引用。

        返回:
        {
            "valid": True,                     # 所有引用均可反查
            "total_citations": 10,
            "valid_citations": 9,
            "invalid_citations": [
                {"citation_id": "cite_xxx", "claim": "...", "reason": "chunk_id 不存在"}
            ],
            "unverified_claims": [
                {"claim": "...", "reason": "无引用标注"}
            ]
        }
        """

    def check_citation(self, citation: dict) -> bool:
        """
        检查单条引用。
        - chunk_id 存在于 mappings 中
        - doc_id 匹配
        - page_num 不为空（PDF 来源时）
        """
```

### markdown_builder.py

```python
class MarkdownBuilder:
    """
    Markdown 格式化工具。不依赖 LLM，纯字符串操作。
    """

    @staticmethod
    def build_report(
        title: str,
        sections: list[dict],
        charts: list[str],
        citations: list[dict]
    ) -> str:
        """
        构建标准格式的 Markdown 报告。

        sections: [
            {"heading": "摘要", "content": "..."},
            {"heading": "核心结论", "content": "...", "citations": ["cite_001"]},
            ...
        ]
        """

    @staticmethod
    def insert_footnotes(report: str, citation_map: dict[str, str]) -> str:
        """
        将 report 中的 [cite_id] 替换为 [1][2] 脚注标记，
        并在文末添加脚注列表。
        """

    @staticmethod
    def sanitize_markdown(text: str) -> str:
        """
        清理 LLM 输出中的异常 Markdown：
        - 修复嵌套不匹配的 **
        - 修复表格格式
        - 确保链接格式正确
        """
```

### pdf_exporter.py（可选，MVP 可跳过）

```python
class PDFExporter:
    """
    将 Markdown 报告转换为 PDF。
    MVP 阶段可用 pandoc 或 weasyprint。
    """

    @staticmethod
    def from_markdown(md_path: str, output_path: str) -> str:
        """
        读取 Markdown 文件，生成 PDF。
        返回 PDF 路径。
        """
```

## 报告存储格式

产物目录结构：
```
data/artifacts/{task_id}/
    report.md               # 最终报告 (Markdown)
    report.pdf              # PDF 版本（可选）
    citations.json           # 引用映射
    evidence.json            # 证据快照
    charts/                  # 图表
        chart_1.png
        chart_2.png
    logs/                    # 执行日志
        event_log.jsonl
        execution_stdout.txt
```

citations.json 格式：
```json
[
    {
        "citation_id": "cite_001",
        "claim": "Transformer 在长序列建模中优于 RNN",
        "source_file": "attention_is_all_you_need.pdf",
        "page_num": 3,
        "chunk_id": "chunk_abc123",
        "source_type": "local_literature",
        "confidence": 0.92
    }
]
```

## 与上下游模块的对接

- **上游调用方**：LangGraph 的 report_node 和 validate_node
- **上游输入**：report_agent 生成的报告、evidence_set、execution_artifact
- **下游消费方**：Streamlit 页面展示
- **数据流向**：`report_agent -> ReportBuilder.build() -> report.md + citations.json`

## 测试要点

- 空报告也能生成标准格式（不含数据章节）
- citations.json 格式正确，每个 citation 包含必填字段
- 引用替换后报告中的脚注编号与文末列表一致
- 图表嵌入后 Markdown 路径正确
- CitationChecker 能正确识别缺失的引用