#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import ssl
import sys
from dataclasses import asdict
from pathlib import Path
from urllib.request import Request, urlopen

from a_review.core import (
    MarketSnapshot,
    build_review_draft,
    collect_quant_uplimit_reason,
    normalize_trade_date,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Quant uplimit reason data.")
    parser.add_argument("trade_date", help="Trade date, for example 2026-06-02 or 20260602")
    parser.add_argument(
        "--out-dir",
        default="A股复盘",
        help="Project output directory. Defaults to A股复盘.",
    )
    parser.add_argument("--page-size", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument(
        "--allow-insecure",
        action="store_true",
        help="Skip TLS certificate verification for this request.",
    )
    args = parser.parse_args()

    trade_date = normalize_trade_date(args.trade_date)
    out_dir = Path(args.out_dir)

    rows = collect_quant_uplimit_reason(
        lambda url: fetch_json(url, allow_insecure=args.allow_insecure),
        trade_date,
        page_size=args.page_size,
        max_pages=args.max_pages,
    )

    raw_dir = out_dir / "data" / "raw" / trade_date
    report_dir = out_dir / "data" / "reports" / trade_date
    raw_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / "quant_uplimit_reason.json"
    report_path = report_dir / "review_draft.md"

    raw_path.write_text(
        json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    draft = build_review_draft(
        MarketSnapshot(
            trade_date=trade_date,
            index_summary="指数和成交额数据待接入 AkShare 后补充。",
            market_sentiment="涨停原因数据已采集，市场情绪待接入情绪接口后补充",
            uplimit_stocks=rows,
            risk_notes=["本稿为自动生成草稿，需人工复核题材归因和重复个股。"],
        )
    )
    report_path.write_text(draft, encoding="utf-8")

    print(f"saved raw data: {raw_path}")
    print(f"saved report draft: {report_path}")
    print(f"uplimit rows: {len(rows)}")
    return 0


def fetch_json(url: str, allow_insecure: bool = False) -> dict:
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


if __name__ == "__main__":
    sys.exit(main())
