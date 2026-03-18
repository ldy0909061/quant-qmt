import random
import sys

from .print_utils import dump_object, print_type, print_xtasset, print_xtorder, print_xtposition


class TraderService:
    def __init__(
        self,
        path,
        account_id: str,
        account_type: str = "STOCK",
        callback=None,
        session_id: int | None = None,
        session_id_candidates: list[int] | None = None,
    ):
        self.path = str(path)
        from xtquant.xttype import StockAccount

        self.account_id = account_id
        self.account_type = account_type
        self.account = StockAccount(account_id, account_type)
        if callback is None:
            from .callbacks import PrintCallback

            callback = PrintCallback()
        self.callback = callback
        self.session_id = session_id
        self.session_id_candidates = session_id_candidates or list(range(100, 120))
        self.trader = None

    def _make_callback_proxy(self):
        from xtquant.xttrader import XtQuantTraderCallback

        outer = self
        delegate = self.callback

        class _CallbackProxy(XtQuantTraderCallback):
            def __getattr__(self, name: str):
                return getattr(delegate, name)

            def on_disconnected(self):
                try:
                    fn = getattr(delegate, "on_disconnected", None)
                    if callable(fn):
                        fn()
                finally:
                    outer.trader = None

        return _CallbackProxy()

    def create_trader(self, session_id: int):
        from xtquant.xttrader import XtQuantTrader

        callback = self._make_callback_proxy()
        trader = XtQuantTrader(self.path, session_id)
        trader.register_callback(callback)
        trader.start()

        connect_result = trader.connect()
        print("connect_result:", connect_result)
        if connect_result != 0:
            trader.stop()
            return None, connect_result, None

        subscribe_result = trader.subscribe(self.account)
        print("subscribe_result:", subscribe_result)

        self.trader = trader
        self.session_id = session_id
        return trader, connect_result, subscribe_result

    def try_connect(self):
        candidates = list(self.session_id_candidates)
        random.shuffle(candidates)
        for sid in candidates:
            trader, connect_result, subscribe_result = self.create_trader(sid)
            if trader is not None and connect_result == 0:
                print("connect_ok_session_id:", sid)
                return trader
        # todo，走到这里应该报警
        print("connect_failed")
        return None

    def get_trader(self):
        if self.trader is not None:
            return self.trader
        if self.session_id is not None:
            trader, connect_result, subscribe_result = self.create_trader(self.session_id)
            if trader is not None and connect_result == 0:
                return trader
        return self.try_connect()

    def stop(self):
        trader = self.trader
        self.trader = None
        if trader is not None:
            trader.stop()

    def query_asset(self, dump_raw: bool) -> None:
        trader = self.get_trader()
        if trader is None:
            print("trader_not_connected")
            return
        asset = trader.query_stock_asset(self.account)
        print_type("asset", asset)
        print_xtasset(asset)
        if dump_raw:
            dump_object(asset, "asset_raw")

    def query_positions(self, dump_raw: bool) -> float:
        trader = self.get_trader()
        if trader is None:
            print("trader_not_connected")
            return 0.0
        positions = trader.query_stock_positions(self.account) or []
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

    def query_orders(self, cancelable_only: bool, dump_raw: bool) -> list:
        trader = self.get_trader()
        if trader is None:
            print("trader_not_connected")
            return []
        orders = trader.query_stock_orders(self.account, cancelable_only) or []
        print("orders_count:", len(orders))
        for o in orders:
            print_type("order", o)
            print_xtorder(o)
            if dump_raw:
                dump_object(o, "order_raw")
        return orders

    def collect_cancel_order_ids(self, explicit_ids: list[int], cancel_last: int) -> list[int]:
        cancel_order_ids: list[int] = [oid for oid in (explicit_ids or []) if isinstance(oid, int) and oid > 0]
        if cancel_last and cancel_last > 0:
            trader = self.get_trader()
            if trader is None:
                return list(dict.fromkeys(cancel_order_ids))
            cancelable_orders = trader.query_stock_orders(self.account, True) or []
            cancelable_order_ids = [
                getattr(o, "order_id", None) for o in cancelable_orders if getattr(o, "order_id", None)
            ]
            cancel_order_ids.extend(
                [oid for oid in cancelable_order_ids[-cancel_last:] if isinstance(oid, int) and oid > 0]
            )
        return list(dict.fromkeys(cancel_order_ids))

    def cancel_orders_async(self, confirm: bool, order_ids: list[int]) -> None:
        trader = self.get_trader()
        if trader is None:
            print("trader_not_connected")
            return
        if not order_ids:
            return
        if not confirm:
            print("cancel_skipped: confirm_not_enabled")
            return
        print("cancel_order_ids:", order_ids)
        for oid in order_ids:
            cancel_seq = trader.cancel_order_stock_async(self.account, oid)
            print("cancel_seq:", cancel_seq)

    def order_async(
        self,
        xtconstant,
        confirm: bool,
        code: str,
        buy_volume: int,
        sell_volume: int,
        price_type,
        price: float,
    ) -> int:
        trader = self.get_trader()
        if trader is None:
            print("trader_not_connected")
            return 2

        do_order = (buy_volume > 0) or (sell_volume > 0)
        if not do_order:
            return 0
        if not confirm:
            print("order_skipped: confirm_not_enabled")
            return 0
        allowed_price_types = {
            getattr(xtconstant, "LATEST_PRICE", None),
            getattr(xtconstant, "FIX_PRICE", None),
            getattr(xtconstant, "MARKET_PEER_PRICE_FIRST", None),
            getattr(xtconstant, "MARKET_MINE_PRICE_FIRST", None),
        }
        allowed_price_types.discard(None)

        if price_type not in allowed_price_types:
            print("不支持的 price_type:", price_type, file=sys.stderr)
            return 2
        if price_type == xtconstant.FIX_PRICE and price <= 0:
            print("FIX_PRICE 下单需要 --price > 0", file=sys.stderr)
            return 2

        if buy_volume > 0:
            buy_seq = trader.order_stock_async(
                self.account,
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
                self.account,
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
