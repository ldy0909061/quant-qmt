import sys


def safe_repr(value: object, max_len: int = 400) -> str:
    try:
        s = repr(value)
    except Exception as e:
        s = f"<repr_failed {type(e).__name__}: {e}>"
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def dump_object(obj: object, title: str, max_attrs: int = 80) -> None:
    print(f"{title}:")
    if obj is None:
        print("  (None)")
        return

    print("  type:", type(obj))
    print("  repr:", safe_repr(obj))

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
        print(f"  {a}: {safe_repr(v)}")


def print_type(prefix: str, obj: object) -> None:
    print(f"{prefix}_type:", type(obj).__name__)


def print_fields(title: str, obj: object, fields: list[str]) -> None:
    print(f"{title}:")
    if obj is None:
        print("  (None)")
        return
    for f in fields:
        print(f"  {f}:", safe_repr(getattr(obj, f, None)))


def print_xtasset(asset) -> None:
    print_fields(
        "asset",
        asset,
        ["account_type", "account_id", "cash", "frozen_cash", "market_value", "total_asset"],
    )


def print_xtposition(position) -> None:
    print_fields(
        "position",
        position,
        [
            "account_type",
            "account_id",
            "stock_code",
            "volume",
            "can_use_volume",
            "open_price",
            "market_value",
            "frozen_volume",
            "on_road_volume",
            "yesterday_volume",
            "avg_price",
            "direction",
        ],
    )


def print_xtorder(order) -> None:
    print_fields(
        "order",
        order,
        [
            "account_type",
            "account_id",
            "stock_code",
            "order_id",
            "order_sysid",
            "order_time",
            "order_type",
            "order_volume",
            "price_type",
            "price",
            "traded_volume",
            "traded_price",
            "order_status",
            "status_msg",
            "strategy_name",
            "order_remark",
            "direction",
            "offset_flag",
        ],
    )


def print_xttrade(trade) -> None:
    print_fields(
        "trade",
        trade,
        [
            "account_type",
            "account_id",
            "stock_code",
            "order_type",
            "traded_id",
            "traded_time",
            "traded_price",
            "traded_volume",
            "traded_amount",
            "order_id",
            "order_sysid",
            "strategy_name",
            "order_remark",
            "direction",
            "offset_flag",
        ],
    )


def print_xtaccountstatus(status) -> None:
    print_fields("account_status", status, ["account_type", "account_id", "status"])


def print_xtorderresponse(response) -> None:
    print_fields(
        "order_response",
        response,
        ["account_type", "account_id", "order_id", "strategy_name", "order_remark", "seq"],
    )


def print_xtcancelorderresponse(response) -> None:
    print_fields(
        "cancel_order_response",
        response,
        ["account_type", "account_id", "order_id", "order_sysid", "cancel_result", "seq"],
    )


def print_xtordererror(order_error) -> None:
    print_fields(
        "order_error",
        order_error,
        ["account_type", "account_id", "order_id", "error_id", "error_msg", "strategy_name", "order_remark"],
    )


def print_xtcancelerror(cancel_error) -> None:
    print_fields(
        "cancel_error",
        cancel_error,
        ["account_type", "account_id", "order_id", "market", "order_sysid", "error_id", "error_msg"],
    )
