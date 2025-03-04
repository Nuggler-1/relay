from utils.eth_account import AccountEVM
from utils.constants import CHAIN_MAP, ZERO_ADDRESS
from .constants import RELAY_URL
from config import RPC
from utils.utils import async_error_handler, error_handler, decimalToInt
from loguru import logger
from web3 import AsyncWeb3
import requests 

class Bridge(AccountEVM):

    """
    MUST MANAGE AMOUNT BEFORE CALLING THE FUNCTIONS 
    """

    def __init__(self,chain_from: str, chain_to:str, private_key:str, proxy: dict | None = None):
        
        self._chain_from = chain_from
        self._chain_to = chain_to
        super().__init__(chain_from, private_key)

    #Если юзер хочет пулять ерс20 то пусть сам пихает контракт на вход и выход. Иначе мы юзаем эфир
    @error_handler("quoting relay API")
    def _quote_tx_data(self, amount: int, from_contract: str = ZERO_ADDRESS, to_contract: str = ZERO_ADDRESS):

        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'referer': f'https://relay.link/bridge/{self._chain_from.lower()}?fromChainId={CHAIN_MAP.nameToId[self._chain_from]}&fromCurrency={from_contract}&toCurrency={to_contract}'
        }

        body = {
            'amount': amount, 
            'destinationChainId':CHAIN_MAP.nameToId[self._chain_to],
            'destinationCurrency': to_contract,
            'originChainId': CHAIN_MAP.nameToId[self._chain_from],
            'originCurrency': from_contract, 
            'recipient':self.address,
            'refferer': 'relay.link/swap',
            'tradeType': 'EXACT_INPUT',
            'useExternalLiquidity': False,
            'user': self.address
        }

        with requests.Session() as s:
            response = s.post(RELAY_URL+'quote', headers=headers, json=body, proxies=self.proxy)
            if response.status_code == 200:
                return response.json()['steps'][0]['items'][0]['data']
            else:
                print(body)
                print(response.content)
                if response.status_code == 400: 
                    try: 
                        msg = response.json()['message']
                        raise Exception(msg)
                    except:
                        pass
                response.raise_for_status()

    async def bridge(self, amount:int,  from_contract:str = ZERO_ADDRESS, to_contract: str = ZERO_ADDRESS): 

        """amount in decimals"""
        
        logger.info(f'{self.address}: bridging {decimalToInt(amount,18)} ETH from {self._chain_from} to {self._chain_to} via Relay')

        tx = self._quote_tx_data(amount, from_contract, to_contract)
        if not tx: 
            logger.warning(f'{self.address}: failed to get tx data from API')
            return 0
        
        return await self.send_tx(tx)



    



