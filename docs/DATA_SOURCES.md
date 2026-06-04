# 数据源维护说明

## 维护位置

数据源统一维护在：

```text
config/data_sources.json
```

这个文件负责回答四个问题：

- 哪里取数据
- 取什么数据
- 输出到哪个文件
- 当前状态是否稳定

## 状态说明

| 状态 | 含义 |
|---|---|
| `enabled` | 已接入，脚本会自动抓 |
| `unstable` | 已写入脚本，但当前网络或接口不稳定 |
| `todo` | 计划接入，还没实现 |

## 当前已接入

| 数据源 | 能获取什么 | 输出 |
|---|---|---|
| 自在量化交易日历 | 最近交易日列表 | `quant_tradedays.json` |
| 自在量化涨停原因 | 板块、涨停股、涨停原因、封单、成交额、换手、连板 | `quant_uplimit_reason_pages.json`、`quant_uplimit_reason_rows.json` |
| 自在量化核心个股行情 | 涨停核心股实时行情 | `quant_market_real_core.json` |
| AkShare 新浪全市场行情 | 全市场 A 股行情、涨跌幅、成交额 | `akshare_a_spot_sina.json` |
| AkShare 新浪指数行情 | 指数行情 | `akshare_index_spot_sina.json` |
| AkShare 涨停池 | 涨停池、封板时间、炸板次数、连板数 | `akshare_zt_pool.json` |
| AkShare 跌停池 | 跌停池、连续跌停、开板次数 | `akshare_zt_pool_dtgc.json` |

## 当前不稳定

| 数据源 | 问题 |
|---|---|
| 东方财富行业板块 | 当前网络访问 `push2.eastmoney.com` 可能空回复 |
| 东方财富概念板块 | 当前网络访问 `push2.eastmoney.com` 可能空回复 |

这些失败不会中断主流程，会写入：

```text
data/raw/{trade_date}/errors.json
```

## 当前待接入

| 数据源 | 目标 |
|---|---|
| 市场情绪接口 | 补情绪阶段、炸板率、短线赚钱效应 |

## 如何新增一个数据源

1. 先在 `config/data_sources.json` 新增一条记录。
2. 在 `tools/collect_daily_data.py` 增加采集逻辑。
3. 在 `tools/a_review/core.py` 增加必要的解析或清洗函数。
4. 在 `tools/tests/test_review_core.py` 补测试。
5. 运行测试：

```bash
PYTHONPATH=tools python3 -m unittest discover -s tools/tests
```

## 数据输出约定

原始数据放：

```text
data/raw/{trade_date}/
```

处理后的摘要放：

```text
data/processed/{trade_date}/
```

复盘草稿放：

```text
data/reports/{trade_date}/
```

