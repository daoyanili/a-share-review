#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from a_review.core import (
    MarketSnapshot,
    QUANT_API_BASE,
    build_eastmoney_clist_url,
    build_review_draft,
    collect_quant_uplimit_reason_pages,
    dataframe_to_records,
    merge_stocks_by_code,
    normalize_trade_date,
    parse_eastmoney_clist_payload,
    parse_quant_uplimit_reason_payload,
    summarize_akshare_market,
)


STOCK_API_BASE = "https://stock.ziruxing.com"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect daily A-share review data.")
    parser.add_argument("trade_date", help="Trade date, for example 2026-06-02 or 20260602")
    parser.add_argument("--out-dir", default="A股复盘")
    parser.add_argument("--allow-insecure", action="store_true")
    parser.add_argument("--skip-akshare", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when optional sources fail.")
    parser.add_argument("--max-quant-pages", type=int, default=20)
    parser.add_argument("--quant-page-size", type=int, default=2)
    args = parser.parse_args()

    trade_date = normalize_trade_date(args.trade_date)
    yyyymmdd = trade_date.replace("-", "")
    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "data" / "raw" / trade_date
    processed_dir = out_dir / "data" / "processed" / trade_date
    report_dir = out_dir / "data" / "reports" / trade_date
    for directory in (raw_dir, processed_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    errors: list[dict] = []
    fetch_json = lambda url: http_get_json(url, allow_insecure=args.allow_insecure)

    quant_rows = collect_quant(reason_date=trade_date, args=args, raw_dir=raw_dir, errors=errors, fetch_json=fetch_json)

    if not args.skip_akshare:
        collect_akshare(yyyymmdd=yyyymmdd, raw_dir=raw_dir, processed_dir=processed_dir, errors=errors)
        collect_eastmoney_fallback(raw_dir=raw_dir, processed_dir=processed_dir, errors=errors, fetch_json=fetch_json)

    save_json(
        raw_dir / "metadata.json",
        {
            "trade_date": trade_date,
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "sources": ["quant.zizizaizai.com", "akshare"] if not args.skip_akshare else ["quant.zizizaizai.com"],
        },
    )
    save_json(raw_dir / "errors.json", errors)

    draft = build_review_draft(
        MarketSnapshot(
            trade_date=trade_date,
            index_summary="市场基础数据已保存到 data/raw 和 data/processed，复盘判断待整合。",
            market_sentiment="涨停原因已采集，情绪接口待继续接入",
            uplimit_stocks=quant_rows,
            risk_notes=["自动采集结果需要人工复核，尤其是题材归因和接口失败项。"],
        )
    )
    (report_dir / "review_draft.md").write_text(draft, encoding="utf-8")

    print(f"saved raw data: {raw_dir}")
    print(f"saved processed data: {processed_dir}")
    print(f"saved report draft: {report_dir / 'review_draft.md'}")
    print(f"quant rows: {len(quant_rows)}")
    print(f"errors: {len(errors)}")
    return 2 if args.strict and errors else 0


def collect_quant(reason_date: str, args, raw_dir: Path, errors: list[dict], fetch_json) -> list:
    rows = []
    try:
        tradedays = fetch_json(f"{STOCK_API_BASE}/open/tradedays")
        save_json(raw_dir / "quant_tradedays.json", tradedays)
    except Exception as exc:
        errors.append(error_record("quant_tradedays", exc))

    try:
        pages = collect_quant_uplimit_reason_pages(
            fetch_json,
            reason_date,
            page_size=args.quant_page_size,
            max_pages=args.max_quant_pages,
        )
        save_json(raw_dir / "quant_uplimit_reason_pages.json", pages)
        for page in pages:
            rows.extend(parse_quant_uplimit_reason_payload(page["payload"]))
        save_json(raw_dir / "quant_uplimit_reason_rows.json", [asdict(row) for row in rows])
    except Exception as exc:
        errors.append(error_record("quant_uplimit_reason", exc))

    unique_rows = merge_stocks_by_code(rows)
    symbols = [row.code for row in unique_rows if row.code]
    if symbols:
        try:
            market_real = []
            for batch in chunked(symbols, 30):
                query = urlencode({"symbols": ",".join(batch)})
                market_real.append(fetch_json(f"{QUANT_API_BASE}/open/market/real?{query}"))
                time.sleep(0.2)
            save_json(raw_dir / "quant_market_real_core.json", market_real)
        except Exception as exc:
            errors.append(error_record("quant_market_real_core", exc))
    return rows


def collect_akshare(yyyymmdd: str, raw_dir: Path, processed_dir: Path, errors: list[dict]) -> None:
    import akshare as ak

    datasets = [
        ("akshare_a_spot_em", lambda: ak.stock_zh_a_spot_em()),
        ("akshare_a_spot_sina", lambda: ak.stock_zh_a_spot()),
        ("akshare_index_spot_em", lambda: ak.stock_zh_index_spot_em()),
        ("akshare_index_spot_sina", lambda: ak.stock_zh_index_spot_sina()),
        ("akshare_industry_boards", lambda: ak.stock_board_industry_name_em()),
        ("akshare_concept_boards", lambda: ak.stock_board_concept_name_em()),
        ("akshare_zt_pool", lambda: ak.stock_zt_pool_em(date=yyyymmdd)),
        ("akshare_zt_pool_dtgc", lambda: ak.stock_zt_pool_dtgc_em(date=yyyymmdd)),
    ]

    for name, loader in datasets:
        try:
            records = dataframe_to_records(loader())
            save_json(raw_dir / f"{name}.json", records)
            if name in {"akshare_a_spot_em", "akshare_a_spot_sina"}:
                save_json(processed_dir / "market_breadth_summary.json", summarize_akshare_market(records))
        except Exception as exc:
            errors.append(error_record(name, exc))


def collect_eastmoney_fallback(raw_dir: Path, processed_dir: Path, errors: list[dict], fetch_json) -> None:
    datasets = [
        ("eastmoney_a_spot", "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048"),
        ("eastmoney_index_spot", "m:1+t:1"),
        ("eastmoney_industry_boards", "m:90+t:2+f:!50"),
        ("eastmoney_concept_boards", "m:90+t:3+f:!50"),
    ]
    for name, fs in datasets:
        try:
            records = collect_eastmoney_clist(fetch_json, fs)
            save_json(raw_dir / f"{name}.json", records)
            if name == "eastmoney_a_spot":
                save_json(processed_dir / "market_breadth_summary.json", summarize_akshare_market(records))
        except Exception as exc:
            errors.append(error_record(name, exc))


def collect_eastmoney_clist(fetch_json, fs: str, page_size: int = 500, max_pages: int = 20) -> list[dict]:
    records: list[dict] = []
    for page in range(1, max_pages + 1):
        payload = fetch_json(build_eastmoney_clist_url(fs, page=page, page_size=page_size))
        page_records = parse_eastmoney_clist_payload(payload)
        records.extend(page_records)
        total = ((payload.get("data") or {}).get("total")) or 0
        if not page_records or len(records) >= total:
            break
    return records


def http_get_json(url: str, allow_insecure: bool = False) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (A-share review collector)",
            "Referer": "https://quant.zizizaizai.com/review/uplimit/reason",
        },
    )
    context = ssl._create_unverified_context() if allow_insecure else None
    with urlopen(request, timeout=60, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def error_record(name: str, exc: Exception) -> dict:
    return {"name": name, "type": type(exc).__name__, "message": str(exc)}


def chunked(items: list[str], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


if __name__ == "__main__":
    sys.exit(main())
