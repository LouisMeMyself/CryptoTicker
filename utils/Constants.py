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


# ABI for web3
try:
    with open("abis/erc20tokenabi.json", "r") as f:
        ERC20_ABI = json.load(f)
except FileNotFoundError:
    with open("../abis/erc20tokenabi.json", "r") as f:
        ERC20_ABI = json.load(f)

# joe ticker
JOE_TICKER = {}

E18 = 10 ** 18

class CatPerID:
    def __init__(self, bot):
        self.catPerID = {}
        dic = {}
        for server in bot.guilds:
            for channel in server.channels:
                if channel.category_id is None and channel.name[:8] == "Cryptos:":
                    dic[server.id] = {}
                    dic[server.id]["category"] = channel
                    dic[server.id]["symbols"] = {}
                    break
            if "category" in dic[server.id]:
                dic[server.id]["channels"], i = {}, 0
                for channel in server.channels:
                    if channel.category_id == dic[server.id]["category"].id:
                        symbol = channel.name.split(":")[0].replace(" ", "").lower()
                        dic[server.id]["symbols"][symbol] = channel
        self.catPerID = dic
