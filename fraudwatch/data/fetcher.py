"""
A 股实时财务数据抓取器。

从东方财富（akshare）拉取真实财务数据，映射为 FinancialStatement 格式，
供 fraudwatch 检测引擎使用。

数据来源（优先级从高到低）：
1. 利润表 + 资产负债表 + 现金流量表（三张表，字段最完整）
2. 财务摘要（备用方案，只有关键指标）

依赖: akshare, pandas, numpy
"""

import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from .companies import FinancialStatement, CompanyProfile

logger = logging.getLogger(__name__)

# ── 工具函数 ─────────────────────────────────────────

def _market_prefix(code: str) -> str:
    """为 A 股代码添加市场标识 (SH/SZ)"""
    code = code.strip()
    if code.startswith(("SH", "SZ")):
        return code
    if code.startswith(("6", "9")):
        return f"SH{code}"
    if code.startswith(("0", "3", "2")):
        return f"SZ{code}"
    return code


def _to_yi(v) -> float:
    """转亿元，akshare 三张报表数据单位是元"""
    if v is None:
        return 0.0
    try:
        v = float(v)
        return round(v / 1e8, 2)
    except (ValueError, TypeError):
        return 0.0


def _find_in_df(df: pd.DataFrame, *keys: str) -> float:
    """在 DataFrame 行中按多个可能的列名取第一个非空值"""
    for k in keys:
        if k in df.index:
            v = df[k]
            if pd.notna(v):
                return _to_yi(v.iloc[0] if hasattr(v, 'iloc') else v)
    return 0.0


def _find_in_series(s: pd.Series, *keys: str, default=0.0) -> float:
    """在 Series 中按多个可能的列名取值"""
    for k in keys:
        if k in s.index:
            v = s[k]
            if pd.notna(v):
                # numpy 标量，直接转
                return _to_yi(float(v))
    return default


# ── 股票信息查询 ─────────────────────────────────────

_STOCK_LIST_CACHE: Optional[pd.DataFrame] = None

def _get_stock_list() -> pd.DataFrame:
    """获取 A 股全量代码-名称对照表"""
    global _STOCK_LIST_CACHE
    if _STOCK_LIST_CACHE is not None:
        return _STOCK_LIST_CACHE
    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        _STOCK_LIST_CACHE = df
        return df
    except Exception as e:
        logger.warning(f"获取股票列表失败: {e}")
        return pd.DataFrame()


def search_stock(query: str) -> List[dict]:
    """
    根据股票代码或名称模糊搜索。
    
    返回：
        [{"code": "600519", "name": "贵州茅台"}, ...]
    """
    df = _get_stock_list()
    if df.empty:
        return []
    
    query = query.strip().upper()
    results = []
    
    # 精确匹配代码
    matched = df[df["code"].astype(str).str.upper() == query]
    if matched.empty:
        # 模糊匹配代码
        matched = df[df["code"].astype(str).str.contains(query, na=False)]
    if matched.empty:
        # 模糊匹配名称
        matched = df[df["name"].str.contains(query, na=False)]
    
    for _, row in matched.head(10).iterrows():
        results.append({
            "code": str(row["code"]),
            "name": str(row["name"]),
        })
    return results


# ── 财务数据抓取（三张表方案） ──────────────────────

def _fetch_name(code: str) -> Optional[str]:
    """通过股票代码反查公司名称"""
    df = _get_stock_list()
    if df.empty:
        return None
    row = df[df["code"].astype(str) == code]
    if row.empty:
        return None
    return str(row.iloc[0]["name"])


def _fetch_sector(market_code: str) -> str:
    """获取公司所属行业"""
    try:
        import akshare as ak
        df = ak.stock_individual_info_em(symbol=market_code)
        for _, row in df.iterrows():
            label = str(row.iloc[0])
            if "行业" in label:
                return str(row.iloc[1])
        return ""
    except Exception:
        return ""


def _get_yearly(df: pd.DataFrame) -> pd.DataFrame:
    """从三张报表中筛选年报（REPORT_TYPE == '年报'）"""
    if df.empty:
        return df
    if "REPORT_TYPE" in df.columns:
        yearly = df[df["REPORT_TYPE"] == "年报"].copy()
        if not yearly.empty:
            yearly = yearly.sort_values("REPORT_DATE", ascending=False)
            return yearly
    # 备用：通过日期过滤
    if "REPORT_DATE" in df.columns:
        yearly = df[df["REPORT_DATE"].astype(str).str.contains(r"12-31|1231", na=False)].copy()
        yearly = yearly.sort_values("REPORT_DATE", ascending=False)
        return yearly
    return df


def _get_year_from_row(row: pd.Series) -> Optional[int]:
    """从一行数据中提取年份"""
    for col in ["REPORT_DATE", "END_DATE", "DATE", "YEAR", "year"]:
        if col in row.index:
            val = str(row[col])
            import re
            m = re.search(r"(\d{4})", val)
            if m:
                return int(m.group(1))
    return None


def fetch_financial_data(code: str) -> Optional[CompanyProfile]:
    """
    从东方财富拉取股票的真实财务数据。
    
    策略：
    1. 优先用 利润表+资产负债表+现金流量表 三张表（字段完整）
    2. 如果三张表拿不到足够数据，回退到财务摘要接口
    """
    import akshare as ak
    market_code = _market_prefix(code)
    
    # 1. 基本信息
    name = _fetch_name(code)
    if not name:
        logger.error(f"无法获取公司 {code} 的基本信息")
        return None
    sector = _fetch_sector(market_code)
    
    # 2. 尝试三张表方案
    try:
        profile = _fetch_from_three_reports(code, market_code, name, sector)
        if profile is not None and len(profile.statements) >= 2:
            return profile
    except Exception as e:
        logger.warning(f"三张表方案失败: {e}")
    
    # 3. 回退到财务摘要
    logger.info(f"回退到财务摘要方案")
    try:
        return _fetch_from_abstract(code, market_code, name, sector)
    except Exception as e:
        logger.error(f"财务摘要方案也失败: {e}")
        return None


def _fetch_from_three_reports(
    code: str, market_code: str, name: str, sector: str
) -> Optional[CompanyProfile]:
    """用利润表+资产负债表+现金流量表构建财务数据"""
    import akshare as ak
    
    # 拉取三张表
    profit_df = ak.stock_profit_sheet_by_report_em(symbol=market_code)
    balance_df = ak.stock_balance_sheet_by_report_em(symbol=market_code)
    cashflow_df = ak.stock_cash_flow_sheet_by_report_em(symbol=market_code)
    
    profit_yearly = _get_yearly(profit_df)
    balance_yearly = _get_yearly(balance_df)
    cashflow_yearly = _get_yearly(cashflow_df)
    
    if len(profit_yearly) < 2:
        return None
    
    # 最近 2 个财年
    stmts = []
    for i in range(2):
        p = profit_yearly.iloc[i]
        b = balance_yearly.iloc[i] if len(balance_yearly) > i else None
        c = cashflow_yearly.iloc[i] if len(cashflow_yearly) > i else None
        
        year = _get_year_from_row(p)
        if not year:
            continue
        
        stmts.append(_build_stmt_from_rows(code, year, p, b, c))
    
    if len(stmts) < 2:
        return None
    
    return CompanyProfile(
        code=code, name=name, sector=sector,
        flagged=False, flag_reason="", statements=stmts,
    )


def _build_stmt_from_rows(
    code: str, year: int,
    profit_row: pd.Series,
    balance_row: Optional[pd.Series],
    cashflow_row: Optional[pd.Series],
) -> FinancialStatement:
    """从三张表的行构建 FinancialStatement"""
    
    # ── 利润表 ──
    revenue = _find_in_series(profit_row,
        "TOTAL_OPERATE_INCOME", "OPERATE_INCOME")
    cogs = _find_in_series(profit_row,
        "TOTAL_OPERATE_COST", "OPERATE_COST")
    net_profit = _find_in_series(profit_row,
        "PARENT_NETPROFIT", "NETPROFIT")
    sale_exp = _find_in_series(profit_row, "SALE_EXPENSE")
    manage_exp = _find_in_series(profit_row, "MANAGE_EXPENSE")
    sgna = round(sale_exp + manage_exp, 2)
    depr = _find_in_series(profit_row,
        "ACF_END_INCOME")  # 折旧摊销一般不在利润表中，用 total compre income 里的
    
    # ── 资产负债表 ──
    total_assets = 0.0
    current_assets = 0.0
    total_liab = 0.0
    current_liab = 0.0
    accounts_recv = 0.0
    gross_ppe = 0.0
    intangibles = 0.0
    
    if balance_row is not None:
        total_assets = _find_in_series(balance_row, "TOTAL_ASSETS")
        current_assets = _find_in_series(balance_row,
            "TOTAL_CURRENT_ASSETS", "CURRENT_ASSET_BALANCE")
        total_liab = _find_in_series(balance_row, "TOTAL_LIABILITIES")
        current_liab = _find_in_series(balance_row,
            "TOTAL_CURRENT_LIAB", "CURRENT_LIAB_BALANCE")
        accounts_recv = _find_in_series(balance_row,
            "ACCOUNTS_RECE", "ACCOUNT_RECEIPT", "NOTE_ACCOUNTS_RECE",
            "ACCOUNTS_RECEIVABLE", "ACCOUNTS_RECEIVABLE_NET")
        gross_ppe = _find_in_series(balance_row,
            "FIXED_ASSET", "FIXED_ASSETS")
        intangibles = _find_in_series(balance_row,
            "INTANGIBLE_ASSET", "INTANGIBLE_ASSETS")
    
    # ── 现金流量表 ──
    operating_cf = 0.0
    if cashflow_row is not None:
        operating_cf = _find_in_series(cashflow_row,
            "NETCASH_OPERATE", "NETCASH_OPERATENOTE",
            "NET_CASH_FLOW_OPERATE", "OPERATE_CASH_FLOW",
            "经营活动产生的现金流量净额")
    
    return FinancialStatement(
        code=code, year=year,
        revenue=revenue, cogs=cogs, net_profit=net_profit,
        operating_cf=operating_cf,
        total_assets=total_assets, current_assets=current_assets,
        current_liab=current_liab, total_liab=total_liab,
        accounts_recv=accounts_recv, depreciation=0.0,
        sgna=sgna, gross_ppe=gross_ppe, intangibles=intangibles,
    )


# ── 备用方案：财务摘要 ──────────────────────────────

def _fetch_from_abstract(
    code: str, market_code: str, name: str, sector: str
) -> Optional[CompanyProfile]:
    """用 stock_financial_abstract 构建（只有关键指标，没有资产负债表明细）"""
    import akshare as ak
    
    df = ak.stock_financial_abstract(symbol=market_code)
    if df.empty:
        return None
    
    # 提取年报列（YYYY1231 格式）
    year_cols = [c for c in df.columns if c not in ("选项", "指标") and str(c).endswith("1231")]
    year_cols.sort(reverse=True)
    
    if len(year_cols) < 2:
        logger.warning(f"财务摘要年报列不足: {year_cols}")
        return None
    
    def _abs_val(keywords, col_name):
        matched = df[df["指标"].str.contains(keywords, na=False)]
        if matched.empty:
            return 0.0
        v = matched.iloc[0].get(col_name, 0)
        return _to_yi(v)
    
    stmts = []
    for col in year_cols[:2]:
        year = int(str(col)[:4])
        
        revenue = _abs_val("营业总收入", col)
        cogs = _abs_val("营业成本", col)
        net_profit = _abs_val("归母净利润", col)
        operating_cf = _abs_val("经营现金流量净额", col)
        # 从净资产+负债估算总资产
        equity = abs(_abs_val("股东权益合计|净资产", col))
        total_liab_approx = abs(_abs_val("总负债|负债合计", col))
        total_assets = round(equity + total_liab_approx, 2) if equity > 0 else 0.0
        
        stmt = FinancialStatement(
            code=code, year=year,
            revenue=revenue, cogs=cogs, net_profit=net_profit,
            operating_cf=operating_cf,
            total_assets=total_assets,
            current_assets=0.0, current_liab=0.0,
            total_liab=0.0, accounts_recv=0.0,
            depreciation=0.0, sgna=0.0,
            gross_ppe=0.0, intangibles=0.0,
        )
        stmts.append(stmt)
    
    if len(stmts) < 2:
        return None
    
    return CompanyProfile(
        code=code, name=name, sector=sector,
        flagged=False, flag_reason="", statements=stmts,
    )
