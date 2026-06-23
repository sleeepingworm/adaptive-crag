"""
数据集分析工具：对 CSV/Excel 做字段分析和数据摘要。
"""

import os
from adaptive_crag.schema import DatasetProfile


def profile_csv(csv_path: str) -> DatasetProfile:
    """
    分析 CSV 文件：
    - 行数、列数
    - 每列名称、类型、缺失值数量
    - 前 5 行样例
    返回 DatasetProfile。
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("需要安装 pandas: pip install pandas")

    df = pd.read_csv(csv_path, nrows=1000)  # 最多读取 1000 行预览
    filename = os.path.basename(csv_path)

    columns = []
    numeric_cols = []
    categorical_cols = []

    for col in df.columns:
        col_info = {
            "name": str(col),
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
            "sample": df[col].dropna().head(5).tolist(),
        }
        columns.append(col_info)

        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(str(col))
        else:
            categorical_cols.append(str(col))

    return DatasetProfile(
        file_path=csv_path,
        filename=filename,
        row_count=len(df),
        column_count=len(df.columns),
        columns=columns,
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        has_header=True,
    )


def profile_excel(excel_path: str, sheet_name: str | None = None) -> DatasetProfile:
    """
    分析 Excel 文件，同上。
    默认读取第一个 sheet。
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("需要安装 pandas: pip install pandas")

    df = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=1000)
    filename = os.path.basename(excel_path)

    columns = []
    numeric_cols = []
    categorical_cols = []

    for col in df.columns:
        col_info = {
            "name": str(col),
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
            "sample": df[col].dropna().head(5).tolist(),
        }
        columns.append(col_info)

        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(str(col))
        else:
            categorical_cols.append(str(col))

    return DatasetProfile(
        file_path=excel_path,
        filename=filename,
        row_count=len(df),
        column_count=len(df.columns),
        columns=columns,
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        has_header=True,
    )
