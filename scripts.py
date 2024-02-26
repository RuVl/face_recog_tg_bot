import asyncio

from scripts.fix_exif import fix_exif

if __name__ == '__main__':
    # asyncio.run(fill_database())
    asyncio.run(fix_exif())
