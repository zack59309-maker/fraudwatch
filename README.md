# FraudWatch — A股财务舞弊检测工具

一个纯 Python 的财务舞弊检测工具，基于公开财报指标 + 经典舞弊检测模型，无需任何 API Key 或外部服务，`pip install` 即可运行。

## 检测模型

| 方法 | 说明 |
|------|------|
| **Beneish M-Score** | 基于 8 个财务指标的操纵检测模型 |
| **现金流-利润偏离** | 经营现金流与净利润的剪刀差检测 |
| **营收质量评分** | 应收账款/营收比、营收增长率异常 |
| **综合舞弊风险评分** | 多项信号加权汇总，输出风险等级 |

## 快速开始

```bash
git clone https://github.com/zack59309-maker/fraudwatch.git
cd fraudwatch
pip install -r requirements.txt

# 分析一家公司
python -m fraudwatch analyze 600519

# 检测一批公司
python -m fraudwatch scan
```

### 在代码中使用

```python
from fraudwatch import FraudDetector

detector = FraudDetector()
result = detector.analyze("600519")
print(result)

# {
#   "code": "600519",
#   "name": "贵州茅台",
#   "m_score": -2.85,        # <- 小于-2.22为正常
#   "risk_level": "低风险",
#   "warning_signals": [],
#   "details": { ... }
# }
```

## 内置数据

包含 20+ 家 A 股公司的样本财务数据，涵盖：
- ✅ 正常公司（贵州茅台、招商银行、宁德时代...）
- ⚠️ 曾被处罚的财务造假案例（康美药业、康得新、獐子岛...）
- ✅ 覆盖白酒、银行、医药、制造、农业等行业

**无需联网，开箱即用。**

## 输出

- CLI 输出彩色表格，一目了然
- 可导出 JSON/CSV 报告
- 支持批量扫描生成排行

## 技术栈

纯 Python 标准库 + NumPy（可选），零外部依赖。

## 项目结构

```
fraudwatch/
├── fraudwatch/
│   ├── __init__.py
│   ├── data/          # 内置样本财务报表
│   ├── rules/         # 舞弊检测规则引擎
│   ├── report/        # 报告格式化
│   └── cli/           # 命令行入口
├── examples/          # 使用示例
├── tests/             # 单元测试
└── README.md
```

## License

MIT
