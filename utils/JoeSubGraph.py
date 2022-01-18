import json

import requests
from web3 import Web3

from utils import Constants

w3 = Web3(Web3.HTTPProvider("https://api.avax.network/ext/bc/C/rpc"))
if not w3.isConnected():
    print("Error web3 can't connect")


class Pair:
    def __init__(self, _address, _name, _token0, _token1, _reserve0, _reserve1, _reserveUSD):
        self.address = _address
        self.name = _name
        self.token0 = _token0
        self.token1 = _token1
        self.reserve0 = _reserve0
        self.reserve1 = _reserve1
        self.reserveUSD = _reserveUSD


class Pairs:
    allPairs = {}
    tokensToPairs = {}

    def addPair(self, address, token0, token1, reserve0, reserve1, reserveUSD):
        pair = Pair(
            address,
            "{}/{}".format(token0.symbol, token1.symbol),
            token0,
            token1,
            reserve0,
            reserve1,
            reserveUSD
        )
        self.allPairs[address] = pair

        if token0.address in self.tokensToPairs:
            self.tokensToPairs[token0.address].append(pair)
        else:
            self.tokensToPairs[token0.address] = [pair]

        if token1.address in self.tokensToPairs:
            self.tokensToPairs[token1.address].append(pair)
        else:
            self.tokensToPairs[token1.address] = [pair]

    def getPair(self, token0, token1):
        if token0.address > token1.address:
            token0, token1 = token1, token0
        return self.allPairs["{}/{}".format(token0, token1)]

    def getPairsFromToken(self, address):
        return self.tokensToPairs[address]


class Token:
    def __init__(self, _address, _symbol, _liquidity):
        self.address = _address
        self.symbol = _symbol
        self.liquidity = _liquidity


class Tokens:
    allTokens = {}
    symbolToToken = {}

    def addToken(self, token: Token):
        self.allTokens[token.address] = token

        symbol = token.symbol.lower().rstrip().lstrip()
        if symbol not in self.symbolToToken:
            self.symbolToToken[symbol] = token

    def getToken(self, address):
        return self.allTokens[address]

    def getTokenFromSymbol(self, symbol):
        symbol = symbol.lower().rstrip().lstrip()
        return self.symbolToToken[symbol]


pairs = Pairs()
tokens = Tokens()


def genericExchangeQuery(query):
    r = requests.post(Constants.JOE_EXCHANGE_SG_URL, json={'query': query})
    assert (r.status_code == 200)
    return json.loads(r.text)


def reloadPairs():
    global pairs, tokens
    last_id_pairs, query_exchange_pairs, reserveUSD = "", {}, 0
    while last_id_pairs == "" or len(query_exchange_pairs["data"]["pairs"]) == 1000:
        query_exchange_pairs = genericExchangeQuery(
            '{pairs(first: 1000, orderBy: reserveUSD, orderDirection: desc, where: {id_gt:"' + last_id_pairs + '"})\
                {id, token0{id, symbol, liquidity}, token1{id, symbol, liquidity}, reserve0, reserve1, reserveUSD}}')
        for pair in query_exchange_pairs["data"]["pairs"]:
            reserve0, reserve1, reserveUSD = float(pair["reserve0"]), float(pair["reserve1"]), float(pair["reserveUSD"])
            if reserveUSD == 0:
                break
            t0, t1 = pair["token0"], pair["token1"]

            if not t0["id"] in tokens.allTokens:
                tokens.addToken(Token(t0["id"], t0["symbol"], t0["liquidity"]))
            if not t1["id"] in tokens.allTokens:
                tokens.addToken(Token(t1["id"], t1["symbol"], t1["liquidity"]))

            token0, token1 = tokens.getToken(t0["id"]), tokens.getToken(t1["id"])

            address = pair["id"]

            if address not in pairs.allPairs:
                pairs.addPair(address, token0, token1, reserve0, reserve1, reserveUSD)
        last_id_pairs = str(query_exchange_pairs["data"]["pairs"][-1]["id"])
        if reserveUSD == 0:
            break
    print(len(pairs.allPairs), len(tokens.allTokens))


def getPrices(symbols):
    prices = {}
    for symbol in symbols:
        p = getPriceOf(symbol)
        prices[symbol] = p
    return prices


def getPriceOf(symbol):
    symbol = symbol.lower().replace(" ", "")
    address = s2a.getAddress(symbol)
    if address is None:
        return "Unknown Token Symbol"
    r = requests.get("https://api.traderjoexyz.com/priceusd/{}".format(address))
    assert (r.status_code == 200)
    return json.loads(r.text) / Constants.E18


def getSymbolOf(address):
    erc20_contract = w3.eth.contract(address=w3.toChecksumAddress(address), abi=Constants.ERC20_ABI)
    symbol = erc20_contract.functions.symbol().call()
    if symbol[-2:].lower() == ".e":
        symbol = symbol[:-2]
        if symbol[0].lower() == "w":
            symbol = symbol[1:]
    return symbol


class Symbol2Address:
    def __init__(self):
        self.symbol2address = {}

    def reloadAssets(self):
        last_id_pairs, queryExchange, tempdic = "", {}, {}
        while last_id_pairs == "" or len(queryExchange["data"]["tokens"]) == 1000:
            queryExchange = genericExchangeQuery(
                '{tokens(first: 1000, where: {id_gt: "' + last_id_pairs + '"}){id, symbol, liquidity, derivedAVAX}}')
            for d in queryExchange["data"]["tokens"]:
                if float(d["liquidity"]) * float(d["derivedAVAX"]) >= 100:
                    tempdic[d["symbol"].lower().replace(" ", "")] = d["id"]
            last_id_pairs = queryExchange["data"]["tokens"][-1]["id"]

        temp = {"avax": "avax"}
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

    def getAddress(self, symbol):
        if symbol in self.symbol2address:
            return self.symbol2address[symbol]
        return None

    def hasKey(self, symbol):
        if symbol in self.symbol2address or symbol == "avax":
            return True
        return False


s2a = Symbol2Address()

if __name__ == '__main__':
    s2a.reloadAssets()
    print(s2a.symbol2address)
    print(getPriceOf("sherpa"))
    print(getSymbolOf("0xa7d7079b0fead91f3e65f86e8915cb59c1a4c664"))
