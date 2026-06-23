# 单元测试说明书：文件解析与索引 (ingestion)

## 对应模块
`03_ingestion.md`

## 目标测试文件
```
tests/
    test_ingestion/
        __init__.py
        conftest.py              # 测试用 PDF/TXT/MD 文件 fixture
        test_document_loader.py  # 文件读取
        test_text_cleaner.py     # 文本清洗
        test_chunker.py          # 文本切片
        test_citation_mapper.py  # 页码映射
        test_dataset_profiler.py # 表格摘要
        test_pipeline.py         # IngestionPipeline 集成测试
```

## 运行方式
```bash
pytest tests/test_ingestion/ -v
```

## 测试依赖
- 需要安装 PyMuPDF (fitz)、pandas、openpyxl
- 需要在 tests 目录下创建测试用文件（见 conftest.py）

## 测试文件资源

conftest.py 需要生成以下临时测试文件：

```
tests/fixtures/
    sample.txt              # 3 段文字
    sample.md               # 3 个标题+内容
    sample_3page.pdf        # 3 页 PDF（每页不同内容，包含页码文字）
    sample_10page.pdf       # 10 页 PDF（用于长时间测试）
    sample_empty.pdf        # 空 PDF（无文字）
    sample_data.csv         # 5 行 3 列数据
    sample_data.xlsx        # 同上，Excel 格式
```

PDF 生成方案：用 `reportlab` 或 `fpdf` 在测试中临时生成，不要提交二进制文件到版本控制。

## 测试用例清单

### test_document_loader.py

```python
def test_load_txt(sample_txt):
    """TXT 文件能正确读取，返回 (Document, raw_text)"""

def test_load_markdown(sample_md):
    """MD 文件能正确读取"""

def test_load_pdf(sample_3page_pdf):
    """PDF 能逐页解析，返回三页内容"""

def test_load_pdf_empty(sample_empty_pdf):
    """空 PDF 返回空文本，不崩溃"""

def test_load_unsupported_format():
    """不支持的文件格式抛出明确的 ValueError"""

def test_document_metadata_correct(sample_txt):
    """返回的 Document 包含正确的 filename/file_size/file_hash/doc_type"""

def test_load_large_text(sample_10page_pdf):
    """大文件不崩溃，能正常读取"""
```

### test_text_cleaner.py

```python
def test_remove_consecutive_blank_lines():
    """连续 3 个空行 -> 保留 1 个空行"""

def test_remove_invisible_chars():
    """\x00\x01\x02 等不可见字符被移除"""

def test_unify_newlines():
    """\r\n 和 \r 统一转换为 \n"""

def test_remove_page_numbers_clean_pdf():
    """clean_pdf_page_text 去除独立的页码数字行"""

def test_clean_empty_text():
    """空字符串返回空字符串"""

def test_clean_only_invisible_chars():
    """只有不可见字符时返回空字符串"""

def test_clean_normal_text_unchanged():
    """正常文本不被修改"""
```

### test_chunker.py

```python
def test_chunk_by_paragraph():
    """3 段文本 -> 返回 3 个 chunk"""

def test_chunk_by_heading():
    """3 个标题+内容 -> 返回 3 个 chunk，每个 chunk.heading 正确"""

def test_chunk_long_paragraph():
    """超过 max_tokens 的段落被拆分成多个 chunk，strategy=FIXED_TOKEN"""

def test_chunk_pdf_3pages(sample_3page_pdf):
    """3 页 PDF -> 至少 3 个 chunk，每个 chunk.page_num 正确"""

def test_chunk_pdf_no_text(sample_empty_pdf):
    """空 PDF -> 空列表，不崩溃"""

def test_chunk_empty_text():
    """空文本 -> 空列表"""

def test_chunk_max_tokens_respected():
    """max_tokens=50 时，单个 chunk 的 token_count 不超过 60（含重叠容忍）"""

def test_chunk_token_count_estimate():
    """token_count 字段不为 0"""
```

### test_citation_mapper.py

```python
def test_build_page_mapping_basic(sample_chunks, sample_raw_text):
    """映射包含所有 chunk，每个 PageMapping 有 chunk_id/doc_id/page_num"""

def test_citation_mapper_coverage():
    """所有 chunk 都在映射表中"""

def test_citation_mapper_char_position():
    """start_char 和 end_char 在 raw_text 范围内"""
```

### test_dataset_profiler.py

```python
def test_profile_csv_basic(sample_csv):
    """
    DatasetProfile 包含:
    - row_count == 5
    - column_count == 3
    - columns 包含 name/dtype/missing/sample
    """

def test_profile_csv_with_missing_values():
    """包含空值的 CSV，missing 字段不为 0"""

def test_profile_excel_basic(sample_xlsx):
    """Excel 文件分析结果与 CSV 一致"""

def test_profile_empty_csv():
    """只有表头的 CSV，row_count==0，不崩溃"""

def test_profile_csv_no_header():
    """无表头 CSV 也能生成 profile，columns 用默认列名"""
```

### test_pipeline.py

```python
def test_pipeline_txt(test_pipeline, sample_txt):
    """IngestionPipeline.process(txt) 返回包含 document/chunks 的 dict"""

def test_pipeline_pdf(test_pipeline, sample_3page_pdf):
    """PDF 处理后 chunks 中的 chunk 都有 page_num"""

def test_pipeline_csv(test_pipeline, sample_csv):
    """CSV 处理后包含 profile"""

def test_pipeline_excel(test_pipeline, sample_xlsx):
    """Excel 处理后包含 profile"""

def test_pipeline_invalid_file(test_pipeline):
    """不存在的文件路径抛出 FileNotFoundError"""

def test_pipeline_chunk_count(test_pipeline, sample_3page_pdf):
    """PDF 处理后 chunk 数量 > 0"""
```