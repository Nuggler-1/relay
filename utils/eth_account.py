
from web3 import AsyncWeb3, AsyncHTTPProvider
from config import MAX_TX_WAIT, GAS_MULT, TX_RETRIES, GAS_PRICE_MULT, RPC, USE_PROXIES_IN_WEB3
from .utils import async_error_handler as error_handler
from .utils import decimalToInt, intToDecimal, get_proxy
from .constants import ERC20_ABI, DEFAULT_DEPOSIT_ADDRESSES, DEFAULT_PRIVATE_KEYS, CHAIN_MAP, TESTNETS_CHAIN_MAP
from loguru import logger
import asyncio


class AccountEVM: 

    def __init__(self, chain_name:str, private_key: str, proxy:bool = USE_PROXIES_IN_WEB3, tx_timeout:int = MAX_TX_WAIT, testnet:bool = False):
        
        if proxy:
            proxies = get_proxy(private_key)
            self.web3 = AsyncWeb3(AsyncHTTPProvider(RPC[chain_name], request_kwargs={"proxies": proxies}))
        else: 
            self.web3 = AsyncWeb3(AsyncHTTPProvider(RPC[chain_name]))

        self._private_key = private_key
        self._account = self.web3.eth.account.from_key(private_key)
        self._tx_timeout = tx_timeout
        if testnet:
            self._eip1559 = TESTNETS_CHAIN_MAP.eip1559_chains[chain_name]
        else:
            self._eip1559 = CHAIN_MAP.eip1559_chains[chain_name]

        self.address = self._account.address
        self.proxy = proxy

    async def _get_priority_fees(self,): 

        fee_history = await self.web3.eth.fee_history(5, 'latest', [10, 20, 30])

        #average base fee
        base_fees = fee_history['baseFeePerGas']
        avg_base_fee = sum(base_fees) / len(base_fees)

        #average priority fee
        priority_fees = fee_history['reward']
        avg_priority_fee = sum([sum(rewards) / len(rewards) for rewards in priority_fees]) / len(priority_fees)

        max_fee_per_gas = (avg_base_fee + avg_priority_fee) * GAS_MULT
        max_priority_fee_per_gas = avg_priority_fee * GAS_PRICE_MULT

        return max_fee_per_gas, max_priority_fee_per_gas
    
    @error_handler('get_gas_prices')
    async def _get_gas_prices(self, tx_dict: dict = None,) -> dict: 
        
        if tx_dict is None:
            tx_dict = {}

        if self._eip1559:
            
            max_fee_per_gas, max_priority_fee_per_gas = await self._get_priority_fees()
            tx_dict['maxFeePerGas'] = int(max_fee_per_gas)
            tx_dict['maxPriorityFeePerGas'] = int(max_priority_fee_per_gas) 

            if max_priority_fee_per_gas > max_fee_per_gas: 
                tx_dict['maxPriorityFeePerGas'] = int(max_fee_per_gas)

        else: 
            
            if await self.web3.eth.chain_id == 56: #BSC
                gas_price = AsyncWeb3.to_wei(3, 'gwei')
            else:
                gas_price = await self.web3.eth.gas_price
                gas_price = int( gas_price * GAS_MULT)
            tx_dict['gasPrice'] = gas_price

        return tx_dict
    
    async def _check_transaction(self, hash_tx:str) -> int:

        tx_data = await self.web3.eth.wait_for_transaction_receipt(hash_tx, timeout=self._tx_timeout)

        if (tx_data['status'])== 1:
            logger.success(f'Transaction  {AsyncWeb3.to_hex(tx_data["transactionHash"])}')
            return 1

        elif (tx_data['status'])== 0: 
            logger.warning(f'Transaction failed  {AsyncWeb3.to_hex(tx_data["transactionHash"])}: {tx_data["logs"]}')
            return 0

    @error_handler('build_and_send_tx', retries=TX_RETRIES)
    async def build_and_send_tx(self, tx, value: int = 0, return_hash: bool = False) -> int | str:

        """tx = contract method"""
    
        gas = await tx.estimate_gas({'value':value, 'from':self.address, 'gas': 0})

        nonce = await self.web3.eth.get_transaction_count(self.address)

        tx_dict = {
                    'from':self.address,
                    'value':value,
                    'nonce':nonce,
                    'gas':gas,
                }

        tx_dict = await self._get_gas_prices(tx_dict)

        built_tx = await tx.build_transaction(
                tx_dict
            )

        signed_tx = self._account.sign_transaction(built_tx)
        hash_tx = await self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f'{self.address}: Transaction was sent')
        tx_passed = await self._check_transaction(hash_tx)

        if tx_passed == 1:
            if return_hash == False:
                return tx_passed
            else: 
                return hash_tx.hex()
        else: 
            raise Exception('Transaction failed')
    
    
    @error_handler('send tx', retries=TX_RETRIES)
    async def send_tx(self, tx_dict:dict, return_hash: bool = False, contract_deployment: bool = False) -> int | str:

        if not contract_deployment:
            tx_dict['to'] = AsyncWeb3.to_checksum_address(tx_dict['to'])
            tx_dict['value'] = int(tx_dict['value'])
        tx_dict['from'] = AsyncWeb3.to_checksum_address(tx_dict['from'])
        tx_dict['chainId'] = await self.web3.eth.chain_id

        try: 
            tx_dict['gas'] = int(tx_dict['gas'])
        except:
            gas = await self.web3.eth.estimate_gas(tx_dict)
            tx_dict['gas'] = gas 

        nonce = await self.web3.eth.get_transaction_count(self.address)

        tx_dict['nonce'] = nonce

        tx_dict = await self._get_gas_prices(tx_dict)
        signed_tx = self._account.sign_transaction(tx_dict)
        hash_tx = await self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f'{self.address}: Transaction was sent')
        tx_passed = await self._check_transaction( hash_tx)

        if tx_passed == 1:
            if return_hash == False:
                return tx_passed
            else: 
                return hash_tx.hex()
        else: 
            raise Exception('Transaction failed')
        
    """
    error_handler('gas waiter')
    async def wait_for_gas(self, ): 

        while True: 
            
            try: 
                if await self.web3.eth.gas_price < AsyncWeb3.to_wei(MAX_ETH_GWEI, 'gwei'): 
                    return  
                logger.info(f'Waiting for gas to drop. Current {AsyncWeb3.from_wei(await self.web3.eth.gas_price, "gwei")}')

            except: 
                pass 

            await asyncio.sleep(20)
    """

    @error_handler('get_erc20_balance')
    async def get_erc20_balance(self, token_address:str, fixed_decimal:bool = False, return_decimal:bool = False) -> float | tuple[int,int]: 

        """
        token_address: str = token address 

        returns balance in human readable format or tuple(balance, decimals)
        """

        contract = self.web3.eth.contract(address = token_address, abi = ERC20_ABI)
        balance = await contract.functions.balanceOf(self.address).call()

        if fixed_decimal == False: 
            decimals = await contract.functions.decimals().call()
            balance = decimalToInt(balance,decimals)

        if return_decimal == True:
            decimals = await contract.functions.decimals().call()
            return balance, decimals
        else: 
            return balance
        
    async def get_erc20_decimals(self,token_address:str):
        contract = self.web3.eth.contract(address = token_address, abi = ERC20_ABI)
        decimals = await contract.functions.decimals().call()
        return decimals
    
    async def get_deposit_wallet(self,deposit_addresses_path:str = DEFAULT_DEPOSIT_ADDRESSES):

        with open(deposit_addresses_path, 'r') as f: 
            dep_addresses = f.read().splitlines()

        with open(DEFAULT_PRIVATE_KEYS, 'r') as f: 
            privates = f.read().splitlines()
                
        assert len(privates) == len(dep_addresses), 'Amount of private keys is not the same as amount of deposit addresses. Please check'

        n = privates.index(str(self._private_key))
        dep_address = dep_addresses[n]

        return AsyncWeb3.to_checksum_address(dep_address)
    
    @error_handler('approve')    
    async def approve(self, approving_token: str, approve_receiver: str, amount:int, approve_max:bool = False): #amount в decimal

        """
        approving_token: str = token address

        approve_receiver: str = address to approve

        amount: int = amount to approve in human readable format

        approve_max: bool = approve max or approve amount 

        """

        contract = self.web3.eth.contract(address = approving_token, abi = ERC20_ABI)

        allowance = await contract.functions.allowance(self.address, approve_receiver).call()
        decimals = await contract.functions.decimals().call()
        amount = intToDecimal(amount, decimals)

        if allowance < amount: 
            logger.info(f'{self.address}: Approving tokens')
            
            if approve_max == True: 
                amount = (2 ** 256 - 1)
            
            approve_tx = contract.functions.approve(approve_receiver,amount)
            tx = await self.build_and_send_tx(approve_tx)

            return tx
        
        else: 
            logger.info(f'{self.address}: Approve not needed')
            return 2

            
    