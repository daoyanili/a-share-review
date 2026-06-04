from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from math import isnan
from urllib.parse import urlencode


QUANT_API_BASE = "https://api.zizizaizai.com"
EASTMONEY_CLIST_BASE = "https://push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_CLIST_FIELDS = (
    "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f23,f62"
)
EASTMONEY_FIELD_MAP = {
    "f2": "最新价",
    "f3": "涨跌幅",
    "f4": "涨跌额",
    "f5": "成交量",
    "f6": "成交额",
    "f7": "振幅",
    "f8": "换手率",
    "f9": "市盈率",
    "f10": "量比",
    "f12": "代码",
    "f14": "名称",
    "f15": "最高",
    "f16": "最低",
    "f17": "今开",
    "f18": "昨收",
    "f20": "总市值",
    "f21": "流通市值",
    "f23": "市净率",
    "f62": "主力净流入",
}


@dataclass(frozen=True)
class StockLimitUp:
    name: str
    code: str
    plate: str
    board_count: int
    reason: str


@dataclass(frozen=True)
class PlateSummary:
    plate: str
    uplimit_count: int
    highest_board: int
    core_stocks: list[str]


@dataclass(frozen=True)
class MarketSnapshot:
    trade_date: str
    index_summary: str = ""
    market_sentiment: str = ""
    uplimit_stocks: list[StockLimitUp] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)


def normalize_trade_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"Unsupported trade date: {value}")


def build_plate_summary(rows: list[StockLimitUp]) -> list[PlateSummary]:
    grouped: dict[str, list[StockLimitUp]] = defaultdict(list)
    for row in rows:
        grouped[row.plate or "未分类"].append(row)

    summaries = [
        PlateSummary(
            plate=plate,
            uplimit_count=len(stocks),
            highest_board=max(stock.board_count for stock in stocks),
            core_stocks=[stock.name for stock in sorted(stocks, key=_stock_rank_key)],
        )
        for plate, stocks in grouped.items()
    ]
    return sorted(
        summaries,
        key=lambda item: (-item.uplimit_count, -item.highest_board, item.plate),
    )


def build_uplimit_ladder(rows: list[StockLimitUp]) -> dict[int, list[StockLimitUp]]:
    grouped: dict[int, list[StockLimitUp]] = defaultdict(list)
    for row in merge_stocks_by_code(rows):
        grouped[row.board_count].append(row)
    return {
        board: sorted(stocks, key=lambda stock: (stock.plate, stock.code))
        for board, stocks in sorted(grouped.items(), reverse=True)
    }


def build_review_draft(snapshot: MarketSnapshot) -> str:
    trade_date = normalize_trade_date(snapshot.trade_date)
    plate_summary = build_plate_summary(snapshot.uplimit_stocks)
    ladder = build_uplimit_ladder(snapshot.uplimit_stocks)

    lines: list[str] = [
        f"# {trade_date} A股复盘草稿",
        "",
        "> 说明：本草稿由数据整理生成，需要人工复核涨停原因和题材归因。",
        "",
        "## 一句话结论",
        "",
        f"- {snapshot.market_sentiment or '待补充'}。",
        "",
        "## 1. 市场环境",
        "",
        f"- {snapshot.index_summary or '待补充指数、成交额和涨跌家数。'}",
        "",
        "## 2. 热门板块",
        "",
    ]

    if plate_summary:
        lines.extend(["| 板块 | 涨停数 | 最高连板 | 核心个股 |", "|---|---:|---:|---|"])
        for item in plate_summary:
            lines.append(
                f"| {item.plate} | {item.uplimit_count} | {item.highest_board} | {', '.join(item.core_stocks)} |"
            )
    else:
        lines.append("- 暂无涨停板块数据。")

    lines.extend(["", "## 3. 连板梯队", ""])
    if ladder:
        for board, stocks in ladder.items():
            names = "、".join(f"{stock.name}({stock.code})" for stock in stocks)
            lines.append(f"- {board}板：{names}")
    else:
        lines.append("- 暂无连板数据。")

    lines.extend(["", "## 4. 涨停原因", ""])
    if snapshot.uplimit_stocks:
        lines.extend(["| 股票 | 代码 | 板块 | 连板 | 涨停原因 |", "|---|---|---|---:|---|"])
        for stock in sorted(merge_stocks_by_code(snapshot.uplimit_stocks), key=_stock_rank_key):
            lines.append(
                f"| {stock.name} | {stock.code} | {stock.plate} | {stock.board_count} | {stock.reason} |"
            )
    else:
        lines.append("- 暂无涨停原因数据。")

    lines.extend(["", "## 5. 风险点", ""])
    if snapshot.risk_notes:
        lines.extend(f"- {note}" for note in snapshot.risk_notes)
    else:
        lines.append("- 待补充。")

    lines.extend(
        [
            "",
            "## 6. 明日观察",
            "",
            "- 优先看主线核心股是否继续走强。",
            "- 如果高位股明显分歧，降低追高动作。",
            "- 如果新题材放量扩散，再单独加入观察池。",
            "",
        ]
    )
    return "\n".join(lines)


def build_quant_uplimit_reason_url(
    trade_date: str,
    page: int = 1,
    page_size: int = 20,
) -> str:
    query = urlencode(
        {
            "date1": normalize_trade_date(trade_date),
            "page": page,
            "page_size": page_size,
        }
    )
    return f"{QUANT_API_BASE}/v3/api/review/uplimit/reason?{query}"


def build_eastmoney_clist_url(
    fs: str,
    page: int = 1,
    page_size: int = 500,
    fields: str = EASTMONEY_CLIST_FIELDS,
) -> str:
    query = urlencode(
        {
            "pn": page,
            "pz": page_size,
            "po": 1,
            "np": 1,
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2,
            "invt": 2,
            "fid": "f3",
            "fs": fs,
            "fields": fields,
        }
    )
    return f"{EASTMONEY_CLIST_BASE}?{query}"


def parse_eastmoney_clist_payload(payload: dict) -> list[dict]:
    diff = (payload.get("data") or {}).get("diff") or []
    records: list[dict] = []
    for row in diff:
        records.append(
            {
                label: _json_value(row.get(field))
                for field, label in EASTMONEY_FIELD_MAP.items()
                if field in row
            }
        )
    return records


def parse_quant_uplimit_reason_payload(payload: dict) -> list[StockLimitUp]:
    plates = payload.get("data") or []
    rows: list[StockLimitUp] = []
    for plate in plates:
        plate_name = str(plate.get("plate_name") or "未分类")
        for stock in plate.get("stocks") or []:
            rows.append(
                StockLimitUp(
                    name=str(stock.get("stock_name") or ""),
                    code=str(stock.get("stock_code") or ""),
                    plate=plate_name,
                    board_count=int(stock.get("up_limit_keep_times") or 1),
                    reason=str(stock.get("reason") or ""),
                )
            )
    return rows


def collect_quant_uplimit_reason(
    fetch_json,
    trade_date: str,
    page_size: int = 20,
    max_pages: int = 20,
) -> list[StockLimitUp]:
    rows: list[StockLimitUp] = []
    for page in range(1, max_pages + 1):
        url = build_quant_uplimit_reason_url(trade_date, page=page, page_size=page_size)
        payload = fetch_json(url)
        page_rows = parse_quant_uplimit_reason_payload(payload)
        rows.extend(page_rows)
        if len(payload.get("data") or []) < page_size:
            break
    return rows


def collect_quant_uplimit_reason_pages(
    fetch_json,
    trade_date: str,
    page_size: int = 2,
    max_pages: int = 20,
) -> list[dict]:
    pages: list[dict] = []
    for page in range(1, max_pages + 1):
        url = build_quant_uplimit_reason_url(trade_date, page=page, page_size=page_size)
        payload = fetch_json(url)
        pages.append({"page": page, "url": url, "payload": payload})
        if len(payload.get("data") or []) < page_size:
            break
    return pages


def dataframe_to_records(frame) -> list[dict]:
    records: list[dict] = []
    for raw in frame.to_dict(orient="records"):
        records.append({str(key): _json_value(value) for key, value in raw.items()})
    return records


def summarize_akshare_market(rows: list[dict]) -> dict:
    up_count = 0
    down_count = 0
    flat_count = 0
    amount = 0
    for row in rows:
        pct = _first_number(row, ["涨跌幅", "changepercent", "change_percent", "pct_chg"])
        if pct is None:
            continue
        if pct > 0:
            up_count += 1
        elif pct < 0:
            down_count += 1
        else:
            flat_count += 1
        amount += _first_number(row, ["成交额", "amount", "turnover"]) or 0
    return {
        "上涨家数": up_count,
        "下跌家数": down_count,
        "平盘家数": flat_count,
        "成交额": amount,
    }


def merge_stocks_by_code(rows: list[StockLimitUp]) -> list[StockLimitUp]:
    merged: dict[str, StockLimitUp] = {}
    plate_order: dict[str, list[str]] = {}
    for row in rows:
        key = row.code or row.name
        plate_order.setdefault(key, [])
        if row.plate and row.plate not in plate_order[key]:
            plate_order[key].append(row.plate)
        if key not in merged:
            merged[key] = row
            continue
        current = merged[key]
        merged[key] = StockLimitUp(
            name=current.name or row.name,
            code=current.code or row.code,
            plate="、".join(plate_order[key]),
            board_count=max(current.board_count, row.board_count),
            reason=current.reason or row.reason,
        )

    result: list[StockLimitUp] = []
    for key, row in merged.items():
        result.append(
            StockLimitUp(
                name=row.name,
                code=row.code,
                plate="、".join(plate_order.get(key) or [row.plate]),
                board_count=row.board_count,
                reason=row.reason,
            )
        )
    return result


def _stock_rank_key(stock: StockLimitUp) -> tuple[int, str, str]:
    return (-stock.board_count, stock.plate, stock.code)


def _json_value(value):
    if value is None:
        return None
    try:
        if isnan(value):
            return None
    except TypeError:
        pass
    if hasattr(value, "item"):
        return _json_value(value.item())
    return value


def _number_or_none(value) -> float | None:
    value = _json_value(value)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_number(row: dict, keys: list[str]) -> float | None:
    for key in keys:
        value = _number_or_none(row.get(key))
        if value is not None:
            return value
    return None
