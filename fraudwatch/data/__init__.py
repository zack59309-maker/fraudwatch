"""
数据层 — 内置样本数据 + 实时抓取器。

companies:  内置 17 家 A 股公司样本数据（含造假案例）
fetcher:    akshare 驱动的 A 股财务数据自动抓取
"""

from .companies import (
    get_company, list_companies, list_flagged, list_clean,
    load_from_csv, load_from_json, merge_external,
    SECTOR_LIST, ALL_COMPANIES,
)
from .fetcher import search_stock, fetch_financial_data

__all__ = [
    "get_company", "list_companies", "list_flagged", "list_clean",
    "load_from_csv", "load_from_json", "merge_external",
    "SECTOR_LIST", "ALL_COMPANIES",
    "search_stock", "fetch_financial_data",
]
