import asyncio
import datetime
import json

from discord.ext import commands, tasks

from utils import Constants, JoeSubGraph
from utils.Utils import humanFormat, Ticker, TaskManager

started = False


class Price0Ticker(commands.Cog, Ticker):
    def __init__(self, bot, pricesat0, s2a, channels):
        self.s2a = s2a
        self.pricesat0 = pricesat0
        self.bot = bot
        self.channels = channels

    @tasks.loop(hours=24)
    async def ticker(self):
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
                except:
                    pass
                await asyncio.sleep(60)

    @ticker.before_loop
    async def before_ticker(self):
        now = datetime.datetime.utcnow()
        todayat0 = now.replace(hour=0, minute=0, second=0)
        tomorrowat0 = todayat0 + datetime.timedelta(days=1)

        await asyncio.sleep((tomorrowat0 - now).total_seconds())


class CryptoTicker(commands.Cog, Ticker):
    def __init__(self, bot, pricesat0, s2a, channels):
        self.s2a = s2a
        self.pricesat0 = pricesat0
        self.bot = bot
        self.channels = channels

    @tasks.loop(seconds=360)
    async def ticker(self):
        tokens = set()
        for channels in self.channels.catPerID.values():
            for token in channels["symbols"]:
                tokens.add(token)
        prices = JoeSubGraph.getPrices(tokens)

        for s_id, channels in self.channels.catPerID.items():
            try:
                await channels["category"].edit(
                    name="Cryptos: ({})".format(datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")))
                for symbol, channel in channels["symbols"].items():
                    price = prices[symbol]
                    try:
                        c_name = "{}: ${}".format(symbol.upper(), humanFormat(float(price), 2))
                    except:
                        c_name = "{}: Unknown address".format(symbol.upper())
                    if symbol in self.pricesat0:
                        r = round(price / self.pricesat0[symbol] * 100, 2)
                        if r > 100:
                            c_name += " 🟢{}%".format(round(r - 100, 2))
                        if r == 100:
                            c_name += " ⚫0%"
                        if r < 100:
                            c_name += " 🔴{}%".format(round(r - 100, 2))

                    if c_name != channel.name:
                        await channel.edit(name=c_name)
            except:
                print(s_id, "error")
                pass

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


class CryptoBot:
    cryptoBot = commands.Bot
    channels = Constants.CatPerID

    def __init__(self, bot=None):
        s2a = JoeSubGraph.s2a
        s2a.reloadAssets()
        channels = Constants.CatPerID(bot)

        pricesat0 = {}

        with open("utils/priceAt0AM.json", "r") as f:
            self.pricesat0 = json.load(f)

        self.cryptoBot = bot

        self.taskManager = TaskManager(
            (
                CryptoTicker(bot, pricesat0, s2a, channels),
                Price0Ticker(bot, pricesat0, s2a, channels),
            )
        )

    async def add(self, ctx):
        await self.taskManager.getTask("CryptoTicker").add(ctx)

    async def delete(self, ctx):
        await self.taskManager.getTask("CryptoTicker").delete(ctx)

    async def list(self, ctx):
        await self.taskManager.getTask("CryptoTicker").list(ctx)

    async def on_ready(self):
        """starts cryptobot"""
        global started

        print('cryptoBot have logged in as {0.user}'.format(self.cryptoBot))
        if not started:
            self.taskManager.start()
            started = True


if __name__ == '__main__':
    cryptoBot = CryptoBot()
