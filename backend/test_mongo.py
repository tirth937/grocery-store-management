import asyncio
from database import db

async def test():
    try:
        await db.command('ping')
        print("PONG")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
