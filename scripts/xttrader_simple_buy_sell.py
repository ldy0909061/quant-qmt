import argparse
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.trading import TraderService


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="xttrader_simple_buy_sell",
        description="XtQuant xttrader: 查询资产/持仓 + 买一笔 + 卖一笔 + 回调示例",
    )
    parser.add_argument("--account-id", required=True, help="资金账号，例如: 1234567890")
    parser.add_argument("--account-type", default="STOCK", help='账号类型，默认 "STOCK"')
    parser.add_argument(
        "--qmt-path",
        default=str(Path.home() / "app" / "国金证券QMT交易端" / "userdata_mini"),
        help="MiniQMT userdata_mini 路径（XtQuantTrader 的 path 参数）",
    )
    parser.add_argument("--session", type=int, default=1, help="会话号（同一台机器上需区分）")

    parser.add_argument("--code", default="000001.SZ", help='证券代码，例如: "000001.SZ"')
    parser.add_argument("--price", type=float, default=0.0, help="委托价格（FIX_PRICE 时必填）")
    parser.add_argument(
        "--price-type",
        default="FIX_PRICE",
        help="价格类型：FIX_PRICE / LATEST_PRICE / MARKET_MINE_PRICE_FIRST / MARKET_PEER_PRICE_FIRST",
    )
    parser.add_argument("--buy-volume", type=int, default=0, help="买入数量（>0 才会下买单）")
    parser.add_argument("--sell-volume", type=int, default=0, help="卖出数量（>0 才会下卖单）")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="真的下单（不加此参数仅演示查询/打印，不会发单）",
    )
    parser.add_argument(
        "--cancel-order-id",
        action="append",
        type=int,
        default=[],
        help="异步撤单：指定要撤的 order_id（可重复传入多个）",
    )
    parser.add_argument(
        "--cancel-last",
        type=int,
        default=0,
        help="异步撤单：从可撤委托中按时间倒序撤前 N 笔（需要 --confirm）",
    )
    parser.add_argument(
        "--query-positions",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否查询持仓（默认查询）",
    )
    parser.add_argument(
        "--query-orders",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否查询当日委托（默认查询）",
    )
    parser.add_argument(
        "--cancelable-only",
        action="store_true",
        help="仅查询可撤委托（query_stock_orders 的 cancelable_only=True）",
    )
    parser.add_argument("--wait", type=float, default=5.0, help="下单/撤单后等待回调秒数")
    parser.add_argument(
        "--dump-raw",
        action="store_true",
        help="打印 query 返回对象的详细属性（用于看返回结构）",
    )

    args = parser.parse_args(argv)

    try:
        from xtquant import xtconstant
    except Exception as e:
        print("导入 xtquant 失败：", e, file=sys.stderr)
        return 2

    qmt_path = Path(args.qmt_path)
    if not qmt_path.exists():
        print("qmt-path 不存在：", str(qmt_path), file=sys.stderr)
        return 2

    svc = TraderService(qmt_path, args.account_id, account_type=args.account_type, session_id=args.session)
    trader = svc.get_trader()
    if trader is None:
        return 2

    svc.query_asset(args.dump_raw)

    if args.query_positions:
        svc.query_positions(args.dump_raw)
    else:
        print("positions_skipped: True")

    if args.query_orders:
        svc.query_orders(args.cancelable_only, args.dump_raw)
    else:
        print("orders_skipped: True")

    cancel_order_ids = svc.collect_cancel_order_ids(list(args.cancel_order_id or []), args.cancel_last)
    svc.cancel_orders_async(args.confirm, cancel_order_ids)

    do_order = (args.buy_volume > 0) or (args.sell_volume > 0)
    if do_order:
        price_type = getattr(xtconstant, args.price_type, None)
        if price_type is None:
            print("未知 price-type：", args.price_type, file=sys.stderr)
            trader.stop()
            return 2
        order_rc = svc.order_async(
            args.confirm,
            args.code,
            args.buy_volume,
            args.sell_volume,
            price_type,
            args.price,
        )
        if order_rc != 0:
            svc.stop()
            return order_rc

    if args.wait > 0:
        time.sleep(args.wait)

    svc.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
