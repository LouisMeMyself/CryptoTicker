import asyncio
import datetime
import json

from discord.ext import commands

from utils import Constants, JoeSubGraph
from utils.beautify_string import human_format


class CryptoBot:
    cryptoBot = commands.Bot
    channels = Constants.CatPerID

    def __init__(self, bot=None):
        self.cryptoBot = bot
        self.pricesat0 = {}
        if self.cryptoBot is not None:
            self.channels = Constants.CatPerID(self.cryptoBot)
            self.s2a = JoeSubGraph.s2a
        print(self.channels.catPerID)

    async def getPriceAt0(self):
        while 1:
            now = datetime.datetime.utcnow()
            todayat0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrowat0 = todayat0 + datetime.timedelta(days=1)

            await asyncio.sleep((tomorrowat0 - now).total_seconds())
            allSymbols = set()
            for symbols in self.channels.catPerID.values():
                for symbol in symbols["symbols"].keys():
                    allSymbols.add(symbol)
            with open("utils/priceAt0AM.json", "w") as f:
                self.pricesat0 = await JoeSubGraph.getPrices(allSymbols)
                json.dump(self.pricesat0, f)

    async def ticker(self, s_id):
        print("CryptoTicker is up")
        while 1:
            channels = self.channels.catPerID[s_id]["symbols"]
            prices = await JoeSubGraph.getPrices(channels.keys())
            for symbol, price in prices.items():
                c_name = "{}: ${}".format(symbol.upper(), human_format(float(price)))
                if symbol in self.pricesat0:
                    r = round(price / self.pricesat0[symbol] * 100, 2)
                    if r > 100:
                        c_name += "🟢{}%".format(round(r - 100, 2))
                    if r == 100:
                        c_name += "⚫0%"
                    if r < 100:
                        c_name += "🔴{}%".format(round(100 - r, 2))

                if c_name != channels[symbol].name:
                    c = channels[symbol]
                    try:
                        await c.edit(name=c_name)
                    except:
                        pass
            await asyncio.sleep(300)

    async def add(self, ctx):
        symbols = ctx.message.content.replace(Constants.ADD_CMD + " ", "").split(" ")
        for symbol in symbols:
            symbol = symbol.lower()
            if not self.s2a.hasKey(symbol):
                await self.s2a.reloadAssets()
                if not self.s2a.hasKey(symbol):
                    continue

            channels = self.channels.catPerID[ctx.guild.id]

            if symbol in channels["symbols"]:
                continue
            channel = await ctx.guild.create_voice_channel("{}: $X".format(symbol.upper()),
                                                           category=channels["category"])
            channels["symbols"][symbol] = channel

    async def delete(self, ctx):
        symbols = ctx.message.content.replace(Constants.DELETE_CMD + " ", "").split(" ")
        for symbol in symbols:
            symbol = symbol.lower()
            channels = self.channels.catPerID[ctx.guild.id]
            channel = channels["symbols"].pop(symbol)
            await channel.delete()

    async def list(self, ctx):
        tokens = [i.upper() for i in self.s2a.symbol2address.keys()]
        tokens.sort()
        await ctx.reply("AVAX, " + ", ".join(tokens))

    async def on_ready(self):
        """starts cryptobot"""
        await self.s2a.reloadAssets()

        with open("utils/priceAt0AM.json", "r") as f:
            self.pricesat0 = json.load(f)

        self.cryptoBot.loop.create_task(self.getPriceAt0())

        for server in self.cryptoBot.guilds:
            self.cryptoBot.loop.create_task(await self.ticker(server.id))
            break
        print('cryptoBot have logged in as {0.user}'.format(self.cryptoBot))


if __name__ == '__main__':
    cryptoBot = CryptoBot()
    asyncio.run(cryptoBot.getPriceAt0())
