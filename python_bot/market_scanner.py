import os 
import sqlite3
from typing import List, Dict
from dataclasses import dataclass
import MetaTrader5 as mt5

@dataclass
class ScannerConfig:
    max_forex: int = 5
    max_indices: int = 3
    max_crypto: int = 2
    max_acoes: int = 0
    spread_maximo: float = 20.0
    caminho_banco: str = "data/sinais.sqlite" #alterar para o banco de dados do APPDATA para se comunicar diretamente com o metatrader
    