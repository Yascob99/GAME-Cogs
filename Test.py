import aiohttp
import asyncio
import os
from io import BytesIO, StringIO
from PIL import Image

async def main(loop):
	payload = {}
	list = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "1000000", "B", "C", "G", "R", "U", "W", "X", "BP", "GP", "RP", "UP", "WP", "BG", "BR", "UB", "WB", "RG", "GU", "GW", "UR", "RW", "WU", "SNOW"]
	url = "http://gatherer.wizards.com/Handlers/Image.ashx?"
	conn = aiohttp.TCPConnector(verify_ssl=False)
	session = aiohttp.ClientSession(connector=conn)
	headers = {'user-agent': 'Red-cog/1.0'}
	for symbol in list:
		payload["name"] = symbol
		payload["type"] = "symbol"
		payload["size"] = "large"
		resize = True
		if "P" in symbol or "C" in symbol:
			payload["size"] = "medium"
		async with session.get(url ,params=payload,headers=headers) as r:
			data = await r.read()
			print(symbol)
			stream = BytesIO(data)
			img = Image.open(stream)
			img = img.resize((75,75), Image.LANCZOS)
			img.save("mtg/data/mtg/mana/" + symbol + ".png")
		
	session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))