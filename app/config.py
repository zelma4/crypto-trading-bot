# app/config.py

import os

# Інші налаштування…

# Risk Management
RISK_PER_TRADE_PCT = float(os.getenv("RISK_PER_TRADE_PCT", 1.0))    # 1% за замовчуванням
STOP_LOSS_PCT       = float(os.getenv("STOP_LOSS_PCT", 1.0))        # 1% стоп-лосс
TAKE_PROFIT_PCT     = float(os.getenv("TAKE_PROFIT_PCT", 2.0))      # 2% тейк-профіт
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"