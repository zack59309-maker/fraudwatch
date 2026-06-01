"""
财务指标计算模块。

基于两家公司的财务报表（连续两个财年），计算用于舞弊检测的各种财务比率。
"""
from typing import Tuple, Optional
from ..data.companies import FinancialStatement, CompanyProfile


def analyze(profile: CompanyProfile) -> dict:
    """
    对公司进行完整的财务分析，返回各项指标。
    """
    if len(profile.statements) < 2:
        return {"error": "需要至少两个连续财年的数据"}

    # 按年份排序（假设 t2 是更近的一年）
    stmts = sorted(profile.statements, key=lambda s: s.year)
    t0 = stmts[-2]  # 前一年
    t1 = stmts[-1]  # 最近一年

    ratios = _calc_ratios(t1)
    changes = _calc_changes(t0, t1)
    benelsh_vars = _calc_beneish_vars(t0, t1)

    return {
        "code": profile.code,
        "name": profile.name,
        "sector": profile.sector,
        "year_t": t1.year,
        "year_t_1": t0.year,
        "ratios": ratios,
        "changes": changes,
        "beneish_vars": benelsh_vars,
    }


def _calc_ratios(fs: FinancialStatement) -> dict:
    """计算最近一年的财务比率"""
    ratios = {}

    # 利润率
    ratios["gross_margin"] = _safe_div(fs.revenue - fs.cogs, fs.revenue)
    ratios["net_margin"] = _safe_div(fs.net_profit, fs.revenue)

    # 资产负债
    ratios["debt_ratio"] = _safe_div(fs.total_liab, fs.total_assets)
    ratios["current_ratio"] = (
        _safe_div(fs.current_assets, fs.current_liab)
        if fs.current_liab != 0 and fs.current_assets != 0
        else None
    )

    # 应收账款占比
    ratios["recv_to_revenue"] = _safe_div(fs.accounts_recv, fs.revenue)

    # 现金流/净利润比 (现金利润比)
    ratios["cf_to_profit"] = _safe_div(fs.operating_cf, fs.net_profit) if fs.net_profit != 0 else None

    # 总资产周转率
    ratios["asset_turnover"] = _safe_div(fs.revenue, fs.total_assets)

    # 杠杆
    ratios["leverage"] = _safe_div(fs.total_assets, fs.total_assets - fs.total_liab)

    # 资产质量
    ratios["current_asset_ratio"] = _safe_div(fs.current_assets, fs.total_assets)

    # SG&A 占比
    ratios["sgna_to_revenue"] = _safe_div(fs.sgna, fs.revenue)

    # 折旧率
    ratios["depr_rate"] = _safe_div(fs.depreciation, fs.gross_ppe) if fs.gross_ppe != 0 else 0

    return ratios


def _calc_changes(t0: FinancialStatement, t1: FinancialStatement) -> dict:
    """计算两年间的变化率"""
    changes = {}

    # 营收增长率
    changes["revenue_growth"] = _safe_div(t1.revenue - t0.revenue, abs(t0.revenue) if t0.revenue != 0 else 1)

    # 净利润增长率
    changes["profit_growth"] = _safe_div(t1.net_profit - t0.net_profit, abs(t0.net_profit) if t0.net_profit != 0 else 1)

    # 经营现金流变化
    changes["cf_growth"] = _safe_div(t1.operating_cf - t0.operating_cf, abs(t0.operating_cf) if t0.operating_cf != 0 else 1)

    # 应收账款增长率 vs 营收增长率
    changes["recv_growth"] = _safe_div(t1.accounts_recv - t0.accounts_recv, abs(t0.accounts_recv) if t0.accounts_recv != 0 else 1)

    # 总资产增长率
    changes["asset_growth"] = _safe_div(t1.total_assets - t0.total_assets, abs(t0.total_assets) if t0.total_assets != 0 else 1)

    # 现金流-利润剪刀差 (变化方向是否一致)
    changes["cf_profit_divergence"] = (
        _safe_div(t1.operating_cf - t0.operating_cf, abs(t0.operating_cf) if t0.operating_cf != 0 else 1)
        - _safe_div(t1.net_profit - t0.net_profit, abs(t0.net_profit) if t0.net_profit != 0 else 1)
    )

    return changes


def _calc_beneish_vars(t0: FinancialStatement, t1: FinancialStatement) -> dict:
    """
    Beneish M-Score 所需的 8 个变量。

    DSRI = 应收账款指数
    GMI  = 毛利率指数
    AQI  = 资产质量指数
    SGI  = 营收增长指数
    DEPI = 折旧指数
    SGAI = 销售管理费用指数
    LVGI = 杠杆指数
    TATA = 总应计/总资产
    """
    vars_ = {}

    # DSRI: 应收账款/营收 (t1) / (t0)
    dsri_t0 = _safe_div(t0.accounts_recv, t0.revenue)
    dsri_t1 = _safe_div(t1.accounts_recv, t1.revenue)
    vars_["DSRI"] = _safe_div(dsri_t1, dsri_t0) if dsri_t0 != 0 else 1

    # GMI: 毛利率 (t0) / 毛利率 (t1)
    gm_t0 = _safe_div(t0.revenue - t0.cogs, t0.revenue)
    gm_t1 = _safe_div(t1.revenue - t1.cogs, t1.revenue)
    vars_["GMI"] = _safe_div(gm_t0, gm_t1) if gm_t1 != 0 else 1

    # AQI: (1 - 流动资产t1/总资产t1 - 固定资产t1/总资产t1) / (1 - 流动资产t0/总资产t0 - 固定资产t0/总资产t0)
    non_current_t1 = 1 - _safe_div(t1.current_assets, t1.total_assets)
    non_current_t0 = 1 - _safe_div(t0.current_assets, t0.total_assets)
    # 对于金融企业（流动/非流动资产定义不同），用无形资产替代
    fixed_ratio_t1 = _safe_div(t1.gross_ppe + t1.intangibles, t1.total_assets)
    fixed_ratio_t0 = _safe_div(t0.gross_ppe + t0.intangibles, t0.total_assets)
    aq_t1 = _safe_div(t1.total_assets - t1.current_assets - t1.gross_ppe, t1.total_assets)
    aq_t0 = _safe_div(t0.total_assets - t0.current_assets - t0.gross_ppe, t0.total_assets)
    vars_["AQI"] = _safe_div(aq_t1, aq_t0) if aq_t0 != 0 else 1

    # SGI: 营收t1/营收t0
    vars_["SGI"] = _safe_div(t1.revenue, t0.revenue) if t0.revenue != 0 else 1

    # DEPI: 折旧率 (t0) / 折旧率 (t1)
    depr_t0 = _safe_div(t0.depreciation, t0.gross_ppe) if t0.gross_ppe != 0 else 0
    depr_t1 = _safe_div(t1.depreciation, t1.gross_ppe) if t1.gross_ppe != 0 else 0
    vars_["DEPI"] = _safe_div(depr_t0, depr_t1) if depr_t1 != 0 else 1

    # SGAI: SG&A/营收 (t1) / (t0)
    sga_t0 = _safe_div(t0.sgna, t0.revenue)
    sga_t1 = _safe_div(t1.sgna, t1.revenue)
    vars_["SGAI"] = _safe_div(sga_t1, sga_t0) if sga_t0 != 0 else 1

    # LVGI: 财务杠杆 (t1) / (t0)
    lev_t0 = _safe_div(t0.total_assets, t0.total_assets - t0.total_liab)
    lev_t1 = _safe_div(t1.total_assets, t1.total_assets - t1.total_liab)
    vars_["LVGI"] = _safe_div(lev_t1, lev_t0) if lev_t0 != 0 else 1

    # TATA: (净利润 - 经营现金流) / 总资产 (t1)
    vars_["TATA"] = _safe_div(t1.net_profit - t1.operating_cf, t1.total_assets)

    return vars_


def _safe_div(a: float, b: float) -> float:
    """安全的除法，避免除零"""
    if b == 0 or b is None:
        return 0.0
    return a / b
