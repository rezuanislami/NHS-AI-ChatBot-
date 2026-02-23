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
        return data["choices"][0]["message"]["content"]