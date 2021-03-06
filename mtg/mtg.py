import os
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from mtgsdk import Card
import difflib
import sys
import aiohttp
from PIL import Image
from io import BytesIO, StringIO
import cairosvg
try:   # check if BeautifulSoup4 is installed
    from bs4 import BeautifulSoup
    soupAvailable = True
except ImportError:
    soupAvailable = False

class MTG:
	"""Fetch info about a MTG card"""

	def __init__(self, bot):
		self.bot = bot
		self.cards = {}
		self.symbols = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16","B", "C", "G", "R", "U", "W", "X", "BP", "GP", "RP", "UP", "WP", "BG", "BR", "UB", "WB", "RG", "GU", "GW", "UR", "RW", "WU", "S", "100", "1000000", "Y", "Z", "OW", "Infinity", "H", "HB", "HC", "HG", "HR", "HU", "HW"]
		
	@commands.command(pass_context=True, no_pm=False, name='MTG', aliases=['mtg', 'Mtg'])
	async def mtg(self, ctx, *card: str):
		"""Searches for named MTG Card"""
		if len(card) > 1:
			card = '"' + " ".join(card) + '"'
		else:
			card = card[0]
		card_match = await self._card_search(card)
		match = card_match[0]
		cards = card_match[1]
		if match:
			em = discord.Embed(title='{}'.format(match['name']), color=discord.Color.blue())
			em.set_image(url=match['imageUrl'])
			#em.set_thumbnail(url= await self._generate_mana_cost(match['manaCost']))
			#em.set_footer(icon_url= await self._generate_set_symbols(match['sets']))
			await self.bot.say(embed=em)
		elif cards:
			message = '```A card called '+ card + ' was not found. But I found close matches:\n\n'
			for card in cards:
				message += '{}\n'.format(card['name'])
			message += '```'
			await self.bot.say(message)
		else:
			message = '`A card called '+ card + ' was not found.`'
			await self.bot.say(message)

	async def _update_cards(self):
		payload = {}
		url = "https://api.magicthegathering.io/v1/cards?"
		page = 1
		conn = aiohttp.TCPConnector(verify_ssl=False)
		session = aiohttp.ClientSession(connector=conn)
		headers = {'user-agent': 'Red-cog/1.0'}
		data = {'cards':[]}
		base_msg = "Downloading updated card data, please wait...\n"
		status = ' %d/? pages updated' % (page - 1)
		msg = await self.bot.say(base_msg + status)
		temp = ""
		while True:
			payload['page'] = page
			async with session.get(url, params=payload ,headers=headers) as r:
				temp = await r.json()
				if temp['cards'] == []:
					break
				for item in list(temp['cards']):
					data['cards'].append(item)
			page += 1
			status = ' %d/? pages updated' % (page - 1)
			msg = await self._robust_edit(msg, base_msg + status)
		session.close()
		self.cards = data
		dataIO.save_json('data/steam/cards.json', data)

	@commands.group(pass_context=True, no_pm=False, name='Mana', aliases=['mana'])	
	async def mana(self, ctx ,*, mana):
		"""Creates and outputs the given mana combo"""
		mana_symbols = mana.split(" ")
		symbols = []
		for symbol in mana_symbols:
			symbol = symbol.upper()
			if (symbol in self.symbols):
				symbols.append(symbol)
			elif len(symbol) == 2 and symbol[::-1] in self.symbols:
				symbols.append(symbol[::-1])
		if mana_symbols[0] == "update":
			await self.update_mana()
		if len(symbols) != 0:
			mana_cost = "{" + "}{".join(symbols) + "}"
			image = await self._generate_mana_cost(mana_cost)
			if os.path.isfile(image):
				await self.bot.send_file(ctx.message.channel, open(image, "rb"))
			else:
				self.bot.say("Something went terribly wrong.")
		else:
			self.bot.say("There were no valid symbols.")
		
	async def update_mana(self):
		"""Updates Mana images"""
		print("Updating Mana")
		await self._update_mana_symbols()
	
	def _resize(self, image, height):
		w = image.size[0]
		h = image.size[1]
		width = round(w/(h/height))
		img = image.resize((width, height), Image.LANCZOS)
		return img
	
	

	async def _generate_mana_cost(self, mana_cost):
		generated = "data/mtg/generated/" + mana_cost + ".png"
		if not os.path.isfile(generated):
			cost = mana_cost.replace("{", "").rstrip("}").split("}")
			images = []
			for part in cost:
				part = self._resize(Image.open("data/mtg/mana/" + part + ".png"), 50)
				images.append(part)
			w = sum(i.size[0] for i in images) + 5 * (len(images) - 1)
			mh = 75

			result = Image.new("RGBA", (w, mh))

			x = 0
			for i in images:
				result.paste(i, (x, 0))
				x += i.size[0] + 5

			result.save("data/mtg/generated/" + mana_cost + ".png")
		
		return generated
	
	async def _generate_set_symbols(self, sets):
		generated = "data/mtg/generated/" + "_".join(sets) + ".png"
		if not os.path.isfile(generated):
			nset = []
			for set in sets:
				set = "data/mtg/sets/" + set + "_symbol.png"
				nset.append(set)
				images = map(Image.open, nset)
				widths, heights = zip(*(i.size for i in images))

				total_width = sum(widths)
				max_height = max(heights)

				new_im = Image.new('RGB', (total_width, max_height))

				x_offset = 0
				for im in images:
					new_im.paste(im, (x_offset,0))
					x_offset += im.size[0]

				new_im.save("data/mtg/generated/" + "_".join(sets) + ".png")
			return generated
		
	async def _card_search(self, query):
		cards = []
		match = False
		for card in self.cards:
			name = card['name']
			x = difflib.SequenceMatcher(None, name.lower(), query.lower()).ratio()
			if x > 0.92:
				match = card
			elif query.lower() in name.lower():
				if len(cards) > 10:
					break
				cards.append(card)
			if query.lower() == name.lower():
				match = card
				break
		if len(cards) == 1:
			match = cards[0]
			cards = []
		return match, cards
	
	"""async def _update_mana_symbols(self):
		Mana = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16","B", "C", "G", "R", "U", "W", "X", "BP", "GP", "RP", "UP", "WP", "BG", "BR", "UB", "WB", "RG", "GU", "GW", "UR", "RW", "WU", "S"]
		Historic = ["100", "1000000", "Y", "Z", "Old_W", "Infinity", "%C2%BD"]
		Half = ["HB", "HC", "HG", "HR", "HU", "HW"]
		url = "http://mtgsalvation.gamepedia.com/Category:Mana_symbols"
		conn = aiohttp.TCPConnector(verify_ssl=False)
		session = aiohttp.ClientSession(connector=conn)
		headers = {'user-agent': 'Red-cog/1.0'}
		for symbol in Mana:
			async with session.get(url,headers=headers) as r:
				print (symbol)
				text = await r.text()
				soup = BeautifulSoup(text, "html.parser")
				link = soup.find('a', attrs={'href': "/File:" + symbol + ".svg"}).find("img")['src']
				print (link)
				async with session.get(link, headers=headers) as resp:
					data = await resp.read()
					cairosvg.svg2png(bytestring=data, write_to="mtg/data/mtg/mana/" + symbol + ".png")
		url = "http://mtgsalvation.gamepedia.com/Category:Historical_mana_symbols"
		for symbol in Historic:
			async with session.get(url,headers=headers) as r:
				text = await r.text()
				soup = BeautifulSoup(text, "html.parser")
				link = soup.find('a', attrs={'href': "/File:" + symbol + ".svg"}).find("img")['src']
				async with session.get(link, headers=headers) as resp:
					data = await resp.read()
					if "Old_W" == symbol:
						symbol = "OW"
					elif "%C2%BD" in symbol:
						symbol = symbol.replace("%C2%BD", "H")
					print(symbol)
					cairosvg.svg2png(bytestring=data, write_to="mtg/data/mtg/mana/" + symbol + ".png")
		session.close()
		for symbol in Half:
			orig = symbol.replace("H", "")
			print (symbol)
			img = Image.open("mtg/data/mtg/mana/" + orig + ".png")
			box = (300, 0, 600, 600)
			half = img.crop(box)
			result = Image.new("RGBA", (600, 600))
			result.paste(half, box)
			result.save("mtg/data/mtg/mana/" + symbol + ".png")
		print ("Updated Mana")"""
	
	async def _update_mana_symbols(self):
		Mana = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16","B", "C", "G", "R", "U", "W", "X", "BP", "GP", "RP", "UP", "WP", "BG", "BR", "UB", "WB", "RG", "GU", "GW", "UR", "RW", "WU", "S", "100", "1000000", "Y", "Z", "OW", "Infinity", "H", "HB", "HC", "HG", "HR", "HU", "HW"]
		url = "https://raw.githubusercontent.com/Yascob99/GAME-Cogs/master/mtg/data/mtg/mana/"
		conn = aiohttp.TCPConnector(verify_ssl=False)
		session = aiohttp.ClientSession(connector=conn)
		headers = {'user-agent': 'Red-cog/1.0'}
		for symbol in Mana:
			async with session.get(url,headers=headers) as r:
				Images.open(BytesIO.())

	@commands.command(no_pm=True, name='MTGUpdate', aliases=['MTGU', 'mtgu', "MtgU", "Mtgu"])
	async def _update(self):
		"""Updates the list of MTG cards, and mana symbols"""
		try:
			await self._update_cards()
			await self._update_mana_symbols()
			message = 'Card list  and mana symbols updated.'
		except Exception as error:
			message = 'Could not update. Check console for more information.'
			print(error)
		await self.bot.say(message)

	async def _robust_edit(self, msg, text):
		try:
			msg = await self.bot.edit_message(msg, text)
		except discord.errors.NotFound:
			msg = await self.bot.send_message(msg.channel, text)
		except:
			raise
		return msg


def check_folder():
	if not os.path.exists('data/mtg/mana'):
		print('Creating data/mtg folder...')
		os.makedirs('data/mtg/mana')
	if not os.path.exists('data/mtg/generated'):
		os.makedirs('data/mtg/generated')
	if not os.path.exists('data/mtg/sets'):
		os.makedirs('data/mtg/sets')

def check_file():
	data = {}
	data['cards'] = {}
	f = 'data/mtg/cards.json'
	if not dataIO.is_valid_json(f):
		print('Creating default cards.json...')
		dataIO.save_json(f, data)
		
def setup(bot):
	if not soupAvailable:
		raise RuntimeError("You need to run \'pip3 install beautifulsoup4\' in command prompt.")
	else:
		check_folder()
		#check_file()
		cog = MTG(bot)
		bot.add_cog(cog)
