"""
财务数据模型定义。

数据单位：所有财务指标均为**亿元**。
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List


@dataclass
class FinancialStatement:
    """一家公司一个财年的财务数据"""

    code: str              # 股票代码
    year: int              # 财年
    revenue: float         # 营业收入（亿元）
    cogs: float            # 营业成本（亿元）
    net_profit: float      # 净利润（亿元）
    operating_cf: float    # 经营活动现金流净额（亿元）
    total_assets: float    # 总资产（亿元）
    current_assets: float  # 流动资产（亿元）
    current_liab: float    # 流动负债（亿元）
    total_liab: float      # 总负债（亿元）
    accounts_recv: float   # 应收账款（亿元）
    depreciation: float    # 折旧（亿元）
    sgna: float            # 销售管理费用（亿元）
    gross_ppe: float       # 固定资产原值（亿元）
    intangibles: float     # 无形资产（亿元）

    @classmethod
    def from_dict(cls, d: dict) -> "FinancialStatement":
        """从字典创建财务数据"""
        return cls(
            code=str(d.get("code", "")),
            year=int(d.get("year", 0)),
            revenue=float(d.get("revenue", 0)),
            cogs=float(d.get("cogs", 0)),
            net_profit=float(d.get("net_profit", 0)),
            operating_cf=float(d.get("operating_cf", 0)),
            total_assets=float(d.get("total_assets", 0)),
            current_assets=float(d.get("current_assets", 0)),
            current_liab=float(d.get("current_liab", 0)),
            total_liab=float(d.get("total_liab", 0)),
            accounts_recv=float(d.get("accounts_recv", 0)),
            depreciation=float(d.get("depreciation", 0)),
            sgna=float(d.get("sgna", 0)),
            gross_ppe=float(d.get("gross_ppe", 0)),
            intangibles=float(d.get("intangibles", 0)),
        )

    def to_dict(self) -> dict:
        """转为字典"""
        return asdict(self)


@dataclass
class CompanyProfile:
    """一家公司的完整档案"""

    code: str
    name: str
    sector: str = ""
    flagged: bool = False
    flag_reason: str = ""
    statements: List[FinancialStatement] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "CompanyProfile":
        """从字典创建公司档案"""
        stmts = [FinancialStatement.from_dict(s) for s in d.get("statements", [])]
        return cls(
            code=str(d.get("code", "")),
            name=str(d.get("name", "")),
            sector=str(d.get("sector", "")),
            flagged=bool(d.get("flagged", False)),
            flag_reason=str(d.get("flag_reason", "")),
            statements=stmts,
        )

    def to_dict(self) -> dict:
        """转为可序列化字典"""
        return asdict(self)

    def __repr__(self) -> str:
        return f"<CompanyProfile {self.code} {self.name}>"
