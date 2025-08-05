import httpx, asyncio, datetime


class AmigoClient:
    def __init__(self, api_key, api_key_id, user_id, base_url="https://api.amigo.ai"):
        self._cfg = {
            "api_key": api_key,
            "api_key_id": api_key_id,
            "user_id": user_id,
            "base_url": base_url,
        }

    
