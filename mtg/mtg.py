import os
import html
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO
from mtgsdk import Card
import difflib
import sys
import aiohttp
from PIL import Image
from io import BytesIO, StringIO
try:   # check if BeautifulSoup4 is installed
    from bs4 import BeautifulSoup
    soupAvailable = True
except ImportError:
    soupAvailable = False

class MTG:
	"""Fetch info about a MTG card"""

	def __init__(self, bot):
		self.bot = bot
		self.cards = dataIO.load_json('data/mtg/cards.json')['cards']
		self.symbols = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "1000000","B", "C", "G", "R", "U", "W", "X", "Y", "Z", "BP", "GP", "RP", "UP", "WP", "BG", "BR", "UB", "WB", "RG", "GU", "GW", "UR", "RW", "WU", "S", "1/2", "1/2R", "1/2W", "OW"]
	
	
	async def _update_sets(self):
		url = "https://api.magicthegathering.io/v1/sets"
		conn = aiohttp.TCPConnector(verify_ssl=False)
		session = aiohttp.ClientSession(connector=conn)
		headers = {'user-agent': 'Red-cog/1.0'}
		data = {'sets':[]}
		base_msg = "Downloading updated sets data, please wait...\n"
		async with session.get(url ,headers=headers) as r:
			data = await r.json()
		sets = []
		session.close()
		for set in data:
			set.append(set['code'])
	

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


	@commands.command(pass_context=True, no_pm=False, name='MTG', aliases=['mtg', 'Mtg'])
	async def _mtg(self, ctx, *card: str):
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
			else:
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
		img = img.resize((50,50), Image.LANCZOS)
	
	

	async def _generate_mana_cost(self, mana_cost):
		generated = "data/mtg/generated/" + mana_cost + ".png"
		if not os.path.isfile(generated):
			cost = mana_cost.replace("{", "").rstrip("}").split("}")
			images = []
			for part in cost:
				part = self._resize(Image.open("data/mtg/mana/" + part + ".png"))
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
	
	async def _update_mana_symbols(self):
		list = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "1000000","B", "C", "G", "R", "U", "W", "X", "Y", "Z", "BP", "GP", "RP", "UP", "WP", "BG", "BR", "UB", "WB", "RG", "GU", "GW", "UR", "RW", "WU", "S", "%C2%BD", "%C2%BDR", "%C2%BDW", "Old_W"]
		url = "http://mtgsalvation.gamepedia.com/File:"
		conn = aiohttp.TCPConnector(verify_ssl=False)
		session = aiohttp.ClientSession(connector=conn)
		headers = {'user-agent': 'Red-cog/1.0'}
		for symbol in list:
			resize = True
			if "P" in symbol or "C" in symbol:
				payload["size"] = "medium"
			async with session.get(url ,params=payload,headers=headers) as r:
				soup = BeautifulSoup(await r.text(), "html.parser")
				link = soup.find('div', attrs={'class': "fullImageLink"}).find("a")["href"]
				async with session.get(link, headers=headers) as resp:
					data = await resp.read()
					stream = BytesIO(data)
					if "%C2%BD" in symbol:
						symbol = symbol.replace("%C2%BD", "1/2")
					elif "Old_W" == symbol:
						symbol = "OW"
					cairosvg.svg2png(bytestring=stream, write_to="data/mtg/mana/" + symbol + ".png")
				
			session.close()
		print ("Updated Mana")


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
	

		session.close()
		
def setup(bot):
	if not soupAvailable:
		raise RuntimeError("You need to run \'pip3 install beautifulsoup4\' in command prompt.")
	else:
		check_folder()
		check_file()
		cog = MTG(bot)
		bot.add_cog(cog)
