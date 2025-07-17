import logging
import os
from datetime import datetime

class Logger:
    @staticmethod
    def configurar(nome_base: str = "trader"):
        if not os.path.exists("logs"):
            os.makedirs("logs")

        data_hoje = datetime.now().strftime("%Y-%m-%d")
        nome_arquivo = f"logs/{nome_base}_{data_hoje}.log"

        # Cria logger manualmente
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # Remove handlers antigos para evitar duplicidade
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Cria handler com codificação UTF-8
        handler = logging.FileHandler(nome_arquivo, encoding='utf-8')
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    @staticmethod
    def info(msg: str):
        logging.info(msg)

    @staticmethod
    def erro(msg: str):
        logging.error(msg)

    @staticmethod
    def aviso(msg: str):
        logging.warning(msg)

    @staticmethod
    def registrar_sinal_processado(sinal: dict, status: str):
        if not os.path.exists("logs"):
            os.makedirs("logs")

        caminho = "logs/sinais_processados.log"
        with open(caminho, "a", encoding="utf-8") as f:
            linha = f"{datetime.now().isoformat()},{sinal['simbolo']},{sinal['direcao']},{sinal['preco_entrada']},{sinal['sl']},{sinal['tp']},{status}\n"
            f.write(linha)
