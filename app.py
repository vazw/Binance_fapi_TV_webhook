#    DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
#
# Copyright (c) 2022 vazw. All rights reserved.
#
# Licensed under the "THE BEER-WARE LICENSE" (Revision 42):
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
#
#     DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
# TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
#     0. You just DO WHAT THE FUCK YOU WANT TO.

import json
import os

import pandas as pd
from binance.client import Client
from flask import Flask, request
from line_notify import LineNotify

API_KEY = f'{os.environ["API_KEY"]}'
API_SECRET = f'{os.environ["API_SECRET"]}'
LINE_TOKEN = f'{os.environ["LINE_TOKEN"]}'
BOT_NAME = f'{os.environ["BOT_NAME"]}'
FREEBALANCE = float(f'{os.environ["FREEBALANCE"]}')
SECRET_KEY = f'{os.environ["SECRET_KEY"]}'
ORDER_ENABLE = True if f'{os.environ["ORDER_ENABLE"]}' == "TRUE" else False
app = Flask(__name__)
client = Client(API_KEY, API_SECRET)
notify = LineNotify(LINE_TOKEN)


def change_leverage(data):
    try:
        client.futures_change_leverage(
            symbol=data["symbol"], leverage=data["leverage"]
        )
        return data
    except Exception as e:
        print(e)
        data["leverage"] = float(
            client.futures_position_information(symbol=data["symbol"])[
                1 if data["mode"] else 0
            ]["leverage"]
        )
        return data


def check_actions(actions):
    if actions == "CloseLong" or actions == "OpenShort":
        return "SELL"
    elif actions == "CloseShort" or actions == "OpenLong":
        return "BUY"
    elif actions == "test":
        return "test"
    else:
        return "test"


def get_position_size(symbol):
    positions = client.futures_position_information(symbol=symbol)
    current_position = [
        position
        for position in positions
        if float(position["positionAmt"]) != 0
    ]
    position_data = pd.DataFrame(
        current_position,
        columns=[
            "symbol",
            "entryPrice",
            "markPrice",
            "positionAmt",
            "unRealizedProfit",
            "positionSide",
            "leverage",
        ],
    )
    return position_data


def check_amount(symbol, order_amount, position_amount, action):
    qty_precision = 0
    m = len(order_amount)
    bids = float(client.futures_orderbook_ticker(symbol="BTCUSDT")["bidPrice"])
    asks = float(client.futures_orderbook_ticker(symbol="BTCUSDT")["askPrice"])
    bidask = bids if action == "SELL" else asks
    qty_precision = (
        int(precistion["quantityPrecision"])
        for precistion in client.futures_exchange_info()["symbols"]
        if precistion["symbol"] == symbol
    ).__next__()
    if order_amount[0] == "%":
        percent = float(order_amount[1:m])
        return round(percent / 100 * position_amount, qty_precision)
    elif order_amount[0] == "@":
        fiat = float(order_amount[1:m])
        return round(fiat, qty_precision)
    elif order_amount[0] == "$":
        usd = float(order_amount[1:m])
        return round(usd / bidask, qty_precision)
    else:
        return 0


def check_balance(fiat):
    balance = (
        asset["balance"]
        for asset in client.futures_account_balance()
        if asset["asset"] == fiat
    ).__next__()
    return balance


def close_order(data, position_data, side):
    order = client.futures_create_order(
        symbol=data["symbol"],
        positionSide=side,
        side=data["order_side"],
        type="MARKET",
        quantity=data["amount"],
    )
    print(order)
    position_size = float(position_data["positionAmt"][data["symbol"]])
    position_entry = float(position_data["entryPrice"][data["symbol"]])
    position_lev = int(position_data["leverage"][data["symbol"]])
    margin = position_entry * position_size / position_lev
    balance = check_balance("USDT")
    profit_loss = (position_data["unRealizedProfit"][data["symbol"]]) * abs(
        data["amount"] / position_size
    )
    message = (
        f"Binance Bot: {BOT_NAME}\n"
        + f"Coin       : {data['symbol']}\n"
        + f"Order      : {data['action']}\n"
        + f"Amount     : {position_size}\n"
        + f"Margin     : {margin}\n"
        + f"P/L        : {profit_loss} USDT\n"
        + f"Leverage   : X{position_lev}\n"
        + f"Balance    : {balance} USDT"
    )
    return notify.send(message=message, sticker_id=1991, package_id=446)


def open_order(data, side):
    data = change_leverage(data)
    order = client.futures_create_order(
        symbol=data["symbol"],
        positionSide=side,
        side=data["order_side"],
        type="MARKET",
        quantity=data["amount"],
    )
    print(order)
    position_data = get_position_size(data["symbol"])
    if data["mode"] and len(position_data.index) > 1:
        if data["action"] == "CloseLong":
            position_data.drop(index=1, inplace=True)
        if data["action"] == "OpenLong":
            position_data.drop(index=0, inplace=True)
        if data["action"] == "CloseShort":
            position_data.drop(index=0, inplace=True)
        if data["action"] == "OpenShort":
            position_data.drop(index=1, inplace=True)
    position_data = position_data.set_index("symbol")
    position_size = float(position_data["positionAmt"][data["symbol"]])
    position_entry = float(position_data["entryPrice"][data["symbol"]])
    position_lev = int(position_data["leverage"][data["symbol"]])
    margin = position_entry * position_size / position_lev
    balance = check_balance("USDT")
    message = (
        f"Binance Bot: {BOT_NAME}\n"
        + f"Coin       : {data['symbol']}\n"
        + f"Order      : {data['action']}\n"
        + f"Amount     : {position_size}\n"
        + f"Margin     : {margin}\n"
        + f"Price      : {position_entry}\n"
        + f"Leverage   : X{position_lev}\n"
        + f"Balance    : {balance} USDT"
    )
    return notify.send(message=message, sticker_id=1997, package_id=446)


def closeall_order(data, position_data, side):
    data["amount"] = position_size = abs(
        float(position_data["positionAmt"][data["symbol"]])
    )
    position_entry = float(position_data["entryPrice"][data["symbol"]])
    position_lev = int(position_data["leverage"][data["symbol"]])

    order = client.futures_create_order(
        symbol=data["symbol"],
        positionSide=side,
        side=data["order_side"],
        type="MARKET",
        quantity=data["amount"],
    )
    print(order)
    margin = position_entry * position_size / position_lev
    balance = check_balance("USDT")
    profit_loss = float(
        position_data["unRealizedProfit"][data["symbol"]]
    ) * abs(float(data["amount"]) / position_size)
    message = (
        f"Binance Bot: {BOT_NAME}\n"
        + f"Coin       : {data['symbol']}\n"
        + "Order      : CloseAll\n"
        + f"Amount     : {position_size}\n"
        + f"Margin     : {margin}\n"
        + f"P/L        : {profit_loss} USDT\n"
        + f"Leverage   : X{position_lev}\n"
        + f"Balance    : {balance} USDT"
    )
    return notify.send(message=message, sticker_id=1988, package_id=446)


def OpenLong(data):
    if data["amount_type"] == "%":
        return notify.send(f"{BOT_NAME : การตั้งค่าไม่ถูกต้อง}")
    open_order(data, data["LongSide"])


def OpenShort(data):
    if data["amount_type"] == "%":
        return notify.send(f"{BOT_NAME : การตั้งค่าไม่ถูกต้อง}")
    open_order(data, data["ShortSide"])


def CloseLong(data, position_data):
    close_order(data, position_data, data["LongSide"])


def CloseShort(data, position_data):
    close_order(data, position_data, data["ShortSide"])


def CloseAllLong(data, position_data):
    closeall_order(data, position_data, data["LongSide"])


def CloseAllShort(data, position_data):
    closeall_order(data, position_data, data["ShortSide"])


def signal_handle(data):
    """
    Sample payload =  '{"side":"OpenShort","amount":"@0.006","symbol":"BTCUSDTPERP","passphrase":"1945","leverage":"125"}' # noqa:
    """
    if data["passphrase"] != SECRET_KEY:
        notify.send("รหัสผ่านไม่ถูกต้อง")
        return "รหัสไม่ถูกต้อง :P"

    balance = check_balance("USDT")

    if float(balance) < FREEBALANCE:
        notify.send("ยอดเงินไม่พอ")
        return "ยอดเงินไม่พอ"

    symbol = data["symbol"]
    if (symbol[len(symbol) - 4 : len(symbol)]) == "PERP":
        symbol = symbol[0 : len(symbol) - 4]
    position_mode = client.futures_get_position_mode()
    position_data = get_position_size(symbol)
    position_size = 0.0
    if position_mode["dualSidePosition"] and len(position_data.index) > 1:
        if data["side"] == "CloseLong":
            position_data.drop(index=1, inplace=True)
        if data["side"] == "OpenLong":
            position_data.drop(index=0, inplace=True)
        if data["side"] == "CloseShort":
            position_data.drop(index=0, inplace=True)
        if data["side"] == "OpenShort":
            position_data.drop(index=1, inplace=True)
        if data["side"] == "test":
            return
    position_data = position_data.set_index("symbol")
    if not position_data.empty:
        position_size = float(position_data["positionAmt"][symbol])
    actions = check_actions((data["side"] if ORDER_ENABLE is True else "test"))
    amount = check_amount(symbol, data["amount"], position_size, actions)
    order_data = {
        "amount_type": data["amount"][0],
        "amount": amount,
        "symbol": symbol,
        "leverage": int(data["leverage"]),
        "action": (data["side"] if ORDER_ENABLE is True else "test"),
        "order_side": actions,
        "mode": position_mode["dualSidePosition"],
        "LongSide": ("LONG" if position_mode["dualSidePosition"] else "BOTH"),
        "ShortSide": (
            "SHORT" if position_mode["dualSidePosition"] else "BOTH"
        ),
        "balance": balance,
    }
    try:
        if order_data["action"] == "CloseLong":
            if position_size > 0.0:
                CloseLong(order_data, position_data)
            else:
                return "No Position : Do Nothing"
        if order_data["action"] == "CloseShort":
            if position_size < 0.0:
                CloseShort(order_data, position_data)
            else:
                return "No Position : Do Nothing"
        if order_data["action"] == "OpenLong":
            if not order_data["mode"] and position_size < 0.0:
                CloseAllShort(order_data, position_data)
                OpenLong(order_data)
            else:
                OpenLong(order_data)
        if order_data["action"] == "OpenShort":
            if order_data["mode"] and position_size > 0.0:
                CloseAllLong(order_data, position_data)
                OpenShort(order_data)
            else:
                OpenShort(order_data)
    except Exception as e:
        print(e)
        notify.send(f"{BOT_NAME} : เกิดข้อผิดพลาด")


@app.route("/")
def first_pages():
    return "hello"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = json.loads(request.data)
    signal_handle(data)


if __name__ == "__main__":
    app.run(debug=True)
    # test = signal_handle(
    #     data={
    #         "side": "OpenShort",
    #         "amount": "@0.02",
    #         "symbol": "ETHUSDTPERP",
    #         "passphrase": "8888",
    #         "leverage": "100",
    #     }
    # )
