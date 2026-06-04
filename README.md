# A股复盘助手

一个用于 A 股盘后复盘的数据采集和草稿生成项目。

它现在做的事很简单：给一个交易日期，自动抓取公开数据，保存原始文件，整理部分核心指标，并生成一份可继续人工修订的复盘草稿。

> 说明：本项目只用于公开市场数据整理和研究记录，不构成投资建议，也不包含自动下单能力。

## 当前能力

已能自动获取并保存：

- 自在量化涨停原因页面数据
- 涨停原因解析结果
- 涨停核心个股实时行情
- 交易日历
- AkShare / 新浪源全市场 A 股行情
- AkShare / 新浪源指数行情
- AkShare 涨停池
- AkShare 跌停池
- 上涨、下跌、平盘家数和成交额摘要
- 自动复盘草稿
- 接口失败记录

暂未完全稳定：

- 东方财富 `push2` 域名在部分网络环境下会空回复，行业板块、概念板块可能失败。
- 市场情绪接口还没有正式接入。
- 自动生成的复盘草稿还需要人工复核题材归因。

## 项目结构

```text
A股复盘/
├── README.md
├── requirements.txt
├── .gitignore
├── config/
│   └── data_sources.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AUTOMATION.md
│   ├── DATA_SOURCES.md
│   ├── CONNECT_SERVER.md
│   ├── DEPLOYMENT.md
│   └── PUBLISHING.md
├── deploy/
│   └── systemd/
├── scripts/
│   └── run_daily.sh
├── tools/
│   ├── collect_daily_data.py
│   ├── collect_quant_reason.py
│   ├── a_review/
│   │   ├── __init__.py
│   │   └── core.py
│   └── tests/
│       └── test_review_core.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── reports/
├── 01-每日复盘/
├── 02-观察池/
├── 03-板块跟踪/
├── 04-个股跟踪/
├── 05-模板/
├── 06-周度总结/
├── 07-数据源/
└── 08-采集方案/
```

## 安装

建议使用 Python 3.11 或更新版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 一键采集

在项目目录的上一级运行：

```bash
PYTHONPATH=A股复盘/tools python3 A股复盘/tools/collect_daily_data.py 2026-06-02 --out-dir A股复盘 --allow-insecure
```

也可以进入项目目录后运行：

```bash
PYTHONPATH=tools python3 tools/collect_daily_data.py 2026-06-02 --out-dir . --allow-insecure
```

成功后会生成：

```text
data/raw/2026-06-02/
data/processed/2026-06-02/
data/reports/2026-06-02/review_draft.md
```

## 只抓涨停原因

```bash
PYTHONPATH=tools python3 tools/collect_quant_reason.py 2026-06-02 --out-dir . --allow-insecure
```

## 运行测试

```bash
PYTHONPATH=tools python3 -m unittest discover -s tools/tests
```

也可以：

```bash
make test
```

## 自动运行

项目已经提供脚本：

```bash
scripts/run_daily.sh 2026-06-02
```

定时运行可以参考：

- [docs/AUTOMATION.md](docs/AUTOMATION.md)
- [docs/CONNECT_SERVER.md](docs/CONNECT_SERVER.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

数据源维护位置：

- [config/data_sources.json](config/data_sources.json)
- [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)

发布到 GitHub 后，也可以使用 GitHub Actions：

- `.github/workflows/ci.yml`：提交代码时自动跑测试。
- `.github/workflows/daily-collect.yml`：支持手动或定时采集，并把数据作为 artifact 上传。

## 数据文件说明

| 文件 | 内容 |
|---|---|
| `quant_tradedays.json` | 交易日历 |
| `quant_uplimit_reason_pages.json` | 自在量化涨停原因原始分页 |
| `quant_uplimit_reason_rows.json` | 解析后的涨停原因记录 |
| `quant_market_real_core.json` | 涨停核心个股实时行情 |
| `akshare_a_spot_sina.json` | 全市场 A 股行情 |
| `akshare_index_spot_sina.json` | 指数行情 |
| `akshare_zt_pool.json` | 涨停池 |
| `akshare_zt_pool_dtgc.json` | 跌停池 |
| `market_breadth_summary.json` | 上涨、下跌、平盘家数和成交额 |
| `errors.json` | 失败接口和错误原因 |

## 设计原则

- 原始数据先落地，再做分析。
- 一个接口失败，不影响其它数据继续采集。
- 自动草稿只做初稿，不把猜测写成结论。
- 所有判断都应允许人工复核和修正。
