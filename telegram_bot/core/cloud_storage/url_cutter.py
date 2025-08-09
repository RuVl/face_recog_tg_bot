import aiohttp


async def cut_url(url: str) -> str:
	""" Makes url shorter or returns itself on error """

	if url is None:
		return None

	endpoint = 'https://clck.ru/--'

	async with aiohttp.ClientSession() as session:
		response = await session.get(endpoint, params={'url': url})
		return await response.text() if response.status == 200 else url
