import json

import discord
from discord.ext import commands

from CryptoBot import CryptoBot

# Discord
from utils import Constants

intents = discord.Intents.all()
intents.members = True

discord_bot = commands.Bot(command_prefix='!', intents=intents)
# discord_bot = commands.Bot(command_prefix='!')

cryptoBot = CryptoBot

@discord_bot.event
async def on_ready():
    """starts elkbot"""
    global cryptoBot
    cryptoBot = CryptoBot(discord_bot)
    await cryptoBot.on_ready()


@discord_bot.command(pass_context=True)
@commands.has_role(Constants.ROLE_FOR_CMD)
async def add(ctx: discord.ext.commands.Context):
    await cryptoBot.add(ctx)


@discord_bot.command(pass_context=True)
@commands.has_role(Constants.ROLE_FOR_CMD)
async def delete(ctx: discord.ext.commands.Context):
    await cryptoBot.delete(ctx)


@discord_bot.command(pass_context=True)
async def list(ctx: discord.ext.commands.Context):
    await cryptoBot.list(ctx)

@discord_bot.command(pass_context=True)
async def a(ctx: discord.ext.commands.Context):
    print(ctx.message.content)



if __name__ == '__main__':
    with open(".key", "r") as f:
        key = json.load(f)
    # Discord
    discord_bot.run(key["discord"])
