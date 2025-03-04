
from relay.bridge import Bridge as RelayBridge
from exchange.manager import CexManager
from utils.constants import DEFAULT_PRIVATE_KEYS, CHAIN_MAP
from utils.eth_account import AccountEVM
from utils.utils import round_decimal_value, intToDecimal, sync_sleep, sleep, async_error_handler 
from config import RANDOMIZE, ACCOUNTS_DELAY, RPC, AMOUNT_TYPE, ACTIONS_DELAY

from typing import Literal
from loguru import logger
from eth_account import Account
import asyncio

import random 
import sys
import questionary

class Runner(): 

    def __init__(self,private_keys:list): 

        self.private_keys = private_keys

        if RANDOMIZE: 
            random.shuffle(self.private_keys)
    
    async def _generate_amount(
        self,
        private_key:str, 
        chain_name:str, 
        amount_range: list[int|float], 
        amount_type: Literal['Percent', 'Absolute'] = AMOUNT_TYPE, 
        token_address: str | None = None
    ): 

        """
        if no token address then native
        amount either in absolute(human readable) or percent 
        """
        account = AccountEVM(chain_name, private_key)

        if token_address: 
            balance, decimals = await account.get_erc20_balance(token_address, fixed_decimal=True, return_decimal=True)
        else: 
            balance = await account.web3.eth.get_balance(account.address)
            decimals = 18
        if balance == 0:
            raise Exception(f'{account.address}: Account balance is 0')
        
        match amount_type: 
            case 'Percent': 
                if amount_range[0] == 100: 
                    return balance
                percent = random.uniform(*amount_range) if amount_range[0] != amount_range[1] else amount_range[0]
                amount_spent = balance * percent/100
                amount_spent = round_decimal_value(amount_spent, random.randrange(2,4))
            case 'Absolute': 
                amount = random.uniform(*amount_range) if amount_range[0] != amount_range[1] else amount_range[0]
                amount = intToDecimal(amount, decimals)
                amount_spent = round_decimal_value(amount, random.randrange(2,4))
                if amount > balance: 
                    raise f'{account.address}: Amount specified in settings is larger than account balance'
                
        return amount_spent

    @async_error_handler('bridge runner function', retries=1)
    async def _single_bridge(
        self,
        private_key:str, 
        chain_from: str, 
        chain_to:str, 
        amount_range:list[float | int], 
    ):
        
        bridge = RelayBridge(chain_from, chain_to, private_key)   
        amount = await self._generate_amount(private_key, chain_from, amount_range)    
        return await bridge.bridge(amount)

    @async_error_handler('cex deposit runner function', retries=1)
    async def _single_deposit_from_cex(
        self,
        private_key: str, 
        amount_range: list[float | int], 
        chain_to:str, 
        token_name: Literal['ETH', 'USDC', 'USDT'] ,
        exchange_name: Literal['OKX', 'Bitget']
    ): 

        manager = CexManager(private_key, chain_to)
        amount = random.uniform(*amount_range)

        if token_name == 'ETH': 
            amount = round(amount, random.randrange(3,5))
        else: 
            amount = round(amount, random.randrange(1,3))

        if exchange_name == 'OKX': 
            return await manager.okx_withdraw(token_name, amount)
        else: 
            return await manager.bitget_withdraw(token_name, amount)
    
    @async_error_handler('cex withdraw runner function', retries=1)
    async def _single_withdraw_from_account(
        self,
        private_key: str, 
        amount_range: list[float | int] | str, 
        chain_from:str, 
        token_name: Literal['ETH', 'USDC', 'USDT'] = 'ETH' , # добавить поддержку Стейблов
    ): 

        manager = CexManager(private_key, chain_from)
        if amount_range != 'FULL':
            amount = await self._generate_amount(private_key, chain_from, amount_range)
        else: 
            amount = 'FULL'

        return await manager.deposit_to_exchange(token_name, amount)
    
    def run_interface(self,): 

        if len(self.private_keys) == 0: 
            logger.warning('Please upload at least one private key!')
            sys.exit()

        while True:

            choice = questionary.select(
                        "Select work mode:",
                        choices=[
                            "Deposit from CEX", 
                            "Withdraw to CEX",
                            "Bridge ETH",
                            "Run range of wallets", 
                            "Run specific wallets",
                            "Reset selction of wallets",
                            "Exit"
                        ]
                    ).ask()
            
            try:
                    
                match choice: 

                    case "Deposit from CEX":

                        cex_name = questionary.select(
                            "choose what exchange to use:",
                            choices=['Bitget', 'OKX']
                        ).unsafe_ask()
                        token_name = questionary.select(
                            "choose token to deposit", 
                            choices=['ETH', 'USDT', 'USDC']
                        ).unsafe_ask()
                        choices=['LINEA'] if token_name == 'ETH' else [] 
                        choices.extend(['ARBITRUM', 'OPTIMISM', 'BASE', 'ETHEREUM'])
                        chain_name = questionary.select(
                            "choose chain:",
                            choices=choices
                        ).unsafe_ask()
                        min_amount = float(
                            questionary.text(f'Input min absolute amount to withdraw: ').unsafe_ask()
                        )
                        max_amount = float(
                            questionary.text(f'Input max absolute amount to withdraw: ').unsafe_ask()
                        )
                        logger.info('Starting withdraw')

                        for private_key in self.private_keys:
                            asyncio.run(self._single_deposit_from_cex(
                                private_key, [min_amount, max_amount], chain_name, token_name, cex_name
                            ))
                            if private_key != self.private_keys[-1]:
                                sync_sleep('Account')

                    case "Withdraw to CEX": 

                        token_name = questionary.select(
                            "choose token to withdraw (Currently only ETH supported)", 
                            choices=['ETH']
                        ).unsafe_ask()
                        choices=['LINEA'] if token_name == 'ETH' else [] 
                        choices.extend(['ARBITRUM', 'OPTIMISM', 'BASE', 'ETHEREUM'])
                        chain_name = questionary.select(
                            "choose chain:",
                            choices=choices
                        ).unsafe_ask()
                        min_amount = float(
                            questionary.text(f'Input min {AMOUNT_TYPE.lower()} amount to withdraw: ').unsafe_ask()
                        )
                        max_amount = float(
                            questionary.text(f'Input max {AMOUNT_TYPE.lower()} amount to withdraw: ').unsafe_ask()
                        )
                        logger.info('Starting withdraw')
                        if min_amount == 100 and AMOUNT_TYPE == 'Percent': 
                            amount_range = 'FULL'
                        else: 
                            amount_range = [min_amount, max_amount]

                        for private_key in self.private_keys:
                            asyncio.run(self._single_withdraw_from_account(
                                private_key, amount_range, chain_name, token_name
                            ))
                            if private_key != self.private_keys[-1]:
                                sync_sleep('Account')
                        
                    case "Bridge ETH": 
                        
                        chain_choices = list(CHAIN_MAP.nameToId.keys())
                        chain_from = questionary.select(
                            "choose chain from:", 
                            choices=chain_choices
                        ).unsafe_ask()
                        chain_choices.remove(chain_from)
                        chain_to = questionary.select(
                            "choose chain to:",
                            choices=chain_choices
                        ).unsafe_ask()
                        min_amount = float(
                            questionary.text(f'Input min {AMOUNT_TYPE.lower()} amount to bridge: ').unsafe_ask()
                        )
                        max_amount = float(
                            questionary.text(f'Input max {AMOUNT_TYPE.lower()} amount to bridge: ').unsafe_ask()
                        )
                        logger.info('Starting bridge')

                        for private_key in self.private_keys:
                            asyncio.run(self._single_bridge(
                                private_key, chain_from, chain_to, [min_amount, max_amount]
                            ))
                            if private_key != self.private_keys[-1]:
                                sync_sleep('Account')

                    case "Run specific wallets": 
                        while True: 
                            addresses = [Account.from_key(private_key).address for private_key in self.private_keys]
                            choice = questionary.checkbox(
                                "Select wallets to run:",
                                choices=[
                                    *addresses
                                ]
                            ).unsafe_ask()


                            if len(choice) == 0: 
                                logger.warning('Please select at least one wallet (USE SPACE TO SELECT)')
                                continue    

                            new_private_keys = []
                            for address in choice: 
                                index = addresses.index(address)
                                new_private_keys.append(self.private_keys[index])

                            self.private_keys = new_private_keys
                            break

                    case "Run range of wallets": 

                        while True: 

                            addresses = [Account.from_key(private_key).address for private_key in self.private_keys]
                            choice = questionary.checkbox(
                                "Select range of wallets to run (first and last):",
                                choices=[
                                    *addresses
                                ]
                            ).unsafe_ask()

                            if len(choice) !=  2: 
                                logger.warning('Please select first and last wallet in range (ONLY 2 WALLETS)')
                                continue

                            first_index = addresses.index(choice[0])
                            last_index = addresses.index(choice[1])

                            self.private_keys = self.private_keys[first_index:last_index+1]
                            break
                    
                    case "Reset selection of wallets": 

                        with open(DEFAULT_PRIVATE_KEYS, 'r', encoding='utf-8') as f: 
                            self.private_keys = f.read().splitlines()

                    case "Exit": 
                        sys.exit()

                    case _:
                        pass

            except KeyboardInterrupt:
                logger.info("exiting to main menu")
                continue