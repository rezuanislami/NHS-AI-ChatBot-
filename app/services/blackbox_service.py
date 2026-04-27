<<<<<<< HEAD
import httpx
from app.config import settings


async def call_blackbox(messages: list):
    headers = {
        "Authorization": f"Bearer {settings.BLACKBOX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": messages
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.BLACKBOX_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()

        data = response.json()

        # Adjust based on actual Blackbox response structure
=======
import httpx
from app.config import settings


async def call_blackbox(messages: list):
    headers = {
        "Authorization": f"Bearer {settings.BLACKBOX_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": messages
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.BLACKBOX_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()

        data = response.json()

        # Adjust based on actual Blackbox response structure
>>>>>>> 3a73f07fd3e0eef72da0d5eac0838f05f6089486
        return data["choices"][0]["message"]["content"]