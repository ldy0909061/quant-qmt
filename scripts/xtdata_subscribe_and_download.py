import argparse
import sys
import time


def _parse_codes(value: str) -> list[str]:
    parts = [p.strip() for p in value.replace(";", ",").replace(" ", ",").split(",")]
    return [p for p in parts if p]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="xtdata_subscribe_and_download",
        description="XtQuant xtdata: 下载历史数据 + 订阅行情（全推）示例脚本",
    )
    parser.add_argument(
        "--codes",
        default="000001.SZ",
        help='标的列表，逗号分隔，例如: "000001.SZ,600000.SH"',
    )
    parser.add_argument("--period", default="1d", help='周期，例如: "tick", "1m", "5m", "1d"')
    parser.add_argument(
        "--download-history",
        action="store_true",
        help="下载/补齐历史行情数据到本地（download_history_data）",
    )
    parser.add_argument(
        "--incremental",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="历史行情是否增量下载（默认增量）",
    )
    parser.add_argument(
        "--download-financial",
        action="store_true",
        help="下载财务数据到本地（download_financial_data）",
    )
    parser.add_argument(
        "--download-sector",
        action="store_true",
        help="下载板块数据到本地（download_sector_data）",
    )
    parser.add_argument(
        "--subscribe",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否订阅实时行情（subscribe_quote）",
    )
    parser.add_argument(
        "--subscribe-count",
        type=int,
        default=-1,
        help="订阅时的count参数，-1 表示取到当天所有实时行情",
    )
    parser.add_argument(
        "--loop",
        type=int,
        default=5,
        help="轮询获取行情的次数（不使用回调时生效）",
    )
    parser.add_argument("--sleep", type=float, default=3.0, help="轮询间隔秒数（不使用回调时生效）")
    parser.add_argument(
        "--use-callback",
        action="store_true",
        help="使用订阅回调模式（会调用 xtdata.run() 阻塞进程）",
    )

    args = parser.parse_args(argv)

    try:
        from xtquant import xtdata
    except Exception as e:
        print("导入 xtquant 失败。请确认在 venv 下能 import xtquant。错误信息：", e, file=sys.stderr)
        return 2

    codes = _parse_codes(args.codes)
    if not codes:
        print("codes 为空。", file=sys.stderr)
        return 2

    try:
        data_dir = getattr(xtdata, "data_dir", None)
        if data_dir:
            print("xtdata.data_dir =", data_dir)
    except Exception:
        pass

    if args.download_history:
        for code in codes:
            xtdata.download_history_data(code, period=args.period, incrementally=args.incremental)

    if args.download_financial:
        xtdata.download_financial_data(codes)

    if args.download_sector:
        xtdata.download_sector_data()

    history = xtdata.get_market_data_ex([], codes, period=args.period, count=-1)
    print("history_market_data_ex:")
    print(history)

    if not args.subscribe:
        return 0

    def on_quote(data):
        code_list = list(data.keys())
        latest = xtdata.get_market_data_ex([], code_list, period=args.period)
        print("callback_market_data_ex:")
        print(latest)

    for code in codes:
        xtdata.subscribe_quote(
            code,
            period=args.period,
            count=args.subscribe_count,
            callback=on_quote if args.use_callback else None,
        )

    time.sleep(1)

    if args.use_callback:
        xtdata.run()
        return 0

    for _ in range(max(args.loop, 0)):
        latest = xtdata.get_market_data_ex([], codes, period=args.period)
        print("poll_market_data_ex:")
        print(latest)
        time.sleep(args.sleep)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
