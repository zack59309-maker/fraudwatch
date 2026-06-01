"""
Beneish M-Score 实现。

M-Score = -4.84
          + 0.920 × DSRI
          + 0.528 × GMI
          + 0.404 × AQI
          + 0.892 × SGI
          + 0.115 × DEPI
          - 0.172 × SGAI
          + 4.679 × TATA
          - 0.327 × LVGI

解释：
- M-Score < -2.22 → 大概率是正常公司
- M-Score > -2.22 → 可能存在财务操纵

来源：Beneish, M.D. (1999). "The Detection of Earnings Manipulation".
"""


def compute_m_score(beneish_vars: dict) -> float:
    """计算 Beneish M-Score"""
    dsri = beneish_vars.get("DSRI", 1)
    gmi = beneish_vars.get("GMI", 1)
    aqi = beneish_vars.get("AQI", 1)
    sgi = beneish_vars.get("SGI", 1)
    depi = beneish_vars.get("DEPI", 1)
    sgai = beneish_vars.get("SGAI", 1)
    tata = beneish_vars.get("TATA", 0)
    lvgi = beneish_vars.get("LVGI", 1)

    m = (-4.84
         + 0.920 * dsri
         + 0.528 * gmi
         + 0.404 * aqi
         + 0.892 * sgi
         + 0.115 * depi
         - 0.172 * sgai
         + 4.679 * tata
         - 0.327 * lvgi)
    return round(m, 4)


def explain_m_score(m: float) -> dict:
    """M-Score 解读"""
    if m < -2.22:
        return {
            "level": "低风险",
            "signal": False,
            "detail": "M-Score 低于 -2.22，未检测到显著财务操纵信号",
        }
    elif m < -1.78:
        return {
            "level": "中风险",
            "signal": True,
            "detail": "M-Score 在 -2.22 到 -1.78 之间，灰色区域，需关注",
        }
    else:
        return {
            "level": "高风险",
            "signal": True,
            "detail": "M-Score 高于 -1.78，存在显著财务操纵可能性",
        }
