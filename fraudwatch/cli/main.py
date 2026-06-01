"""
CLI 命令行入口。

用法：
  python -m fraudwatch analyze <股票代码>    # 分析单家公司
  python -m fraudwatch scan                  # 扫描所有公司
  python -m fraudwatch list                  # 列出所有公司
  python -m fraudwatch top [N]               # 风险最高的 N 家
"""
import sys
import argparse

from ..data.companies import get_company, list_companies, list_flagged, list_clean
from ..rules.engine import detect
from ..report.formatter import format_company_report, format_csv, format_json


def main():
    parser = argparse.ArgumentParser(
        description="FraudWatch — A股财务舞弊检测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", nargs="?", default="scan",
                        choices=["analyze", "scan", "list", "top", "help"],
                        help="命令: analyze <代码>, scan, list, top [N]")
    parser.add_argument("args", nargs="*", help="参数")

    opts = parser.parse_args()
    cmd = opts.command
    args = opts.args

    if cmd == "help" or cmd not in ("analyze", "scan", "list", "top"):
        print("FraudWatch — A股财务舞弊检测工具\n")
        print("用法:")
        print("  python -m fraudwatch analyze <股票代码>    分析单家公司")
        print("  python -m fraudwatch scan                  扫描所有公司")
        print("  python -m fraudwatch list                   列出所有公司")
        print("  python -m fraudwatch top [N]                风险最高的 N 家")
        print("\n示例:")
        print("  python -m fraudwatch analyze 600519     # 分析贵州茅台")
        print("  python -m fraudwatch analyze 600518     # 分析康美药业")
        print("  python -m fraudwatch scan               # 扫描全部 17 家公司")
        print("  python -m fraudwatch top 5              # 风险最高的 5 家")
        return

    if cmd == "list":
        _cmd_list(args)
        return

    if cmd == "top":
        _cmd_top(args)
        return

    if cmd == "analyze":
        _cmd_analyze(args)
        return

    if cmd == "scan":
        _cmd_scan()
        return


def _cmd_analyze(args):
    if not args:
        print("❌ 请指定股票代码，如: python -m fraudwatch analyze 600519")
        return

    code = args[0]
    profile = get_company(code)
    if not profile:
        print(f"❌ 未找到公司: {code}")
        print(f"   可用代码: 600519, 600036, 300750, 000858, 600518, 002450, ...")
        return

    result = detect(profile)
    print(format_company_report(result))

    # 输出 JSON 选项
    if "--json" in args or "-j" in args:
        print("\n=== JSON ===")
        print(format_json(result))


def _cmd_scan():
    profiles = list_companies()
    if not profiles:
        print("❌ 没有公司数据")
        return

    results = [detect(p) for p in profiles]

    # 按风险排序（高风险 > 中风险 > 低风险）
    risk_order = {"高风险": 0, "中风险": 1, "低风险": 2}
    results.sort(key=lambda r: (risk_order.get(r["risk_level"], 9), -r["m_score"]))

    # 头部摘要
    print(f"{'='*70}")
    print(f"  FraudWatch 批量扫描报告 — {len(results)} 家公司")
    print(f"{'='*70}")
    print(f"{'代码':8s} {'名称':12s} {'行业':8s} {'风险':8s} {'M-Score':10s} {'信号':4s} {'标记':4s}")
    print(f"{'-'*8} {'-'*12} {'-'*8} {'-'*8} {'-'*10} {'-'*4} {'-'*4}")

    for r in results:
        icon = {"低风险": "✅", "中风险": "⚠️", "高风险": "🚨"}
        risk_icon = icon.get(r["risk_level"], "❓")
        flagged_mark = "⚠️" if r.get("flagged") else "  "
        print(f"{r['code']:8s} {r['name']:12s} {r.get('sector',''):8s} "
              f"{risk_icon} {r['risk_level']:6s} {r['m_score']:<10.4f} "
              f"{r['signal_count']:<4d} {flagged_mark}")

    print(f"{'='*70}")

    # 统计
    high = sum(1 for r in results if r["risk_level"] == "高风险")
    med = sum(1 for r in results if r["risk_level"] == "中风险")
    low = sum(1 for r in results if r["risk_level"] == "低风险")
    print(f"  高风险: {high} | 中风险: {med} | 低风险: {low}")
    print()

    # 想看详细的分析某一家，可以 python -m fraudwatch analyze <代码>
    print("提示: 用 `python -m fraudwatch analyze <代码>` 查看详细信息")
    print("      用 `python -m fraudwatch top 5` 查看风险排名")


def _cmd_top(args):
    n = 5
    if args:
        try:
            n = int(args[0])
        except ValueError:
            pass

    profiles = list_companies()
    results = [detect(p) for p in profiles]
    results.sort(key=lambda r: -r["m_score"])

    top_n = results[:n]

    print(f"{'='*70}")
    print(f"  FraudWatch 风险排名 — Top {n}")
    print(f"{'='*70}")
    print(f"{'排名':4s} {'代码':8s} {'名称':16s} {'M-Score':10s} {'风险':8s} {'信号':4s}")
    print(f"{'-'*4} {'-'*8} {'-'*16} {'-'*10} {'-'*8} {'-'*4}")

    for i, r in enumerate(top_n, 1):
        icon = {"低风险": "✅", "中风险": "⚠️", "高风险": "🚨"}
        print(f"{i:<4d} {r['code']:8s} {r['name']:16s} "
              f"{r['m_score']:<10.4f} {icon.get(r['risk_level'],'❓')} {r['risk_level']:6s} "
              f"{r['signal_count']:<4d}")

    print(f"{'='*70}")
