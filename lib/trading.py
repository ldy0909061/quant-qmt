import sys

from .print_utils import dump_object, print_type, print_xtasset, print_xtorder, print_xtposition


def query_asset(trader, account, dump_raw: bool) -> None:
    asset = trader.query_stock_asset(account)
    print_type("asset", asset)
    print_xtasset(asset)
    if dump_raw:
        dump_object(asset, "asset_raw")


def query_positions(trader, account, dump_raw: bool) -> float:
    positions = trader.query_stock_positions(account) or []
    print("positions_count:", len(positions))
    total_position_market_value = 0.0
    for p in positions:
        print_type("position", p)
        print_xtposition(p)
        if dump_raw:
            dump_object(p, "position_raw")
        try:
            total_position_market_value += float(getattr(p, "market_value", 0) or 0)
        except Exception:
            pass
    print("positions_market_value_sum:", total_position_market_value)
    return total_position_market_value


def query_orders(trader, account, cancelable_only: bool, dump_raw: bool) -> list:
    orders = trader.query_stock_orders(account, cancelable_only) or []
    print("orders_count:", len(orders))
    for o in orders:
        print_type("order", o)
        print_xtorder(o)
        if dump_raw:
            dump_object(o, "order_raw")
    return orders


def collect_cancel_order_ids(trader, account, explicit_ids: list[int], cancel_last: int) -> list[int]:
    cancel_order_ids: list[int] = [oid for oid in (explicit_ids or []) if isinstance(oid, int) and oid > 0]
    if cancel_last and cancel_last > 0:
        cancelable_orders = trader.query_stock_orders(account, True) or []
        cancelable_order_ids = [
            getattr(o, "order_id", None) for o in cancelable_orders if getattr(o, "order_id", None)
        ]
        cancel_order_ids.extend(
            [oid for oid in cancelable_order_ids[-cancel_last:] if isinstance(oid, int) and oid > 0]
        )
    return list(dict.fromkeys(cancel_order_ids))


def cancel_orders_async(trader, account, confirm: bool, order_ids: list[int]) -> None:
    if not order_ids:
        return
    if not confirm:
        print("cancel_skipped: confirm_not_enabled")
        return
    print("cancel_order_ids:", order_ids)
    for oid in order_ids:
        cancel_seq = trader.cancel_order_stock_async(account, oid)
        print("cancel_seq:", cancel_seq)


def order_async(
    trader,
    account,
    xtconstant,
    confirm: bool,
    code: str,
    buy_volume: int,
    sell_volume: int,
    price_type,
    price: float,
) -> int:
    do_order = (buy_volume > 0) or (sell_volume > 0)
    if not do_order:
        return 0
    if not confirm:
        print("order_skipped: confirm_not_enabled")
        return 0
    if price_type is None:
        print("未知 price-type", file=sys.stderr)
        return 2
    if price_type == xtconstant.FIX_PRICE and price <= 0:
        print("FIX_PRICE 下单需要 --price > 0", file=sys.stderr)
        return 2

    if buy_volume > 0:
        buy_seq = trader.order_stock_async(
            account,
            code,
            xtconstant.STOCK_BUY,
            buy_volume,
            price_type,
            price,
            strategy_name="manual_test",
            order_remark="buy_once",
        )
        print("buy_seq:", buy_seq)
    if sell_volume > 0:
        sell_seq = trader.order_stock_async(
            account,
            code,
            xtconstant.STOCK_SELL,
            sell_volume,
            price_type,
            price,
            strategy_name="manual_test",
            order_remark="sell_once",
        )
        print("sell_seq:", sell_seq)

    return 0

