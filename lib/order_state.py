from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class OrderStatus(IntEnum):
    ORDER_UNREPORTED = 48
    ORDER_WAIT_REPORTING = 49
    ORDER_REPORTED = 50
    ORDER_REPORTED_CANCEL = 51
    ORDER_PARTSUCC_CANCEL = 52
    ORDER_PART_CANCEL = 53
    ORDER_CANCELED = 54
    ORDER_PART_SUCC = 55
    ORDER_SUCCEEDED = 56
    ORDER_JUNK = 57
    ORDER_UNKNOWN = 255


Status = OrderStatus


@dataclass(slots=True)
class OrderState:
    order_id: int | None
    stock_code: str | None
    target_volume: int = 0
    traded_volume: int = 0
    status: OrderStatus = OrderStatus.ORDER_UNREPORTED
    seq: int = 0
    is_canceling: bool = False
    is_canceld: bool = False
    error_msg: str | None = None
    created_ts: int = 0
    update_ts: int = 0
    trades: list[Any] = field(default_factory=list)

    @property
    def is_canceled(self) -> bool:
        return self.is_canceld

    @is_canceled.setter
    def is_canceled(self, value: bool) -> None:
        self.is_canceld = bool(value)

    def remaining(self) -> int:
        r = self.target_volume - self.traded_volume
        return r if r > 0 else 0

    def is_finished(self) -> bool:
        return self.status in {OrderStatus.ORDER_SUCCEEDED, OrderStatus.ORDER_CANCELED, OrderStatus.ORDER_JUNK}

    def final_state(self) -> OrderStatus:
        if self.traded_volume == self.target_volume and self.target_volume > 0:
            return OrderStatus.ORDER_SUCCEEDED
        if self.is_canceled:
            if self.traded_volume > 0:
                return OrderStatus.ORDER_PART_CANCEL
            return OrderStatus.ORDER_CANCELED
        if self.traded_volume > 0:
            return OrderStatus.ORDER_PART_SUCC
        return OrderStatus.ORDER_UNREPORTED
