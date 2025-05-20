# app/scheduler.py
import os
from datetime import datetime
from redis import Redis
from rq_scheduler import Scheduler
from dotenv import load_dotenv

load_dotenv()
redis_conn = Redis.from_url(os.getenv("REDIS_URL"))
scheduler = Scheduler(connection=redis_conn)

# --- Tweets collector ---
# Видаляємо старі job-і collect_tweets
for job in scheduler.get_jobs():
    if job.func_name == 'app.collectors.twitter_collector.collect_tweets':
        scheduler.cancel(job)
# Запланувати collect_tweets
scheduler.schedule(
    scheduled_time=datetime.utcnow(),
    func='app.collectors.twitter_collector.collect_tweets',
    args=['bitcoin OR BTC', 20],
    interval=300,
    repeat=None
)

# --- Signal generator ---
# Видаляємо старі job-і generate_signal
for job in scheduler.get_jobs():
    if job.func_name == 'app.strategy.signal_generator.generate_signal':
        scheduler.cancel(job)
# Запланувати generate_signal
scheduler.schedule(
    scheduled_time=datetime.utcnow(),
    func='app.strategy.signal_generator.generate_signal',
    args=[],
    interval=300,
    repeat=None
)

print("Scheduler configured: collect_tweets & generate_signal every 5 minutes")