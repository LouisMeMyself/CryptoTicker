import json

# Roles
ROLE_FOR_CMD = 833627278760083466

# Commands
DELETE_CMD = "!delete"
ADD_CMD = "!add"

# SubGraph links
JOE_EXCHANGE_SG_URL = "https://api.thegraph.com/subgraphs/name/traderjoe-xyz/exchange"

# address for web3
ADDRESS = {}

# joe ticker
JOE_TICKER = {}

E18 = 10 ** 18

class CatPerID:
    def __init__(self, bot):
        self.catPerID = {}
        for server in bot.guilds:
            dic = {}
            for channel in server.channels:
                if channel.category_id is None and channel.name == "Cryptos":
                    dic["category"] = channel
                    dic["symbols"] = {}
                    break
            if "category" in dic:
                dic["channels"], i = {}, 0
                for channel in server.channels:
                    if channel.category_id == dic["category"].id:
                        symbol = channel.name.split(":")[0].replace(" ", "").lower()
                        dic["symbols"][symbol] = channel
                self.catPerID[server.id] = dic
