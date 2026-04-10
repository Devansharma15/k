import os
from upstash_redis import Redis

UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "https://novel-sheep-93398.upstash.io")
UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "gQAAAAAAAWzWAAIncDE1MzhhNDg4NzBmOGI0YzRhOWVmZTdlODZkZTJjNzdiMHAxOTMzOTg")

redis_client = Redis(url=UPSTASH_REDIS_REST_URL, token=UPSTASH_REDIS_REST_TOKEN)
