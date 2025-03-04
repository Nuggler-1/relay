from runner.runner import Runner
from utils.constants import DEFAULT_PRIVATE_KEYS, logo, PROJECT
from loguru import logger 
import sys 

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> |  <level>{message}</level>",
    colorize=True
)

def main(): 
    with open(DEFAULT_PRIVATE_KEYS, 'r', encoding = 'utf-8') as f: 
        private_keys = f.read().splitlines()
    runner = Runner(private_keys)
    logger.opt(raw=True).info(logo)
    logger.opt(raw=True, colors=True).info(f"<lm>{PROJECT}</lm>")
    runner.run_interface()

if __name__ == '__main__': 
    main()