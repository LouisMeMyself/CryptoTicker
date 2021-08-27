import asyncio
import json, requests

from web3 import Web3
from utils import Constants
from utils.beautify_string import readable, human_format


async def genericExchangeQuery(query):
    r = requests.post(Constants.JOE_EXCHANGE_SG_URL, json={'query': query})
    assert (r.status_code == 200)
    return json.loads(r.text)


async def getAvaxPrice():
    query = await genericExchangeQuery("{bundles {avaxPrice}}")
    return float(query["data"]["bundles"][0]["avaxPrice"])


async def getPrices(symbols):
    prices = {}
    for symbol in symbols:
        p = await getPriceOf(symbol)
        prices[symbol] = p
    return prices


async def getPriceOf(symbol):
    symbol = symbol.lower().replace(" ", "")
    if symbol == "avax":
        return await getAvaxPrice()
    address = s2a.getAdress(symbol)
    if address is None:
        return "Unknown Token Symbol"
    query = await genericExchangeQuery('{token(id: "' + address + '") {derivedAVAX}}')
    avaxPrice = await getAvaxPrice()
    derivedAvax = float(query["data"]["token"]["derivedAVAX"])
    return avaxPrice * derivedAvax


class Symbol2Address():
    def __init__(self):
        self.symbol2address = {}

    async def reloadAssets(self):
        skip, queryExchange, tempdic = 0, {}, {}
        while skip == 0 or len(queryExchange["data"]["tokens"]) == 1000:
            queryExchange = await genericExchangeQuery(
                "{tokens(first: 1000, skip: " + str(skip) + "){id, symbol, liquidity, derivedAVAX}}")
            for d in queryExchange["data"]["tokens"]:
                if float(d["liquidity"]) * float(d["derivedAVAX"]) >= 100:
                    tempdic[d["symbol"].lower().replace(" ", "")] = d["id"]
            skip += 1000

        temp = {}
        for key, value in tempdic.items():
            if key[0] == "w" and key[-2:] == ".e":
                temp[key[1:-2]] = value
            elif key[-2:] == ".e":
                temp[key[:-2]] = value
            elif key in temp:
                pass
            else:
                temp[key] = value
        self.symbol2address = temp

    def getAdress(self, symbol):
        if symbol in self.symbol2address:
            return self.symbol2address[symbol]
        return None

    def hasKey(self, symbol):
        if symbol in self.symbol2address or symbol == "avax":
            return True
        return False


s2a = Symbol2Address()

if __name__ == '__main__':
    asyncio.run(s2a.reloadAssets())
    print(s2a.symbol2address)
