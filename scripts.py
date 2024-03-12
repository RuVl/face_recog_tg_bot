import asyncio

from scripts.change_heic2jpg import change_heic2jpg

if __name__ == '__main__':
    # asyncio.run(fill_database())
    # asyncio.run(fix_exif())
    asyncio.run(change_heic2jpg())
