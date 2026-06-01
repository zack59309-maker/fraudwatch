"""
舞弊预警信号引擎。

综合 M-Score + 多个财务异常信号，输出风险等级和详细解释。
"""

from .indicators import analyze as calc_indicators
from .m_score import compute_m_score, explain_m_score


def detect(profile) -> dict:
    """
    对公司执行全面舞弊检测。

    返回：
    {
        "code": "600519",
        "name": "贵州茅台",
        "risk_level": "低风险|中风险|高风险",
        "m_score": -2.85,
        "signal_count": 0,
        "signals": [...],
        "details": { ... }
    }
    """
    analysis = calc_indicators(profile)

    signals = []

    # ── 1. M-Score ──
    m = compute_m_score(analysis["beneish_vars"])
    m_result = explain_m_score(m)
    if m_result["signal"]:
        signals.append({
            "name": "Beneish M-Score",
            "severity": m_result["level"],
            "value": m,
            "detail": m_result["detail"],
        })

    # ── 2. 现金流-利润背离 ──
    cf_to_profit = analysis["ratios"].get("cf_to_profit")
    if cf_to_profit is not None and cf_to_profit < 0.3:
        signals.append({
            "name": "现金流远低于利润",
            "severity": "中风险" if cf_to_profit > 0 else "高风险",
            "value": cf_to_profit,
            "detail": f"经营现金流/净利润比率 = {cf_to_profit:.2f}，利润质量存疑",
        })

    # ── 3. 应收账款异常 ──
    recv_ratio = analysis["ratios"].get("recv_to_revenue", 0)
    if recv_ratio > 0.3:
        signals.append({
            "name": "应收账款比例过高",
            "severity": "高风险" if recv_ratio > 0.5 else "中风险",
            "value": recv_ratio,
            "detail": f"应收账款/营收 = {recv_ratio:.2%}，需关注营收质量",
        })

    # ── 4. 营收增长 vs 应收增长背离 ──
    rev_growth = analysis["changes"].get("revenue_growth", 0)
    recv_growth = analysis["changes"].get("recv_growth", 0)
    if recv_growth > rev_growth + 0.2 and rev_growth > 0:
        signals.append({
            "name": "应收增长远超营收增长",
            "severity": "高风险",
            "value": recv_growth - rev_growth,
            "detail": f"应收增速({recv_growth:.1%}) 远超营收增速({rev_growth:.1%})",
        })

    # ── 5. 利润快速增长但现金流下降 ──
    profit_growth = analysis["changes"].get("profit_growth", 0)
    cf_growth = analysis["changes"].get("cf_growth", 0)
    if profit_growth > 0.2 and cf_growth < -0.1:
        signals.append({
            "name": "利润增长但现金流下降",
            "severity": "高风险",
            "value": profit_growth - cf_growth,
            "detail": f"净利润增速 {profit_growth:.1%} 但现金流增速 {cf_growth:.1%}，严重背离",
        })

    # ── 6. 总资产高速扩张 ──
    asset_growth = analysis["changes"].get("asset_growth", 0)
    if asset_growth > 0.5:
        signals.append({
            "name": "资产高速扩张",
            "severity": "中风险",
            "value": asset_growth,
            "detail": f"总资产增长率 {asset_growth:.1%}，警惕过度扩张",
        })

    # ── 7. 净利润为负 ──
    if analysis["ratios"].get("net_margin", 0) < 0:
        signals.append({
            "name": "净利润为负",
            "severity": "高风险",
            "value": analysis["ratios"]["net_margin"],
            "detail": "公司处于亏损状态",
        })

    # ── 8. 经营现金流为负 ──
    # Need to check the raw operating_cf from the most recent statement
    raw_cf = profile.statements[-1].operating_cf
    if raw_cf < 0:
        signals.append({
            "name": "经营现金流为负",
            "severity": "高风险",
            "value": raw_cf,
            "detail": f"经营活动现金流净额 {raw_cf} 亿元，造血能力不足",
        })

    # ── 综合评级 ──
    high_risk = sum(1 for s in signals if s["severity"] == "高风险")
    med_risk = sum(1 for s in signals if s["severity"] == "中风险")

    if high_risk >= 3:
        risk_level = "高风险"
    elif high_risk >= 1 or med_risk >= 2:
        risk_level = "中风险"
    elif m_result["level"] == "高风险":
        risk_level = "高风险"
    elif m_result["level"] == "中风险":
        risk_level = "中风险"
    else:
        risk_level = "低风险"

    return {
        "code": profile.code,
        "name": profile.name,
        "sector": profile.sector,
        "flagged": profile.flagged,
        "flag_reason": profile.flag_reason,
        "risk_level": risk_level,
        "m_score": m,
        "signal_count": len(signals),
        "signals": signals,
        "details": {
            "beneish_vars": analysis["beneish_vars"],
            "ratios": analysis["ratios"],
            "changes": analysis["changes"],
        },
    }
