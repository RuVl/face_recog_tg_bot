import asyncio
import logging

from scripts.fill_database import fill_database

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(fill_database())
