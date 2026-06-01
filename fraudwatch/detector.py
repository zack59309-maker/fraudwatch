"""
FraudDetector — 主要接口类。

用法：
    from fraudwatch import FraudDetector

    detector = FraudDetector()

    # 分析内置数据
    result = detector.analyze("600519")
    result = detector.analyze("600518")  # 康美药业

    # 自动从网络抓取真实 A 股数据
    result = detector.fetch_and_analyze("600519")
    result = detector.fetch_and_analyze("茅台")
    result = detector.fetch_and_analyze("宁德时代")

    # 扫描所有内置公司
    results = detector.scan()

    # 外部导入
    detector.load_csv("my_companies.csv")
    detector.load_json("my_companies.json")
    result = detector.analyze("000001")
"""
from typing import Optional, List, Dict, Union

from .data.companies import (
    get_company, list_companies, list_flagged, list_clean,
    load_from_csv, load_from_json, merge_external, CompanyProfile,
)
from .data.fetcher import search_stock, fetch_financial_data
from .rules.engine import detect
from .report.formatter import format_company_report, format_csv, format_json


class FraudDetector:
    """财务舞弊检测器"""

    def __init__(self):
        self._external_companies: Dict[str, CompanyProfile] = {}

    def analyze(self, code: str) -> Optional[dict]:
        """分析单家公司（内置 + 已导入的外部数据）"""
        profile = get_company(code)
        if not profile:
            profile = self._external_companies.get(code)
        if not profile:
            return None
        return detect(profile)

    def fetch_and_analyze(self, query: str) -> Optional[dict]:
        """
        从网络抓取并分析 A 股公司。
        支持股票代码或名称（如 "600519" 或 "茅台"）。
        """
        # 先尝试当成代码直接抓取
        profile = fetch_financial_data(query)
        if profile is not None:
            return detect(profile)

        # 失败了，按名称搜索
        results = search_stock(query)
        if not results:
            return None

        # 用第一个结果尝试抓取
        code = results[0]["code"]
        profile = fetch_financial_data(code)
        if profile is None:
            return None

        result = detect(profile)
        result["_fetched_name"] = results[0]["name"]
        return result

    def scan(self) -> List[dict]:
        """扫描所有公司（内置 + 已导入的外部数据）"""
        all_profiles = list_companies() + list(self._external_companies.values())
        return [detect(p) for p in all_profiles]

    def scan_flagged(self) -> List[dict]:
        """只扫描标记为有风险的公司"""
        all_profiles = list_flagged() + [
            p for p in self._external_companies.values() if p.flagged
        ]
        return [detect(p) for p in all_profiles]

    def scan_clean(self) -> List[dict]:
        """只扫描正常公司"""
        all_profiles = list_clean() + [
            p for p in self._external_companies.values() if not p.flagged
        ]
        return [detect(p) for p in all_profiles]

    def top_by_risk(self, n: int = 5) -> List[dict]:
        """按 M-Score 降序排列（风险最高）"""
        results = self.scan()
        results.sort(key=lambda r: -r["m_score"])
        return results[:n]

    # ── 外部数据导入 ──────────────────────────────

    def add_company(self, profile: CompanyProfile) -> None:
        """手动添加一家公司"""
        self._external_companies[profile.code] = profile

    def load_csv(self, path: str) -> int:
        """从 CSV 文件加载公司数据，返回加载的公司数量"""
        companies = load_from_csv(path)
        self._external_companies.update(companies)
        return len(companies)

    def load_json(self, path: str) -> int:
        """从 JSON 文件加载公司数据，返回加载的公司数量"""
        companies = load_from_json(path)
        self._external_companies.update(companies)
        return len(companies)

    def merge_external(self) -> int:
        """将外部数据永久合并到内置数据库"""
        return merge_external(self._external_companies.copy())

    def external_companies(self) -> Dict[str, CompanyProfile]:
        """返回已导入的外部公司"""
        return dict(self._external_companies)

    def clear_external(self) -> None:
        """清除已导入的外部数据"""
        self._external_companies.clear()

    # ── 输出 ──────────────────────────────────────

    def print_report(self, result: dict) -> str:
        """打印人类可读报告"""
        return format_company_report(result)

    def to_csv(self, results: List[dict]) -> str:
        """导出 CSV"""
        return format_csv(results)

    def to_json(self, results: Union[dict, List[dict]]) -> str:
        """导出 JSON"""
        return format_json(results)
