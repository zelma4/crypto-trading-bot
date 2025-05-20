import os
import json
from dotenv import load_dotenv
import redis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Завантажуємо .env
load_dotenv()

# Підключення до Redis
redis_url = os.getenv("REDIS_URL")
redis_client = redis.from_url(redis_url)

# Ініціалізація VADER
analyzer = SentimentIntensityAnalyzer()

def analyze_tweets(input_list: str = "tweets",
                   output_list: str = "tweets_sentiment",
                   batch_size: int = 50) -> int:
    """
    Беремо до `batch_size` твітів із Redis-списку `input_list`,
    аналізуємо тональність і пушимо результат у `output_list`.
    Повертає кількість оброблених твітів.
    """
    count = 0
    for _ in range(batch_size):
        raw = redis_client.rpop(input_list)
        if raw is None:
            break
        tweet = json.loads(raw)
        vs = analyzer.polarity_scores(tweet["text"])
        # додаємо поле з тональністю
        tweet["sentiment"] = {
            "neg": vs["neg"],
            "neu": vs["neu"],
            "pos": vs["pos"],
            "compound": vs["compound"]
        }
        redis_client.lpush(output_list, json.dumps(tweet))
        count += 1
    return count