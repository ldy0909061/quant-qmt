import time

from .order_state import OrderState, OrderStatus


class OrderManager:
    def __init__(self):
        self.orders: dict[int, OrderState] = {}

    def create_order(self, order_id: int, stock_code: str, volume: int) -> OrderState:
        now = int(time.time())
        state = OrderState(order_id=order_id, stock_code=stock_code, target_volume=volume, created_ts=now, update_ts=now)
        self.orders[order_id] = state
        return state

    def on_order(self, order) -> None:
        oid = getattr(order, "order_id", None)
        if not isinstance(oid, int) or oid <= 0:
            return
        state = self.orders.get(oid)
        if state is None:
            return

        raw_status = getattr(order, "order_status", getattr(order, "status", None))
        state.status = self._coerce_status(raw_status)

        ov = getattr(order, "order_volume", None)
        if isinstance(ov, int) and ov > 0:
            state.target_volume = ov

        tv = getattr(order, "traded_volume", None)
        if isinstance(tv, int) and tv >= 0:
            state.traded_volume = tv

        state.is_canceled = state.status in {OrderStatus.ORDER_CANCELED, OrderStatus.ORDER_PART_CANCEL}
        state.is_canceling = state.status in {OrderStatus.ORDER_REPORTED_CANCEL, OrderStatus.ORDER_PARTSUCC_CANCEL}
        state.update_ts = int(time.time())

        print(f"[ORDER] {oid} -> {state.status.name}({int(state.status)})")

    def on_trade(self, trade) -> None:
        oid = getattr(trade, "order_id", None)
        if not isinstance(oid, int) or oid <= 0:
            return
        state = self.orders.get(oid)
        if state is None:
            return

        vol = getattr(trade, "traded_volume", getattr(trade, "volume", 0))
        if not isinstance(vol, int):
            vol = 0
        if vol < 0:
            vol = 0

        state.traded_volume += vol
        state.trades.append(trade)
        state.update_ts = int(time.time())

        print(f"[TRADE] {oid} +{vol}")

        if state.target_volume > 0 and state.traded_volume >= state.target_volume:
            state.status = OrderStatus.ORDER_SUCCEEDED
        elif state.is_canceled:
            state.status = OrderStatus.ORDER_PART_CANCEL if state.traded_volume > 0 else OrderStatus.ORDER_CANCELED
        elif state.is_canceling:
            if state.traded_volume > 0 and state.remaining() > 0:
                state.status = OrderStatus.ORDER_PARTSUCC_CANCEL
            else:
                state.status = OrderStatus.ORDER_REPORTED_CANCEL
        elif state.traded_volume > 0:
            state.status = OrderStatus.ORDER_PART_SUCC

    def mark_cancel(self, order_id: int) -> bool:
        state = self.orders.get(order_id)
        if state is None:
            return False
        if state.is_finished():
            return False
        state.is_canceling = True
        state.status = OrderStatus.ORDER_PARTSUCC_CANCEL if state.traded_volume > 0 else OrderStatus.ORDER_REPORTED_CANCEL
        state.update_ts = int(time.time())
        return True

    def get_result(self, order_id: int) -> OrderStatus | None:
        state = self.orders.get(order_id)
        if state is None:
            return None
        return state.final_state()

    @staticmethod
    def _coerce_status(value) -> OrderStatus:
        if isinstance(value, OrderStatus):
            return value
        if isinstance(value, int):
            try:
                return OrderStatus(value)
            except ValueError:
                return OrderStatus.ORDER_UNKNOWN
        if isinstance(value, str):
            s = value.strip()
            if s.isdigit():
                try:
                    return OrderStatus(int(s))
                except ValueError:
                    return OrderStatus.ORDER_UNKNOWN
        return OrderStatus.ORDER_UNKNOWN
