from enum import Enum
from dataclasses import dataclass


class Status(Enum):
    INIT = "INIT"
    SUBMITTING = "SUBMITTING"
    SUBMITTED = "SUBMITTED"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    FILLED = "FILLED"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"
    PARTIAL_CANCEL = "PARTIAL_CANCEL"
    REJECTED = "REJECTED"
    CANCEL_FAILED = "CANCEL_FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class OrderState:
    seq: int
    status: Status
    order_id: int | None
    stock_code: str | None
    target_volume: int = 0
    traded_volume: int = 0
    is_canceling: bool = False
    is_canceld: bool = False
    error_msg: str | None = None
    created_ts: int = 0
    update_ts: int = 0

    @property
    def is_canceled(self) -> bool:
        return self.is_canceld

    def remaining(self) -> int:
        r = self.target_volume - self.traded_volume
        return r if r > 0 else 0

    def is_finished(self) -> bool:
        return self.status in {Status.FILLED, Status.CANCELED, Status.REJECTED}

    def final_state(self) -> Status:
        if self.traded_volume == self.target_volume and self.target_volume > 0:
            return Status.FILLED
        if self.is_canceled:
            if self.traded_volume > 0:
                return Status.PARTIAL_CANCEL
            return Status.CANCELED
        if self.traded_volume > 0:
            return Status.PARTIAL_FILLED
        return Status.INIT
