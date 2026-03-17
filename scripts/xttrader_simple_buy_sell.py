import argparse
import sys
import time
from pathlib import Path


def _safe_repr(value: object, max_len: int = 400) -> str:
    try:
        s = repr(value)
    except Exception as e:
        s = f"<repr_failed {type(e).__name__}: {e}>"
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def _dump_object(obj: object, title: str, max_attrs: int = 80) -> None:
    print(f"{title}:")
    if obj is None:
        print("  (None)")
        return

    print("  type:", type(obj))
    print("  repr:", _safe_repr(obj))

    attrs = []
    try:
        attrs = [a for a in dir(obj) if not a.startswith("_")]
    except Exception:
        attrs = []

    if not attrs:
        return

    attrs = sorted(attrs)[:max_attrs]
    for a in attrs:
        try:
            v = getattr(obj, a)
        except Exception as e:
            print(f"  {a}: <getattr_failed {type(e).__name__}: {e}>")
            continue
        if callable(v):
            continue
        print(f"  {a}: {_safe_repr(v)}")


def _print_xtasset(asset) -> None:
    print("asset:")
    if asset is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(asset, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(asset, "account_id", None)))
    print("  cash:", _safe_repr(getattr(asset, "cash", None)))
    print("  frozen_cash:", _safe_repr(getattr(asset, "frozen_cash", None)))
    print("  market_value:", _safe_repr(getattr(asset, "market_value", None)))
    print("  total_asset:", _safe_repr(getattr(asset, "total_asset", None)))


def _print_xtposition(position) -> None:
    print("position:")
    if position is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(position, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(position, "account_id", None)))
    print("  stock_code:", _safe_repr(getattr(position, "stock_code", None)))
    print("  volume:", _safe_repr(getattr(position, "volume", None)))
    print("  can_use_volume:", _safe_repr(getattr(position, "can_use_volume", None)))
    print("  open_price:", _safe_repr(getattr(position, "open_price", None)))
    print("  market_value:", _safe_repr(getattr(position, "market_value", None)))
    print("  frozen_volume:", _safe_repr(getattr(position, "frozen_volume", None)))
    print("  on_road_volume:", _safe_repr(getattr(position, "on_road_volume", None)))
    print("  yesterday_volume:", _safe_repr(getattr(position, "yesterday_volume", None)))
    print("  avg_price:", _safe_repr(getattr(position, "avg_price", None)))
    print("  direction:", _safe_repr(getattr(position, "direction", None)))


def _print_xtorder(order) -> None:
    print("order:")
    if order is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(order, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(order, "account_id", None)))
    print("  stock_code:", _safe_repr(getattr(order, "stock_code", None)))
    print("  order_id:", _safe_repr(getattr(order, "order_id", None)))
    print("  order_sysid:", _safe_repr(getattr(order, "order_sysid", None)))
    print("  order_time:", _safe_repr(getattr(order, "order_time", None)))
    print("  order_type:", _safe_repr(getattr(order, "order_type", None)))
    print("  order_volume:", _safe_repr(getattr(order, "order_volume", None)))
    print("  price_type:", _safe_repr(getattr(order, "price_type", None)))
    print("  price:", _safe_repr(getattr(order, "price", None)))
    print("  traded_volume:", _safe_repr(getattr(order, "traded_volume", None)))
    print("  traded_price:", _safe_repr(getattr(order, "traded_price", None)))
    print("  order_status:", _safe_repr(getattr(order, "order_status", None)))
    print("  status_msg:", _safe_repr(getattr(order, "status_msg", None)))
    print("  strategy_name:", _safe_repr(getattr(order, "strategy_name", None)))
    print("  order_remark:", _safe_repr(getattr(order, "order_remark", None)))
    print("  direction:", _safe_repr(getattr(order, "direction", None)))
    print("  offset_flag:", _safe_repr(getattr(order, "offset_flag", None)))


def _print_xttrade(trade) -> None:
    print("trade:")
    if trade is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(trade, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(trade, "account_id", None)))
    print("  stock_code:", _safe_repr(getattr(trade, "stock_code", None)))
    print("  order_type:", _safe_repr(getattr(trade, "order_type", None)))
    print("  traded_id:", _safe_repr(getattr(trade, "traded_id", None)))
    print("  traded_time:", _safe_repr(getattr(trade, "traded_time", None)))
    print("  traded_price:", _safe_repr(getattr(trade, "traded_price", None)))
    print("  traded_volume:", _safe_repr(getattr(trade, "traded_volume", None)))
    print("  traded_amount:", _safe_repr(getattr(trade, "traded_amount", None)))
    print("  order_id:", _safe_repr(getattr(trade, "order_id", None)))
    print("  order_sysid:", _safe_repr(getattr(trade, "order_sysid", None)))
    print("  strategy_name:", _safe_repr(getattr(trade, "strategy_name", None)))
    print("  order_remark:", _safe_repr(getattr(trade, "order_remark", None)))
    print("  direction:", _safe_repr(getattr(trade, "direction", None)))
    print("  offset_flag:", _safe_repr(getattr(trade, "offset_flag", None)))


def _print_xtaccountstatus(status) -> None:
    print("account_status:")
    if status is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(status, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(status, "account_id", None)))
    print("  status:", _safe_repr(getattr(status, "status", None)))


def _print_xtorderresponse(response) -> None:
    print("order_response:")
    if response is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(response, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(response, "account_id", None)))
    print("  order_id:", _safe_repr(getattr(response, "order_id", None)))
    print("  strategy_name:", _safe_repr(getattr(response, "strategy_name", None)))
    print("  order_remark:", _safe_repr(getattr(response, "order_remark", None)))
    print("  seq:", _safe_repr(getattr(response, "seq", None)))


def _print_xtcancelorderresponse(response) -> None:
    print("cancel_order_response:")
    if response is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(response, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(response, "account_id", None)))
    print("  order_id:", _safe_repr(getattr(response, "order_id", None)))
    print("  order_sysid:", _safe_repr(getattr(response, "order_sysid", None)))
    print("  cancel_result:", _safe_repr(getattr(response, "cancel_result", None)))
    print("  seq:", _safe_repr(getattr(response, "seq", None)))


def _print_xtordererror(order_error) -> None:
    print("order_error:")
    if order_error is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(order_error, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(order_error, "account_id", None)))
    print("  order_id:", _safe_repr(getattr(order_error, "order_id", None)))
    print("  error_id:", _safe_repr(getattr(order_error, "error_id", None)))
    print("  error_msg:", _safe_repr(getattr(order_error, "error_msg", None)))
    print("  strategy_name:", _safe_repr(getattr(order_error, "strategy_name", None)))
    print("  order_remark:", _safe_repr(getattr(order_error, "order_remark", None)))


def _print_xtcancelerror(cancel_error) -> None:
    print("cancel_error:")
    if cancel_error is None:
        print("  (None)")
        return
    print("  account_type:", _safe_repr(getattr(cancel_error, "account_type", None)))
    print("  account_id:", _safe_repr(getattr(cancel_error, "account_id", None)))
    print("  order_id:", _safe_repr(getattr(cancel_error, "order_id", None)))
    print("  market:", _safe_repr(getattr(cancel_error, "market", None)))
    print("  order_sysid:", _safe_repr(getattr(cancel_error, "order_sysid", None)))
    print("  error_id:", _safe_repr(getattr(cancel_error, "error_id", None)))
    print("  error_msg:", _safe_repr(getattr(cancel_error, "error_msg", None)))

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
        help='价格类型：FIX_PRICE / MARKET_MINE_PRICE_FIRST / MARKET_PEER_PRICE_FIRST',
    )
    parser.add_argument("--buy-volume", type=int, default=0, help="买入数量（>0 才会下买单）")
    parser.add_argument("--sell-volume", type=int, default=0, help="卖出数量（>0 才会下卖单）")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="真的下单（不加此参数仅演示查询/打印，不会发单）",
    )
    parser.add_argument("--wait", type=float, default=5.0, help="下单后等待回调秒数")
    parser.add_argument(
        "--dump-raw",
        action="store_true",
        help="打印 query 返回对象的详细属性（用于看 XtAsset/XtPosition 的 raw 结构）",
    )

    args = parser.parse_args(argv)

    try:
        from xtquant.xttrader import XtQuantTrader
        from xtquant.xttrader import XtQuantTraderCallback
        from xtquant.xttype import (
            StockAccount,
            XtAccountStatus,
            XtAsset,
            XtCancelError,
            XtCancelOrderResponse,
            XtOrder,
            XtOrderError,
            XtOrderResponse,
            XtPosition,
            XtTrade,
        )
        from xtquant import xtconstant
    except Exception as e:
        print("导入 xtquant 失败：", e, file=sys.stderr)
        return 2

    class PrintCallback(XtQuantTraderCallback):
        def on_connected(self):
            print("on_connected")

        def on_disconnected(self):
            print("on_disconnected")

        def on_account_status(self, status):
            print("account_status_type:", type(status).__name__)
            _print_xtaccountstatus(status)

        def on_stock_asset(self, asset):
            print("asset_type:", type(asset).__name__)
            _print_xtasset(asset)

        def on_stock_position(self, position):
            print("position_type:", type(position).__name__)
            _print_xtposition(position)

        def on_stock_order(self, order):
            print("order_type:", type(order).__name__)
            _print_xtorder(order)

        def on_stock_trade(self, trade):
            print("trade_type:", type(trade).__name__)
            _print_xttrade(trade)

        def on_order_error(self, order_error):
            print("order_error_type:", type(order_error).__name__)
            _print_xtordererror(order_error)

        def on_cancel_error(self, cancel_error):
            print("cancel_error_type:", type(cancel_error).__name__)
            _print_xtcancelerror(cancel_error)

        def on_order_stock_async_response(self, response):
            print("order_response_type:", type(response).__name__)
            _print_xtorderresponse(response)

        def on_cancel_order_stock_async_response(self, response):
            print("cancel_order_response_type:", type(response).__name__)
            _print_xtcancelorderresponse(response)

    qmt_path = Path(args.qmt_path)
    if not qmt_path.exists():
        print("qmt-path 不存在：", str(qmt_path), file=sys.stderr)
        return 2

    account = StockAccount(args.account_id, args.account_type)

    callback = PrintCallback()
    trader = XtQuantTrader(str(qmt_path), args.session)
    trader.register_callback(callback)
    trader.start()
    connect_result = trader.connect()
    print("connect_result:", connect_result)

    asset = trader.query_stock_asset(account)
    print("asset_type:", type(asset).__name__)
    _print_xtasset(asset)
    if args.dump_raw:
        _dump_object(asset, "asset_raw")

    positions = trader.query_stock_positions(account) or []
    print("positions_count:", len(positions))
    total_position_market_value = 0.0
    
    for p in positions:
        print("position_type:", type(p).__name__)
        _print_xtposition(p)
        if args.dump_raw:
            _dump_object(p, "position_raw")
        try:
            total_position_market_value += float(p.market_value or 0)
        except Exception:
            pass
    print("positions_market_value_sum:", total_position_market_value)

    price_type = getattr(xtconstant, args.price_type, None)
    if price_type is None:
        print("未知 price-type：", args.price_type, file=sys.stderr)
        return 2

    if args.confirm:
        if price_type == xtconstant.FIX_PRICE and args.price <= 0:
            print("FIX_PRICE 下单需要 --price > 0", file=sys.stderr)
            return 2

        if args.buy_volume > 0:
            buy_order_id = trader.order_stock(
                account,
                args.code,
                xtconstant.STOCK_BUY,
                args.buy_volume,
                price_type,
                args.price,
                strategy_name="manual_test",
                order_remark="buy_once",
            )
            print("buy_order_id:", buy_order_id)

        if args.sell_volume > 0:
            sell_order_id = trader.order_stock(
                account,
                args.code,
                xtconstant.STOCK_SELL,
                args.sell_volume,
                price_type,
                args.price,
                strategy_name="manual_test",
                order_remark="sell_once",
            )
            print("sell_order_id:", sell_order_id)
    else:
        print("confirm 未开启：不会发单。若需要下单请加 --confirm")

    if args.wait > 0:
        time.sleep(args.wait)

    trader.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
