import asyncio
from app.main import app
from httpx import AsyncClient

async def test():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/persons")
        print("Status:", response.status_code)
        if response.status_code != 200:
            print("Body:", response.text)
        else:
            data = response.json()
            print(f"Loaded {len(data['items'])} persons. Total: {data['total']}")

asyncio.run(test())
