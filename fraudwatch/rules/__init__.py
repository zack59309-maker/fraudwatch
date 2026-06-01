"""
检测规则引擎 — Beneish M-Score + 辅助指标。

m_score:     Beneish M-Score 核心计算
indicators:  财务指标分析（毛利率、应收占比、现金流比等）
engine:      检测引擎，组装所有规则生成最终报告
"""

from .engine import detect
from .m_score import compute_m_score, explain_m_score
from .indicators import analyze as calc_indicators

__all__ = [
    "detect",
    "compute_m_score", "explain_m_score",
    "calc_indicators",
]
