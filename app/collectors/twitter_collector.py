import os
import json
from dotenv import load_dotenv
import redis
import tweepy

# Завантажуємо змінні середовища з .env
load_dotenv()

# Підключення до Redis
redis_url = os.getenv("REDIS_URL")
redis_client = redis.from_url(redis_url)

# Налаштування Twitter API v2
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
client = tweepy.Client(bearer_token=bearer_token)

def collect_tweets(query: str, max_results: int = 10) -> int:
    """
    Шукає останні твіти за запитом `query` (наприклад "bitcoin OR BTC")
    і пушить їх у Redis-список "tweets".
    Повертає кількість зібраних твітів.
    """
    response = client.search_recent_tweets(
        query=query,
        tweet_fields=["created_at", "author_id"],
        max_results=max_results
    )
    tweets = response.data or []
    for tweet in tweets:
        data = {
            "id": tweet.id,
            "text": tweet.text,
            "author_id": tweet.author_id,
            "created_at": tweet.created_at.isoformat()
        }
        # Записуємо твіт у Redis
        redis_client.lpush("tweets", json.dumps(data))
    return len(tweets)