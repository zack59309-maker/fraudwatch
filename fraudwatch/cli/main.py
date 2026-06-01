"""
FraudWatch CLI — 命令行入口。

用法：
  python -m fraudwatch analyze   <代码>    分析内置数据中的公司
  python -m fraudwatch fetch     <代码/名称>  从东方财富抓取并分析真实 A 股公司
  python -m fraudwatch scan                扫描所有内置公司
  python -m fraudwatch list                列出所有内置公司
  python -m fraudwatch top     [N]          风险最高的 N 家
  python -m fraudwatch import  <文件路径>     从 CSV/JSON 导入公司数据
"""

import sys
import argparse

from .. import FraudDetector
from ..data.companies import get_company, list_companies


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fraudwatch",
        description="FraudWatch — A股财务舞弊检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", default="scan",
                        choices=["analyze", "fetch", "scan", "list", "top", "import", "help"],
                        help="命令")
    parser.add_argument("args", nargs="*", help="参数")
    return parser


_HELP_TEXT = """\
FraudWatch — A股财务舞弊检测工具

用法:
  python -m fraudwatch analyze   <代码>        分析内置公司
  python -m fraudwatch fetch     <代码/名称>    实时抓取并分析 A 股公司
  python -m fraudwatch scan                    扫描所有内置公司
  python -m fraudwatch list                    列出所有内置公司
  python -m fraudwatch top     [N]             风险最高的 N 家
  python -m fraudwatch import  <文件>          从 CSV/JSON 导入

示例:
  python -m fraudwatch analyze 600519          # 分析贵州茅台
  python -m fraudwatch analyze 600518          # 分析康美药业
  python -m fraudwatch fetch 600519            # 抓取并分析贵州茅台
  python -m fraudwatch fetch 茅台              # 按名称搜索并分析
  python -m fraudwatch scan                    # 扫描全部 17 家内置公司
  python -m fraudwatch top 5                   # 风险最高的 5 家
  python -m fraudwatch import data.csv         # 从 CSV 导入
"""


def main():
    parser = _build_parser()
    opts = parser.parse_args()

    cmd = opts.command
    args = opts.args

    if cmd == "help" or cmd not in ("analyze", "fetch", "scan", "list", "top", "import"):
        print(_HELP_TEXT)
        return

    dispatch = {
        "list": _cmd_list,
        "top": _cmd_top,
        "analyze": _cmd_analyze,
        "fetch": _cmd_fetch,
        "import": _cmd_import,
        "scan": _cmd_scan,
    }
    dispatch[cmd](args)


# ── 命令实现 ──────────────────────────────────────


def _cmd_list(_args):
    """列出所有内置公司"""
    companies = list_companies()
    print(f"\n{'='*70}")
    print(f"  FraudeWatch 公司列表 — 共 {len(companies)} 家")
    print(f"{'='*70}")
    print(f"{'代码':8s} {'名称':16s} {'行业':10s} {'标记':6s}")
    print(f"{'-'*8} {'-'*16} {'-'*10} {'-'*6}")

    flagged_count = 0
    for c in companies:
        mark = "⚠️" if c.flagged else "  "
        if c.flagged:
            flagged_count += 1
        print(f"{c.code:8s} {c.name:16s} {c.sector:10s} {mark:6s}")

    print(f"{'='*70}")
    print(f"  正常: {len(companies) - flagged_count} | 标记: {flagged_count}")
    print()


def _cmd_top(args):
    """风险最高的 N 家"""
    n = 5
    if args:
        try:
            n = int(args[0])
        except ValueError:
            pass

    detector = FraudDetector()
    results = detector.top_by_risk(n)

    print(f"{'='*70}")
    print(f"  FraudWatch 风险排名 — Top {n}")
    print(f"{'='*70}")
    print(f"{'排名':4s} {'代码':8s} {'名称':16s} {'M-Score':10s} {'风险':8s} {'信号':4s}")
    print(f"{'-'*4} {'-'*8} {'-'*16} {'-'*10} {'-'*8} {'-'*4}")

    icon_map = {"低风险": "✅", "中风险": "⚠️", "高风险": "🚨"}
    for i, r in enumerate(results, 1):
        print(f"{i:<4d} {r['code']:8s} {r['name']:16s} "
              f"{r['m_score']:<10.4f} {icon_map.get(r['risk_level'], '❓')} {r['risk_level']:6s} "
              f"{r['signal_count']:<4d}")

    print(f"{'='*70}")


def _cmd_analyze(args):
    """分析一家内置公司"""
    if not args:
        print("❌ 请指定股票代码，如: python -m fraudwatch analyze 600519")
        return

    code = args[0]
    profile = get_company(code)
    if not profile:
        print(f"❌ 未找到公司: {code}")
        print(f"   可用: 600519, 600036, 300750, 000858, 600518, 002450, ...")
        return

    detector = FraudDetector()
    result = detector.analyze(code)
    from ..report.formatter import format_company_report, format_json
    print(format_company_report(result))

    if "--json" in args or "-j" in args:
        print("\n=== JSON ===")
        print(format_json(result))


def _cmd_fetch(args):
    """从东方财富抓取真实 A 股公司数据并检测"""
    if not args:
        print("❌ 请指定股票代码或名称，如:")
        print("   python -m fraudwatch fetch 600519")
        print("   python -m fraudwatch fetch 茅台")
        return

    from ..data.fetcher import search_stock, fetch_financial_data
    from ..report.formatter import format_company_report

    query = " ".join(args)
    print(f"🔍 正在搜索: {query} ...")

    results = search_stock(query)
    if not results:
        print(f"❌ 未找到股票: {query}")
        return

    if len(results) > 1:
        print(f"⚠️  找到多个匹配，使用第一个:")
        for r in results:
            print(f"   {r['code']} - {r['name']}")
        print()

    target = results[0]
    code = target["code"]

    print(f"📥 正在抓取 {target['name']}({code}) 的财务数据...")
    import time
    start = time.time()

    profile = fetch_financial_data(code)
    elapsed = time.time() - start

    if profile is None:
        print(f"❌ 抓取失败，请检查股票代码是否正确")
        return

    print(f"✅ 抓取完成 ({elapsed:.1f}s)，共 {len(profile.statements)} 个财年数据\n")

    detector = FraudDetector()
    result = detector.analyze(code)  # 内置数据
    # 但如果是从网络抓取的，要用不同的路径
    # 直接使用 rules.engine.detect
    from ..rules.engine import detect
    result = detect(profile)
    print(format_company_report(result))

    print("提示: 用 --json 或 -j 可输出 JSON 格式")


def _cmd_import(args):
    """从 CSV/JSON 导入公司数据"""
    if not args:
        print("❌ 请指定文件路径")
        print("   用法: python -m fraudwatch import <data.csv|data.json>")
        return

    import os
    path = args[0]
    if not os.path.exists(path):
        print(f"❌ 文件不存在: {path}")
        return

    from ..data.companies import load_from_csv, load_from_json, merge_external

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".csv":
            companies = load_from_csv(path)
        elif ext == ".json":
            companies = load_from_json(path)
        else:
            print(f"❌ 不支持的文件格式: {ext}（支持 .csv 和 .json）")
            return
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return

    if not companies:
        print("⚠️ 文件中没有有效公司数据")
        return

    n = merge_external(companies)
    print(f"✅ 成功导入 {len(companies)} 家公司（新增 {n} 家）")
    print(f"   现在共有 {len(list_companies())} 家公司在数据库")


def _cmd_scan(_args=None):
    """扫描所有内置公司"""
    from ..report.formatter import format_company_report

    detector = FraudDetector()
    results = detector.scan()

    if not results:
        print("❌ 没有公司数据")
        return

    # 按风险排序
    risk_order = {"高风险": 0, "中风险": 1, "低风险": 2}
    results.sort(key=lambda r: (risk_order.get(r["risk_level"], 9), -r["m_score"]))

    icon_map = {"低风险": "✅", "中风险": "⚠️", "高风险": "🚨"}

    print(f"{'='*70}")
    print(f"  FraudWatch 批量扫描报告 — {len(results)} 家公司")
    print(f"{'='*70}")
    print(f"{'代码':8s} {'名称':12s} {'行业':8s} {'风险':8s} {'M-Score':10s} {'信号':4s}")
    print(f"{'-'*8} {'-'*12} {'-'*8} {'-'*8} {'-'*10} {'-'*4}")

    for r in results:
        icon = icon_map.get(r["risk_level"], "❓")
        print(f"{r['code']:8s} {r['name']:12s} {r.get('sector', ''):8s} "
              f"{icon} {r['risk_level']:6s} {r['m_score']:<10.4f} "
              f"{r['signal_count']:<4d}")

    print(f"{'='*70}")

    high = sum(1 for r in results if r["risk_level"] == "高风险")
    med = sum(1 for r in results if r["risk_level"] == "中风险")
    low = sum(1 for r in results if r["risk_level"] == "低风险")
    print(f"  高风险: {high} | 中风险: {med} | 低风险: {low}")
    print()
    print("提示: 用 `python -m fraudwatch analyze <代码>` 查看详细信息")
    print("      用 `python -m fraudwatch top 5` 查看风险排名")
