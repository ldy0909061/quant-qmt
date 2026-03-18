from xtquant.xttrader import XtQuantTraderCallback

from .print_utils import (
    print_type,
    print_xtaccountstatus,
    print_xtasset,
    print_xtcancelerror,
    print_xtcancelorderresponse,
    print_xtorder,
    print_xtordererror,
    print_xtorderresponse,
    print_xtposition,
    print_xttrade,
)


class PrintCallback(XtQuantTraderCallback):
    def on_connected(self):
        print("on_connected")

    def on_disconnected(self):
        print("on_disconnected")

    def on_account_status(self, status):
        print_type("account_status", status)
        print_xtaccountstatus(status)

    def on_stock_asset(self, asset):
        print_type("asset", asset)
        print_xtasset(asset)

    def on_stock_position(self, position):
        print_type("position", position)
        print_xtposition(position)

    def on_stock_order(self, order):
        print_type("order", order)
        print_xtorder(order)

    def on_stock_trade(self, trade):
        print_type("trade", trade)
        print_xttrade(trade)

    def on_order_error(self, order_error):
        print_type("order_error", order_error)
        print_xtordererror(order_error)

    def on_cancel_error(self, cancel_error):
        print_type("cancel_error", cancel_error)
        print_xtcancelerror(cancel_error)

    def on_order_stock_async_response(self, response):
        print_type("order_response", response)
        print_xtorderresponse(response)

    def on_cancel_order_stock_async_response(self, response):
        print_type("cancel_order_response", response)
        print_xtcancelorderresponse(response)
