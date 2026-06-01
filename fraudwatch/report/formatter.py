"""
报告格式化 — 输出人类可读的检测报告。
"""
import json
from typing import List, Dict


def format_company_report(result: dict) -> str:
    """生成单家公司检测报告（CLI 友好文本）"""
    lines = []
    lines.append(f"{'='*60}")
    lines.append(f"  {result['name']} ({result['code']}) — {result.get('sector', '')}")
    if result.get("flagged"):
        lines.append(f"  ⚠️  历史风险: {result.get('flag_reason', '')}")
    lines.append(f"{'='*60}")

    # 风险等级
    level = result["risk_level"]
    icon = {"低风险": "✅", "中风险": "⚠️", "高风险": "🚨"}
    lines.append(f"  综合风险等级: {icon.get(level, '❓')} {level}")
    lines.append(f"  Beneish M-Score: {result['m_score']:.4f}  (阈值: -2.22)")
    lines.append(f"  预警信号数: {result['signal_count']}")
    lines.append("")

    # 信号详情
    if result["signals"]:
        lines.append("  ── 预警信号 ──")
        for s in result["signals"]:
            severity_icon = {"低风险": "ℹ️", "中风险": "⚠️", "高风险": "🔴"}
            lines.append(f"  [{severity_icon.get(s['severity'], '❓')}] {s['severity']}: {s['name']}")
            lines.append(f"       {s['detail']}")
        lines.append("")

    # M-Score 明细
    bv = result.get("details", {}).get("beneish_vars", {})
    if bv:
        lines.append("  ── M-Score 变量明细 ──")
        for k in ["DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI", "LVGI", "TATA"]:
            v = bv.get(k, "—")
            if isinstance(v, float):
                flag = " ⚠️" if abs(v) > 2 else ""
                lines.append(f"    {k:6s} = {v:.4f}{flag}")
            else:
                lines.append(f"    {k:6s} = {v}")
        lines.append("")

    return "\n".join(lines)


def format_csv(results: List[Dict]) -> str:
    """CSV 格式输出"""
    import csv, io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["代码", "名称", "行业", "风险等级", "M-Score", "信号数", "历史标记", "历史原因"])
    for r in results:
        writer.writerow([
            r["code"], r["name"], r.get("sector", ""),
            r["risk_level"], r["m_score"], r["signal_count"],
            r.get("flagged", ""), r.get("flag_reason", ""),
        ])
    return buf.getvalue()


def format_json(results) -> str:
    """JSON 格式输出"""
    if isinstance(results, list):
        return json.dumps(results, ensure_ascii=False, indent=2)
    return json.dumps(results, ensure_ascii=False, indent=2)
