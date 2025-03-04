import ccxt
import random 
from config import OKX_API_KEYS, BITGET_API_KEYS, GAS_MULT, GAS_PRICE_MULT
from utils.constants import CHAIN_MAP
from .constants import MAPPING
from loguru import logger
from web3 import AsyncWeb3
from utils.utils import async_error_handler as error_handler
from utils.utils import decimalToInt
from utils.eth_account import AccountEVM

class CexManager(AccountEVM): 

    """
    MUST MANAGE AMOUNTS BEFORE CALLING THE FUNCTIONS 
    """

    def __init__(self, private_key:str, chain_name:str, ): 

        super().__init__(chain_name, private_key)

        self._chain_name = chain_name

    @error_handler('OKX withdraw')
    async def okx_withdraw(self, token_name:str, amount:float | int): 

        """
        Token name for okx api 
        amount in human readable
        """

        logger.info(f'{self.address}: withdrawing {amount} {token_name} from OKX to {self._chain_name}')
        
        account_okx = ccxt.okx({
            'apiKey': OKX_API_KEYS[0],
            'secret': OKX_API_KEYS[1],
            'password': OKX_API_KEYS[2],
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })

        account_okx.withdraw(
            code    = token_name,
            amount  = amount,
            address = self.address,
            tag     = None, 
            params  = {
                "chain": token_name+MAPPING[self._chain_name]['okx-chain'],
                "fee":MAPPING[self._chain_name][token_name+'-fee'],
                "password":"",
                "toAddr":self.address
            }
        )
        
        logger.success(f'{self.address}: withdrawn {amount} {token_name} to {self._chain_name}')
        return 1
    
    @error_handler('BITGET withdraw')
    async def bitget_withdraw(self, token_name:str, amount:float | int): 

        dict_ = {
                'apiKey': BITGET_API_KEYS[0],
                'secret': BITGET_API_KEYS[1],
                'password': BITGET_API_KEYS[2],
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
        }

        account = ccxt.bitget(
            dict_
        )   
        logger.info(f'{self.address}: withdrawing {amount} {token_name} from BITGET to {self._chain_name}')
        account.withdraw (
            code    = token_name,
            amount  = amount,
            address = self.address,
            tag     = None, 
            params  = {
                "chain": MAPPING[self._chain_name]['bitget-chain'],
            }
        )
        logger.success(f'{self.address}: withdrawn {amount} {token_name} to {self._chain_name}')
        return 1
    
    @error_handler('deposit to exchange')
    async def deposit_to_exchange(self, token_name:str , amount: int | str): 
        """
        amount in decimals
        """
        dep_address = await self.get_deposit_wallet()

        if token_name == 'ETH': 
            if amount == 'FULL': 
                balance = await self.web3.eth.get_balance(self.address)
                priority, max_fee = await self._get_priority_fees()
                amount = int(balance - (priority * max_fee * 2))
            
            tx = {
                'from': self.address,
                'to': dep_address,
                'value': amount,
                'gas': 21_000
            }
            logger.info(f'{self.address}: sending {decimalToInt(amount)} {token_name} to {dep_address}')
            return await self.send_tx(tx)
        
        else: 
            #get contract based on self.chain_name and some MAP of chain-contracts 
            pass

