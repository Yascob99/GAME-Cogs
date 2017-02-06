import os
import discord
from discord.ext import commands
from cogs.utils.dataIO import dataIO

class Colours:
	"""Sets a role's colour"""

	def __init__(self, bot):
		self.bot = bot
		
		
	@commands.command(pass_context=True, no_pm=False, name='Colour', aliases=['colour', 'Color', 'color'])
	async def colour(self, ctx, *hex: str):
		"""Set's your colour to a hexcode"""
		server = ctx.message.server
		hex = hex.rstrip(" ").lstrip(" ")
		roles = []
		for member in server.members:
			for r in member.roles:
				if r.id not in roles:
					roles.append(r)
		for rol in server.roles:
			if "#" == rol.id[0]:
				if rol not in roles:
					self.bot.delete_role(server, rol)
		if hex[0] != "#":
			self.bot.say("Invalid hex colour, please make it a '#' followed by six hexidecimal characters.")
			return
		else:
			member = ctx.message.author
			added = False
			for role in server.roles:
				if role == hex:
					for role in member.roles:
						if "#" == role.id[0]:
							self.bot.remove_roles(member, role)
					self.bot.add_roles(member, role)
					return
			for role in member.roles:
				if "#" == role.id[0]:
					self.bot.remove_roles(member, role)
			new_role = self.bot.create_role(server, name = hex, colour = discord.Colour(hex.replace("#", "0x")) )
			self.bot.add_roles(member, new_role)
			self.bot.move_role(server, new_role, len(server.roles)-3))			
		
def setup(bot):
		cog = Colours(bot)
		bot.add_cog(cog)