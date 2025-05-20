import os
import json
from datetime import datetime
import redis
import ccxt
import pandas as pd
from dotenv import load_dotenv

# Завантажуємо .env
load_dotenv()

# Підключення до Redis
redis_url = os.getenv("REDIS_URL")
redis_client = redis.from_url(redis_url)

# Налаштування біржі (наприклад, Binance)
exchange = ccxt.binance({
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_API_SECRET"),
    "enableRateLimit": True,
})

# Параметри стратегії
SYMBOL = "BTC/USDT"
TIMEFRAME = "5m"
SMA_PERIOD = 20
SENTIMENT_THRESHOLD_BUY = 0.2
SENTIMENT_THRESHOLD_SELL = -0.2

def fetch_price_history(symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
    """
    Завантажуємо історичні дані цін у DataFrame з колонками ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
    """
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def compute_technical_signal(df: pd.DataFrame) -> str:
    """
    Рахуємо просту ковзну середню SMA та повертаємо "BUY", "SELL" або "HOLD" 
    залежно від останньої ціни та SMA.
    """
    df["sma"] = df["close"].rolling(window=SMA_PERIOD).mean()
    last_close = df["close"].iloc[-1]
    last_sma   = df["sma"].iloc[-1]
    if last_close > last_sma:
        return "BUY"
    elif last_close < last_sma:
        return "SELL"
    else:
        return "HOLD"

def compute_sentiment_signal(batch_size: int = 100) -> tuple[str, float]:
    """
    Беремо останні batch_size твітів із Redis-списку 'tweets_sentiment',
    рахуємо середнє compound-значення тональності.
    Повертаємо ("BUY"/"SELL"/"HOLD", avg_compound).
    """
    compounds = []
    for _ in range(batch_size):
        raw = redis_client.rpop("tweets_sentiment")
        if not raw:
            break
        tweet = json.loads(raw)
        compounds.append(tweet["sentiment"]["compound"])
    if not compounds:
        return "HOLD", 0.0
    avg = sum(compounds) / len(compounds)
    if avg > SENTIMENT_THRESHOLD_BUY:
        return "BUY", avg
    elif avg < SENTIMENT_THRESHOLD_SELL:
        return "SELL", avg
    else:
        return "HOLD", avg

def generate_signal():
    """
    Об’єднуємо технічний та сентимент-сигнали.
    Логіка:
      • Якщо обидва — BUY → сильний BUY
      • Якщо обидва — SELL → сильний SELL
      • Якщо вони різні або хоча б один HOLD → HOLD
    Результат пушимо у Redis-список "trade_signals".
    """
    # 1. Технічний аналіз
    price_df = fetch_price_history(SYMBOL, TIMEFRAME)
    tech_sig = compute_technical_signal(price_df)

    # 2. Сентимент-аналіз
    sent_sig, sent_score = compute_sentiment_signal()

    # 3. Об’єднаний сигнал
    if tech_sig == sent_sig and tech_sig in ("BUY", "SELL"):
        final = tech_sig
    else:
        final = "HOLD"

    signal = {
        "timestamp": datetime.utcnow().isoformat(),
        "symbol": SYMBOL,
        "technical": tech_sig,
        "sentiment": sent_sig,
        "sentiment_score": sent_score,
        "final": final
    }
    # Записуємо сигнал у Redis
    redis_client.lpush("trade_signals", json.dumps(signal))
    return signal