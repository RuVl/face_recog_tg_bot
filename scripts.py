import asyncio

from scripts.fill_database import fill_database

if __name__ == '__main__':
    asyncio.run(fill_database())
