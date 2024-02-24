import logging
import platform

from core import start_bot

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    if platform.system() == 'Windows':
        import asyncio
        asyncio.run(start_bot())
    else:  # Linux, Darwin, Java
        # noinspection PyUnresolvedReferences
        import uvloop
        uvloop.run(start_bot())
