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

    async def getPriceAt0(self):
        while 1:
            now = datetime.datetime.utcnow()
            todayat0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrowat0 = todayat0 + datetime.timedelta(days=1)

            await asyncio.sleep((tomorrowat0 - now).total_seconds())
            temp = None
            while temp is None:
                try:
                    await self.s2a.reloadAssets()
                    with open("utils/priceAt0AM.json", "w") as f:
                        temp = await JoeSubGraph.getPrices(list(self.s2a.symbol2address.keys()) + list(["avax"]))
                        self.pricesat0 = temp
                        json.dump(self.pricesat0, f)
                except: pass
                await asyncio.sleep(60)

    async def ticker(self, s_id):
        while 1:
            print("CryptoTicker is up")
            try:
                while 1:
                    channels = self.channels.catPerID[s_id]["symbols"]
                    prices = JoeSubGraph.getPrices(channels.keys())
                    for symbol, price in prices.items():
                        c_name = "{}: ${}".format(symbol.upper(), human_format(float(price)))
                        if symbol in self.pricesat0:
                            r = round(price / self.pricesat0[symbol] * 100, 2)
                            if r > 100:
                                c_name += " 🟢{}%".format(round(r - 100, 2))
                            if r == 100:
                                c_name += " ⚫0%"
                            if r < 100:
                                c_name += " 🔴{}%".format(round(r - 100, 2))

                        if c_name != channels[symbol].name:
                            c = channels[symbol]
                            await c.edit(name=c_name)
                    await asyncio.sleep(300)
            except ConnectionError:
                print("Connection error, retrying in 60 seconds...")
            except AssertionError:
                print("Assertion Error, retrying in 60 seconds...")
            except KeyboardInterrupt:
                print(KeyboardInterrupt)
                return
            await asyncio.sleep(60)
        

    async def add(self, ctx):
        symbols = ctx.message.content.replace(Constants.ADD_CMD + " ", "").split(" ")
        for symbol in symbols:
            symbol = symbol.lower()
            if not self.s2a.hasKey(symbol):
                self.s2a.reloadAssets()
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
        self.s2a.reloadAssets()

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
