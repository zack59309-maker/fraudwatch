"""
FraudDetector — 主要接口类。

用法：
    from fraudwatch import FraudDetector

    detector = FraudDetector()
    result = detector.analyze("600519")
    result = detector.analyze("600518")  # 康美药业

    results = detector.scan()  # 扫描所有公司
"""
from typing import Optional, List, Dict, Union

from .data.companies import get_company, list_companies, list_flagged, list_clean
from .rules.engine import detect
from .report.formatter import format_company_report, format_csv, format_json


class FraudDetector:
    """财务舞弊检测器"""

    def analyze(self, code: str) -> Optional[dict]:
        """分析单家公司"""
        profile = get_company(code)
        if not profile:
            return None
        return detect(profile)

    def scan(self) -> List[dict]:
        """扫描所有公司"""
        return [detect(p) for p in list_companies()]

    def scan_flagged(self) -> List[dict]:
        """只扫描标记为有风险的公司"""
        return [detect(p) for p in list_flagged()]

    def scan_clean(self) -> List[dict]:
        """只扫描正常公司"""
        return [detect(p) for p in list_clean()]

    def top_by_risk(self, n: int = 5) -> List[dict]:
        """按 M-Score 降序排列（风险最高）
        注意: M-Score 越大风险越高
        """
        results = self.scan()
        results.sort(key=lambda r: -r["m_score"])
        return results[:n]

    def print_report(self, result: dict) -> str:
        """打印人类可读报告"""
        return format_company_report(result)

    def to_csv(self, results: List[dict]) -> str:
        """导出 CSV"""
        return format_csv(results)

    def to_json(self, results: Union[dict, List[dict]]) -> str:
        """导出 JSON"""
        return format_json(results)
