import aiohttp
import asyncio
import os
from io import BytesIO, StringIO
from PIL import Image
from bs4 import BeautifulSoup
import cairosvg
from PIL import Image
from dataIO import dataIO
import ast
import sys

async def main(loop):
	Mana = ["1", "2", "2B", "2G", "2P", "2R", "2U", "2W", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "B", "C", "G", "R", "U", "W", "X", "BPH", "GPH", "RP", "UPH", "WPH", "BG", "BR", "UB", "WB", "RG", "GU", "GW", "UR", "RW", "WU", "S"]
	Historic = ["100", "1000000", "Y", "Z", "Old_W", "Infinity", "%C2%BD"]
	Half = ["HB", "HC", "HG", "HR", "HU", "HW", "HP"]
	for symbol in Half:
		orig = symbol.replace("H", "")
		print (symbol)
		img = Image.open("mtg/data/mtg/mana/" + orig + ".png")
		box = (300, 0, 600, 600)
		half = img.crop(box)
		result = Image.new("RGBA", (600, 600))
		result.paste(half, box)
		result.save("mtg/data/mtg/mana/" + symbol + ".png")
	print ("Updated Mana")




	"""payload = {}
	url = "https://api.magicthegathering.io/v1/cards?"
	page = 1
	conn = aiohttp.TCPConnector(verify_ssl=False)
	session = aiohttp.ClientSession(connector=conn)
	headers = {'user-agent': 'Red-cog/1.0'}
	data = {'cards':[]}
	base_msg = "Downloading updated card data, please wait...\n"
	status = ' %d/? pages updated' % (page - 1)
	print ("Downloading updated card data, please wait...\n")
	temp = ""
	while True:
		payload['page'] = page
		async with session.get(url, params=payload ,headers=headers) as r:
			temp = await r.json()
			if temp['cards'] == []:
					break
			header_data = ast.literal_eval("{" + str(r).lstrip("<ClientResponse(" + url + "page=" + str(page) + ") [200 OK]>\n<CIMultiDictProxy(").rstrip(")>\n") + "}")
			max = int(header_data["Total-Count"])/100
			if max > round(max):
				max = round(max) + 1
			else:
				max = round(max)
			for item in list(temp['cards']):
				card = {}
				card['name'] = item['name']
				try:
					card['names'] = item['names']
				except:
					card['names'] = ""
				try:
					card["id"] = item["multiverseid"]
				except:
					card["id"] = ""
				try:
					card['manaCost'] = item['manaCost']
				except:
					card['manaCost'] = ""
				try:
					card['text'] = item['text']
				except:
					card['text'] = ""
				try:
					card['flavor'] = item['flavor']
				except:
					card['flavor'] = ""
				try:
					card['alts'] = item['variations']
				except:
					card['alts'] = ""
			
			
				data['cards'].append(card)
		page += 1
		status = ' %d/%d pages updated' % (page, max)
		if page != max:
			print (status, end='\r')
		else:
			print (status)
		
		sys.stdout.flush()
	session.close()
	dataIO.save_json('mtg/data/mtg/cards.json', data)"""
		
	
	

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))