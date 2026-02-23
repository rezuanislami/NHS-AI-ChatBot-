import httpx
from app.config import settings


async def call_blackbox(message: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.BLACKBOX_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "message": message
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.BLACKBOX_BASE_URL,
            headers=headers,
            json=payload
        )

        response.raise_for_status()

        data = response.json()

        # Adjust this depending on actual Blackbox response structure
        return data.get("reply", "Sorry, I couldn't generate a response.")