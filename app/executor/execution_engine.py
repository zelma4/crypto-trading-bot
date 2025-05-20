# app/executor/execution_engine.py

import os
import json
from datetime import datetime
import ccxt
from dotenv import load_dotenv
from app.risk.risk_manager import calculate_position_size
from app.config import DRY_RUN, TAKE_PROFIT_PCT, STOP_LOSS_PCT

load_dotenv()

# Налаштування біржі для торгівлі
exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_API_SECRET"),
    "enableRateLimit": True,
})

SYMBOL = "BTC/USDT"

def place_market_order(side: str, amount: float) -> dict:
    """
    Відкриває ринковий ордер. 
    `side` — 'buy' або 'sell', `amount` — обсяг у базовій валюті.
    """
    order = exchange.create_order(
        symbol=SYMBOL,
        type="market",
        side=side,
        amount=amount
    )
    return order

def place_oco_order(entry_price: float, qty: float) -> dict:
    """
    Після відкриття позиції ставимо OCO-ордер:
      • stopPrice = entry_price * (1 - STOP_LOSS_PCT/100)
      • stopLimitPrice = stopPrice * 0.995 (щоб гарантовано спрацював)
      • takeProfitPrice = entry_price * (1 + TAKE_PROFIT_PCT/100)
    OCO-ордер автоматично виконує одну з двох умов.
    """
    stop_price      = entry_price * (1 - STOP_LOSS_PCT / 100)
    stop_limit_price= stop_price * 0.995
    take_profit     = entry_price * (1 + TAKE_PROFIT_PCT / 100)

    params = {
        "stopPrice":       round(stop_price, 2),
        "stopLimitPrice":  round(stop_limit_price, 2),
        "stopLimitTimeInForce": "GTC"
    }
    oco = exchange.create_order(
        symbol=SYMBOL,
        type="OCO",
        side="sell",
        amount=qty,
        price=round(take_profit, 2),
        params=params
    )
    return oco

def execute_trade(signal: dict) -> dict:
    """
    На вхід подається сигнал із полем "final": "BUY"/"SELL"/"HOLD".
    Якщо BUY → відкриваємо позицію ↦ ставимо OCO.
    Якщо SELL → закриваємо всі позиції ринковим ордером.
    """
    action = signal["final"]
    result = {"timestamp": datetime.utcnow().isoformat(), "action": action}

    if DRY_RUN:
        result["dry_run"] = True
        result["note"] = "Dry‐run mode — no orders executed"
        return result

    if action == "BUY":
        # 1) беремо ціну ринку
        ticker = exchange.fetch_ticker(SYMBOL)
        entry_price = ticker["last"]
        # 2) розраховуємо розмір
        qty = float(calculate_position_size(SYMBOL, entry_price))
        # 3) відкриваємо Market‐BUY
        order = place_market_order("buy", qty)
        # 4) ставимо Stop‐Loss + Take‐Profit (OCO)
        oco = place_oco_order(entry_price, qty)
        result.update({"order": order, "oco": oco})

    elif action == "SELL":
        # закриваємо всі позиції Market‐SELL
        # можна змінити на Stripe через fetch_positions для Futures
        # тут для спот‐ринку просто продаємо весь баланс BTC
        bal = exchange.fetch_balance()
        qty = bal["BTC"]["free"]
        order = place_market_order("sell", qty)
        result.update({"order": order})

    else:
        result["info"] = "No action taken"
    
    return result