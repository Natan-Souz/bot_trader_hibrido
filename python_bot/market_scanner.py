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

class Ativo:
    def __init__(self, symbol_info):
        self.symbol = symbol_info.name
        self.description = symbol_info.description
        self.path = symbol_info.path.lower()
        self.tipo = self.classificar_tipo()
        self.spread = symbol_info.spread
        self.volume_ajustado = symbol_info.volume

    def classificar_tipo(self) -> str:
        if "forex" in self.path:
            return "forex"
        elif "indice" in self.path or "index" in self.path:
            return "indices"
        elif "crypto" in self.path or "cripto" in self.path:
            return "crypto"
        elif "stock" in self.path or "acoes" in self.path:
            return "acoes"
        else:
            return "outro"