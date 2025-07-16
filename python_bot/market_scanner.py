import os
import sqlite3
from typing import List, Dict
from dataclasses import dataclass
import MetaTrader5 as mt5
import pandas as pd


@dataclass
class ScannerConfig:
    max_forex: int = 5
    max_indices: int = 3
    max_crypto: int = 2
    max_acoes: int = 0
    spread_maximo: float = 40.0
    caminho_banco: str = "data/sinais.sqlite" #ajustar posteriormente para o caminho APPDATA


def calcular_volume_ajustado(simbolo: str, n_barras: int = 100) -> float:
    if not mt5.symbol_select(simbolo, True):
        return 0.0
    rates = mt5.copy_rates_from_pos(simbolo, mt5.TIMEFRAME_M5, 0, n_barras)
    if rates is None or len(rates) == 0:
        return 0.0
    df = pd.DataFrame(rates)
    return df['tick_volume'].sum()


class Ativo:
    def __init__(self, symbol_info, volume_ajustado: float = 0):
        self.symbol = symbol_info.name
        self.description = symbol_info.description
        self.path = symbol_info.path.lower()
        self.tipo = self.classificar_tipo()
        self.spread = symbol_info.spread
        self.volume_ajustado = volume_ajustado

    def classificar_tipo(self) -> str:
        if "forex" in self.path:
            return "forex"
        elif "indice" in self.path or "index" in self.path:
            return "indices"
        elif "crypto" in self.path or "cripto" in self.path:
            return "crypto"
        elif "stock" in self.path or "acoes" in self.path:
            if "usa" in self.path or "nasdaq" in self.path or "nyse" in self.path:
                return "acoes"
            else:
                return "outro"
        else:
            return "outro"


class MarketScanner:
    def __init__(self, config: ScannerConfig):
        self.config = config
        self.ativos: List[Ativo] = []

    def carregar_dados_mt5(self):
        if not mt5.initialize():
            raise RuntimeError("Erro ao inicializar conexão com o MetaTrader 5")

        ativos_mt5 = mt5.symbols_get()
        ativos_visiveis = [s for s in ativos_mt5 if s.visible]

        self.ativos = []
        for s in ativos_visiveis:
            volume = calcular_volume_ajustado(s.name, n_barras=200)
            self.ativos.append(Ativo(s, volume_ajustado=volume))

        mt5.shutdown()

    def gerar_lista_observados(self) -> Dict[str, List[Ativo]]:
        tipos = {"forex": [], "indices": [], "crypto": [], "acoes": []}
        for tipo in tipos:
            ativos_filtrados = [a for a in self.ativos if a.tipo == tipo and a.spread <= self.config.spread_maximo]
            ativos_ordenados = sorted(ativos_filtrados, key=lambda a: a.volume_ajustado, reverse=True)
            limite = getattr(self.config, f"max_{tipo}", 0)
            tipos[tipo] = ativos_ordenados[:limite]
        return tipos

    def salvar_no_banco(self):
        ativos_por_tipo = self.gerar_lista_observados()
        conn = sqlite3.connect(self.config.caminho_banco)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM ativos")

        for tipo, lista in ativos_por_tipo.items():
            for ativo in lista:
                cursor.execute(
                    """
                    INSERT INTO ativos (
                        simbolo, tipo, descricao, path, spread, volume_ajustado, observando
                    ) VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        ativo.symbol,
                        tipo,
                        ativo.description,
                        ativo.path,
                        ativo.spread,
                        float(ativo.volume_ajustado)
                    )
                )

        conn.commit()
        conn.close()
        print("✅ Ativos observados atualizados com dados completos no banco.")


if __name__ == "__main__":
    config = ScannerConfig()
    scanner = MarketScanner(config)
    scanner.carregar_dados_mt5()
    scanner.salvar_no_banco()
