"""FraudWatch 单元测试"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fraudwatch import FraudDetector
from fraudwatch.data.companies import get_company, list_companies, list_flagged, list_clean
from fraudwatch.rules.m_score import compute_m_score, explain_m_score
from fraudwatch.rules.indicators import analyze as calc_indicators


def test_detector_imports():
    """验证模块可以正确导入"""
    detector = FraudDetector()
    assert detector is not None


def test_analyze_normal():
    """正常公司应输出低风险"""
    detector = FraudDetector()
    result = detector.analyze("600519")  # 贵州茅台
    assert result is not None
    assert result["code"] == "600519"
    assert result["name"] == "贵州茅台"
    assert result["risk_level"] == "低风险"
    assert result["signal_count"] == 0


def test_analyze_flagged():
    """造假公司应检测到信号"""
    detector = FraudDetector()
    result = detector.analyze("600518")  # 康美药业
    assert result is not None
    assert result["flag_reason"] != ""
    assert result["signal_count"] >= 1


def test_analyze_unknown():
    """未知代码应返回 None"""
    detector = FraudDetector()
    result = detector.analyze("999999")
    assert result is None


def test_scan_count():
    """scan 应返回 17 家公司"""
    detector = FraudDetector()
    results = detector.scan()
    assert len(results) == 17


def test_flagged_count():
    """标记为有风险的公司应为 9 家"""
    flagged = list_flagged()
    assert len(flagged) == 9


def test_clean_count():
    """正常公司应为 8 家"""
    clean = list_clean()
    assert len(clean) == 8


def test_all_companies_have_two_years():
    """每家公司应有 2 个财年的数据"""
    for c in list_companies():
        assert len(c.statements) == 2, f"{c.code} {c.name} 数据缺失"


def test_m_score_formula():
    """M-Score 计算正确性"""
    profile = get_company("600519")
    analysis = calc_indicators(profile)
    bv = analysis["beneish_vars"]
    m = compute_m_score(bv)

    # 茅台应该远低于 -2.22
    assert m < -2.22, f"M-Score for 茅台 should be negative, got {m}"

    # 验证各变量在合理范围（AQI 允许为负，如轻资产公司非流动资产增加）
    for k in ["DSRI", "GMI", "SGI", "DEPI", "SGAI", "LVGI"]:
        assert 0 < bv.get(k, 0) < 10, f"{k} 异常: {bv.get(k)}"
    assert -10 < bv.get("AQI", 0) < 10, f"AQI 异常: {bv.get('AQI')}"


def test_m_score_threshold():
    """M-Score 阈值分类"""
    # 低风险
    low = explain_m_score(-3.0)
    assert low["level"] == "低风险"
    assert not low["signal"]

    # 灰色区域
    mid = explain_m_score(-2.0)
    assert mid["level"] == "中风险"
    assert mid["signal"]

    # 高风险
    high = explain_m_score(-1.5)
    assert high["level"] == "高风险"
    assert high["signal"]


def test_top_by_risk():
    """Top N 风险排名"""
    detector = FraudDetector()
    top = detector.top_by_risk(3)
    assert len(top) == 3
    # M-Score 应递减（从高到低）
    assert top[0]["m_score"] >= top[1]["m_score"] >= top[2]["m_score"]


def test_indicators_consistency():
    """指标计算应一致"""
    profile = get_company("000858")  # 五粮液
    analysis = calc_indicators(profile)
    ratios = analysis["ratios"]

    # 白酒毛利率应该很高
    assert ratios["gross_margin"] > 0.7, f"五粮液毛利率异常: {ratios['gross_margin']}"

    # 白酒应收占比应该很低
    assert ratios["recv_to_revenue"] < 0.01, f"五粮液应收占比异常: {ratios['recv_to_revenue']}"
