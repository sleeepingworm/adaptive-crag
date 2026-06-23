"""
文本清洗工具：去除页眉页脚、乱码、多余空白。
"""

import re


def clean_text(raw_text: str, doc_type: str = "txt") -> str:
    """
    清洗文本。
    - 去除连续空行（保留单空行分段）
    - 去除不可见字符
    - 统一换行符为 \\n
    - PDF 文本额外处理页眉页脚

    不改变语义内容。
    """
    # 统一换行符
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")

    # 去除不可见字符（保留换行和制表符）
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

    # 去除连续空行（保留最多一个空行）
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 去除首尾空白
    text = text.strip()

    # PDF 额外处理
    if doc_type == "pdf":
        text = _clean_pdf_specific(text)

    return text


def clean_pdf_page_text(page_text: str) -> str:
    """
    对单页 PDF 文本做精细清洗。
    - 去除页码行
    - 去除页眉/页脚（短行、重复模式）
    """
    lines = page_text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # 跳过页码行（纯数字或 "— X —" 格式）
        if re.match(r"^\s*[-—]*\s*\d+\s*[-—]*\s*$", stripped):
            continue

        # 跳过过短的页眉/页脚行（< 5 字符且不含中文/英文词）
        if len(stripped) < 5 and not re.search(r"[\u4e00-\u9fff\w]{2,}", stripped):
            continue

        # 跳过常见的页眉页脚模式
        skip_patterns = [
            r"^\d+\s*of\s*\d+$",     # "1 of 10"
            r"^Page\s+\d+$",           # "Page 1"
            r"^\d+/\d+$",             # "1/10"
            r"^www\.",                 # 网址开头
        ]
        if any(re.match(p, stripped, re.IGNORECASE) for p in skip_patterns):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _clean_pdf_specific(text: str) -> str:
    """PDF 文本的特殊清洗"""
    lines = text.split("\n")
    # 去除重复页眉（连续出现 3 次以上的相同短行）
    from collections import Counter
    short_lines = [l.strip() for l in lines if len(l.strip()) < 30 and l.strip()]
    line_counts = Counter(short_lines)
    repeated_headers = {line for line, count in line_counts.items() if count >= 3}

    if repeated_headers:
        filtered = [l for l in lines if l.strip() not in repeated_headers]
        text = "\n".join(filtered)

    return text
