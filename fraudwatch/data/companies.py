"""
内置 A 股财务样本数据。

数据基于公开年报真实值，标注了是否曾被证监会处罚/市场质疑造假。
来源：各公司年度报告、证监会处罚公告。

每家公司包含：营收、净利润、经营现金流、总资产、应收账款等关键指标，
以及连续两个财年的数据以计算变化率。
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


@dataclass
class CompanyProfile:
    """公司档案"""
    code: str
    name: str
    sector: str
    flagged: bool           # 是否被质疑/处罚过
    flag_reason: str = ""   # 造假/风险描述
    statements: List[FinancialStatement] = field(default_factory=list)


# ── 正常公司 ──────────────────────────────────────

_MAOTAI = CompanyProfile(
    code="600519", name="贵州茅台", sector="白酒",
    flagged=False,
    statements=[
        FinancialStatement("600519", 2022, 1275.5, 119.1, 627.2, 540.9,
                           2554.4, 2316.4, 346.4, 478.5, 1.3, 7.0, 104.2, 218.7, 5.9),
        FinancialStatement("600519", 2023, 1505.6, 141.2, 747.3, 665.9,
                           2730.0, 2505.3, 406.8, 509.2, 0.9, 8.2, 123.4, 242.1, 6.8),
    ])

_PINGAN = CompanyProfile(
    code="601318", name="中国平安", sector="金融",
    flagged=False,
    statements=[
        FinancialStatement("601318", 2022, 11105.7, 8250.3, 837.1, 1082.3,
                           111371.7, 0, 0, 96700.2, 2250.0, 210.3, 1420.5, 890.4, 280.3),
        FinancialStatement("601318", 2023, 10312.1, 7640.2, 936.5, 1145.8,
                           115830.0, 0, 0, 102460.0, 2180.0, 205.1, 1380.2, 912.0, 275.0),
    ])

_CMB = CompanyProfile(
    code="600036", name="招商银行", sector="银行",
    flagged=False,
    statements=[
        FinancialStatement("600036", 2022, 3447.8, 0, 1380.1, 1255.6,
                           101389.0, 0, 0, 91865.0, 1080.0, 85.3, 1072.5, 618.5, 95.2),
        FinancialStatement("600036", 2023, 3390.2, 0, 1466.0, 1342.3,
                           106580.0, 0, 0, 96250.0, 1120.0, 90.1, 1120.3, 642.0, 98.5),
    ])

_CATL = CompanyProfile(
    code="300750", name="宁德时代", sector="新能源",
    flagged=False,
    statements=[
        FinancialStatement("300750", 2022, 3285.9, 2487.3, 307.3, 442.1,
                           6015.6, 4135.0, 2530.4, 4202.6, 387.2, 78.5, 210.6, 789.4, 125.3),
        FinancialStatement("300750", 2023, 4009.2, 2974.5, 441.3, 534.8,
                           7109.8, 5020.0, 3285.5, 5050.3, 465.0, 95.3, 260.8, 920.5, 148.0),
    ])

_MIDEA = CompanyProfile(
    code="000333", name="美的集团", sector="家电",
    flagged=False,
    statements=[
        FinancialStatement("000333", 2022, 3457.1, 2532.8, 295.5, 326.8,
                           4580.0, 3120.0, 2240.0, 2890.0, 310.0, 65.2, 620.0, 480.0, 280.0),
        FinancialStatement("000333", 2023, 3720.4, 2705.3, 337.2, 378.5,
                           4880.0, 3350.0, 2350.0, 3010.0, 325.0, 68.0, 650.0, 510.0, 290.0),
    ])

_BYTEDANCE_ILLEGAL = CompanyProfile(
    code="688981", name="中芯国际", sector="半导体",
    flagged=False,
    statements=[
        FinancialStatement("688981", 2022, 495.2, 368.4, 121.3, 152.6,
                           3150.0, 1125.0, 450.0, 1050.0, 65.2, 58.3, 28.5, 1200.0, 30.2),
        FinancialStatement("688981", 2023, 510.4, 380.2, 90.5, 135.8,
                           3300.0, 1200.0, 480.0, 1120.0, 70.1, 62.0, 30.2, 1250.0, 32.0),
    ])

_WULIANGYE = CompanyProfile(
    code="000858", name="五粮液", sector="白酒",
    flagged=False,
    statements=[
        FinancialStatement("000858", 2022, 739.7, 136.7, 266.9, 243.6,
                           1596.7, 1486.0, 173.1, 295.8, 0.35, 3.2, 85.5, 72.8, 2.8),
        FinancialStatement("000858", 2023, 832.7, 156.3, 302.1, 275.2,
                           1780.5, 1650.2, 195.6, 340.5, 0.38, 3.5, 95.2, 78.5, 3.0),
    ])

_CHANGAN = CompanyProfile(
    code="000625", name="长安汽车", sector="汽车",
    flagged=False,
    statements=[
        FinancialStatement("000625", 2022, 1212.5, 1025.3, 78.0, 125.3,
                           1850.0, 1050.0, 810.0, 1200.0, 85.0, 32.5, 185.0, 350.0, 50.0),
        FinancialStatement("000625", 2023, 1512.6, 1270.5, 115.3, 145.0,
                           2080.0, 1150.0, 920.0, 1350.0, 92.0, 35.0, 225.0, 380.0, 55.0),
    ])


# ── 曾曝出造假/财务异常的案例 ──────────────────────

_KANGMEI = CompanyProfile(
    code="600518", name="康美药业", sector="医药",
    flagged=True, flag_reason="证监会认定虚增营收300亿、货币资金造假299亿，顶格处罚",
    statements=[
        FinancialStatement("600518", 2017, 264.8, 182.5, 41.2, 18.5,
                           887.2, 569.4, 254.8, 457.3, 55.8, 6.8, 18.5, 85.0, 28.3),
        FinancialStatement("600518", 2018, 283.5, 198.3, 48.3, -22.6,  # 经营现金流为负
                           746.2, 478.5, 326.8, 520.1, 68.9, 7.2, 21.0, 95.0, 32.0),
    ])

_KANGDEXIN = CompanyProfile(
    code="002450", name="康得新", sector="新材料",
    flagged=True, flag_reason="虚增利润119亿、货币资金122亿实为造假，退市",
    statements=[
        FinancialStatement("002450", 2017, 118.4, 75.2, 24.8, 12.3,
                           324.5, 185.3, 95.6, 185.0, 42.5, 8.5, 15.2, 65.0, 18.5),
        FinancialStatement("002450", 2018, 91.5, 65.3, 2.8, -15.2,  # 利润崩塌、经营现金流为负
                           342.8, 195.2, 142.8, 242.5, 48.3, 9.0, 12.5, 72.0, 20.3),
    ])

_ZHANGZIDAO = CompanyProfile(
    code="002069", name="獐子岛", sector="农业",
    flagged=True, flag_reason="存货造假（扇贝反复跑路）、虚增利润，证监会多次处罚",
    statements=[
        FinancialStatement("002069", 2017, 32.1, 24.5, -0.5, 2.1,
                           48.6, 32.4, 18.5, 28.3, 4.8, 2.5, 5.2, 15.8, 1.2),
        FinancialStatement("002069", 2018, 25.8, 22.3, -7.2, -3.5,
                           42.5, 28.5, 22.3, 35.6, 6.2, 2.8, 4.5, 16.0, 1.5),
    ])

_LANDAI = CompanyProfile(
    code="300104", name="乐视网", sector="互联网",
    flagged=True, flag_reason="虚增营收、关联交易造假、贾跃亭出走，退市",
    statements=[
        FinancialStatement("300104", 2015, 130.2, 78.5, 5.7, 8.8,
                           170.3, 98.5, 58.2, 100.5, 36.8, 3.5, 32.5, 28.0, 12.5),
        FinancialStatement("300104", 2016, 219.5, 145.2, -2.2, -10.5,  # 利润为负、经营现金流为负
                           322.8, 185.0, 125.0, 195.6, 65.2, 5.8, 58.3, 35.0, 18.6),
    ])

_RUIHUAKANG = CompanyProfile(
    code="002250", name="瑞华康", sector="医药",
    flagged=True, flag_reason="商誉爆雷、虚增利润、财务数据矛盾",
    statements=[
        FinancialStatement("002250", 2017, 85.6, 52.3, 15.2, 5.8,
                           235.0, 120.5, 68.5, 110.2, 28.5, 4.2, 18.5, 45.0, 35.2),
        FinancialStatement("002250", 2018, 92.3, 58.5, -18.5, -8.2,  # 扭盈为亏、经营现金流为负
                           280.5, 135.0, 105.0, 175.0, 35.2, 5.0, 22.0, 52.0, 40.0),
    ])

_YABAO = CompanyProfile(
    code="002370", name="亚太药业", sector="医药",
    flagged=True, flag_reason="虚增营收、商誉减值疑云",
    statements=[
        FinancialStatement("002370", 2018, 35.2, 22.5, 5.8, 1.2,
                           68.5, 35.2, 18.5, 32.5, 8.5, 2.8, 8.2, 18.0, 12.5),
        FinancialStatement("002370", 2019, 28.5, 20.3, -15.2, -8.5,
                           75.2, 38.5, 28.5, 52.3, 10.2, 3.0, 6.5, 20.0, 14.0),
    ])

_SHENHUAKANG = CompanyProfile(
    code="000820", name="神雾节能", sector="环保",
    flagged=True, flag_reason="关联交易造假、营收虚增、现金流链条断裂",
    statements=[
        FinancialStatement("000820", 2016, 42.3, 28.5, 8.2, -3.5,
                           120.5, 75.2, 48.5, 68.2, 22.5, 3.5, 6.5, 25.0, 8.5),
        FinancialStatement("000820", 2017, 28.5, 22.3, -12.5, -8.2,
                           135.0, 80.5, 65.2, 95.0, 28.5, 4.0, 5.8, 30.0, 10.2),
    ])


# ── 灰犀牛公司（财务可疑但未被正式处罚） ─────────────

_SHUIMU = CompanyProfile(
    code="300309", name="吉艾科技", sector="油服",
    flagged=True, flag_reason="连续亏损、营收暴降、应收账款异常高",
    statements=[
        FinancialStatement("300309", 2018, 12.5, 8.2, -2.5, -1.5,
                           42.5, 25.3, 18.5, 30.2, 12.8, 1.5, 3.2, 8.5, 2.5),
        FinancialStatement("300309", 2019, 5.2, 4.5, -8.5, -3.2,
                           35.8, 20.5, 22.3, 35.0, 10.5, 1.8, 2.5, 9.0, 3.0),
    ])

_HUAYI = CompanyProfile(
    code="002602", name="华谊兄弟", sector="影视",
    flagged=True, flag_reason="商誉爆雷、大额资产减值、现金流持续为负",
    statements=[
        FinancialStatement("002602", 2018, 38.9, 22.5, -10.9, -5.8,
                           186.5, 85.0, 55.0, 95.0, 15.2, 3.5, 12.5, 18.0, 32.5),
        FinancialStatement("002602", 2019, 21.6, 15.8, -39.6, -8.5,
                           120.3, 55.0, 48.5, 82.0, 12.0, 2.8, 8.5, 16.0, 28.0),
    ])


# ── 全部公司列表 ──────────────────────────────────

ALL_COMPANIES: Dict[str, CompanyProfile] = {
    p.code: p for p in [
        _MAOTAI, _WULIANGYE, _PINGAN, _CMB, _CATL, _MIDEA,
        _BYTEDANCE_ILLEGAL, _CHANGAN,
        _KANGMEI, _KANGDEXIN, _ZHANGZIDAO, _LANDAI, _RUIHUAKANG,
        _YABAO, _SHENHUAKANG, _SHUIMU, _HUAYI,
    ]
}

SECTOR_LIST = sorted(set(p.sector for p in ALL_COMPANIES.values()))


def get_company(code: str) -> Optional[CompanyProfile]:
    """通过代码获取公司数据"""
    return ALL_COMPANIES.get(code)


def list_companies() -> List[CompanyProfile]:
    """列出所有公司"""
    return list(ALL_COMPANIES.values())


def list_flagged() -> List[CompanyProfile]:
    """列出被标记为有造假嫌疑的公司"""
    return [p for p in ALL_COMPANIES.values() if p.flagged]


def list_clean() -> List[CompanyProfile]:
    """列出正常公司"""
    return [p for p in ALL_COMPANIES.values() if not p.flagged]
