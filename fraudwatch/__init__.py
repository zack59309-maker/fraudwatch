"""
FraudWatch — A股财务舞弊检测工具。

基于 Beneish M-Score 模型，结合多项辅助指标，
分析公司在财务报表中各指标之间的异常关系，
判断是否存在财务舞弊/造假的概率。

主要接口：
    detector = FraudDetector()
    result = detector.analyze("600519")            # 分析内置数据
    result = detector.fetch_and_analyze("茅台")     # 实时抓取并分析
    results = detector.scan()                       # 批量扫描
"""

from .detector import FraudDetector
from .models import FinancialStatement, CompanyProfile

__all__ = [
    "FraudDetector",
    "FinancialStatement",
    "CompanyProfile",
]
