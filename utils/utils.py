from loguru import logger
from config import ERR_ATTEMPTS, ACCOUNTS_DELAY, ACTIONS_DELAY
from .constants import DEFAULT_PRIVATE_KEYS, DEFAULT_PROXIES
import sys
import time
import asyncio
import random
from typing import Literal

def intToDecimal(qty, decimal):
    return int(qty * int("".join(["1"] + ["0"]*decimal)))

def decimalToInt(price, decimal):
    return price/ int("".join((["1"]+ ["0"]*decimal)))



def round_decimal_value(value:int, rounding:int): 

    value = int(value)
    l = len(str(value))

    value = str(value)[:rounding] 
    if int(value[-1]) > 5: 
        value = int(value)+1

    while len(str(value)) < l: 
        value = str(value) + "0"

    return int(value)

def pad32Bytes(data):
      
      s = data[2:] if data[:2] == '0x' else data
      while len(s) < 64 :
        s = "0" + s
      return s

def error_handler(error_msg, retries = ERR_ATTEMPTS):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(0, retries):
                try: 
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"{error_msg}: {str(e)[:100]}")
                    logger.info(f'Retrying in 10 sec. Attempts left: {ERR_ATTEMPTS-i}')
                    time.sleep(10)
                    if i == retries-1: 
                        return 0
        return wrapper
    return decorator

def get_proxy(private_key): 

    check_proxy()

    with open(DEFAULT_PROXIES, 'r') as f: 
        proxies = f.read().splitlines()
        if len(proxies) == 0:
            return None
        
    with open(DEFAULT_PRIVATE_KEYS, 'r') as f: 
        privates = f.read().splitlines()
            
    n = privates.index(str(private_key))
    proxy = proxies[n]
    proxy = {
        'http': f'http://{proxy}',
        'https':f'http://{proxy}'
    }
    return proxy

def check_proxy():

    with open(DEFAULT_PROXIES, 'r') as f: 
        proxies = f.read().splitlines()
    with open(DEFAULT_PRIVATE_KEYS, 'r') as f: 
        stark_privates = f.read().splitlines()

    if len(proxies) < len(stark_privates) and len(proxies) != 0:
        logger.error('Proxies do not match private keys')
        sys.exit()

def async_error_handler(error_msg, retries=ERR_ATTEMPTS):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for i in range(0, retries):
                try:
                    return await func(*args, **kwargs)
                
                except TimeoutError as e:
                    logger.error(f"{error_msg}: TimeoutError - {str(e)[:250]}")
                    if i == retries - 1:
                        return 0
                    logger.info(f"TimeoutError: Retrying in 10 sec. Attempts left: {retries-i-1}")
                    await asyncio.sleep(10)

                except Exception as e:
                    logger.error(f"{error_msg}: {str(e)}")
                    if i == retries - 1:
                        return 0
                    logger.info(f"Retrying in 10 sec. Attempts left: {retries-i-1}")
                    await asyncio.sleep(10)
                    
        return wrapper
    return decorator

async def sleep(type_delay = Literal['Account', 'Action'], account_address: str | None = None): 
    match type_delay: 
        case 'Account': 
            sleep_time = ACTIONS_DELAY
        case 'Action': 
            sleep_time = ACCOUNTS_DELAY
        case _: 
            raise Exception('Wrong sleep type in delay function (async sleep)')
    sleep_time = random.uniform(*sleep_time)
    logger.info(f'{account_address if account_address else ""}: waiting {int(sleep_time)} seconds before next {type_delay}')
    await asyncio.sleep(sleep_time)

def sync_sleep(type_delay = Literal['Account', 'Action'], account_address: str | None = None): 
    match type_delay: 
        case 'Account': 
            sleep_time = ACTIONS_DELAY
        case 'Action': 
            sleep_time = ACCOUNTS_DELAY
        case _: 
            raise Exception('Wrong sleep type in delay function (async sleep)')
    sleep_time = random.uniform(*sleep_time)
    logger.info(f'{account_address + ":" if account_address else ""} waiting {int(sleep_time)} seconds before next {type_delay}')
    time.sleep(sleep_time)