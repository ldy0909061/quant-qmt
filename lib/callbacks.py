from xtquant.xttrader import XtQuantTraderCallback

from collections import deque
import threading
import time

from .print_utils import (
    print_type,
    print_xtaccountstatus,
    print_xtcancelerror,
    print_xtcancelorderresponse,
    print_xtorder,
    print_xtordererror,
    print_xtorderresponse,
    print_xtsmtappointmentresponse,
    print_xttrade,
)
from .order_state import OrderState, Status


class CallbackCache:
    def __init__(self, maxlen: int = 2000):
        self._lock = threading.RLock()

        self.stock_orders = deque(maxlen=maxlen)
        self.stock_trades = deque(maxlen=maxlen)
        self.order_errors = deque(maxlen=maxlen)
        self.cancel_errors = deque(maxlen=maxlen)
        self.order_async_responses = deque(maxlen=maxlen)

        self.orders_by_order_id: dict[int, object] = {}
        self.trades_by_traded_id: dict[str, object] = {}
        self.order_errors_by_order_id: dict[int, object] = {}
        self.cancel_errors_by_order_id: dict[int, object] = {}
        self.order_async_responses_by_seq: dict[int, object] = {}
        self.seq_tasks_by_key: dict[tuple[str, int], OrderState] = {}
        self.seq_task_account_id_by_key: dict[tuple[str, int], str] = {}
        self.seq_task_key_by_kind_account_order_id: dict[tuple[str, str, int], tuple[str, int]] = {}
        # TODO: cancel_order 复用 order_id（目标委托号）。如果对同一订单发起多次撤单，会产生多个 cancel seq。
        # TODO: 目前用 (kind, account_id, order_id) 做唯一索引，重复会直接抛异常；需要结合真实回调时序再验证是否合理。

    def _seq_key(self, seq: int, kind: str) -> tuple[str, int]:
        if not isinstance(seq, int) or seq <= 0:
            raise RuntimeError("invalid seq", {"seq": seq})
        if not isinstance(kind, str) or not kind:
            raise RuntimeError("invalid kind", {"kind": kind})
        return (kind, seq)

    def _add_task_indexes(self, key: tuple[str, int], order_id: int | None, account_id: str) -> None:
        if not isinstance(order_id, int) or order_id <= 0:
            return
        idx = (key[0], account_id, order_id)
        existing = self.seq_task_key_by_kind_account_order_id.get(idx)
        if existing is not None and existing != key:
            raise RuntimeError(
                "duplicate kind+account_id+order_id mapping",
                {"idx": idx, "existing": existing, "new": key},
            )
        self.seq_task_key_by_kind_account_order_id[idx] = key

    def _remove_task_indexes(self, key: tuple[str, int], order_id: int | None, account_id: str) -> None:
        if not isinstance(order_id, int) or order_id <= 0:
            return
        idx = (key[0], account_id, order_id)
        existing = self.seq_task_key_by_kind_account_order_id.get(idx)
        if existing == key:
            self.seq_task_key_by_kind_account_order_id.pop(idx, None)

    def _post_update_identity_check(self, key: tuple[str, int], task: OrderState, old_order_id: int | None, old_account_id: str) -> None:
        account_id = self.seq_task_account_id_by_key.get(key)
        if not isinstance(account_id, str) or not account_id:
            raise RuntimeError("seq task missing account_id mapping", {"key": key})
        if old_account_id != account_id:
            raise RuntimeError(
                "seq task changed account_id unexpectedly",
                {"key": key, "old_account_id": old_account_id, "new_account_id": account_id},
            )

        if old_order_id == task.order_id:
            return
        if old_order_id is None and isinstance(task.order_id, int) and task.order_id > 0:
            self._add_task_indexes(key, task.order_id, account_id)
            return
        raise RuntimeError(
            "seq task changed order_id unexpectedly",
            {"key": key, "old_order_id": old_order_id, "new_order_id": task.order_id},
        )

    def record_stock_order(self, order) -> None:
        with self._lock:
            self.stock_orders.append(order)
            oid = getattr(order, "order_id", None)
            if isinstance(oid, int):
                self.orders_by_order_id[oid] = order

    def record_stock_trade(self, trade) -> None:
        with self._lock:
            self.stock_trades.append(trade)
            tid = getattr(trade, "traded_id", None)
            if isinstance(tid, str) and tid:
                self.trades_by_traded_id[tid] = trade

    def record_order_error(self, order_error) -> None:
        with self._lock:
            self.order_errors.append(order_error)
            oid = getattr(order_error, "order_id", None)
            msg = getattr(order_error, "error_msg", None)
            account_id = getattr(order_error, "account_id", None)
            if not isinstance(oid, int) or oid <= 0:
                raise RuntimeError("order_error missing order_id", {"order_id": oid})
            if not isinstance(account_id, str) or not account_id:
                raise RuntimeError(
                    "order_error missing account_id",
                    {"account_id": account_id, "order_id": oid},
                )
            self.order_errors_by_order_id[oid] = order_error
            self.mark_failed_by_order_id("order", account_id, oid, error_msg=msg)

    def record_cancel_error(self, cancel_error) -> None:
        with self._lock:
            self.cancel_errors.append(cancel_error)
            oid = getattr(cancel_error, "order_id", None)
            if isinstance(oid, int):
                self.cancel_errors_by_order_id[oid] = cancel_error

    def record_order_async_response(self, response) -> None:
        with self._lock:
            self.order_async_responses.append(response)
            seq = getattr(response, "seq", None)
            if isinstance(seq, int):
                self.order_async_responses_by_seq[seq] = response

    def record_seq_sent(
        self,
        seq: int,
        kind: str,
        account_id: str,
        stock_code: str | None = None,
        order_id: int | None = None,
        order_remark: str | None = None,
    ) -> None:
        if not isinstance(account_id, str) or not account_id:
            raise RuntimeError("record_seq_sent missing account_id", {"seq": seq, "kind": kind})
        key = self._seq_key(seq, kind)
        now = int(time.time())
        with self._lock:
            if key in self.seq_tasks_by_key:
                raise RuntimeError("record_seq_sent duplicate seq task", {"key": key, "seq": seq, "kind": kind})
            task = OrderState(
                seq=seq,
                status=Status.CANCELING if kind == "cancel_order" else Status.SUBMITTING,
                order_id=order_id,
                stock_code=stock_code,
                created_ts=now,
                update_ts=now,
                is_canceling=(kind == "cancel_order"),
            )
            self.seq_tasks_by_key[key] = task
            self.seq_task_account_id_by_key[key] = account_id
            self._add_task_indexes(key, task.order_id, account_id)

    def mark_seq_successful(
        self,
        seq: int,
        kind: str,
        order_id: int | None = None,
        account_id: str | None = None,
        cancel_result: int | None = None,
        order_remark: str | None = None,
    ) -> None:
        key = self._seq_key(seq, kind)
        now = int(time.time())
        with self._lock:
            task = self.seq_tasks_by_key.get(key)
            if task is None:
                raise RuntimeError("mark_seq_successful missing seq task", {"key": key, "seq": seq, "kind": kind})
            old_order_id = task.order_id
            old_account_id = self.seq_task_account_id_by_key.get(key)
            if not isinstance(old_account_id, str) or not old_account_id:
                raise RuntimeError("mark_seq_successful missing account_id mapping", {"key": key, "seq": seq, "kind": kind})
            task.status = Status.CANCELED if kind == "cancel_order" else Status.SUBMITTED
            task.update_ts = now
            if account_id is not None and account_id != old_account_id:
                raise RuntimeError(
                    "mark_seq_successful account_id mismatch",
                    {"key": key, "existing": old_account_id, "incoming": account_id},
                )
            if order_id is not None:
                task.order_id = order_id
            if kind == "cancel_order":
                task.is_canceling = False
                if cancel_result == 0:
                    task.is_canceld = True
            self._post_update_identity_check(key, task, old_order_id, old_account_id)

    def upsert_seq_task_order_response(
        self,
        seq: int,
        order_id: int | None = None,
        order_remark: str | None = None,
        account_id: str | None = None,
        kind: str = "order",
    ) -> None:
        key = self._seq_key(seq, kind)
        now = int(time.time())
        with self._lock:
            task = self.seq_tasks_by_key.get(key)
            if task is None:
                raise RuntimeError(
                    "upsert_seq_task_order_response missing seq task",
                    {"key": key, "seq": seq, "kind": kind},
                )

            old_order_id = task.order_id
            old_account_id = self.seq_task_account_id_by_key.get(key)
            if not isinstance(old_account_id, str) or not old_account_id:
                raise RuntimeError("upsert_seq_task_order_response missing account_id mapping", {"key": key, "seq": seq, "kind": kind})
            task.update_ts = now
            if account_id is not None and account_id != old_account_id:
                raise RuntimeError(
                    "upsert_seq_task_order_response account_id mismatch",
                    {"key": key, "existing": old_account_id, "incoming": account_id},
                )
            if order_id is not None:
                task.order_id = order_id
            self._post_update_identity_check(key, task, old_order_id, old_account_id)

    def mark_seq_failed(
        self,
        seq: int,
        kind: str,
        account_id: str | None = None,
        error_msg: str | None = None,
        cancel_result: int | None = None,
    ) -> None:
        key = self._seq_key(seq, kind)
        now = int(time.time())
        with self._lock:
            task = self.seq_tasks_by_key.get(key)
            if task is None:
                raise RuntimeError("mark_seq_failed missing seq task", {"key": key, "seq": seq, "kind": kind})
            old_order_id = task.order_id
            old_account_id = self.seq_task_account_id_by_key.get(key)
            if not isinstance(old_account_id, str) or not old_account_id:
                raise RuntimeError("mark_seq_failed missing account_id mapping", {"key": key, "seq": seq, "kind": kind})
            task.status = Status.CANCEL_FAILED if kind == "cancel_order" else Status.REJECTED
            task.update_ts = now
            if account_id is not None and account_id != old_account_id:
                raise RuntimeError(
                    "mark_seq_failed account_id mismatch",
                    {"key": key, "existing": old_account_id, "incoming": account_id},
                )
            if error_msg is not None:
                task.error_msg = error_msg
            if kind == "cancel_order":
                task.is_canceling = False
            self._post_update_identity_check(key, task, old_order_id, old_account_id)

    def mark_failed_by_order_id(self, kind: str, account_id: str, order_id: int, error_msg: str | None = None) -> bool:
        if not isinstance(account_id, str) or not account_id:
            raise RuntimeError("mark_failed_by_order_id invalid account_id", {"account_id": account_id})
        if not isinstance(order_id, int) or order_id <= 0:
            raise RuntimeError("mark_failed_by_order_id invalid order_id", {"order_id": order_id})
        now = int(time.time())
        with self._lock:
            idx = (kind, account_id, order_id)
            key = self.seq_task_key_by_kind_account_order_id.get(idx)
            if key is None:
                raise RuntimeError(
                    "mark_failed_by_order_id missing seq task for order_id",
                    {"kind": kind, "account_id": account_id, "order_id": order_id, "idx": idx},
                )
            task = self.seq_tasks_by_key.get(key)
            if task is None:
                raise RuntimeError(
                    "mark_failed_by_order_id index corrupted",
                    {"account_id": account_id, "order_id": order_id, "key": key, "idx": idx},
                )
            if key[0] != kind:
                raise RuntimeError(
                    "mark_failed_by_order_id kind mismatch",
                    {"expected_kind": kind, "actual_kind": key[0], "account_id": account_id, "order_id": order_id},
                )
            task.status = Status.CANCEL_FAILED if kind == "cancel_order" else Status.REJECTED
            task.update_ts = now
            if error_msg is not None:
                task.error_msg = error_msg
            if kind == "cancel_order":
                task.is_canceling = False
            return True
        return True

    def get_seq_task(self, seq: int, kind: str) -> OrderState | None:
        key = self._seq_key(seq, kind)
        with self._lock:
            return self.seq_tasks_by_key.get(key)

    @property
    def last_order(self):
        with self._lock:
            return self.stock_orders[-1] if self.stock_orders else None

    @property
    def last_trade(self):
        with self._lock:
            return self.stock_trades[-1] if self.stock_trades else None

    @property
    def last_order_error(self):
        with self._lock:
            return self.order_errors[-1] if self.order_errors else None

    @property
    def last_cancel_error(self):
        with self._lock:
            return self.cancel_errors[-1] if self.cancel_errors else None

    @property
    def last_order_async_response(self):
        with self._lock:
            return self.order_async_responses[-1] if self.order_async_responses else None


class PrintCallback(XtQuantTraderCallback):
    def __init__(self, cache: CallbackCache | None = None):
        self.cache = cache or CallbackCache()

    def on_disconnected(self):
        print("on_disconnected")

    def on_account_status(self, status):
        print_type("account_status", status)
        print_xtaccountstatus(status)

    def on_stock_order(self, order):
        self.cache.record_stock_order(order)
        print_type("order", order)
        print_xtorder(order)

    def on_stock_trade(self, trade):
        self.cache.record_stock_trade(trade)
        print_type("trade", trade)
        print_xttrade(trade)

    def on_order_error(self, order_error):
        self.cache.record_order_error(order_error)
        print_type("order_error", order_error)
        print_xtordererror(order_error)

    def on_cancel_error(self, cancel_error):
        self.cache.record_cancel_error(cancel_error)
        print_type("cancel_error", cancel_error)
        print_xtcancelerror(cancel_error)

    def on_order_stock_async_response(self, response):
        self.cache.record_order_async_response(response)
        seq = getattr(response, "seq", None)
        account_id = getattr(response, "account_id", None)
        order_id = getattr(response, "order_id", None)
        order_remark = getattr(response, "order_remark", None)
        self.cache.upsert_seq_task_order_response(
            seq,
            order_id=order_id,
            order_remark=order_remark,
            account_id=account_id,
            kind="order",
        )
        print_type("order_response", response)
        print_xtorderresponse(response)

    def on_smt_appointment_async_response(self, response):
        print_type("smt_appointment_response", response)
        print_xtsmtappointmentresponse(response)

    def on_cancel_order_stock_async_response(self, response):
        print_type("cancel_order_response", response)
        print_xtcancelorderresponse(response)
        seq = getattr(response, "seq", None)
        account_id = getattr(response, "account_id", None)
        cancel_result = getattr(response, "cancel_result", None)
        if cancel_result == 0:
            self.cache.mark_seq_successful(seq, "cancel_order", account_id=account_id, cancel_result=cancel_result)
        else:
            self.cache.mark_seq_failed(seq, "cancel_order", account_id=account_id, cancel_result=cancel_result)
