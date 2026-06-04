import unittest

from a_review.core import (
    MarketSnapshot,
    StockLimitUp,
    build_plate_summary,
    build_quant_uplimit_reason_url,
    build_eastmoney_clist_url,
    build_review_draft,
    build_uplimit_ladder,
    collect_quant_uplimit_reason,
    collect_quant_uplimit_reason_pages,
    dataframe_to_records,
    parse_eastmoney_clist_payload,
    summarize_akshare_market,
    normalize_trade_date,
    parse_quant_uplimit_reason_payload,
)


class ReviewCoreTest(unittest.TestCase):
    def test_normalize_trade_date_accepts_common_formats(self):
        self.assertEqual(normalize_trade_date("2026-06-02"), "2026-06-02")
        self.assertEqual(normalize_trade_date("20260602"), "2026-06-02")

    def test_build_plate_summary_groups_uplimit_stocks_by_plate(self):
        rows = [
            StockLimitUp("汇源通信", "000586", "通信设备", 4, "通信链走强"),
            StockLimitUp("铭普光磁", "002902", "通信设备", 1, "光模块"),
            StockLimitUp("百花医药", "600721", "医药", 1, "创新药"),
        ]

        summary = build_plate_summary(rows)

        self.assertEqual(summary[0].plate, "通信设备")
        self.assertEqual(summary[0].uplimit_count, 2)
        self.assertEqual(summary[0].highest_board, 4)
        self.assertEqual(summary[0].core_stocks, ["汇源通信", "铭普光磁"])
        self.assertEqual(summary[1].plate, "医药")

    def test_build_uplimit_ladder_orders_by_board_height(self):
        rows = [
            StockLimitUp("首板A", "000001", "算力", 1, "低位补涨"),
            StockLimitUp("二板B", "000002", "算力", 2, "题材发酵"),
            StockLimitUp("四板C", "000003", "通信", 4, "市场高度"),
        ]

        ladder = build_uplimit_ladder(rows)

        self.assertEqual(list(ladder.keys()), [4, 2, 1])
        self.assertEqual(ladder[4][0].name, "四板C")

    def test_build_uplimit_ladder_deduplicates_stocks_across_plates(self):
        rows = [
            StockLimitUp("中京电子", "002579", "通信", 5, "AI PC"),
            StockLimitUp("中京电子", "002579", "芯片", 5, "AI PC"),
        ]

        ladder = build_uplimit_ladder(rows)

        self.assertEqual(len(ladder[5]), 1)
        self.assertEqual(ladder[5][0].plate, "通信、芯片")

    def test_build_review_draft_contains_core_sections(self):
        snapshot = MarketSnapshot(
            trade_date="2026-06-02",
            index_summary="指数震荡，量能略有放大",
            market_sentiment="情绪修复",
            uplimit_stocks=[
                StockLimitUp("汇源通信", "000586", "通信设备", 4, "通信链走强"),
                StockLimitUp("铭普光磁", "002902", "通信设备", 1, "光模块"),
            ],
            risk_notes=["高位股波动加大"],
        )

        draft = build_review_draft(snapshot)

        self.assertIn("# 2026-06-02 A股复盘草稿", draft)
        self.assertIn("## 一句话结论", draft)
        self.assertIn("通信设备", draft)
        self.assertIn("汇源通信", draft)
        self.assertIn("高位股波动加大", draft)

    def test_build_review_draft_deduplicates_stock_reason_rows(self):
        snapshot = MarketSnapshot(
            trade_date="2026-06-02",
            uplimit_stocks=[
                StockLimitUp("中京电子", "002579", "通信", 5, "AI PC"),
                StockLimitUp("中京电子", "002579", "芯片", 5, "AI PC"),
            ],
        )

        draft = build_review_draft(snapshot)

        self.assertEqual(draft.count("| 中京电子 | 002579 |"), 1)
        self.assertIn("| 中京电子 | 002579 | 通信、芯片 | 5 | AI PC |", draft)

    def test_build_quant_uplimit_reason_url_uses_discovered_page_api(self):
        url = build_quant_uplimit_reason_url("2026-06-02", page=2, page_size=50)

        self.assertEqual(
            url,
            "https://api.zizizaizai.com/v3/api/review/uplimit/reason?date1=2026-06-02&page=2&page_size=50",
        )

    def test_parse_quant_uplimit_reason_payload_maps_page_rows(self):
        payload = {
            "code": 20000,
            "data": [
                {
                    "plate_name": "通信设备",
                    "stocks": [
                        {
                            "stock_name": "汇源通信",
                            "stock_code": "000586",
                            "up_limit_keep_times": 4,
                            "reason": "通信链走强",
                        }
                    ],
                }
            ],
        }

        rows = parse_quant_uplimit_reason_payload(payload)

        self.assertEqual(rows, [StockLimitUp("汇源通信", "000586", "通信设备", 4, "通信链走强")])

    def test_collect_quant_uplimit_reason_reads_pages_until_short_page(self):
        calls = []

        def fetch_json(url):
            calls.append(url)
            if "page=1" in url:
                return {
                    "data": [
                        {
                            "plate_name": "通信设备",
                            "stocks": [
                                {
                                    "stock_name": "汇源通信",
                                    "stock_code": "000586",
                                    "up_limit_keep_times": 4,
                                    "reason": "通信链走强",
                                },
                            ],
                        },
                        {
                            "plate_name": "芯片",
                            "stocks": [
                                {
                                    "stock_name": "铭普光磁",
                                    "stock_code": "002902",
                                    "up_limit_keep_times": 1,
                                    "reason": "光模块",
                                }
                            ],
                        }
                    ]
                }
            return {
                "data": [
                    {
                        "plate_name": "医药",
                        "stocks": [
                            {
                                "stock_name": "百花医药",
                                "stock_code": "600721",
                                "up_limit_keep_times": 1,
                                "reason": "创新药",
                            }
                        ],
                    }
                ]
            }

        rows = collect_quant_uplimit_reason(fetch_json, "2026-06-02", page_size=2)

        self.assertEqual([row.name for row in rows], ["汇源通信", "铭普光磁", "百花医药"])
        self.assertEqual(len(calls), 2)

    def test_collect_quant_uplimit_reason_pages_keeps_raw_pages(self):
        def fetch_json(url):
            if "page=1" in url:
                return {"data": [{"plate_name": "通信", "stocks": []}]}
            return {"data": []}

        pages = collect_quant_uplimit_reason_pages(fetch_json, "2026-06-02", page_size=1)

        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["page"], 1)
        self.assertEqual(pages[0]["url"], build_quant_uplimit_reason_url("2026-06-02", 1, 1))
        self.assertEqual(pages[0]["payload"]["data"][0]["plate_name"], "通信")

    def test_collect_quant_uplimit_reason_stops_by_plate_page_count_not_stock_count(self):
        calls = []

        def fetch_json(url):
            calls.append(url)
            return {
                "data": [
                    {
                        "plate_name": "通信设备",
                        "stocks": [
                            {
                                "stock_name": "汇源通信",
                                "stock_code": "000586",
                                "up_limit_keep_times": 4,
                                "reason": "通信链走强",
                            },
                            {
                                "stock_name": "铭普光磁",
                                "stock_code": "002902",
                                "up_limit_keep_times": 1,
                                "reason": "光模块",
                            },
                        ],
                    }
                ]
            }

        rows = collect_quant_uplimit_reason(fetch_json, "2026-06-02", page_size=2)

        self.assertEqual([row.name for row in rows], ["汇源通信", "铭普光磁"])
        self.assertEqual(len(calls), 1)

    def test_dataframe_to_records_normalizes_non_json_values(self):
        import pandas as pd

        frame = pd.DataFrame(
            [
                {"代码": "000001", "成交额": 1.5, "备注": None},
                {"代码": "000002", "成交额": float("nan"), "备注": "测试"},
            ]
        )

        records = dataframe_to_records(frame)

        self.assertEqual(records[0]["代码"], "000001")
        self.assertIsNone(records[1]["成交额"])
        self.assertIsNone(records[0]["备注"])

    def test_summarize_akshare_market_counts_breadth_and_amount(self):
        rows = [
            {"代码": "000001", "涨跌幅": 1.2, "成交额": 100},
            {"代码": "000002", "涨跌幅": -0.5, "成交额": 200},
            {"代码": "000003", "涨跌幅": 0, "成交额": 300},
        ]

        summary = summarize_akshare_market(rows)

        self.assertEqual(summary["上涨家数"], 1)
        self.assertEqual(summary["下跌家数"], 1)
        self.assertEqual(summary["平盘家数"], 1)
        self.assertEqual(summary["成交额"], 600)

    def test_summarize_akshare_market_accepts_sina_style_fields(self):
        rows = [
            {"code": "sh600000", "changepercent": 1.2, "amount": 100},
            {"code": "sz000001", "changepercent": -0.5, "amount": 200},
        ]

        summary = summarize_akshare_market(rows)

        self.assertEqual(summary["上涨家数"], 1)
        self.assertEqual(summary["下跌家数"], 1)
        self.assertEqual(summary["成交额"], 300)

    def test_build_eastmoney_clist_url_contains_market_filters(self):
        url = build_eastmoney_clist_url("m:1+t:1", page=2, page_size=50)

        self.assertIn("https://push2.eastmoney.com/api/qt/clist/get?", url)
        self.assertIn("pn=2", url)
        self.assertIn("pz=50", url)
        self.assertIn("fs=m%3A1%2Bt%3A1", url)

    def test_parse_eastmoney_clist_payload_maps_core_fields(self):
        payload = {
            "data": {
                "diff": [
                    {"f12": "000001", "f14": "平安银行", "f3": 1.2, "f6": 1000},
                    {"f12": "000002", "f14": "万科A", "f3": -0.5, "f6": 2000},
                ]
            }
        }

        records = parse_eastmoney_clist_payload(payload)

        self.assertEqual(records[0]["代码"], "000001")
        self.assertEqual(records[0]["名称"], "平安银行")
        self.assertEqual(records[0]["涨跌幅"], 1.2)
        self.assertEqual(records[1]["成交额"], 2000)


if __name__ == "__main__":
    unittest.main()
