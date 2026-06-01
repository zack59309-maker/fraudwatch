"""
报告展示层 — 格式化输出。

formatter:  人类可读报告、CSV、JSON 导出
"""

from .formatter import format_company_report, format_csv, format_json

__all__ = [
    "format_company_report",
    "format_csv",
    "format_json",
]
