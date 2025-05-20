# app/risk/risk_manager.py

from decimal import Decimal, ROUND_DOWN
import os
from dotenv import load_dotenv
import ccxt
from app.config import RISK_PER_TRADE_PCT, STOP_LOSS_PCT

load_dotenv()

# Налаштування біржі (для отримання балансу)
exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_API_SECRET"),
    "enableRateLimit": True,
})

def get_balance(asset: str = "USDT") -> Decimal:
    """Повертає баланс у зазначеному активі."""
    bal = exchange.fetch_balance()
    return Decimal(str(bal[asset]["free"]))

def calculate_position_size(symbol: str, entry_price: float) -> Decimal:
    """
    Розраховує обсяг позиції (в контракті), виходячи з:
      • Ризику RISK_PER_TRADE_PCT від усіх коштів
      • Стоп-лоссу STOP_LOSS_PCT від ціни входу
    Повертає кількість одиниць (наприклад, USDT), округлену до 8 знаків.
    """
    balance     = get_balance("USDT")
    risk_amount = balance * Decimal(RISK_PER_TRADE_PCT / 100)
    stop_loss_price = entry_price * (1 - STOP_LOSS_PCT / 100)
    # втрати на одиницю контракту
    loss_per_unit = Decimal(str(entry_price)) - Decimal(str(stop_loss_price))
    if loss_per_unit <= 0:
        return Decimal("0")
    # кількість одиниць (контрактів/монет)
    qty = (risk_amount / loss_per_unit).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
    return qty