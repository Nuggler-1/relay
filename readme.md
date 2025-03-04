### Установка

Убедись, что у тебя установлена версия python==3.11

Клонируй/скачай репозиторий и установи зависимости:

`git clone https://github.com/Nuggler-1/relay.git`

`cd relay`

`pip install -r requirements.txt`

### Конфигурация

В папке `user_files` заполни файлы `private_keys.txt`, `deposit_addresses.txt` и `proxies.txt` 

*прокси в формате user:pass@ip:port*

**Не забудь добавить API-ключ от OKX и BITGET в `config.py` если собираешься использовать деп**

Заходишь в конфиг и смотришь все настройки, там все максимально понятно подписано.

*Меняешь под себя* 

### Режимы работы

**— Deposit from CEX** <br>
Загонит на кошельки валюту с указанной биржи в указанном объеме.<br>
*Не забудь указать апи ключи в конфиге*

**— Withdraw to CEX** <br>
Выведет эфир с кошельков на указанные депозит адреса (можно туда засунуть любой адрес по-сути).<br>
*Депозит адреса указать 1 к 1 с приватниками в deposit_addresses.txt*

**— Bridge ETH** <br>
Будет бриджить эфир на загруженных кошельках по указанному маршруту.<br>
*Можно зайти по пути utils/constants.py и отредактировать CHAIN_MAP чтобы добавить нужные вам сети <br>(chain id есть на chainlist.org)*

### Запуск

`python main.py`

### Связь 📞

Личка: https://t.me/fttavk

Telegram channel: https://t.me/fttavksoft