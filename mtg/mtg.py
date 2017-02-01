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

class MTG:
	"""Fetch info about a MTG card"""

	def __init__(self, bot):
		self.bot = bot
		self.cards = dataIO.load_json('data/mtg/cards.json')['cards']

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
				print (await r.text())
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
	async def _MTG(self, ctx, *card: str):
		"""Searches for named MTG Card"""
		card = "_".join(card)
		card_match = await self._card_search(card)
		match = card_match[0]
		cards = card_match[1]
		if match:
			em = discord.Embed(title='{}'.format(match['name']), color=discord.Color.blue())
			em.set_image(url=match['imageUrl'])
			print(await self._generate_mana_cost(match['manaCost']))
			em.set_thumbnail(await self._generate_mana_cost(match['manaCost']))
			em.set_footer(icon_url= self._generate_set_symbols(match['sets']))
			await self.bot.say(embed=em)
		elif cards:
			message = '```A card called "'+ card + '" was not found. But I found close matches:\n\n'
			for card in cards:
				message += '{}\n'.format(card['name'])
			message += '```'
			await self.bot.say(message)
		else:
			message = '`This game could not be found`'
			await self.bot.say(message)

	async def _generate_mana_cost(self, mana_cost):
		generated = "data/mtg/generated/" + mana_cost + ".png"
		if not os.path.isfile(generated):
			cost = mana_cost.replace("{", "").rstrip("}").split("}")
			ncost = []
			for part in cost:
				part = "data/mtg/mana/" + part + ".png"
				ncost.append(part)
			images = map(Image.open, ncost)
			widths, heights = zip(*(i.size for i in images))

			total_width = sum(widths)
			max_height = max(heights)

			new_im = Image.new('RGB', (total_width, max_height))

			x_offset = 0
			for im in images:
				new_im.paste(im, (x_offset,0))
				x_offset += im.size[0]

			new_im.save("data/mtg/generated/" + mana_cost + ".png")
		return generated
		
	async def _generate_set_symbols(self, sets):
		generated = "data/mtg/generated/" + mana_cost + ".png"
		if not os.path.isfile(generated):
			nset = []
			for set in sets:
				set = "data/mtg/sets/" + set + ".png"
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

				new_im.save("data/mtg/generated/" + mana_cost + ".png")
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
		return match, cards


	@commands.command(no_pm=True, name='MTGUpdate', aliases=['MTGU', 'mtgu', "MtgU", "Mtgu"])
	async def _update(self):
		"""Updates the list of MTG cards"""
		try:
			await self._update_cards()
			message = 'Card list updated.'
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
	check_folder()
	check_file()
	cog = MTG(bot)
	bot.add_cog(cog)
