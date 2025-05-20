from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Crypto News Trading Bot")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/run_cycle")
async def run_cycle():
    from app.collectors.twitter_collector import collect_tweets
    from app.analyzer.sentiment_analyzer import analyze_tweets
    from app.strategy.signal_generator import generate_signal
    from app.executor.execution_engine import execute_trade

    # 1) Збір
    collect_tweets("bitcoin OR BTC", max_results=20)
    # 2) Аналіз
    analyze_tweets(batch_size=50)
    # 3) Сигнал
    sig = generate_signal()
    # 4) Виконання (або dry-run)
    result = execute_trade(sig)
    return result

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)