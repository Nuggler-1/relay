
# Использовать ли прокси при обращении к блокчейну (RPC)
USE_PROXIES_IN_WEB3 = False

#Рандомная задержка в указанном диапазоне (в секундах) между действиями
ACTIONS_DELAY = [1,2]
#Рандомная задержка в указанном диапазоне (в секундах) между аккаунтами
ACCOUNTS_DELAY = [1,2]

#Перемешивать ли порядок кошельков
RANDOMIZE = False

# Как софт будет воспринимать вводимые значения для действий с балансом кошелька (свапы/ликва/отправки и тд)
# Absolute - случайное значение в указанном диапазоне
# Percent - случайный процент от баланса в указанном диапазоне
AMOUNT_TYPE = 'Percent' 

#Ключи от ОКХ
OKX_API_KEYS = [
    'public',
    'private', 
    'passphrase'
]

#Ключи от битгет
BITGET_API_KEYS = [
    'public',
    'private', 
    'passphrase'
]

#RPC Для каждой сети. Менять если хотите свои или если что-то сломалось
RPC = {
    'ARBITRUM': 'https://arbitrum-one-rpc.publicnode.com',
    'OPTIMISM': 'https://optimism.lava.build',
    'BNB': 'https://bsc-rpc.publicnode.com',
    'TAIKO': 'https://rpc.taiko.xyz',
    'REYA': 'https://rpc.reya.network',
    'ZORA': 'https://rpc.zora.energy',
    'MODE': 'https://1rpc.io/mode',
    'LINEA': 'https://linea-rpc.publicnode.com',
    'INK': 'https://rpc-gel.inkonchain.com',
    'SONEIUM': 'https://rpc.soneium.org',
    'UNICHAIN': 'https://mainnet.unichain.org',
    'BLAST': 'https://rpc.blast.io',
    'ETHEREUM': 'https://gateway.tenderly.co/public/mainnet',
    'BASE': 'https://base.blockpi.network/v1/rpc/public'
}

#Можно поиграться с этими настройками если очень хочется
ERR_ATTEMPTS = 3
TX_RETRIES = 3
MAX_TX_WAIT = 500
GAS_MULT = 1.2
GAS_PRICE_MULT = 1.5


